import asyncio
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from pymongo.errors import ConfigurationError, OperationFailure, ServerSelectionTimeoutError


fake_config = ModuleType("backend.config")
fake_config.settings = SimpleNamespace(MONGO_URI="mongodb://localhost:27017/education_platform")
module_spec = importlib.util.spec_from_file_location(
    "database_under_test", Path(__file__).resolve().parents[1] / "backend" / "database.py"
)
database_module = importlib.util.module_from_spec(module_spec)
with patch.dict("sys.modules", {"backend.config": fake_config}):
    module_spec.loader.exec_module(database_module)


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings = SimpleNamespace(MONGO_URI="mongodb://localhost:27017/education_platform")
        self.settings_patch = patch.object(database_module, "settings", self.settings)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.client_factory_patch = patch.object(database_module, "AsyncIOMotorClient")
        self.client_factory = self.client_factory_patch.start()
        self.addCleanup(self.client_factory_patch.stop)
        self.client = self.client_factory.return_value
        self.database = self.client.get_default_database.return_value
        self.database.command = AsyncMock(return_value={"ok": 1})
        self.database.__bool__.side_effect = NotImplementedError("Database truth testing is invalid")
        self.client.__bool__.return_value = False
        self.manager = database_module.Database()

    def client_options(self):
        return self.client_factory.call_args.kwargs

    def test_local_connection_has_bounded_timeouts_without_tls(self):
        self.assertIs(self.manager.connect(), self.database)
        options = self.client_options()
        self.assertEqual(options["serverSelectionTimeoutMS"], 5000)
        self.assertEqual(options["connectTimeoutMS"], 5000)
        self.assertEqual(options["socketTimeoutMS"], 10000)
        self.assertEqual(options["waitQueueTimeoutMS"], 5000)
        self.assertEqual(options["timeoutMS"], 15000)
        self.assertFalse(options["tls"])
        self.assertNotIn("tlsCAFile", options)
        self.database.command.assert_not_called()
        self.database.__getitem__.assert_not_called()

    def test_timeout_settings_override_defaults(self):
        for setting_name, option, default in database_module.TIMEOUT_SETTINGS:
            setattr(self.settings, setting_name, default + 123)
        self.settings.MONGO_PING_TIMEOUT_MS = 999
        self.manager.connect()
        for setting_name, option, default in database_module.TIMEOUT_SETTINGS:
            self.assertEqual(self.client_options()[option], default + 123)
        self.assertEqual(self.manager._ping_timeout_ms, 999)

    def test_invalid_timeout_does_not_create_client(self):
        setting_names = [name for name, option, default in database_module.TIMEOUT_SETTINGS]
        setting_names.append("MONGO_PING_TIMEOUT_MS")
        for setting_name in setting_names:
            for value in (0, -1, True, None, "5000", 1.5):
                with self.subTest(setting=setting_name, value=value):
                    setattr(self.settings, setting_name, value)
                    with self.assertRaisesRegex(RuntimeError, "initialization failed"):
                        self.manager.connect()
                    self.client_factory.assert_not_called()
                    self.assertIsNone(self.manager.client)
                    self.assertIsNone(self.manager.db)
            delattr(self.settings, setting_name)

    def test_atlas_and_srv_enable_verified_tls(self):
        uris = (
            "mongodb+srv://example.mongodb.net/education_platform",
            "mongodb://example.mongodb.net:27017/education_platform",
            "mongodb://first.mongodb.net:27017,second.mongodb.net:27017/education_platform",
            "mongodb+srv://mongo.example.test/education_platform",
        )
        with patch.object(database_module.certifi, "where", return_value="trusted-ca.pem"):
            for uri in uris:
                with self.subTest(uri=uri):
                    self.settings.MONGO_URI = uri
                    self.manager.connect()
                    self.assertTrue(self.client_options()["tls"])
                    self.assertEqual(self.client_options()["tlsCAFile"], "trusted-ca.pem")
                    self.manager.disconnect()

    def test_local_tls_opt_in_and_custom_ca(self):
        for query in ("tls=true", "SSL=true", "tlsCAFile=custom-ca.pem"):
            with self.subTest(query=query):
                self.settings.MONGO_URI = "mongodb://localhost:27017/app?" + query
                self.manager.connect()
                self.assertTrue(self.client_options()["tls"])
                if "tlsCAFile" in query:
                    self.assertNotIn("tlsCAFile", self.client_options())
                self.manager.disconnect()

    def test_local_and_non_atlas_srv_can_explicitly_disable_tls(self):
        for uri in ("mongodb://[::1]:27017/app?tls=false", "mongodb+srv://mongo.example.test/app?ssl=false"):
            with self.subTest(uri=uri):
                self.settings.MONGO_URI = uri
                self.manager.connect()
                self.assertFalse(self.client_options()["tls"])
                self.assertNotIn("tlsCAFile", self.client_options())
                self.manager.disconnect()

    def test_tls_host_detection_ignores_credentials_and_similar_domains(self):
        self.settings.MONGO_URI = "mongodb://name.mongodb.net:<placeholder>@mongodb.net.example.test/app"
        self.manager.connect()
        self.assertFalse(self.client_options()["tls"])

    def test_invalid_or_insecure_uri_rejected_without_exposing_details(self):
        uris = (
            "https://mongo.example.test/app",
            "mongodb:///app",
            "mongodb://[bad/app",
            "mongodb+srv://example.mongodb.net/app?tls=false",
            "mongodb://example.mongodb.net/app?SSL=false",
            "mongodb://localhost/app?tls=invalid",
            "mongodb://localhost/app?tls=true&ssl=false",
            "mongodb://localhost/app?tls=true&tls=false",
            "mongodb://localhost/app?tlsInsecure=true",
            "mongodb://localhost/app?tlsAllowInvalidCertificates=true",
            "mongodb://localhost/app?tlsAllowInvalidHostnames=true",
        )
        for uri in uris:
            with self.subTest(uri=uri):
                self.settings.MONGO_URI = uri
                with self.assertRaisesRegex(RuntimeError, "initialization failed") as caught:
                    self.manager.connect()
                self.assertNotIn(uri, str(caught.exception))
                self.client_factory.assert_not_called()

    def test_database_name_is_selected_by_driver(self):
        for uri in (
            "mongodb://localhost:27017",
            "mongodb://localhost:27017/?authSource=admin",
            "mongodb://localhost:27017/app?authSource=admin",
            "mongodb://localhost:27017/my%2Dapp",
        ):
            with self.subTest(uri=uri):
                self.settings.MONGO_URI = uri
                self.manager.connect()
                self.client_factory.assert_called_with(uri, **self.client_options())
                self.client.get_default_database.assert_called_with(default="education_platform")
                self.manager.disconnect()

    def test_connect_and_disconnect_are_idempotent(self):
        self.manager.disconnect()
        self.manager.connect()
        self.manager.connect()
        self.client_factory.assert_called_once()
        self.manager.disconnect()
        self.manager.disconnect()
        self.client.close.assert_called_once()
        self.assertIsNone(self.manager.client)
        self.assertIsNone(self.manager.db)

    def test_restart_uses_fresh_client(self):
        second_client = MagicMock()
        self.client_factory.side_effect = (self.client, second_client)
        self.manager.connect()
        self.manager.disconnect()
        self.manager.connect()
        self.assertIs(self.manager.client, second_client)
        self.assertIs(self.manager.db, second_client.get_default_database.return_value)
        self.client.close.assert_called_once()

    def test_failed_initialization_is_sanitized_and_can_be_retried(self):
        self.client_factory.side_effect = ConfigurationError("sensitive connection details")
        with self.assertRaisesRegex(RuntimeError, "initialization failed") as caught:
            self.manager.connect()
        self.assertNotIn("sensitive", str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)
        self.assertIsNone(self.manager.client)
        self.assertIsNone(self.manager.db)
        self.client_factory.side_effect = None
        self.manager.connect()
        self.assertIs(self.manager.client, self.client)

    def test_database_selection_failure_closes_partial_client(self):
        self.client.get_default_database.side_effect = ConfigurationError("sensitive details")
        with self.assertRaisesRegex(RuntimeError, "initialization failed"):
            self.manager.connect()
        self.client.close.assert_called_once()
        self.assertIsNone(self.manager.client)
        self.assertIsNone(self.manager.db)

    def test_cleanup_failure_leaves_cleared_handles(self):
        self.manager.connect()
        self.client.close.side_effect = RuntimeError("sensitive details")
        with self.assertRaisesRegex(RuntimeError, "client cleanup failed") as caught:
            self.manager.disconnect()
        self.assertNotIn("sensitive", str(caught.exception))
        self.assertIsNone(self.manager.client)
        self.assertIsNone(self.manager.db)
        self.manager.disconnect()

    async def test_uninitialized_or_disconnected_manager_is_not_ready(self):
        self.assertFalse(await self.manager.is_ready())
        self.manager.connect()
        self.manager.disconnect()
        self.assertFalse(await self.manager.ping())
        self.database.command.assert_not_called()

    async def test_readiness_checks_are_fresh_and_use_selected_database(self):
        self.manager.connect()
        self.assertTrue(await self.manager.ping())
        self.assertTrue(await self.manager.is_ready())
        self.assertEqual(self.database.command.await_count, 2)
        self.database.command.assert_awaited_with("ping")
        self.client.admin.command.assert_not_called()

    async def test_ping_failure_recovers_without_replacing_client(self):
        self.manager.connect()
        self.database.command.side_effect = (
            ServerSelectionTimeoutError("sensitive topology details"),
            {"ok": 1},
        )
        with self.assertLogs(database_module.logger, level="WARNING") as logs:
            self.assertFalse(await self.manager.is_ready())
        self.assertNotIn("sensitive", " ".join(logs.output))
        self.assertTrue(await self.manager.is_ready())
        self.client_factory.assert_called_once()
        self.client.close.assert_not_called()

    async def test_ping_auth_failure_and_non_ok_reply_are_not_ready(self):
        self.manager.connect()
        self.database.command.side_effect = OperationFailure("sensitive auth details", code=18)
        with self.assertLogs(database_module.logger, level="WARNING"):
            self.assertFalse(await self.manager.ping())
        self.database.command.side_effect = None
        self.database.command.return_value = {"ok": 0}
        self.assertFalse(await self.manager.ping())

    async def test_ping_has_an_outer_deadline(self):
        cancelled = asyncio.Event()

        async def blocked_ping(*args):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        self.settings.MONGO_PING_TIMEOUT_MS = 10
        self.manager.connect()
        self.database.command.side_effect = blocked_ping
        with self.assertLogs(database_module.logger, level="WARNING"):
            self.assertFalse(await asyncio.wait_for(self.manager.ping(), timeout=1))
        self.assertTrue(cancelled.is_set())
        self.client.close.assert_not_called()

    async def test_cancellation_propagates(self):
        self.manager.connect()
        self.database.command.side_effect = asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await self.manager.ping()

    async def test_in_flight_ping_cannot_report_ready_after_restart(self):
        self.manager.connect()

        async def restart_during_ping(*args):
            self.manager.disconnect()
            self.client_factory.return_value = MagicMock()
            self.manager.connect()
            return {"ok": 1}

        self.database.command.side_effect = restart_during_ping
        self.assertFalse(await self.manager.ping())

    def test_getters_guard_uninitialized_state_and_return_handles(self):
        with patch.object(database_module, "db_client", self.manager):
            for getter, args in ((database_module.get_db, ()), (database_module.get_collection, ("users",))):
                with self.assertRaisesRegex(RuntimeError, "not initialized"):
                    getter(*args)
            self.manager.connect()
            self.assertIs(database_module.get_db(), self.database)
            self.assertIs(database_module.get_collection("users"), self.database["users"])
            self.manager.disconnect()
            with self.assertRaisesRegex(RuntimeError, "not initialized"):
                database_module.get_db()

    async def test_indexes_are_explicit_non_unique_and_repeatable(self):
        collections = {}
        for collection_name, keys in database_module.INDEXES:
            collections.setdefault(collection_name, SimpleNamespace(create_index=AsyncMock(return_value="index")))
        self.database.__getitem__.side_effect = collections.__getitem__
        self.manager.connect()
        for collection in collections.values():
            collection.create_index.assert_not_called()
        first_result = await self.manager.ensure_indexes()
        second_result = await self.manager.ensure_indexes()
        self.assertEqual(first_result, second_result)
        self.assertEqual(len(first_result), len(database_module.INDEXES))
        for collection_name, keys in database_module.INDEXES:
            collections[collection_name].create_index.assert_any_await(list(keys), unique=False)
        for collection in collections.values():
            for call in collection.create_index.await_args_list:
                self.assertEqual(call.kwargs, {"unique": False})

    async def test_index_failure_is_sanitized_without_dropping_indexes(self):
        self.manager.connect()
        collection = self.database.__getitem__.return_value
        collection.create_index = AsyncMock(side_effect=OperationFailure("sensitive details"))
        with self.assertRaisesRegex(RuntimeError, "index setup failed") as caught:
            await self.manager.ensure_indexes()
        self.assertNotIn("sensitive", str(caught.exception))
        collection.drop_indexes.assert_not_called()
        collection.drop_index.assert_not_called()
        collection.delete_many.assert_not_called()

    async def test_indexes_require_initialization(self):
        with self.assertRaisesRegex(RuntimeError, "not initialized"):
            await self.manager.ensure_indexes()
        self.client_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()

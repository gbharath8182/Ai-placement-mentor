import asyncio
import logging
from urllib.parse import parse_qsl, urlsplit

import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from backend.config import settings


logger = logging.getLogger(__name__)

TIMEOUT_SETTINGS = (
    ("MONGO_SERVER_SELECTION_TIMEOUT_MS", "serverSelectionTimeoutMS", 5000),
    ("MONGO_CONNECT_TIMEOUT_MS", "connectTimeoutMS", 5000),
    ("MONGO_SOCKET_TIMEOUT_MS", "socketTimeoutMS", 10000),
    ("MONGO_WAIT_QUEUE_TIMEOUT_MS", "waitQueueTimeoutMS", 5000),
    ("MONGO_OPERATION_TIMEOUT_MS", "timeoutMS", 15000),
)

INDEXES = (
    ("users", (("email", 1),)),
    ("domains", (("slug", 1),)),
    ("topics", (("slug", 1),)),
    ("topics", (("domain_slug", 1),)),
    ("practice_problems", (("topic_slug", 1),)),
    ("user_progress", (("user_id", 1), ("topic_slug", 1))),
    ("chat_sessions", (("user_id", 1), ("topic_slug", 1))),
)


def _timeout(setting_name, default):
    value = getattr(settings, setting_name, default)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{setting_name} must be a positive integer in milliseconds")
    return value


def _tls_options(uri):
    parsed = urlsplit(uri)
    if parsed.scheme not in ("mongodb", "mongodb+srv") or not parsed.netloc:
        raise ValueError("MONGO_URI must be a MongoDB connection URI")
    options = {}
    for name, value in parse_qsl(parsed.query, keep_blank_values=True):
        options.setdefault(name.lower(), []).append(value.lower())
    hosts = parsed.netloc.rsplit("@", 1)[-1].split(",")
    is_atlas = any(
        host.split(":", 1)[0].lower().rstrip(".").endswith(".mongodb.net")
        for host in hosts
    )
    tls_values = options.get("tls", []) + options.get("ssl", [])
    if any(value not in ("true", "false") for value in tls_values):
        raise ValueError("MongoDB TLS options must be true or false")
    if len(set(tls_values)) > 1:
        raise ValueError("MongoDB TLS options conflict")
    if is_atlas and "false" in tls_values:
        raise ValueError("MongoDB Atlas requires TLS")
    for name in ("tlsinsecure", "tlsallowinvalidcertificates", "tlsallowinvalidhostnames"):
        if any(value != "false" for value in options.get(name, [])):
            raise ValueError("MongoDB TLS certificate and hostname verification is required")
    tls = (
        tls_values[0] == "true" if tls_values else
        is_atlas or parsed.scheme == "mongodb+srv" or
        any(name in options for name in ("tlscafile", "tlscertificatekeyfile", "tlscrlfile"))
    )
    result = {"tls": tls}
    if tls and "tlscafile" not in options:
        result["tlsCAFile"] = certifi.where()
    return result


class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self._ping_timeout_ms = 2000

    def connect(self):
        """Initialize once; connectivity is verified separately by ping()."""
        if self.client is not None:
            return self.db
        candidate = None
        try:
            options = {
                option: _timeout(setting_name, default)
                for setting_name, option, default in TIMEOUT_SETTINGS
            }
            ping_timeout_ms = _timeout("MONGO_PING_TIMEOUT_MS", 2000)
            options.update(_tls_options(settings.MONGO_URI))
            candidate = AsyncIOMotorClient(settings.MONGO_URI, **options)
            database = candidate.get_default_database(default="education_platform")
        except Exception:
            if candidate is not None:
                try:
                    candidate.close()
                except Exception:
                    logger.warning("MongoDB initialization cleanup failed")
            raise RuntimeError("MongoDB initialization failed; check connection settings") from None
        self.client = candidate
        self.db = database
        self._ping_timeout_ms = ping_timeout_ms
        logger.info("MongoDB client initialized; readiness not yet verified")
        return self.db

    async def ping(self):
        """Return current readiness without logging credentials or replacing the pool."""
        client = self.client
        database = self.db
        if client is None or database is None:
            return False
        try:
            result = await asyncio.wait_for(
                database.command("ping"), timeout=self._ping_timeout_ms / 1000
            )
        except (PyMongoError, asyncio.TimeoutError):
            logger.warning("MongoDB readiness check failed")
            return False
        return (
            self.client is client and self.db is database and result.get("ok") == 1
        )

    async def is_ready(self):
        """Perform a fresh ping; readiness is never cached across failures."""
        return await self.ping()

    async def ensure_indexes(self):
        """Explicit maintenance only: additive, non-unique, non-TTL query indexes."""
        database = self.db
        if database is None:
            raise RuntimeError("MongoDB client is not initialized")
        created = []
        try:
            for collection_name, keys in INDEXES:
                index_name = await database[collection_name].create_index(
                    list(keys), unique=False
                )
                created.append((collection_name, index_name))
        except PyMongoError:
            raise RuntimeError("MongoDB index setup failed; review existing indexes and permissions") from None
        return created

    def disconnect(self):
        """Clear handles before closing, so the next startup creates a fresh client."""
        client = self.client
        self.client = None
        self.db = None
        if client is not None:
            try:
                client.close()
            except Exception:
                raise RuntimeError("MongoDB client cleanup failed") from None
            logger.info("MongoDB client disconnected")


db_client = Database()


def get_db():
    if db_client.db is None:
        raise RuntimeError("MongoDB client is not initialized")
    return db_client.db


def get_collection(name: str):
    return get_db()[name]


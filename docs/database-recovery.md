# MongoDB / Render reliability and recovery

## Scope and guarantees

`backend/database.py` keeps the existing synchronous `connect()` / `disconnect()`
interface. Initializing the Motor client is **not** proof of database connectivity.
`await db_client.ping()` and `await db_client.is_ready()` perform a fresh ping on
the selected database and return a boolean. They do not create indexes, read user
data, replay writes, or replace the client after a transient failure.

Repeated `connect()` calls reuse the client. `disconnect()` clears both handles
before closing; another `connect()` creates a new client. Accessing `get_db()` or
`get_collection()` before initialization or after shutdown raises a generic
`RuntimeError`. Lifecycle operations belong on the application's event-loop
thread, not concurrent worker threads; drain requests before manual replacement.

The selected database is taken from the URI by the driver, including escaped
names. If the URI has no database, it defaults to `education_platform`. An
`authSource` query parameter chooses the authentication database, not the data
database. Set the data database explicitly in the production URI to avoid an
accidental fallback.

## Connection and timeout settings

No `.env` or configuration files were changed. Existing `settings.MONGO_URI`
continues to work. Use the Render secret environment configuration for credentials;
never put an actual URI in logs, tickets, screenshots, or commands shared publicly.

- Local default: `mongodb://localhost:27017/education_platform` uses no TLS and no
  CA file. IPv6 and ordinary non-Atlas hosts follow the same policy.
- Atlas: `mongodb+srv://<credentials>@<cluster>.mongodb.net/education_platform`
  enables verified TLS with `certifi`. Standard `mongodb://` Atlas seed lists
  also require TLS. Explicit `tls=false` / `ssl=false` on Atlas is rejected.
- Other SRV deployments default to TLS but may explicitly use `tls=false` when
  appropriate for a trusted local deployment.
- Non-Atlas TLS can be enabled with `?tls=true` or `?ssl=true`. A URI
  `tlsCAFile` is preserved for a private CA instead of being overwritten by
  `certifi`; a CA/client-certificate/CRL option also opts in to TLS unless
  explicitly disabled. Certificate and hostname verification bypasses are rejected.
- Conflicting TLS options and malformed settings fail with a sanitized error;
  underlying connection strings and driver exception text are not logged here.

These optional **integer attributes on `settings`** override built-in defaults:

| Settings attribute | Driver option / purpose | Default (ms) |
| --- | --- | ---: |
| `MONGO_SERVER_SELECTION_TIMEOUT_MS` | `serverSelectionTimeoutMS` | 5000 |
| `MONGO_CONNECT_TIMEOUT_MS` | `connectTimeoutMS` | 5000 |
| `MONGO_SOCKET_TIMEOUT_MS` | `socketTimeoutMS` | 10000 |
| `MONGO_WAIT_QUEUE_TIMEOUT_MS` | `waitQueueTimeoutMS` | 5000 |
| `MONGO_OPERATION_TIMEOUT_MS` | `timeoutMS`, including driver retries | 15000 |
| `MONGO_PING_TIMEOUT_MS` | Outer asyncio readiness deadline | 2000 |

All must be positive integers; zero, negative values, booleans and strings are
rejected. Defaults apply immediately without editing `config.py`. For environment
overrides, the configuration owner must add each attribute to `Settings` using
`int(os.getenv("ATTRIBUTE_NAME", "DEFAULT"))`, substituting the exact names and
defaults from this table. Merely adding those environment variables in Render
does not work with the current `config.py`. Driver timeout keywords deliberately
take precedence over any corresponding timeout options in `MONGO_URI`.

The ping deadline should stay below Render's HTTP health-check response deadline
(currently five seconds), leaving room for request handling. Cancellation of a
Motor await does not necessarily stop its worker-thread operation immediately;
the driver deadlines still bound that work. SRV DNS lookup can occur during the
synchronous constructor and is not bounded by the outer ping deadline. See the
[PyMongo client options](https://pymongo.readthedocs.io/en/4.9.1/api/pymongo/mongo_client.html)
and [Render health checks](https://render.com/docs/health-checks).

## Required integration in `backend/main.py` (not applied)

Replace the existing lifespan body with this pattern, keeping its decorator and
signature. The `try/finally` must surround startup validation as well as `yield`:

```python
try:
    db_client.connect()
    if not await db_client.is_ready():
        raise RuntimeError("MongoDB unavailable during startup")
    yield
finally:
    db_client.disconnect()
```

Add `HTTPException` to the existing `fastapi` import and a database-aware readiness
route. Do not include raw exception text, topology, database names or credentials
in responses:

```python
@app.get("/health/ready", include_in_schema=False)
async def readiness():
    if not await db_client.is_ready():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ready"}
```

After the route exists, set the Render web service **Health Check Path** to
`/health/ready` (or `healthCheckPath: /health/ready` in a maintainer-managed
Blueprint). Keep a separate process-only liveness endpoint if your monitoring
needs one. Do not configure the new path before deploying the route.

**Current limitation:** the `main.py` lifespan, as inspected, only initializes a lazy client.
It does not fail startup on a failed ping, use guaranteed `finally` cleanup, or
expose the readiness route. These snippets must be integrated by its owner.

## Opt-in index maintenance

`await db_client.ensure_indexes()` is available for a separately authorized,
controlled maintenance session after connecting and checking readiness. It is
never called from `connect()`, a ping, a request, or normal startup.

It requests only ascending, non-unique indexes on existing query fields:

- `users.email`, `domains.slug`, `topics.slug`, `topics.domain_slug`;
- `practice_problems.topic_slug`;
- `user_progress(user_id, topic_slug)` and `chat_sessions(user_id, topic_slug)`.

It returns `(collection_name, index_name)` pairs. Default driver index names make
identical repeated requests idempotent. It never drops indexes, deletes documents,
adds TTL expiration, changes validators, deduplicates records, or enforces new
uniqueness constraints. It does **not** resolve signup/upsert races or duplicates.

Index builds still consume resources and may create a missing collection. Inspect
existing indexes, collection presence, permissions and deployment capacity first;
approve a maintenance window and verified backup/snapshot. Existing indexes with
different names/options (including unique, sparse, partial or collation options)
may conflict. On error the helper stops with a sanitized `RuntimeError`; preceding
builds may already have completed. Do not drop or recreate conflicting indexes
automatically. Inspect privately and obtain a maintainer decision. A client timeout
does not guarantee that a server-side index build has stopped. No indexes were
created as part of this implementation or its tests.

## Recovery runbook

1. **Protect data.** Do not run seed scripts, migrations, deduplication, destructive
   repairs, or index maintenance as an outage workaround. Confirm the last known
   good deployment and backup/snapshot. Preserve existing content and user data.
2. **Classify privately.** Check Render service logs and Atlas status/metrics for
   reachability, DNS, connection limits, authentication or TLS failures. This module
   emits generic failure messages intentionally; do not enable broad driver debug
   logging or publish unredacted exceptions. A failed readiness ping must yield
   HTTP 503 once the integration above is installed.
3. **Restore the dependency.** For local development confirm `mongod` is running
   at the configured host/port. For Atlas confirm the cluster is available, database
   user credentials/roles are valid, the URI names the intended database, and Atlas
   network access allows the service's Render outbound addresses. Confirm SRV/TXT
   resolution and CA trust. Do not disable TLS verification or broaden access to
   all addresses to mask a failure. Let the authorized owner correct secret settings
   in Render; this task does not alter `.env` or secrets.
4. **Allow pool recovery.** Keep the same client for transient outages; the driver
   monitors and reconnects. Probe readiness again after fixing the dependency. Do
   not loop on `disconnect()` / `connect()` inside health checks or requests and
   never replay an application write solely because it timed out: its outcome may
   be unknown. See [PyMongo connection recovery](https://pymongo.readthedocs.io/en/4.9.1/api/pymongo/mongo_client.html).
5. **Restart only when needed.** If settings changed or the process remains stuck,
   drain traffic and use Render's service restart/redeploy controls. Do not rotate
   clients with in-flight requests. A controlled same-process restart must call
   `disconnect()`, then `connect()`, then await `is_ready()`; never reuse old database
   or collection handles. A [closed Motor client cannot be reused](https://motor.readthedocs.io/en/3.6.0/api-asyncio/asyncio_motor_client.html).
6. **Verify before restoring traffic.** Require successful startup ping and repeated
   HTTP 200 readiness checks. Verify read-only content access and an authorized
   normal login without creating test data. If the new deployment is unhealthy,
   roll back application code only; do not restore/drop a production database
   without explicit incident-owner approval. After recovery, review the cause and
   timeouts before scheduling any separately authorized index work.

Readiness proves a ping succeeded at that moment, not collection permissions,
schema completeness, durable writes, or backup health. Actual network/Render/Atlas
behavior still needs a controlled staging verification after integration.

## Focused validation

From the repository root, with the project's driver dependencies installed:

```text
python -m unittest discover -s tests -p test_database.py -v
```

Tests use `unittest`, `IsolatedAsyncioTestCase`, mocked Motor clients and a synthetic
settings module. They never import the real config, read `.env`, connect to MongoDB,
execute seed/migration scripts, or build real indexes. Coverage includes TLS policy,
driver-selected database fallback, timeout options and validation, sanitized errors,
idempotent lifecycle, restart after shutdown, failed-ping recovery, cancellation,
ping deadlines, stale in-flight probes, getters, and explicit index behavior.

Implementation validation passed all 25 tests on the available local Python 3.14.2
with Motor 3.5.1 / PyMongo 4.8.0. This is not the declared Render Python 3.11.9
runtime or pinned Motor 3.6.0 / PyMongo 4.9.1 dependencies; rerun the same command
in that deployment environment before release.

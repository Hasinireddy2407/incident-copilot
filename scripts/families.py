FAMILIES = {
    "pool_exhaustion": {
        "root_cause": "A config deploy reduced the DB connection pool size, so requests wait for connections.",
        "log_hints": "timeout acquiring connection from pool; HikariPool-1 - Connection is not available, request timed out after 30000ms; FATAL: remaining connection slots are reserved",
        "wrong_actions": [
            ("Restarted pods", "harmful", "reconnect storm exhausted the pool again"),
            ("Scaled up replicas", "harmful", "more replicas opened more DB connections and hit max_connections"),
        ],
        "good_fix": "Rolled back the config deploy that changed pool settings",
    },
    "cache_stampede": {
        "root_cause": "Redis failover emptied the cache, and a thundering herd of misses overloaded the database.",
        "log_hints": "cache miss ratio 0.94; redis: master changed, connection reset; DB CPU 95%; slow query log spike",
        "wrong_actions": [
            ("Flushed the cache", "harmful", "cold cache made the stampede worse"),
            ("Restarted the cache tier", "harmful", "second cold start, DB fell over again"),
        ],
        "good_fix": "Enabled request coalescing and warmed hot keys gradually while rate-limiting DB traffic",
    },
    "tls_expiry": {
        "root_cause": "An internal mTLS certificate expired and was not auto-renewed.",
        "log_hints": "x509: certificate has expired or is not yet valid; SSL handshake failed; tls: bad certificate",
        "wrong_actions": [
            ("Restarted the service", "failed", "no effect, the same expired cert was reloaded"),
        ],
        "good_fix": "Renewed the certificate and reloaded it on the affected services",
    },
    "disk_full": {
        "root_cause": "Unrotated log files filled the volume.",
        "log_hints": "No space left on device; write failed: ENOSPC; pod evicted: node had condition DiskPressure",
        "wrong_actions": [
            ("Scaled up replicas", "failed", "new pods landed on the same full nodes and were evicted"),
        ],
        "good_fix": "Purged old logs and fixed the log rotation config",
    },
}

SPECS = [
    ("INC-101","pool_exhaustion","checkout-service","2026-02-03","sev1","seed"),
    ("INC-104","pool_exhaustion","orders-api","2026-04-11","sev2","seed"),
    ("INC-108","pool_exhaustion","inventory-service","2026-06-20","sev2","seed"),
    ("INC-113","pool_exhaustion","payments-api","2026-09-02","sev1","heldout"),
    ("INC-102","cache_stampede","catalog-service","2026-02-17","sev2","seed"),
    ("INC-106","cache_stampede","search-api","2026-05-05","sev2","seed"),
    ("INC-109","cache_stampede","user-profile-service","2026-07-08","sev1","seed"),
    ("INC-114","cache_stampede","cart-service","2026-09-10","sev1","heldout"),
    ("INC-103","tls_expiry","auth-service","2026-03-09","sev1","seed"),
    ("INC-107","tls_expiry","notifications-service","2026-05-28","sev3","seed"),
    ("INC-110","tls_expiry","billing-service","2026-07-22","sev2","seed"),
    ("INC-115","tls_expiry","shipping-service","2026-09-18","sev2","heldout"),
    ("INC-105","disk_full","log-ingest","2026-04-02","sev2","seed"),
    ("INC-111","disk_full","reporting-service","2026-08-04","sev3","seed"),
    ("INC-112","disk_full","analytics-worker","2026-08-25","sev2","seed"),
]
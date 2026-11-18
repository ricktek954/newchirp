PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO schema_metadata (key, value)
VALUES ('schema_version', '1')
ON CONFLICT(key) DO UPDATE SET value = excluded.value;

CREATE TABLE IF NOT EXISTS manufacturers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    aliases TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS radios (
    id INTEGER PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(id),
    model TEXT NOT NULL COLLATE NOCASE,
    aliases TEXT NOT NULL DEFAULT '',
    driver_path TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (manufacturer_id, model)
);

CREATE TABLE IF NOT EXISTS work_items (
    id INTEGER PRIMARY KEY,
    radio_id INTEGER NOT NULL REFERENCES radios(id),
    kind TEXT NOT NULL CHECK (
        kind IN (
            'new_driver',
            'bug',
            'enhancement',
            'maintenance',
            'hardware_validation',
            'release'
        )
    ),
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'open',
            'investigating',
            'awaiting_user',
            'fix_committed',
            'pending_validation',
            'hardware_tested',
            'experimental',
            'released',
            'blocked',
            'closed'
        )
    ),
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (
        priority IN ('critical', 'high', 'normal', 'low')
    ),
    summary TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    source_ref TEXT NOT NULL DEFAULT '',
    reporter TEXT NOT NULL DEFAULT '' CHECK (reporter NOT LIKE '%@%'),
    occurred_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (radio_id, kind, title)
);

CREATE TABLE IF NOT EXISTS work_events (
    id INTEGER PRIMARY KEY,
    work_item_id INTEGER NOT NULL REFERENCES work_items(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    external_ref TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL DEFAULT (date('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (work_item_id, event_type, occurred_at, summary)
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY,
    work_item_id INTEGER NOT NULL REFERENCES work_items(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    label TEXT NOT NULL,
    uri TEXT NOT NULL DEFAULT '',
    sha256 TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hardware_tests (
    id INTEGER PRIMARY KEY,
    work_item_id INTEGER NOT NULL REFERENCES work_items(id) ON DELETE CASCADE,
    tester TEXT NOT NULL CHECK (tester NOT LIKE '%@%'),
    tested_at TEXT NOT NULL DEFAULT (date('now')),
    result TEXT NOT NULL CHECK (
        result IN ('pass', 'fail', 'partial', 'blocked')
    ),
    details TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIEW IF NOT EXISTS work_overview AS
SELECT
    w.id AS work_id,
    m.name AS manufacturer,
    r.model,
    w.kind,
    w.title,
    w.status,
    w.priority,
    w.summary,
    w.source,
    w.source_ref,
    w.reporter,
    w.updated_at,
    COUNT(DISTINCT e.id) AS evidence_count,
    COUNT(DISTINCT h.id) AS hardware_test_count
FROM work_items w
JOIN radios r ON r.id = w.radio_id
JOIN manufacturers m ON m.id = r.manufacturer_id
LEFT JOIN evidence e ON e.work_item_id = w.id
LEFT JOIN hardware_tests h ON h.work_item_id = w.id
GROUP BY w.id;

CREATE INDEX IF NOT EXISTS work_items_radio_status
ON work_items(radio_id, status);

CREATE INDEX IF NOT EXISTS work_events_work_date
ON work_events(work_item_id, occurred_at);

CREATE INDEX IF NOT EXISTS evidence_work
ON evidence(work_item_id);

CREATE INDEX IF NOT EXISTS hardware_tests_work
ON hardware_tests(work_item_id);

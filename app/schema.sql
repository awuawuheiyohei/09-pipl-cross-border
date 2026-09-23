-- PIPL Cross-Border Data Transfer Audit - SQLite schema (v1.0)
-- 依据：《个人信息保护法》《数据出境安全评估办法》《个人信息出境标准合同办法》（2024网信办令第16号）

-- ============================================
-- 数据资产分类（按敏感度）
-- ============================================
CREATE TABLE IF NOT EXISTS data_assets (
    asset_id        TEXT PRIMARY KEY,                  -- DA-001
    asset_name      TEXT NOT NULL,
    asset_type      TEXT NOT NULL,                     -- DATABASE / API / FILE / LOG / BACKUP / SAAS
    location_country TEXT NOT NULL,                    -- CN / US / SG / DE / JP / etc
    location_region TEXT,                              -- cn-north-1 / us-west-2 / sg-1
    data_categories TEXT NOT NULL,                      -- JSON array (PII / SPI / BEHAVIORAL / BIOMETRIC / MINORS / etc)
    sensitivity     TEXT NOT NULL DEFAULT 'NORMAL',    -- NORMAL / SENSITIVE / IMPORTANT
    volume_records  INTEGER DEFAULT 0,                 -- 数据条数
    purpose         TEXT,                              -- 业务用途
    data_subject    TEXT,                              -- EMPLOYEE / CUSTOMER / PARTNER / PUBLIC
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_asset_country ON data_assets(location_country);
CREATE INDEX IF NOT EXISTS idx_asset_sensitivity ON data_assets(sensitivity);

-- ============================================
-- 数据出境流（跨境链路）
-- ============================================
CREATE TABLE IF NOT EXISTS data_flows (
    flow_id             TEXT PRIMARY KEY,              -- DF-001
    flow_name           TEXT NOT NULL,
    source_asset_id     TEXT NOT NULL,
    recipient_id        TEXT NOT NULL,                  -- → recipient_entities
    data_categories     TEXT NOT NULL,                  -- 流动的数据类别（JSON）
    volume_per_year     INTEGER NOT NULL,               -- 年均条数
    transfer_method     TEXT NOT NULL,                  -- API_SYNC / SFTP / DB_REPL / MANUAL_EXPORT / EMAIL
    frequency           TEXT NOT NULL,                  -- REAL_TIME / DAILY / WEEKLY / MONTHLY / AD_HOC
    encryption_in_transit TEXT NOT NULL DEFAULT 'TLS_1.2',
    pseudonymization    INTEGER NOT NULL DEFAULT 0,     -- 0/1
    start_date          TEXT,
    last_transfer_at    TEXT,
    legal_basis         TEXT NOT NULL,                  -- SCC / SECURITY_ASSESSMENT / CERTIFICATION / EXEMPTION
    status              TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE / PAUSED / DISCONTINUED
    notes               TEXT,
    FOREIGN KEY (source_asset_id) REFERENCES data_assets(asset_id),
    FOREIGN KEY (recipient_id) REFERENCES recipient_entities(recipient_id)
);

CREATE INDEX IF NOT EXISTS idx_flow_status ON data_flows(status);
CREATE INDEX IF NOT EXISTS idx_flow_legal ON data_flows(legal_basis);

-- ============================================
-- 境外接收方（境外主体）
-- ============================================
CREATE TABLE IF NOT EXISTS recipient_entities (
    recipient_id     TEXT PRIMARY KEY,                  -- RE-001
    recipient_name   TEXT NOT NULL,
    recipient_country TEXT NOT NULL,
    recipient_type   TEXT NOT NULL,                    -- HQ / SUBSIDIARY / VENDOR / CLOUD_PROVIDER
    contact_person   TEXT,
    contract_signed  INTEGER NOT NULL DEFAULT 0,        -- SCC 是否已签
    contract_date    TEXT,
    data_protection_law TEXT,                          -- GDPR / CCPA / LGPD / PIPL_EQUIV
    security_cert    TEXT,                              -- ISO27001/SOC2
    last_audit_at    TEXT,
    risk_level       TEXT NOT NULL DEFAULT 'MEDIUM',    -- LOW / MEDIUM / HIGH
    notes            TEXT
);

CREATE INDEX IF NOT EXISTS idx_recipient_country ON recipient_entities(recipient_country);
CREATE INDEX IF NOT EXISTS idx_recipient_risk ON recipient_entities(risk_level);

-- ============================================
-- PIA/DPIA 评估记录
-- ============================================
CREATE TABLE IF NOT EXISTS pia_assessments (
    pia_id            TEXT PRIMARY KEY,                 -- PIA-001
    pia_name          TEXT NOT NULL,
    flow_id           TEXT NOT NULL,                    -- 关联到数据流
    assessor          TEXT NOT NULL DEFAULT 'GRC Team',
    assessment_date   TEXT NOT NULL DEFAULT (datetime('now')),
    framework         TEXT NOT NULL DEFAULT 'PIPL',
    -- 11 项 DPIA 评估维度（GB/T 39335 国标）
    necessity_score   INTEGER NOT NULL,                 -- 出境必要性 1-5
    risk_score        INTEGER NOT NULL,                 -- 出境风险 1-5
    sensitivity_score INTEGER NOT NULL,                 -- 敏感度 1-5
    volume_score      INTEGER NOT NULL,                 -- 数据量级 1-5
    recipient_score   INTEGER NOT NULL,                 -- 接收方安全 1-5
    -- 关键控制项
    separate_consent INTEGER NOT NULL DEFAULT 0,        -- 是否取得单独同意
    dpia_completed   INTEGER NOT NULL DEFAULT 0,
    scc_signed       INTEGER NOT NULL DEFAULT 0,
    security_assessment INTEGER NOT NULL DEFAULT 0,     -- 网信办安全评估（>100万人或SPI>10万人）
    certification     INTEGER NOT NULL DEFAULT 0,        -- 个人信息保护认证
    -- 评估结果
    total_score       INTEGER NOT NULL,
    risk_level        TEXT NOT NULL,                    -- LOW / MEDIUM / HIGH / CRITICAL
    recommendations   TEXT,                             -- JSON array
    approved_by       TEXT,
    approved_at       TEXT,
    FOREIGN KEY (flow_id) REFERENCES data_flows(flow_id)
);

CREATE INDEX IF NOT EXISTS idx_pia_flow ON pia_assessments(flow_id);
CREATE INDEX IF NOT EXISTS idx_pia_risk ON pia_assessments(risk_level);

-- ============================================
-- 合规风险例外（高风险项跟踪）
-- ============================================
CREATE TABLE IF NOT EXISTS compliance_exceptions (
    exception_id      TEXT PRIMARY KEY,
    flow_id           TEXT NOT NULL,
    finding           TEXT NOT NULL,
    severity          TEXT NOT NULL,                    -- CRITICAL / HIGH / MEDIUM
    remediation       TEXT,
    due_date          TEXT,
    status            TEXT NOT NULL DEFAULT 'OPEN',     -- OPEN / IN_PROGRESS / RESOLVED / ACCEPTED
    resolved_at       TEXT,
    FOREIGN KEY (flow_id) REFERENCES data_flows(flow_id)
);

CREATE INDEX IF NOT EXISTS idx_exc_status ON compliance_exceptions(status);

-- ============================================
-- Evidence Items（含 SHA-256 防篡改）
-- ============================================
CREATE TABLE IF NOT EXISTS evidence_items (
    evidence_id      TEXT PRIMARY KEY,
    flow_id           TEXT,
    pia_id            TEXT,
    source_name       TEXT NOT NULL,
    collected_at      TEXT NOT NULL DEFAULT (datetime('now')),
    content_payload   TEXT NOT NULL,
    sha256_hash       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_flow ON evidence_items(flow_id);

-- ============================================
-- 审计 trail
-- ============================================
CREATE TABLE IF NOT EXISTS audit_trail (
    audit_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    actor         TEXT NOT NULL,
    action        TEXT NOT NULL,
    entity_type   TEXT,
    entity_id     TEXT,
    details       TEXT,
    occurred_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
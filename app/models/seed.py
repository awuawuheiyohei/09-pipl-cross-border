"""Seed PIPL 数据资产 + 出境流 + 接收方 + DPIA + 例外"""
from datetime import datetime, timezone, timedelta
import json
import uuid
from .db import get_conn, init_db
from .pipl_models import compute_dpia_scores


def seed_data_assets(verbose=False):
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM compliance_exceptions")
    conn.execute("DELETE FROM pia_assessments")
    conn.execute("DELETE FROM evidence_items")
    conn.execute("DELETE FROM audit_trail")
    conn.execute("DELETE FROM data_flows")
    conn.execute("DELETE FROM data_assets")
    conn.execute("DELETE FROM recipient_entities")

    assets = [
        # CN 境内核心
        {"asset_id": "DA-001", "asset_name": "Customer PII Database (Production)", "asset_type": "DATABASE",
         "country": "CN", "region": "cn-north-1 (AWS 宁夏)", "categories": ["PII_NAME", "PII_ID_CARD", "PII_PHONE", "PII_EMAIL"],
         "sensitivity": "SENSITIVE", "volume": 5_000_000, "purpose": "Customer relationship management",
         "subject": "CUSTOMER"},
        {"asset_id": "DA-002", "asset_name": "Employee HRIS (Workday)", "asset_type": "SAAS",
         "country": "CN", "region": "Workday CN", "categories": ["PII_NAME", "EMPLOYMENT", "PII_EMAIL"],
         "sensitivity": "SENSITIVE", "volume": 50_000, "purpose": "HR management",
         "subject": "EMPLOYEE"},
        {"asset_id": "DA-003", "asset_name": "Booking Order Database", "asset_type": "DATABASE",
         "country": "CN", "region": "Aliyun Hangzhou", "categories": ["PII_NAME", "PII_PHONE"],
         "sensitivity": "NORMAL", "volume": 8_000_000, "purpose": "Travel order records",
         "subject": "CUSTOMER"},
        {"asset_id": "DA-004", "asset_name": "Health Insurance Records (SPI)", "asset_type": "DATABASE",
         "country": "CN", "region": "cn-north-1", "categories": ["SPI_HEALTH", "PII_NAME"],
         "sensitivity": "IMPORTANT", "volume": 25_000, "purpose": "Employee health benefits",
         "subject": "EMPLOYEE"},
        {"asset_id": "DA-005", "asset_name": "Facial Recognition Login System", "asset_type": "DATABASE",
         "country": "CN", "region": "On-premise Beijing", "categories": ["SPI_BIOMETRIC"],
         "sensitivity": "IMPORTANT", "volume": 5_000, "purpose": "Employee office access",
         "subject": "EMPLOYEE"},
        {"asset_id": "DA-006", "asset_name": "Marketing Analytics (Aggregated)", "asset_type": "DATABASE",
         "country": "US", "region": "AWS us-west-2", "categories": ["BEHAVIORAL"],
         "sensitivity": "NORMAL", "volume": 1_000_000, "purpose": "Marketing analysis",
         "subject": "CUSTOMER"},
    ]
    inserted = 0
    for a in assets:
        conn.execute(
            """INSERT INTO data_assets
               (asset_id, asset_name, asset_type, location_country, location_region,
                data_categories, sensitivity, volume_records, purpose, data_subject)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (a["asset_id"], a["asset_name"], a["asset_type"], a["country"], a["region"],
             json.dumps(a["categories"]), a["sensitivity"], a["volume"], a["purpose"], a["subject"])
        )
        inserted += 1
    conn.commit()
    if verbose:
        print(f"[+] Seeded {inserted} data assets")
    return inserted


def seed_recipients(verbose=False):
    conn = get_conn()
    recipients = [
        {"recipient_id": "RE-001", "recipient_name": "Trip.Biz USA Inc. (HQ)",
         "country": "US", "type": "HQ",
         "contact": "dpo@tripbiz.us.", "contract_signed": 1, "contract_date": "2024-06-01",
         "law": "CCPA", "cert": "SOC 2 Type II + ISO 27001",
         "audit": "2025-12-01", "risk": "LOW"},
        {"recipient_id": "RE-002", "recipient_name": "Trip.Biz Singapore Pte Ltd.",
         "country": "SG", "type": "SUBSIDIARY",
         "contact": "dpo@tripbiz.sg", "contract_signed": 1, "contract_date": "2024-07-15",
         "law": "PDPA (Singapore)", "cert": "ISO 27001",
         "audit": "2025-06-01", "risk": "LOW"},
        {"recipient_id": "RE-003", "recipient_name": "AWS Asia Pacific (Singapore Region)",
         "country": "SG", "type": "CLOUD_PROVIDER",
         "contact": "aws-apac-compliance@aws.amazon.com", "contract_signed": 1, "contract_date": "2023-12-01",
         "law": "PDPA (Singapore)", "cert": "ISO 27001 / 27017 / 27018 / SOC 1/2/3",
         "audit": "2025-09-01", "risk": "LOW"},
        {"recipient_id": "RE-004", "recipient_name": "Salesforce.com Inc.",
         "country": "US", "type": "VENDOR",
         "contact": "trust@salesforce.com", "contract_signed": 1, "contract_date": "2024-03-01",
         "law": "CCPA + GDPR (EU customers)", "cert": "SOC 2 Type II + ISO 27001",
         "audit": "2025-04-01", "risk": "MEDIUM"},
        {"recipient_id": "RE-005", "recipient_name": "Workday Inc.",
         "country": "US", "type": "VENDOR",
         "contact": "trust@workday.com", "contract_signed": 0, "contract_date": None,
         "law": "CCPA", "cert": "SOC 2 Type II",
         "audit": "2025-02-01", "risk": "HIGH"},
        {"recipient_id": "RE-006", "recipient_name": "Overseas Analytics Vendor (Unknown)",
         "country": "DE", "type": "VENDOR",
         "contact": "vendor@unknown.com", "contract_signed": 0, "contract_date": None,
         "law": "GDPR", "cert": "None",
         "audit": None, "risk": "HIGH"},
    ]
    inserted = 0
    for r in recipients:
        conn.execute(
            """INSERT INTO recipient_entities
               (recipient_id, recipient_name, recipient_country, recipient_type, contact_person,
                contract_signed, contract_date, data_protection_law, security_cert,
                last_audit_at, risk_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (r["recipient_id"], r["recipient_name"], r["country"], r["type"], r["contact"],
             r["contract_signed"], r["contract_date"], r["law"], r["cert"],
             r["audit"], r["risk"])
        )
        inserted += 1
    conn.commit()
    if verbose:
        print(f"[+] Seeded {inserted} recipients")
    return inserted


def seed_data_flows(verbose=False):
    """数据出境流（跨境链路）"""
    conn = get_conn()
    today = datetime.now(timezone.utc)
    flows = [
        # Customer PII → 美国 HQ（RE-001）— 最大体量跨境流
        {"flow_id": "DF-001", "name": "Customer PII to HQ (aggregated reporting)",
         "source": "DA-001", "recipient": "RE-001", "categories": ["PII_NAME", "PII_EMAIL"],
         "volume": 500_000, "method": "API_SYNC", "freq": "DAILY",
         "encryption": "TLS_1.3", "pseudo": 1, "start": "2024-01-15",
         "legal_basis": "SCC", "status": "ACTIVE",
         "necessity": 4, "risk": 3, "sensitivity": 3, "vol_score": 5, "recipient_score": 4,
         "consent": 1, "scc": 1, "assessment": 0, "cert": 0},

        # Employee HRIS → USA HQ
        {"flow_id": "DF-002", "name": "Employee HR data to HQ (HRIS sync)",
         "source": "DA-002", "recipient": "RE-001", "categories": ["EMPLOYMENT", "PII_NAME", "PII_EMAIL"],
         "volume": 50_000, "method": "API_SYNC", "freq": "DAILY",
         "encryption": "TLS_1.2", "pseudo": 0, "start": "2024-03-01",
         "legal_basis": "SCC", "status": "ACTIVE",
         "necessity": 3, "risk": 3, "sensitivity": 2, "vol_score": 2, "recipient_score": 4,
         "consent": 1, "scc": 1, "assessment": 0, "cert": 0},

        # HR 数据 → US Sales Corp (无 SCC!)
        {"flow_id": "DF-003", "name": "HR data to Salesforce CRM",
         "source": "DA-002", "recipient": "RE-004", "categories": ["PII_NAME", "PII_EMAIL"],
         "volume": 50_000, "method": "API_SYNC", "freq": "DAILY",
         "encryption": "TLS_1.2", "pseudo": 0, "start": "2024-05-01",
         "legal_basis": "SCC", "status": "ACTIVE",
         "necessity": 3, "risk": 3, "sensitivity": 2, "vol_score": 2, "recipient_score": 3,
         "consent": 0, "scc": 0, "assessment": 0, "cert": 0},  # 重大问题

        # SPI Health → USA HQ — 高风险 SPI 跨境
        {"flow_id": "DF-004", "name": "Employee health insurance data to HQ",
         "source": "DA-004", "recipient": "RE-001", "categories": ["SPI_HEALTH", "PII_NAME"],
         "volume": 25_000, "method": "SFTP", "freq": "MONTHLY",
         "encryption": "TLS_1.2", "pseudo": 0, "start": "2024-04-01",
         "legal_basis": "SECURITY_ASSESSMENT", "status": "ACTIVE",
         "necessity": 4, "risk": 5, "sensitivity": 5, "vol_score": 2, "recipient_score": 4,
         "consent": 1, "scc": 1, "assessment": 1, "cert": 0},  # Critical SPI

        # Biometric → Unknown vendor
        {"flow_id": "DF-005", "name": "Face recognition to overseas vendor (LEGACY)",
         "source": "DA-005", "recipient": "RE-006", "categories": ["SPI_BIOMETRIC"],
         "volume": 5_000, "method": "API_SYNC", "freq": "DAILY",
         "encryption": "TLS_1.0", "pseudo": 0, "start": "2023-01-01",
         "legal_basis": "EXEMPTION", "status": "ACTIVE",
         "necessity": 2, "risk": 5, "sensitivity": 5, "vol_score": 1, "recipient_score": 1,
         "consent": 0, "scc": 0, "assessment": 0, "cert": 0},  # 极高风险

        # Booking → SG subsidiary
        {"flow_id": "DF-006", "name": "Booking orders to Singapore APAC hub",
         "source": "DA-003", "recipient": "RE-002", "categories": ["PII_NAME", "PII_PHONE"],
         "volume": 200_000, "method": "DB_REPL", "freq": "REAL_TIME",
         "encryption": "TLS_1.3", "pseudo": 1, "start": "2024-02-01",
         "legal_basis": "CERTIFICATION", "status": "ACTIVE",
         "necessity": 3, "risk": 2, "sensitivity": 2, "vol_score": 3, "recipient_score": 4,
         "consent": 1, "scc": 0, "assessment": 0, "cert": 1},  # 集团内部认证

        # Marketing Aggregated → US (无 PII SPI, 风险低)
        {"flow_id": "DF-007", "name": "Aggregated marketing data to US analytics",
         "source": "DA-006", "recipient": "RE-001", "categories": ["BEHAVIORAL"],
         "volume": 1_000_000, "method": "API_SYNC", "freq": "DAILY",
         "encryption": "TLS_1.3", "pseudo": 1, "start": "2024-01-01",
         "legal_basis": "SCC", "status": "ACTIVE",
         "necessity": 4, "risk": 1, "sensitivity": 1, "vol_score": 5, "recipient_score": 4,
         "consent": 1, "scc": 1, "assessment": 0, "cert": 0},  # 体量大但已脱敏 + 非 PII
    ]
    inserted = 0
    for f in flows:
        conn.execute(
            """INSERT INTO data_flows
               (flow_id, flow_name, source_asset_id, recipient_id, data_categories,
                volume_per_year, transfer_method, frequency, encryption_in_transit,
                pseudonymization, start_date, legal_basis, status, last_transfer_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f["flow_id"], f["name"], f["source"], f["recipient"],
             json.dumps(f["categories"]), f["volume"], f["method"], f["freq"],
             f["encryption"], f["pseudo"], f["start"], f["legal_basis"], f["status"],
             today.isoformat())
        )

        # 同步生成 PIA
        pia_id = f"PIA-{f['flow_id'][3:]}"
        score = compute_dpia_scores(
            necessity=f["necessity"], risk=f["risk"], sensitivity=f["sensitivity"],
            volume=f["vol_score"], recipient=f["recipient_score"],
            has_separate_consent=bool(f["consent"]), scc_signed=bool(f["scc"])
        )
        conn.execute(
            """INSERT INTO pia_assessments
               (pia_id, pia_name, flow_id, framework, assessor,
                necessity_score, risk_score, sensitivity_score, volume_score, recipient_score,
                separate_consent, dpia_completed, scc_signed, security_assessment, certification,
                total_score, risk_level, recommendations)
               VALUES (?, ?, ?, 'PIPL', 'GRC Team', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pia_id, f"PIA for {f['name']}", f["flow_id"],
             f["necessity"], f["risk"], f["sensitivity"], f["vol_score"], f["recipient_score"],
             f["consent"], 1, f["scc"], f["assessment"], f["cert"],
             score["raw_total"], score["risk_level"],
             json.dumps(score["recommendations"], ensure_ascii=False))
        )
        inserted += 1
    conn.commit()
    if verbose:
        print(f"[+] Seeded {inserted} data flows + DPIAs")
    return inserted


def seed_exceptions(verbose=False):
    """高风险 exception 跟踪"""
    conn = get_conn()
    today = datetime.now(timezone.utc)
    exceptions = [
        # DF-003 无 SCC
        {"flow_id": "DF-003", "finding": "Salesforce SCC 未签 — 需立即补救",
         "severity": "CRITICAL", "remediation": "立即签署 SCC 并在网信办备案（10 工作日内）",
         "due_days": 7},
        # DF-004 网信办评估
        {"flow_id": "DF-004", "finding": "SPI 健康数据跨境 — 已触发网信办安全评估（结果待出）",
         "severity": "HIGH", "remediation": "持续跟踪评估结果 + 取得单独同意",
         "due_days": 30},
        # DF-005 严重
        {"flow_id": "DF-005", "finding": "Critical SPI（人脸识别）跨境至未评估的境外供应商 — 立即停止",
         "severity": "CRITICAL", "remediation": "立即停止 + 评估改为本地化处理 + 删除历史跨境",
         "due_days": 3},
        # DF-006 网信办 16号令
        {"flow_id": "DF-006", "finding": "跨国集团内部 — 需走个人信息保护认证路径（GB/T 39335）",
         "severity": "MEDIUM", "remediation": "准备认证申请材料（60 工作日）",
         "due_days": 60},
    ]
    inserted = 0
    for e in exceptions:
        eid = str(uuid.uuid4())
        due = (today + timedelta(days=e["due_days"])).strftime("%Y-%m-%d")
        conn.execute(
            """INSERT INTO compliance_exceptions
               (exception_id, flow_id, finding, severity, remediation, due_date, status)
               VALUES (?, ?, ?, ?, ?, ?, 'OPEN')""",
            (eid, e["flow_id"], e["finding"], e["severity"], e["remediation"], due)
        )
        inserted += 1
    conn.commit()
    if verbose:
        print(f"[+] Seeded {inserted} exceptions")
    return inserted


def seed_all(verbose=False):
    n_a = seed_data_assets(verbose=verbose)
    n_r = seed_recipients(verbose=verbose)
    n_f = seed_data_flows(verbose=verbose)
    n_e = seed_exceptions(verbose=verbose)
    return {"assets": n_a, "recipients": n_r, "flows": n_f, "exceptions": n_e}


if __name__ == "__main__":
    stats = seed_all(verbose=True)
    print(f"\n[+] Seed: {stats}")
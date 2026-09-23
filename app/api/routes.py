"""
PIPL API Routes
- 数据资产 / 数据流 / 接收方 / DPIA / Exception / SCC / Pathway
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field

from ..models.db import get_conn, init_db, rows_to_dicts, row_to_dict, write_audit
from ..models.pipl_models import (
    determine_pipl_pathway,
    compute_dpia_scores,
    generate_scc_contract,
    THRESHOLDS,
    DATA_CATEGORIES_OPTIONS,
)
from ..models.seed import seed_all

router = APIRouter()


# ============================================
# Pydantic Schemas
# ============================================
class FlowCreate(BaseModel):
    flow_id: str
    flow_name: str
    source_asset_id: str
    recipient_id: str
    data_categories: List[str]
    volume_per_year: int
    transfer_method: str
    frequency: str
    encryption_in_transit: str = "TLS_1.2"
    pseudonymization: bool = False
    start_date: Optional[str] = None
    legal_basis: str = "SCC"
    # DPIA 5 维
    necessity: int = Field(3, ge=1, le=5)
    risk: int = Field(3, ge=1, le=5)
    sensitivity: int = Field(2, ge=1, le=5)
    volume_score: int = Field(2, ge=1, le=5)
    recipient_score: int = Field(3, ge=1, le=5)
    # 控制项
    separate_consent: bool = False
    scc_signed: bool = False
    security_assessment: bool = False
    certification: bool = False


class PathwayRequest(BaseModel):
    is_ciio: bool = False
    total_subjects: int = 0
    spi_subjects: int = 0
    is_internal_group: bool = False
    is_necessary: bool = True


class DPIARequest(BaseModel):
    necessity: int = Field(3, ge=1, le=5)
    risk: int = Field(3, ge=1, le=5)
    sensitivity: int = Field(2, ge=1, le=5)
    volume: int = Field(2, ge=1, le=5)
    recipient: int = Field(3, ge=1, le=5)
    has_separate_consent: bool
    scc_signed: bool


class SCCRequest(BaseModel):
    flow_id: str
    exporter_name: str
    exporter_country: str = "中国"
    exporter_contact: str = "dpo@example.com"


class EvidenceCreate(BaseModel):
    flow_id: Optional[str] = None
    pia_id: Optional[str] = None
    source_name: str
    content_payload: str


# ============================================
# Dashboard summary
# ============================================
@router.get("/dashboard/summary")
async def dashboard_summary():
    """总览统计 — 用于 Dashboard 单页"""
    init_db()
    conn = get_conn()
    # 资产
    a_total = conn.execute("SELECT COUNT(*) FROM data_assets").fetchone()[0]
    a_spi = conn.execute("SELECT COUNT(*) FROM data_assets WHERE sensitivity='IMPORTANT'").fetchone()[0]
    # 数据流
    f_total = conn.execute("SELECT COUNT(*) FROM data_flows WHERE status='ACTIVE'").fetchone()[0]
    f_volume = conn.execute("SELECT COALESCE(SUM(volume_per_year),0) FROM data_flows WHERE status='ACTIVE'").fetchone()[0]
    # 按 legal_basis 分组
    f_by_basis = rows_to_dicts(conn.execute(
        "SELECT legal_basis, COUNT(*) as cnt FROM data_flows WHERE status='ACTIVE' GROUP BY legal_basis"
    ).fetchall())
    # 按 risk 分组
    pia_by_risk = rows_to_dicts(conn.execute(
        "SELECT risk_level, COUNT(*) as cnt FROM pia_assessments GROUP BY risk_level"
    ).fetchall())
    # Exception
    e_total = conn.execute("SELECT COUNT(*) FROM compliance_exceptions").fetchone()[0]
    e_open = conn.execute("SELECT COUNT(*) FROM compliance_exceptions WHERE status='OPEN'").fetchone()[0]
    e_critical = conn.execute("SELECT COUNT(*) FROM compliance_exceptions WHERE severity='CRITICAL' AND status='OPEN'").fetchone()[0]
    # 接收方 SCC 覆盖率
    r_total = conn.execute("SELECT COUNT(*) FROM recipient_entities").fetchone()[0]
    r_signed = conn.execute("SELECT COUNT(*) FROM recipient_entities WHERE contract_signed=1").fetchone()[0]

    return {
        "assets": {"total": a_total, "spi": a_spi},
        "flows": {"total": f_total, "annual_volume": f_volume, "by_legal_basis": f_by_basis},
        "pia": {"by_risk_level": pia_by_risk},
        "exceptions": {"total": e_total, "open": e_open, "critical_open": e_critical},
        "recipients": {"total": r_total, "scc_signed": r_signed, "scc_coverage_pct": round(r_signed/r_total*100, 1) if r_total else 0},
    }


# ============================================
# Data Assets
# ============================================
@router.get("/assets")
async def list_assets(sensitivity: Optional[str] = None, country: Optional[str] = None):
    init_db()
    conn = get_conn()
    sql = "SELECT * FROM data_assets WHERE 1=1"
    params = []
    if sensitivity:
        sql += " AND sensitivity=?"
        params.append(sensitivity)
    if country:
        sql += " AND location_country=?"
        params.append(country)
    sql += " ORDER BY asset_id"
    rows = rows_to_dicts(conn.execute(sql, params).fetchall())
    # 反序列化 JSON
    for r in rows:
        try:
            r["data_categories"] = json.loads(r["data_categories"]) if r["data_categories"] else []
        except Exception:
            r["data_categories"] = []
    return {"count": len(rows), "items": rows}


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM data_assets WHERE asset_id=?", (asset_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Asset not found: {asset_id}")
    d = row_to_dict(row)
    try:
        d["data_categories"] = json.loads(d["data_categories"]) if d["data_categories"] else []
    except Exception:
        d["data_categories"] = []
    return d


# ============================================
# Data Flows
# ============================================
@router.get("/flows")
async def list_flows(status: Optional[str] = "ACTIVE", recipient_id: Optional[str] = None):
    init_db()
    conn = get_conn()
    sql = "SELECT * FROM data_flows WHERE 1=1"
    params = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if recipient_id:
        sql += " AND recipient_id=?"
        params.append(recipient_id)
    sql += " ORDER BY flow_id"
    rows = rows_to_dicts(conn.execute(sql, params).fetchall())
    for r in rows:
        try:
            r["data_categories"] = json.loads(r["data_categories"]) if r["data_categories"] else []
        except Exception:
            r["data_categories"] = []
    return {"count": len(rows), "items": rows}


@router.get("/flows/{flow_id}")
async def get_flow(flow_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM data_flows WHERE flow_id=?", (flow_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Flow not found: {flow_id}")
    d = row_to_dict(row)
    try:
        d["data_categories"] = json.loads(d["data_categories"]) if d["data_categories"] else []
    except Exception:
        d["data_categories"] = []
    # Join recipient
    rec = conn.execute("SELECT * FROM recipient_entities WHERE recipient_id=?", (d["recipient_id"],)).fetchone()
    if rec:
        rd = row_to_dict(rec)
        d["recipient"] = rd
    # Join PIA
    pia = conn.execute("SELECT * FROM pia_assessments WHERE flow_id=? ORDER BY assessment_date DESC LIMIT 1", (flow_id,)).fetchone()
    if pia:
        pd = row_to_dict(pia)
        try:
            pd["recommendations"] = json.loads(pd["recommendations"]) if pd["recommendations"] else []
        except Exception:
            pd["recommendations"] = []
        d["pia"] = pd
    # Join exceptions
    excs = rows_to_dicts(conn.execute("SELECT * FROM compliance_exceptions WHERE flow_id=?", (flow_id,)).fetchall())
    d["exceptions"] = excs
    return d


@router.post("/flows")
async def create_flow(req: FlowCreate, actor: str = "user"):
    """新建数据流（同步生成 PIA）"""
    init_db()
    conn = get_conn()
    # 检查 source_asset / recipient 存在
    if not conn.execute("SELECT 1 FROM data_assets WHERE asset_id=?", (req.source_asset_id,)).fetchone():
        raise HTTPException(400, f"Source asset 不存在: {req.source_asset_id}")
    if not conn.execute("SELECT 1 FROM recipient_entities WHERE recipient_id=?", (req.recipient_id,)).fetchone():
        raise HTTPException(400, f"Recipient 不存在: {req.recipient_id}")
    if conn.execute("SELECT 1 FROM data_flows WHERE flow_id=?", (req.flow_id,)).fetchone():
        raise HTTPException(409, f"Flow ID 已存在: {req.flow_id}")

    conn.execute(
        """INSERT INTO data_flows
           (flow_id, flow_name, source_asset_id, recipient_id, data_categories,
            volume_per_year, transfer_method, frequency, encryption_in_transit,
            pseudonymization, start_date, legal_basis, status, last_transfer_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)""",
        (req.flow_id, req.flow_name, req.source_asset_id, req.recipient_id,
         json.dumps(req.data_categories), req.volume_per_year, req.transfer_method,
         req.frequency, req.encryption_in_transit, int(req.pseudonymization),
         req.start_date, req.legal_basis,
         datetime.now(timezone.utc).isoformat())
    )

    # DPIA
    pia_id = f"PIA-{req.flow_id[3:]}"
    score = compute_dpia_scores(
        necessity=req.necessity, risk=req.risk, sensitivity=req.sensitivity,
        volume=req.volume_score, recipient=req.recipient_score,
        has_separate_consent=req.separate_consent, scc_signed=req.scc_signed,
    )
    conn.execute(
        """INSERT INTO pia_assessments
           (pia_id, pia_name, flow_id, framework, assessor,
            necessity_score, risk_score, sensitivity_score, volume_score, recipient_score,
            separate_consent, dpia_completed, scc_signed, security_assessment, certification,
            total_score, risk_level, recommendations)
           VALUES (?, ?, ?, 'PIPL', 'GRC Team', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (pia_id, f"PIA for {req.flow_name}", req.flow_id,
         req.necessity, req.risk, req.sensitivity, req.volume_score, req.recipient_score,
         int(req.separate_consent), 1, int(req.scc_signed),
         int(req.security_assessment), int(req.certification),
         score["raw_total"], score["risk_level"],
         json.dumps(score["recommendations"], ensure_ascii=False))
    )

    write_audit(conn, actor=actor, action="create_flow",
                entity_type="data_flows", entity_id=req.flow_id,
                details={"legal_basis": req.legal_basis, "risk_level": score["risk_level"]})
    conn.commit()
    return {"flow_id": req.flow_id, "pia_id": pia_id, "risk_level": score["risk_level"], "recommendations": score["recommendations"]}


# ============================================
# Recipients
# ============================================
@router.get("/recipients")
async def list_recipients(risk_level: Optional[str] = None):
    init_db()
    conn = get_conn()
    sql = "SELECT * FROM recipient_entities WHERE 1=1"
    params = []
    if risk_level:
        sql += " AND risk_level=?"
        params.append(risk_level)
    sql += " ORDER BY recipient_id"
    rows = rows_to_dicts(conn.execute(sql, params).fetchall())
    return {"count": len(rows), "items": rows}


@router.get("/recipients/{recipient_id}")
async def get_recipient(recipient_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM recipient_entities WHERE recipient_id=?", (recipient_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Recipient not found: {recipient_id}")
    d = row_to_dict(row)
    # 关联 flows
    flows = rows_to_dicts(conn.execute("SELECT flow_id, flow_name, legal_basis, status FROM data_flows WHERE recipient_id=?", (recipient_id,)).fetchall())
    d["flows"] = flows
    return d


# ============================================
# PIA
# ============================================
@router.get("/pia")
async def list_pia(risk_level: Optional[str] = None, flow_id: Optional[str] = None):
    init_db()
    conn = get_conn()
    sql = "SELECT * FROM pia_assessments WHERE 1=1"
    params = []
    if risk_level:
        sql += " AND risk_level=?"
        params.append(risk_level)
    if flow_id:
        sql += " AND flow_id=?"
        params.append(flow_id)
    sql += " ORDER BY pia_id"
    rows = rows_to_dicts(conn.execute(sql, params).fetchall())
    for r in rows:
        try:
            r["recommendations"] = json.loads(r["recommendations"]) if r["recommendations"] else []
        except Exception:
            r["recommendations"] = []
    return {"count": len(rows), "items": rows}


@router.post("/pia/recompute/{flow_id}")
async def recompute_pia(flow_id: str, actor: str = "user"):
    """基于当前 flow 状态重算 DPIA"""
    init_db()
    conn = get_conn()
    row = conn.execute("SELECT * FROM pia_assessments WHERE flow_id=? ORDER BY assessment_date DESC LIMIT 1", (flow_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"PIA not found for flow: {flow_id}")
    p = row_to_dict(row)
    score = compute_dpia_scores(
        necessity=p["necessity_score"], risk=p["risk_score"], sensitivity=p["sensitivity_score"],
        volume=p["volume_score"], recipient=p["recipient_score"],
        has_separate_consent=bool(p["separate_consent"]), scc_signed=bool(p["scc_signed"]),
    )
    conn.execute(
        """UPDATE pia_assessments SET total_score=?, risk_level=?, recommendations=?,
           assessment_date=datetime('now') WHERE pia_id=?""",
        (score["raw_total"], score["risk_level"],
         json.dumps(score["recommendations"], ensure_ascii=False), p["pia_id"])
    )
    write_audit(conn, actor=actor, action="recompute_pia",
                entity_type="pia_assessments", entity_id=p["pia_id"],
                details={"new_risk_level": score["risk_level"]})
    conn.commit()
    return {"pia_id": p["pia_id"], "risk_level": score["risk_level"], "recommendations": score["recommendations"]}


# ============================================
# Exceptions
# ============================================
@router.get("/exceptions")
async def list_exceptions(status: Optional[str] = None, severity: Optional[str] = None):
    init_db()
    conn = get_conn()
    sql = "SELECT * FROM compliance_exceptions WHERE 1=1"
    params = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if severity:
        sql += " AND severity=?"
        params.append(severity)
    sql += " ORDER BY CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 ELSE 2 END, due_date"
    rows = rows_to_dicts(conn.execute(sql, params).fetchall())
    return {"count": len(rows), "items": rows}


@router.post("/exceptions/{exception_id}/resolve")
async def resolve_exception(exception_id: str, actor: str = "user"):
    init_db()
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM compliance_exceptions WHERE exception_id=?", (exception_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Exception not found: {exception_id}")
    conn.execute(
        """UPDATE compliance_exceptions SET status='RESOLVED', resolved_at=datetime('now')
           WHERE exception_id=?""",
        (exception_id,)
    )
    write_audit(conn, actor=actor, action="resolve_exception",
                entity_type="compliance_exceptions", entity_id=exception_id,
                details={})
    conn.commit()
    return {"exception_id": exception_id, "status": "RESOLVED"}


# ============================================
# Pathway determination
# ============================================
@router.post("/pathway/determine")
async def pathway_determine(req: PathwayRequest):
    """根据 PIPL + 网信办令第16号 判定 4 种合规路径"""
    pathway = determine_pipl_pathway(
        is_ciio=req.is_ciio,
        total_subjects=req.total_subjects,
        spi_subjects=req.spi_subjects,
        is_internal_group=req.is_internal_group,
        is_necessary=req.is_necessary,
    )
    info = THRESHOLDS.get(f"{pathway}_REQUIRED") or THRESHOLDS.get(f"{pathway}_FILING") or {
        "name": pathway, "triggers": [], "timeline": "N/A", "fee": "N/A", "validity": "N/A",
    }
    return {
        "pathway": pathway,
        "info": {
            "name": info.get("name", pathway),
            "triggers": info.get("triggers", []),
            "timeline": info.get("timeline"),
            "fee": info.get("fee"),
            "validity": info.get("validity"),
        },
    }


# ============================================
# DPIA score (standalone)
# ============================================
@router.post("/dpia/score")
async def dpia_score(req: DPIARequest):
    return compute_dpia_scores(
        necessity=req.necessity, risk=req.risk, sensitivity=req.sensitivity,
        volume=req.volume, recipient=req.recipient,
        has_separate_consent=req.has_separate_consent, scc_signed=req.scc_signed,
    )


# ============================================
# SCC Contract generation
# ============================================
@router.post("/scc/generate")
async def scc_generate(req: SCCRequest, actor: str = "user"):
    """根据 flow_id + 出境方信息生成 PIPL 标准合同"""
    init_db()
    conn = get_conn()
    flow = conn.execute("SELECT * FROM data_flows WHERE flow_id=?", (req.flow_id,)).fetchone()
    if not flow:
        raise HTTPException(404, f"Flow not found: {req.flow_id}")
    f = row_to_dict(flow)
    rec = conn.execute("SELECT * FROM recipient_entities WHERE recipient_id=?", (f["recipient_id"],)).fetchone()
    if not rec:
        raise HTTPException(404, f"Recipient not found: {f['recipient_id']}")
    r = row_to_dict(rec)
    try:
        categories = json.loads(f["data_categories"])
    except Exception:
        categories = []

    is_spi = any(c.startswith("SPI_") for c in categories) or any(c.startswith("BIOMETRIC") for c in categories)
    contract = generate_scc_contract(
        exporter_name=req.exporter_name,
        exporter_country=req.exporter_country,
        exporter_contact=req.exporter_contact,
        recipient_name=r["recipient_name"],
        recipient_country=f"{r['recipient_country']} ({r.get('recipient_name', '')})",
        recipient_law=r["data_protection_law"] or "N/A",
        data_categories=categories,
        data_subject="在职员工 / 客户 / 合作伙伴",
        volume_records=f["volume_per_year"],
        transfer_method=f["transfer_method"],
        frequency=f["frequency"],
        is_spi=is_spi,
    )
    write_audit(conn, actor=actor, action="generate_scc",
                entity_type="data_flows", entity_id=req.flow_id,
                details={"is_spi": is_spi, "recipient": r["recipient_name"]})
    conn.commit()
    return {"flow_id": req.flow_id, "is_spi": is_spi, "contract_markdown": contract}


# ============================================
# Evidence (SHA-256 防篡改)
# ============================================
@router.post("/evidence")
async def add_evidence(req: EvidenceCreate, actor: str = "user"):
    init_db()
    conn = get_conn()
    eid = f"EV-{uuid.uuid4().hex[:12]}"
    sha = hashlib.sha256(req.content_payload.encode("utf-8")).hexdigest()
    conn.execute(
        """INSERT INTO evidence_items (evidence_id, flow_id, pia_id, source_name, content_payload, sha256_hash)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (eid, req.flow_id, req.pia_id, req.source_name, req.content_payload, sha)
    )
    write_audit(conn, actor=actor, action="add_evidence",
                entity_type="evidence_items", entity_id=eid,
                details={"flow_id": req.flow_id, "sha256": sha})
    conn.commit()
    return {"evidence_id": eid, "sha256": sha}


# ============================================
# Audit trail
# ============================================
@router.get("/audit")
async def list_audit(limit: int = Query(50, ge=1, le=500)):
    init_db()
    conn = get_conn()
    rows = rows_to_dicts(conn.execute(
        "SELECT * FROM audit_trail ORDER BY occurred_at DESC LIMIT ?", (limit,)).fetchall())
    return {"count": len(rows), "items": rows}


# ============================================
# Admin: reseed
# ============================================
@router.post("/admin/seed")
async def admin_seed(actor: str = "user"):
    init_db()
    stats = seed_all(verbose=False)
    conn = get_conn()
    write_audit(conn, actor=actor, action="reseed",
                entity_type="system", entity_id="all",
                details=stats)
    conn.commit()
    return {"status": "ok", "stats": stats}

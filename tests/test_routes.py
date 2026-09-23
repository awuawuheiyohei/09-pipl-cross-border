"""Phase 5: 端到端 smoke + model unit tests"""
import os
import sys
import json
import pytest

# 让 test 直接 import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.models.db import init_db, DB_PATH
from app.models.pipl_models import (
    determine_pipl_pathway,
    compute_dpia_scores,
    generate_scc_contract,
)
from app.models.seed import seed_all


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Test 开始前：init_db + reseed"""
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    seed_all(verbose=False)
    yield


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ============================================
# Model unit tests
# ============================================
class TestPIPLPathway:
    def test_security_assessment_ciio(self):
        assert determine_pipl_pathway(True, 50_000, 1000, False, True) == "SECURITY_ASSESSMENT"

    def test_security_assessment_over_1m(self):
        assert determine_pipl_pathway(False, 1_500_000, 1000, False, True) == "SECURITY_ASSESSMENT"

    def test_security_assessment_spi_over_100k(self):
        assert determine_pipl_pathway(False, 500_000, 100_000, False, True) == "SECURITY_ASSESSMENT"

    def test_certification_internal_group(self):
        assert determine_pipl_pathway(False, 200_000, 5000, True, True) == "CERTIFICATION"

    def test_scc_default(self):
        assert determine_pipl_pathway(False, 50_000, 1000, False, True) == "SCC"

    def test_exemption_under_10k_unnecessary(self):
        assert determine_pipl_pathway(False, 5000, 100, False, False) == "EXEMPTION"


class TestDPIAScoring:
    def test_critical_no_consent(self):
        """一票否决：无单独同意 → CRITICAL"""
        r = compute_dpia_scores(3, 3, 3, 3, 4, has_separate_consent=False, scc_signed=True)
        assert r["risk_level"] == "CRITICAL"
        assert any("单独同意" in x for x in r["recommendations"])

    def test_high_no_scc(self):
        r = compute_dpia_scores(3, 3, 3, 3, 4, has_separate_consent=True, scc_signed=False)
        assert r["risk_level"] == "HIGH"
        assert any("标准合同" in x for x in r["recommendations"])

    def test_low_reasonable(self):
        r = compute_dpia_scores(2, 2, 2, 2, 5, has_separate_consent=True, scc_signed=True)
        assert r["risk_level"] == "LOW"

    def test_high_high_volume(self):
        r = compute_dpia_scores(5, 4, 5, 5, 5, has_separate_consent=True, scc_signed=True)
        assert r["risk_level"] in ("HIGH", "CRITICAL")


class TestSCCContract:
    def test_generate_non_spi(self):
        scc = generate_scc_contract(
            exporter_name="TestCo",
            exporter_country="中国",
            exporter_contact="dpo@test.com",
            recipient_name="TestCo US",
            recipient_country="US",
            recipient_law="CCPA",
            data_categories=["PII_NAME", "PII_EMAIL"],
            data_subject="员工",
            volume_records=1000,
            transfer_method="API_SYNC",
            frequency="DAILY",
            is_spi=False,
        )
        assert "TestCo" in scc
        assert "不涉及敏感个人信息" in scc
        assert "CCPA" in scc

    def test_generate_spi(self):
        scc = generate_scc_contract(
            exporter_name="TestCo",
            exporter_country="中国",
            exporter_contact="dpo@test.com",
            recipient_name="TestCo US",
            recipient_country="US",
            recipient_law="CCPA",
            data_categories=["SPI_HEALTH"],
            data_subject="员工",
            volume_records=5000,
            transfer_method="SFTP",
            frequency="MONTHLY",
            is_spi=True,
        )
        assert "敏感个人信息" in scc
        assert "AES-256" in scc
        assert "72 小时" in scc or "72 小时" in scc or "72" in scc


# ============================================
# FastAPI smoke tests
# ============================================
class TestHealthEndpoint:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "ok"
        assert d["service"] == "pipl-audit"


class TestDashboardSummary:
    def test_summary(self, client):
        r = client.get("/api/dashboard/summary")
        assert r.status_code == 200
        d = r.json()
        assert d["assets"]["total"] >= 6
        assert d["flows"]["total"] >= 7
        assert "by_legal_basis" in d["flows"]
        assert "by_risk_level" in d["pia"]
        assert d["exceptions"]["critical_open"] >= 1  # DF-003 + DF-005 都是 CRITICAL


class TestAssetsAPI:
    def test_list(self, client):
        r = client.get("/api/assets")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 6
        assert isinstance(d["items"][0]["data_categories"], list)

    def test_filter_country_cn(self, client):
        r = client.get("/api/assets?country=CN")
        assert r.status_code == 200
        d = r.json()
        assert all(a["location_country"] == "CN" for a in d["items"])

    def test_get_one(self, client):
        r = client.get("/api/assets/DA-001")
        assert r.status_code == 200
        d = r.json()
        assert d["asset_id"] == "DA-001"
        assert "PII_NAME" in d["data_categories"]

    def test_get_404(self, client):
        r = client.get("/api/assets/DA-999")
        assert r.status_code == 404


class TestFlowsAPI:
    def test_list_active(self, client):
        r = client.get("/api/flows")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 7
        for f in d["items"]:
            assert f["status"] == "ACTIVE"

    def test_get_one_with_joins(self, client):
        r = client.get("/api/flows/DF-003")
        assert r.status_code == 200
        d = r.json()
        assert d["flow_id"] == "DF-003"
        assert "recipient" in d
        assert "pia" in d
        assert d["pia"]["risk_level"] == "CRITICAL"  # 无 SCC 无 单独同意

    def test_create_flow(self, client):
        body = {
            "flow_id": "DF-T01",
            "flow_name": "Test flow creation",
            "source_asset_id": "DA-002",
            "recipient_id": "RE-002",
            "data_categories": ["PII_EMAIL"],
            "volume_per_year": 1000,
            "transfer_method": "API_SYNC",
            "frequency": "WEEKLY",
            "necessity": 3, "risk": 2, "sensitivity": 1, "volume_score": 1, "recipient_score": 4,
            "separate_consent": True, "scc_signed": True, "security_assessment": False, "certification": False,
        }
        r = client.post("/api/flows", json=body)
        assert r.status_code == 200
        d = r.json()
        assert d["flow_id"] == "DF-T01"
        assert d["pia_id"] == "PIA-T01"  # PIA ID = PIA-{flow_id suffix}
        assert d["risk_level"] == "LOW"  # consent + scc + 4 receiver

    def test_create_flow_invalid_source(self, client):
        body = {
            "flow_id": "DF-T02",
            "flow_name": "Bad source",
            "source_asset_id": "DA-999",
            "recipient_id": "RE-001",
            "data_categories": ["PII_EMAIL"],
            "volume_per_year": 100, "transfer_method": "API_SYNC", "frequency": "DAILY",
        }
        r = client.post("/api/flows", json=body)
        assert r.status_code == 400


class TestRecipientsAPI:
    def test_list(self, client):
        r = client.get("/api/recipients")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 6

    def test_filter_high_risk(self, client):
        r = client.get("/api/recipients?risk_level=HIGH")
        assert r.status_code == 200
        d = r.json()
        assert all(rcp["risk_level"] == "HIGH" for rcp in d["items"])

    def test_get_with_flows(self, client):
        r = client.get("/api/recipients/RE-001")
        assert r.status_code == 200
        d = r.json()
        assert d["recipient_id"] == "RE-001"
        assert len(d["flows"]) >= 3  # DF-001 DF-002 DF-004 DF-007


class TestPIAActions:
    def test_list_pia(self, client):
        r = client.get("/api/pia")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 7

    def test_filter_critical(self, client):
        r = client.get("/api/pia?risk_level=CRITICAL")
        assert r.status_code == 200
        d = r.json()
        assert all(p["risk_level"] == "CRITICAL" for p in d["items"])
        assert d["count"] >= 2  # DF-003 + DF-005

    def test_recompute(self, client):
        r = client.post("/api/pia/recompute/DF-001")
        assert r.status_code == 200
        d = r.json()
        assert "risk_level" in d


class TestExceptionsAPI:
    def test_list(self, client):
        r = client.get("/api/exceptions")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 4

    def test_filter_critical(self, client):
        r = client.get("/api/exceptions?severity=CRITICAL")
        assert r.status_code == 200
        d = r.json()
        assert all(e["severity"] == "CRITICAL" for e in d["items"])
        assert d["count"] >= 2

    def test_resolve(self, client):
        # 拿到第一个 OPEN exception
        r = client.get("/api/exceptions?status=OPEN")
        assert r.status_code == 200
        first = r.json()["items"][0]
        eid = first["exception_id"]

        # Resolve
        r2 = client.post(f"/api/exceptions/{eid}/resolve")
        assert r2.status_code == 200
        assert r2.json()["status"] == "RESOLVED"


class TestPathwayDetermination:
    def test_over_1m(self, client):
        r = client.post("/api/pathway/determine", json={
            "is_ciio": False, "total_subjects": 1_500_000, "spi_subjects": 1000,
            "is_internal_group": False, "is_necessary": True,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["pathway"] == "SECURITY_ASSESSMENT"

    def test_scc(self, client):
        r = client.post("/api/pathway/determine", json={
            "is_ciio": False, "total_subjects": 50_000, "spi_subjects": 1000,
            "is_internal_group": False, "is_necessary": True,
        })
        assert r.status_code == 200
        assert r.json()["pathway"] == "SCC"

    def test_certification(self, client):
        r = client.post("/api/pathway/determine", json={
            "is_ciio": False, "total_subjects": 200_000, "spi_subjects": 5000,
            "is_internal_group": True, "is_necessary": True,
        })
        assert r.status_code == 200
        assert r.json()["pathway"] == "CERTIFICATION"

    def test_exemption(self, client):
        r = client.post("/api/pathway/determine", json={
            "is_ciio": False, "total_subjects": 5000, "spi_subjects": 100,
            "is_internal_group": False, "is_necessary": False,
        })
        assert r.status_code == 200
        assert r.json()["pathway"] == "EXEMPTION"


class TestDPIAScore:
    def test_score_endpoint(self, client):
        r = client.post("/api/dpia/score", json={
            "necessity": 3, "risk": 4, "sensitivity": 5, "volume": 4, "recipient": 2,
            "has_separate_consent": True, "scc_signed": False,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] == "HIGH"


class TestSCCGeneration:
    def test_generate_for_df001(self, client):
        r = client.post("/api/scc/generate", json={
            "flow_id": "DF-001",
            "exporter_name": "Trip.Biz (Beijing) Co., Ltd.",
            "exporter_country": "中国 北京",
            "exporter_contact": "dpo@tripbiz.com",
        })
        assert r.status_code == 200
        d = r.json()
        assert "Trip.Biz" in d["contract_markdown"]
        assert d["flow_id"] == "DF-001"

    def test_generate_for_df004_spi(self, client):
        """SPI 数据流应该 is_spi=true + 含 SPI 特别条款"""
        r = client.post("/api/scc/generate", json={
            "flow_id": "DF-004",
            "exporter_name": "Trip.Biz (Beijing) Co., Ltd.",
            "exporter_country": "中国 北京",
            "exporter_contact": "dpo@tripbiz.com",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["is_spi"] is True
        assert "AES-256" in d["contract_markdown"]

    def test_generate_404(self, client):
        r = client.post("/api/scc/generate", json={
            "flow_id": "DF-999", "exporter_name": "X", "exporter_country": "Y", "exporter_contact": "Z",
        })
        assert r.status_code == 404


class TestEvidence:
    def test_add_evidence(self, client):
        r = client.post("/api/evidence", json={
            "flow_id": "DF-001",
            "pia_id": "PIA-001",
            "source_name": "test_log.txt",
            "content_payload": "Log content for SHA-256 test 2026-09-23",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["evidence_id"].startswith("EV-")
        assert len(d["sha256"]) == 64  # SHA-256 hex

    def test_audit_trail_records(self, client):
        """Audit trail 应该记录 admin/seed / scc generate / evidence 等"""
        r = client.get("/api/audit?limit=20")
        assert r.status_code == 200
        d = r.json()
        # 至少有 seed / scc / evidence 等记录
        actions = set(item["action"] for item in d["items"])
        assert "add_evidence" in actions
        assert "generate_scc" in actions


class TestAdmin:
    def test_admin_seed(self, client):
        r = client.post("/api/admin/seed")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "ok"
        assert d["stats"]["assets"] >= 6


class TestStaticUI:
    def test_index_served(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "<html" in r.text.lower() or "<!doctype" in r.text.lower()
        assert "PIPL" in r.text

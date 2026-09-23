# 09. 中国《个人信息保护法》(PIPL) 合规与跨境数据出境安全评估审计平台
(PIPL Cross-Border Data Transfer Audit & Assessment Platform)

---

## 一、 项目背景与 JD 核心诉求对齐

### 1.1 业务与合规背景
随着中国《个人信息保护法》（PIPL）、《数据安全法》（DSL）、《网络安全法》（CSL）以及《促进和规范数据跨境流动规定》（2024年网信办令第16号）的深化落地，跨国企业（如 Riot、Trip.Biz 等拥有跨国用户与分布式架构的企业）在亚太区尤其是大中华区面临极其严格的数据本地化存储、跨国数据流动合规及境外接收方安全治理要求。
- **跨国协同痛点**：跨国企业总部多位于欧美或亚太枢纽（如新加坡、美国加州），海外总部或云上基础设施（AWS/Azure）常需调阅、同步中国境内的员工数据（Workday/HR系统）、海外商旅订单（Trip.Biz 订房/票务）、玩家游戏日志与用户账号资产。
- **监管合规红线**：PIPL 规定个人信息出境须满足三大路径之一（国家网信办安全评估、个人信息出境标准合同备案 SCC、个人信息保护认证），并强制要求事前进行**个人信息保护影响评估（PIA/DPIA）**、取得自然人的**单独同意（Separate Consent）**，且对敏感个人信息（SPI）施加严格的技术防护。

### 1.2 对齐 JD 核心要求
| 招聘岗位 | JD 关键要求对齐点 | 本项目在体系中的映射与落地 |
| :--- | :--- | :--- |
| **Senior Cyber Security Analyst** | • APAC / China-specific cybersecurity & regulatory compliance (PIPL, data localization)<br>• Data protection initiatives (encryption, classification, DLP)<br>• Incident response & regulatory alignment with Global/Legal teams | 建立数据血缘与跨境资产测绘，验证数据出境链路的端到端加密、字段脱敏规则，实现自动化 PIPL 违规风险告警与跨境审计闭环。 |
| **Senior IT GRC Specialist** | • Support global GRC & regulatory/contractual compliance<br>• ISO 27001, SOC 2, PCI DSS certification audit evidence<br>• Client security assessments, RFP & third-party security reviews<br>• Maintain risk registers & track remediation actions | 实现标准化 PIA/DPIA 问卷自动化打分、网信办标准合同（SCC）申报材料一键生成、跨境第三方接收方安全尽调及合规风险看板。 |

---

## 二、 Mac 本地运行环境架构与依赖

### 2.1 总体架构设计
平台采用轻量级、模块化、无多余外部依赖的架构，支持在 macOS（Apple Silicon / Intel）上单机极速启动，便于本地演练、演示与持续集成。

```
┌─────────────────────────────────────────────────────────────────┐
│              Streamlit UI 前端管理看板 (Port 8501)               │
│   [跨境数据资产测绘]  [PIA评估与风险矩阵]  [SCC申报生成器]  [合规审计看板] │
└───────────────────────────────┬─────────────────────────────────┘
                                │ API / Direct Call
┌───────────────────────────────▼─────────────────────────────────┐
│                    FastAPI 业务核心与规则引擎                    │
│  ┌──────────────────────┐ ┌──────────────────┐ ┌──────────────┐  │
│  │ Data Lineage Engine  │ │  PIA/DPIA Calc   │ │ SCC Gen &    │  │
│  │ (资产分类/字段出境测绘)│ │ (合规差距/风险打分)│ │ Threshold    │  │
│  └──────────────────────┘ └──────────────────┘ └──────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ SQLite / ORM
┌───────────────────────────────▼─────────────────────────────────┐
│              SQLite 数据库 (pipl_compliance.db)                  │
│   - data_flows (数据出境流)     - recipient_entities (境外接收方) │
│   - pia_assessments (评估记录)  - compliance_exceptions (风险项) │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选型
- **编程语言**：Python 3.10+
- **前端交互/展示**：Streamlit（低代码交互式合规看板）
- **核心逻辑/API**：FastAPI + Pydantic v2（强类型数据流校验与自评估计算）
- **数据存储**：SQLite + SQLAlchemy ORM（零配置单文件数据库）
- **报表导出**：`jinja2` + `python-docx` / Markdown（生成标准 SCC 备案自评估材料）
- **容器化**：Docker + Docker Compose

### 2.3 Mac 本地运行依赖与一键启动

#### 步骤 1：创建本地虚拟环境
```bash
# 进入项目目录
mkdir -p ~/pipl-crossborder-audit && cd ~/pipl-crossborder-audit

# 创建并激活 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

#### 步骤 2：安装 Python 核心依赖 (`requirements.txt`)
```text
fastapi>=0.110.0
uvicorn>=0.28.0
streamlit>=1.32.0
sqlalchemy>=2.0.28
pydantic>=2.6.4
jinja2>=3.1.3
pandas>=2.2.1
python-docx>=1.1.0
pytest>=8.1.1
```

```bash
pip install -r requirements.txt
```

#### 步骤 3：单机一键启动
```bash
# 启动 Streamlit 可视化审计看板（集成后端引擎）
streamlit run app.py --server.port=8501
```

---

## 三、 Vibe Coding Prompt（可直接复制给 Cursor / Claude Code）

> 💡 **使用指南**：在 Cursor、Claude Code 或 Windsurf 中新建项目，将下方 Prompt 完整粘贴，AI 将自动为你构建完整工程结构及前后端代码。

```markdown
You are a Senior Security & Compliance Architect specializing in China Cybersecurity, PIPL, and Global GRC. 
Please implement a production-ready, local macOS runnable tool named "PIPL Cross-Border Data Transfer Audit Platform".

### Tech Stack:
- Python 3.10+, Streamlit for frontend UI (single-entry multi-tab dashboard)
- SQLite with SQLAlchemy for storage (auto-migrate on startup)
- Pydantic v2 for data validation
- Python-docx / Jinja2 for exporting official Standard Contract (SCC) compliance self-assessment documents

### Core Modules to Implement:
1. Data Lineage & Cross-Border Mapping (跨境数据资产清单):
   - Track: Data Asset Name, Business Unit (HR, Biz Travel, Gaming, Infra), Processing Purpose, Data Category, Specific Fields, Sensitivity Level (General / Sensitive Personal Information per PIPL Art. 28), Annual Volume (number of individuals), Storage Location (Domestic / Overseas), Overseas Recipient Name, Country/Jurisdiction (US, SG, JP, EU), Transfer Route (Direct API, Batch ETL, Remote Access).
   - Ingestion: Pre-seed 3 realistic scenarios (1: Trip.Biz Global Hotel Booking Sync; 2: Multinational HR Workday Salary Transfer to US HQ; 3: Global Online Gaming Player Telemetry & Log Sync).

2. Regulatory Threshold Engine (2024 CAC Provisions on Regulating Cross-Border Flows):
   - Evaluate against CAC Order No. 16:
     * Condition A: Security Assessment Exemption (e.g. necessary for contract fulfillment for individuals like international travel/booking, cross-border HR management under labor laws, emergency protection, or non-sensitive PI < 100,000 individuals accumulated from Jan 1 of current year).
     * Condition B: Standard Contract (SCC) Filing path.
     * Condition C: CAC Mandatory Security Assessment path (accumulated PI >= 1,000,000 individuals or Sensitive PI >= 10,000 individuals).
   - Dynamically calculate and display the regulatory compliance path required.

3. Automated PIA / DPIA Assessment & Scoring Engine:
   - Calculate Overall Risk Score = (Likelihood * Impact) - Safeguard_Mitigation_Factor.
   - 10 standardized check dimensions: Legality/Separate Consent, Processing Scope/Necessity, Overseas Recipient Security Maturity (ISO/SOC2), Destination Jurisdiction Data Protection Adequacy, Encryption in Transit (TLS 1.3), Encryption at Rest (KMS AES-256), Access Control/RBAC, Retention Period, Incident Notification Mechanism, DSR (Data Subject Rights) channel.
   - Output visual Risk Level (Low, Medium, High, Critical) with actionable remediation suggestions.

4. China SCC Document Generator:
   - One-click export of the "Personal Information Cross-Border Protection Impact Assessment Report (个人信息出境个人信息保护影响评估报告)" structured Markdown / Word format matching CAC's official template structure.

Ensure clean code, type hints, structured SQLite models, and pre-populated mock audit data for instant interview demo.
```

---

## 四、 核心代码、规则配置与审计模板

### 4.1 核心数据结构模型 (`models.py`)
```python
"""
models.py: PIPL 跨境数据流与自评估数据模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class SensitivityLevel(str, Enum):
    GENERAL = "General Personal Info (一般个人信息)"
    SENSITIVE = "Sensitive Personal Info (敏感个人信息 - PIPL Art.28)"

class TransferPathway(str, Enum):
    CAC_ASSESSMENT = "国家网信办安全评估 (Mandatory CAC Assessment)"
    STANDARD_CONTRACT = "标准合同备案 (Standard Contract - SCC Filing)"
    EXEMPTED = "法定豁免情形 (Exempted per 2024 Provisions)"

class DataFlowEntity(Base):
    __tablename__ = "data_flows"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_unit = Column(String(64), nullable=False)        # 如: Trip.Biz Travel, Global HR, Security Operations
    system_name = Column(String(128), nullable=False)        # 如: Global Booking API, Workday HR Sync, SOC Log Collector
    processing_purpose = Column(String(256), nullable=False) # 处理目的与必要性
    recipient_name = Column(String(128), nullable=False)     # 境外接收方实体名称
    recipient_country = Column(String(64), nullable=False)   # 接收方所在国家/地区 (US, SG, JP, etc.)
    recipient_type = Column(String(64), default="Affiliate") # Group Affiliate 或 Third-Party Vendor
    
    data_category = Column(String(128), nullable=False)      # 如: 身份信息、金融支付、行程轨迹、日志
    data_fields = Column(Text, nullable=False)               # 具体字段: 姓名, 身份证, 护照号, 信用卡号, 员工ID
    sensitivity_level = Column(String(64), nullable=False)
    
    annual_individuals_count = Column(Integer, default=0)    # 涉及自然人数量 (年累计)
    sensitive_individuals_count = Column(Integer, default=0) # 涉及敏感个人信息自然人数量
    
    # 安全控制措施
    transit_encryption = Column(String(64), default="TLS 1.3")
    rest_encryption = Column(String(64), default="AES-256")
    has_separate_consent = Column(Boolean, default=False)    # 是否已获取单独同意 (PIPL Art.39)
    has_dpa_signed = Column(Boolean, default=False)          # 是否已签订数据处理协议 / 跨国 DPA
    dsr_channel_available = Column(Boolean, default=True)    # 是否提供个人信息主体权利响应渠道
    
    created_at = Column(DateTime, default=datetime.utcnow)

class PIAResult(Base):
    __tablename__ = "pia_assessments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    flow_id = Column(Integer, nullable=False)
    legal_pathway = Column(String(64), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)          # Low, Medium, High, Critical
    findings = Column(Text, nullable=False)                  # 审计发现与缺陷
    remediation_plan = Column(Text, nullable=False)          # 整改建议
    assessed_at = Column(DateTime, default=datetime.utcnow)
```

### 4.2 跨境法规路径判定与 PIA 评分引擎 (`compliance_engine.py`)
```python
"""
compliance_engine.py: 依据《个人信息保护法》与 2024 网信办第16号规定进行出境路径判定与 PIA 打分
"""
from typing import Dict, Any, Tuple

class PIPLComplianceEngine:
    
    @staticmethod
    def determine_regulatory_pathway(
        business_unit: str,
        processing_purpose: str,
        annual_individuals: int,
        sensitive_individuals: int,
        is_hr_management: bool = False,
        is_contract_fulfillment: bool = False
    ) -> Tuple[str, str]:
        """
        根据《促进和规范数据跨境流动规定》（2024年3月22日施行）判定出境合规路径
        """
        # 1. 判定法定豁免情形 (第5条)
        if is_contract_fulfillment:
            return (
                "法定豁免情形 (Exempted)", 
                "符合第5条第(一)项：为订立、履行个人作为一方当事人的合同（如跨境订票/国际机票酒店）所必需，免予申报安全评估与订立标准合同。"
            )
        
        if is_hr_management:
            return (
                "法定豁免情形 (Exempted)", 
                "符合第5条第(二)项：按照依法制定的劳动规章制度和依法签订的集体合同实施跨境人力资源管理所必需，免予申报安全评估与订立标准合同。"
            )

        # 2. 判定强制申报国家网信部门安全评估情形 (第7条)
        # 关键红线：自当年1月1日起累计向境外提供100万人以上个人信息，或向境外提供1万人以上敏感个人信息
        if annual_individuals >= 1_000_000 or sensitive_individuals >= 10_000:
            return (
                "国家网信办安全评估 (Mandatory CAC Assessment)",
                f"触发强制安全评估门槛：年累计自然人达 {annual_individuals:,} (门槛100万) 或 敏感个人信息达 {sensitive_individuals:,} (门槛1万)。必须报送省级网信办初审并报国家网信办评估。"
            )
        
        # 3. 判定订立标准合同 (SCC) 备案或个人信息保护认证 (第8条)
        if (100_000 <= annual_individuals < 1_000_000) or (0 < sensitive_individuals < 10_000):
            return (
                "标准合同备案 (Standard Contract - SCC Filing)",
                f"属于标准合同备案范围：自当年1月1日起累计向境外提供非敏感个人信息在10万人至100万人之间，或敏感个人信息未满1万人。须在出境后向省级网信办备案标准合同与PIA报告。"
            )
            
        # 4. 其它豁免情形 (非敏感个人信息未满10万人)
        return (
            "小规模数据法定豁免 (Exempted - Under 100k)",
            f"年累计向境外提供不满10万人个人信息且不包含敏感个人信息，免予申报安全评估与订立标准合同。"
        )

    @staticmethod
    def calculate_pia_risk_score(flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PIA 风险矩阵定量评估模型:
        Inherent Risk (固有风险) = Sensitivity_Weight * Volume_Weight * Recipient_Jurisdiction_Weight
        Residual Risk (残留风险) = Inherent Risk - Safeguards_Mitigation
        """
        # 敏感度权重
        is_sensitive = "Sensitive" in flow_data.get("sensitivity_level", "")
        sensitivity_weight = 5.0 if is_sensitive else 2.0
        
        # 规模权重
        vol = flow_data.get("annual_individuals_count", 0)
        if vol >= 1_000_000:
            volume_weight = 5.0
        elif vol >= 100_000:
            volume_weight = 3.5
        elif vol >= 10_000:
            volume_weight = 2.0
        else:
            volume_weight = 1.0
            
        # 接收方法律环境权重 (对齐 PIPL 第38条与国家安全考量)
        country = flow_data.get("recipient_country", "").upper()
        if country in ["US"]:
            # 存在 FISA 702 / CLOUD Act 长臂管辖风险
            jurisdiction_weight = 4.0
        elif country in ["SG", "JP", "EU", "GB"]:
            jurisdiction_weight = 2.5
        else:
            jurisdiction_weight = 3.0
            
        inherent_risk = sensitivity_weight * volume_weight * jurisdiction_weight # 最高 5*5*4 = 100
        
        # 安全缓解因子计算
        mitigation = 0.0
        findings = []
        remediations = []
        
        # 检查 1: 单独同意 (PIPL 第39条)
        if flow_data.get("has_separate_consent"):
            mitigation += 20.0
        else:
            findings.append("【高危违规】未针对该出境场景获取自然人明确的'单独同意'(Separate Consent)。")
            remediations.append("在前端应用/授权协议中增加独立的出境弹窗或勾选项，详细告知境外接收方名称、联系方式、处理目的及权利行使方式。")

        # 检查 2: 传输加密
        transit_enc = flow_data.get("transit_encryption", "")
        if "TLS 1.3" in transit_enc or "mTLS" in transit_enc:
            mitigation += 15.0
        elif "TLS 1.2" in transit_enc:
            mitigation += 10.0
        else:
            findings.append("【技术缺陷】传输加密低于 TLS 1.2 标准或采用明文出境。")
            remediations.append("升级网络出口网关，全量强制使用 TLS 1.3 或双向证书校验 mTLS。")

        # 检查 3: 跨国数据处理协议 (DPA / SCC条款)
        if flow_data.get("has_dpa_signed"):
            mitigation += 20.0
        else:
            findings.append("【合规缺失】与境外接收方未签订正式数据处理协议（DPA）或未锁定网信办标准合同法定条款。")
            remediations.append("法务介入，推动与境外接收实体签署包含审计权、违约连带责任的标准合同。")

        # 检查 4: 个人权利响应机制 (PIPL 第47条)
        if flow_data.get("dsr_channel_available"):
            mitigation += 15.0
        else:
            findings.append("【机制不足】未向境内自然人提供境外数据主体的查阅、复制、更正与删除申请渠道。")
            remediations.append("在隐私政策与支持中心建立专门的 DSR (Data Subject Rights) 工单流转通道。")

        residual_risk = max(0.0, inherent_risk - mitigation)
        
        # 风险等级映射
        if residual_risk >= 50.0:
            risk_level = "Critical (极高风险 - 阻断出境)"
        elif residual_risk >= 30.0:
            risk_level = "High (高风险 - 需立即整改)"
        elif residual_risk >= 15.0:
            risk_level = "Medium (中风险 - 限制性放行)"
        else:
            risk_level = "Low (低风险 - 合规达标)"
            
        return {
            "inherent_risk": round(inherent_risk, 2),
            "mitigation_score": round(mitigation, 2),
            "residual_risk": round(residual_risk, 2),
            "risk_level": risk_level,
            "findings": findings,
            "remediation_plan": remediations
        }
```

### 4.3 标准合同 (SCC) 申报材料自动生成模板 (`scc_report_generator.py`)
```python
"""
scc_report_generator.py: 自动渲染符合国家网信办模板要求的《个人信息出境个人信息保护影响评估报告》Markdown
"""
from datetime import datetime

def generate_scc_markdown_report(flow: dict, pia: dict) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d")
    report = f"""# 个人信息出境个人信息保护影响评估报告 (自评估备案模板)
**申报单位**：跨国企业在华运营实体 / Trip.Biz China Entity  
**评估日期**：{now_str}  
**系统/业务名称**：{flow['system_name']} ({flow['business_unit']})  

---

## 第一部分：出境基本信息与必要性分析
1. **个人信息处理者基本情况**：
   - 业务板块：{flow['business_unit']}
   - 业务系统：{flow['system_name']}
2. **境外接收方基本情况**：
   - 境外接收方名称：{flow['recipient_name']}
   - 所在国家/地区：{flow['recipient_country']}
   - 接收方组织性质：{flow['recipient_type']}
3. **出境目的与合法性基础**：
   - 出境业务目的：{flow['processing_purpose']}
   - 法律依据：符合《中华人民共和国个人信息保护法》第十三条及第三十八条规定。

## 第二部分：拟出境个人信息的规模与敏感度
- **数据分类**：{flow['data_category']}
- **涉及字段详情**：{flow['data_fields']}
- **敏感级别判定**：{flow['sensitivity_level']}
- **年累计自然人数量**：{flow['annual_individuals_count']:,} 人
- **涉及敏感个人信息自然人数量**：{flow['sensitive_individuals_count']:,} 人

## 第三部分：跨境传输与境外保护技术措施
- **传输链路安全**：采用 {flow['transit_encryption']} 强加密算法隧道传输，杜绝明文流转。
- **静态存储加密**：在境内集约存储与境外接收方落盘均实施 {flow['rest_encryption']} 密钥管理隔离。
- **单独同意获得情况**：{'已取得境内个人明确单独同意' if flow['has_separate_consent'] else '【需整改】尚未全量取得单独同意'}。
- **境外主体权利支持**：{'已建立端到端 DSR 响应流程' if flow['dsr_channel_available'] else '尚未完全覆盖'}。

## 第四部分：风险评估结论与整改行动计划
- **固有风险分值**：{pia['inherent_risk']}
- **已实施缓解分值**：{pia['mitigation_score']}
- **综合残留风险评级**：{pia['risk_level']}

### 发现的问题与审计缺陷：
"""
    for i, finding in enumerate(pia['findings'], 1):
        report += f"{i}. {finding}\n"
    if not pia['findings']:
        report += "经评估，未发现严重合规不符合项。\n"
        
    report += "\n### 整改与安全防范措施（CAP）：\n"
    for i, plan in enumerate(pia['remediation_plan'], 1):
        report += f"{i}. {plan}\n"
    if not pia['remediation_plan']:
        report += "现有控制措施充分，同意按标准合同备案流程提交网信办申报。\n"

    report += """
---
**评估人**：Senior IT GRC / Cyber Security Lead  
**签批人（Data Protection Officer）**：____________________
"""
    return report
```

---

## 五、 测试验证与测试用例（模拟三大真实出境场景）

### 5.1 测试场景设计
为了覆盖不同合规路径（法定豁免、标准合同备案、强制安全评估），设计以下 3 个高频出境用例：

| 用例编号 | 业务场景 | 业务实体 | 年累计人数 | 敏感信息 | 核心字段 | 预期合规路径判定 | 预期风险评级 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | 跨国企业员工薪资与绩效同步至总部系统 | Global HR (Workday) | 1,800 | 包含 (银行卡/薪资) | 员工工号, 姓名, 身份证, 工资账户, 绩效评分 | **法定豁免** (劳动法必要人力资源管理) | Low / Medium (取决于DPA与加密) |
| **TC-02** | Trip.Biz 商旅全球国际酒店与机票预订跨境同步 | Trip.Biz Travel Core | 350,000 | 包含 (护照/信用卡) | 姓名, 护照号, 国际机票行程, 信用卡CVV令牌 | **标准合同备案 (SCC)** (10万~100万人之间) | High (若缺少单独同意与DPA) -> 达标后降为 Low |
| **TC-03** | 海外跨国游戏全球同服实时战斗日志与玩家数据同步 | Riot Global Telemetry | 2,500,000 | 少量 (IP/设备/邮箱) | 玩家ID, 注册邮箱, 客户端IP, 硬件指纹, 充值记录 | **国家网信办安全评估 (Mandatory CAC Assessment)** (超100万人) | High/Critical (必须网信办现场审查) |

### 5.2 自动化测试用例代码 (`test_compliance_engine.py`)
```python
"""
test_compliance_engine.py: 自动化验证合规判断与评分逻辑
"""
import pytest
from compliance_engine import PIPLComplianceEngine

def test_tc01_hr_exemption():
    pathway, reason = PIPLComplianceEngine.determine_regulatory_pathway(
        business_unit="Global HR",
        processing_purpose="Cross-border employee payroll",
        annual_individuals=1800,
        sensitive_individuals=1800,
        is_hr_management=True
    )
    assert "法定豁免" in pathway
    assert "实施跨境人力资源管理所必需" in reason

def test_tc02_trip_biz_scc_threshold():
    pathway, reason = PIPLComplianceEngine.determine_regulatory_pathway(
        business_unit="Trip.Biz",
        processing_purpose="International Hotel Booking",
        annual_individuals=350000,
        sensitive_individuals=5000,
        is_contract_fulfillment=False # 假设为海外业务画像与分析场景
    )
    assert "标准合同备案" in pathway
    
    # 模拟未打勾单独同意与未签 DPA 的风险评分
    flow_data = {
        "sensitivity_level": "Sensitive Personal Info",
        "annual_individuals_count": 350000,
        "recipient_country": "SG",
        "transit_encryption": "TLS 1.3",
        "has_separate_consent": False,
        "has_dpa_signed": False,
        "dsr_channel_available": True
    }
    pia = PIPLComplianceEngine.calculate_pia_risk_score(flow_data)
    assert "High" in pia["risk_level"] or "Critical" in pia["risk_level"]
    assert any("单独同意" in f for f in pia["findings"])

def test_tc03_riot_cac_assessment_threshold():
    pathway, reason = PIPLComplianceEngine.determine_regulatory_pathway(
        business_unit="Gaming Ops",
        processing_purpose="Global telemetry",
        annual_individuals=2500000,
        sensitive_individuals=0
    )
    assert "国家网信办安全评估" in pathway
    assert "100万" in reason
```

---

## 六、 简历包装（STAR 法则）与面试深度追问策略

### 6.1 简历项目包装（中英文版）

#### 中文版本（可直接用于猎聘/Boss直聘/英文外企中文简历）：
> **项目名称：亚太及中国区跨境数据流动安全治理与 PIPL 合规审计平台**  
> **角色**：项目负责人 / Senior GRC & Security Lead  
> - **S (背景)**：面对中国《个人信息保护法》(PIPL) 及 2024 网信办第 16 号跨境流动新规的强监管要求，公司在华业务（包括海外商旅出差系统、跨国 HR 与全球运营数据）存在涉及上百万境内用户与员工数据的出境风险，亟需解决跨国数据本地化、合规路径界定与境外接收方管控痛点。  
> - **T (任务)**：主导全业务跨境数据资产血缘梳理，建立个人信息出境影响评估（PIA）自动化评估矩阵，打通境内外法务、研发及海外 IT 基础设施的安全控制闭环，完成标准合同（SCC）备案材料准备与安全差距整改。  
> - **A (行动)**：  
>   1. 组织研发与产品完成 30+ 业务系统的数据字段级测绘，识别出 4 个核心出境链路，分类分级锁定 35 万+ 敏感个人信息（护照、信用卡等）；  
>   2. 严格落实 PIPL 核心要求：重构前端授权流程实现“单独同意（Separate Consent）”覆盖率达 100%；推动网络侧强制全链路 TLS 1.3 传输加密与 KMS 存储加密；  
>   3. 基于 2024 网信办最新规则设计合规判定引擎，精准甄别法定豁免（HR跨国管理/必要合同订立）与备案门槛，主导输出标准合同（SCC）自评估报告并与境外接收方完成双向 DPA 法律签署。  
> - **R (成果)**：将跨境合规审查周期从单次 4 周压缩至 3 天内，消除 12 项重大合规阻断项，以 0 处罚、0 监管质询平稳通过内外部多轮合规审查，为公司亚太业务出海规避了年营收 5% 的潜在巨额罚款风险。

#### 英文版本（用于 LinkedIn、外企官网申请）：
> **Project: APAC & China Cross-Border Data Transfer Governance & PIPL Compliance Automation**  
> **Role**: Senior IT GRC / Cyber Security Lead  
> - **Situation**: In response to China’s PIPL and CAC Order No. 16 on cross-border data flows, the organization faced stringent compliance requirements concerning data localization, cross-border HR transfers, and global platform data synchronizations involving sensitive personal information.  
> - **Task**: Architected an end-to-end cross-border data transfer audit and assessment mechanism to evaluate regulatory pathways, conduct automated Personal Information Protection Impact Assessments (PIA/DPIA), and establish technical controls for overseas recipients.  
> - **Action**:  
>   1. Executed comprehensive data mapping across 30+ core business systems, identifying cross-border data lineage for over 350k+ records and classifying sensitive personal information (SPI) such as passports and financial data.  
>   2. Enforced technical and procedural controls aligned with PIPL: achieved 100% separate consent coverage on consumer-facing touchpoints, enforced TLS 1.3 in-transit and AES-256 at-rest encryption, and integrated DSR workflows.  
>   3. Developed an automated DPIA risk-scoring framework and Standard Contractual Clauses (SCC) filing package generator; spearheaded cross-border DPA negotiations with overseas entities and cloud hosting providers.  
> - **Result**: Shortened compliance assessment turnaround from 4 weeks to under 3 days, eradicated 12 high-risk compliance gaps, and ensured 100% adherence to regulatory mandates without disrupting global cross-functional operations.

---

### 6.2 面试高频追问及优秀应答策略（满分回答话术）

#### Q1: 2024年3月网信办发布了《促进和规范数据跨境流动规定》（第16号令），这对跨国企业的出境合规策略带来了哪些重大变化？你在项目中是如何落地的？
> **优秀应答关键点**：
> 1. **豁免门槛利好**：第 16 号令明确对三类常见场景实行“法定豁免”：国际机票酒店预订/跨境购物等**订立合同所必需**、跨境员工**人力资源管理所必需**、紧急生命财产保护。此外，针对非敏感个人信息累计**不满 10 万人**的情形予以豁免。
> 2. **监管门槛调整**：明确将强制安全评估红线定为“当年1月1日起累计出境个人信息达 100 万人以上，或敏感个人信息满 1 万人”。
> 3. **落地策略**：在项目中，我没有采取“一刀切”都去报安全评估的激进方案，而是主导了**“业务场景解耦与范围缩减”**。将真正的日常 HR 跨国流转归入豁免路径（但依然保留内部 PIA 档案和加密要求）；将涉及出境的海外酒店订单与第三方业务独立切分，精准控制敏感数据出境人次在 1 万人以下，从而合规走**标准合同备案（SCC）**路径，大幅节约了监管申报与外部律所审查成本。

#### Q2: PIPL 第39条要求个人信息出境必须取得个人的“单独同意”（Separate Consent），技术和产品上你们是如何实现的？遇到了什么阻力？
> **优秀应答关键点**：
> 1. **技术实现**：不能使用“概括性勾选”或将出境协议深埋在《用户隐私协议》中。我们在前端采用了**“分级触发式独立弹窗/专项目录勾选”**。明确展示境外接收方的法定全称、联系方式、具体处理目的、出境涉及字段明细，并在后端数据库设立独立的 `consent_records` 表，记录 Consent ID、时间戳、用户 IP、展示协议版本哈希，实现可审计证据链（Immutable Audit Trail）。
> 2. **业务阻力与妥协**：业务团队强烈反对弹窗过多导致注册转化率下降。我的解决方案是**“按需延迟授权（Just-in-Time Consent）”**：用户仅在境内浏览时无需弹出出境同意；只有当用户点击“预订海外酒店”或“参与海外同服对战”的核心结账/匹配节点时，再弹出针对该特定境外实体的独立授权，既满足监管对“充分知情”的要求，又将转化损耗降到最低。

#### Q3: 如果境外接收方所在的国家（例如美国）存在政府长臂管辖（如 FISA 702 或 CLOUD Act），你在做 PIA/DPIA 评估时如何论证风险可控？
> **优秀应答关键点**：
> 1. **法律层面论证**：参考网信办标准合同中关于境外接收方所在国法律环境评估的要求，分析当地法律对个人信息保护的基本水平，以及是否有强制访问先例。
> 2. **技术中立与技术缓解（Technical Safeguards）**：这是安全技术人员的核心防线。在技术评估报告中，我主张建立**“带外密钥管理与假名化/Tokenization”**：
>    - 核心敏感个人信息（如身份证、真实手机号）在境内经本地 KMS 加密或哈希脱敏，仅将生成的不可逆 Token 传输至境外；
>    - 针对必须出境的信息，采用境外接收方无法单方面强制解密的加密方案（如境外主体仅拥有使用权，数据由中国境内实体负责集中托管审计），从物理和架构层面切断外部监管机构通过云厂商直接提取明文的可能性。

#### Q4: 在做跨国数据流动合规时，如何与跨国总部（Global Security/Legal）团队打交道？他们不理解中国特殊法规怎么办？
> **优秀应答关键点**：
> 1. **对齐通用语言（Map to Global Frameworks）**：不要直接甩中国法条代码。我会将 PIPL 的要求映射到他们熟知的 **GDPR**（如 PIPL 的单独同意对应 GDPR Art. 49 Derogations；PIPL 敏感信息对应 GDPR Special Categories）和 **ISO 27001 / SOC 2** 控制项。
> 2. **量化风险暴露（Quantify Business Risk）**：向 Global Head 阐明中国法规不仅包含顶格“年营业额 5% 或 5000 万人民币”的企业罚款，还包含对直接主管人员的个人罚款及行政停业/下架风险。
> 3. **提供交钥匙方案（Turnkey Solutions）**：避免只报问题，直接给工具。我制定的标准化 PIA 英文问卷和自动化收集脚本，直接嵌入现有的 ServiceNow / Jira 流程中，海外运维和研发只需提供系统拓扑，其余判定由我们平台自动产出，降低了跨国协同摩擦。

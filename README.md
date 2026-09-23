# PIPL Cross-Border Data Transfer Audit

> **一句话**：FastAPI + 跨境数据资产测绘 + DPIA + 标准合同生成
> 对齐 **Senior IT GRC Specialist** / **Senior Cyber Security Analyst** 岗位核心能力。

---

## ✨ 状态

**v0.1 完成**（2026-09-23）— 端到端实跑：43/43 tests PASS

| 模块 | 完成度 | 备注 |
|---|---|---|
| 数据模型 + DB schema (8 张表) | ✅ | `app/schema.sql` |
| 4 大合规路径判定 | ✅ | SECURITY_ASSESSMENT / SCC / CERTIFICATION / EXEMPTION |
| DPIA 5 维评分 + 一票否决 | ✅ | 无单独同意 → CRITICAL |
| PIPL SCC 合同模板 | ✅ | 含 SPI 特别条款 + 72h 通知 + 30 天销毁 |
| 数据资产 + 数据流 + 接收方 seed | ✅ | 6 assets / 6 recipients / 7 flows + PIA |
| FastAPI 18 endpoints | ✅ | 含 evidence SHA-256 防篡改 |
| Vanilla JS Dashboard | ✅ | 6 tab (流向/DPIA/接收方/exception/pathway/SCC) |
| 端到端测试 | ✅ | **43/43 PASS** |
| GitHub public | ✅ | `awuawuheiyohei/09-pipl-cross-border` |

## 📁 项目结构

```
09-pipl-cross-border/
├── README.md
├── pyproject.toml
├── .env.example
├── main.py                     # CLI 入口 (serve / help)
├── app/
│   ├── __init__.py            # strip_thinking + call_llm + DB_PATH 重导出
│   ├── main.py                # FastAPI app + lifespan + static mount
│   ├── schema.sql             # 8 张表
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # 18 endpoints
│   └── models/
│       ├── __init__.py
│       ├── db.py              # get_conn / init_db / row_to_dict / write_audit
│       ├── pipl_models.py     # 3 大引擎: pathway / DPIA / SCC
│       └── seed.py            # 6+6+7+4 seed
├── static/
│   └── index.html             # Dashboard 6 tab (Vanilla JS, 0 CDN)
├── tests/
│   └── test_routes.py         # 43 tests
└── docs/
    └── PRD.md
```

## 🚀 快速开始

```bash
cd /Users/jiangwenrui/Downloads/mass/09-pipl-cross-border
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 启动服务（端口 5036）
python main.py serve
# 浏览器: http://localhost:5036/
# API docs: http://localhost:5036/docs

# 跑测试
pytest tests/ -v
```

## 🔑 核心 API

| Endpoint | 方法 | 说明 |
|---|---|---|
| `/health` | GET | 健康检查 |
| `/api/dashboard/summary` | GET | Dashboard 总览（资产/流/PIA/exception/接收方统计） |
| `/api/assets` | GET | 数据资产列表（按 sensitivity / country 过滤） |
| `/api/flows` | GET / POST | 数据流列表 + 新建（自动同步生成 PIA） |
| `/api/flows/{flow_id}` | GET | 数据流详情（含 recipient + PIA + exceptions join） |
| `/api/recipients` | GET | 境外接收方列表（按 risk_level 过滤） |
| `/api/pia` | GET | PIA 评估列表 |
| `/api/pia/recompute/{flow_id}` | POST | 基于当前 control 重算 DPIA |
| `/api/exceptions` | GET | 合规风险例外 |
| `/api/exceptions/{id}/resolve` | POST | 标记 RESOLVED |
| `/api/pathway/determine` | POST | 4 大合规路径判定（SECURITY_ASSESSMENT / SCC / CERTIFICATION / EXEMPTION） |
| `/api/dpia/score` | POST | 单条 DPIA 5 维评分 |
| `/api/scc/generate` | POST | 生成 PIPL 标准合同（SCC） |
| `/api/evidence` | POST | 写入证据（SHA-256 防篡改） |
| `/api/audit` | GET | 审计 trail |
| `/api/admin/seed` | POST | 重置 seed 数据 |

## 📊 Dashboard 6 Tab

1. **🌐 数据出境流向** — 7 条 active 流，按风险等级 + 法律基础着色
2. **📊 DPIA 风险** — 5 维评分表 + 单条快速计算器
3. **🏢 接收方** — SCC 签约状态 / 数据保护法 / 认证 / 风险等级
4. **⚠️ 风险例外** — CRITICAL/HIGH 优先排序，OPEN 一键 RESOLVED
5. **🧭 Pathway 判定** — 输入 5 阈值 → 输出 4 路径 + 时间表
6. **📄 SCC 生成** — 基于数据流生成 PIPL 标准合同（含 SPI 条款）

## 🇨🇳 PIPL 合规依据

- 《中华人民共和国个人信息保护法》（2021）第 38 / 39 条
- 《数据出境安全评估办法》（网信办 2022）
- 《个人信息出境标准合同办法》（网信办 2023）
- 网信办令第 16 号（2024）阈值更新：
  - 累计向境外提供 ≥ 100 万人 **或** SPI ≥ 1 万人（年度）→ 网信办安全评估
  - 跨国集团内部 → 个人信息保护认证
  - 非 CIIO + < 100 万人 且 SPI < 10 万人 → SCC 备案
  - < 1 万人且非必要 → 豁免

## 🧪 测试覆盖（43/43 PASS）

- 模型单测（pathway / DPIA / SCC）：12 个
- FastAPI 路由 smoke：31 个
  - /health / dashboard summary
  - 资产 / 流 / 接收方 / PIA / exception CRUD
  - Pathway 判定 4 路径全覆盖
  - SCC 生成 SPI / 非 SPI
  - Evidence SHA-256
  - Audit trail 记录

## 📝 PRD 来源

本项目基于 `/Users/jiangwenrui/Downloads/mass/Interview/Security_and_GRC_14_Projects_Plan/09_PIPL_Cross_Border_Data_Transfer_Audit.md` 完整规划。

## 📄 License

MIT — 自由使用、修改、二次分发。

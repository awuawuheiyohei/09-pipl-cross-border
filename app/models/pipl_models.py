"""
PIPL 跨境数据传输合规模型
- 阈值触发：网信办安全评估 vs SCC 备案 vs 个人信息保护认证
- DPIA 风险打分（5 维度）
- SCC 标准合同生成模板
"""

# ============================================
# 1. PIPL 跨境出境 3 大路径判定
# ============================================
# 网信办令第16号（2024）阈值：
# 1) 网信办安全评估：处理 100 万人以上 + 跨境；SPI 跨境 ≥ 10 万人；CIIO 跨境
# 2) SCC 备案：非 CIIO + < 100 万人 或 SPI < 10 万人
# 3) 个人信息保护认证：跨国集团内跨境
# 4) 豁免：< 1 万人（必要）

# 阈值定义
THRESHOLDS = {
    "SECURITY_ASSESSMENT_REQUIRED": {
        "name": "国家网信办安全评估",
        "triggers": [
            "处理个人信息 ≥ 100 万人",
            "SPI（敏感个人信息）跨境 ≥ 10 万人",
            "CIIO（关键信息基础设施运营者）",
            "累计向境外提供 ≥ 100 万人 / SPI ≥ 1 万人（年度）",
        ],
        "timeline": "60 个工作日内决定（复杂可延长）",
        "fee": "免费",
        "validity": "3 年",
    },
    "SCC_FILING": {
        "name": "标准合同 (SCC) 备案",
        "triggers": [
            "非 CIIO",
            "< 100 万人 且 SPI < 10 万人",
            "需与境外接收方签署 PIPL 标准合同",
        ],
        "timeline": "10 个工作日内备案（实质性审查 45 天）",
        "fee": "免费",
        "validity": "3 年（续签）",
    },
    "CERTIFICATION": {
        "name": "个人信息保护认证",
        "triggers": [
            "跨国集团内部跨境",
            "或专业机构认证（GB/T 39335）",
        ],
        "timeline": "60 个工作日",
        "fee": "市场化定价",
        "validity": "3 年",
    },
}


def determine_pipl_pathway(
    is_ciio: bool,
    total_subjects: int,
    spi_subjects: int,
    is_internal_group: bool,
    is_necessary: bool,
) -> str:
    """根据 PIPL + 网信办令第16号判定 4 种合规路径
    返回：SECURITY_ASSESSMENT / SCC / CERTIFICATION / EXEMPTION
    """
    # 豁免：< 1 万人且非必要
    if total_subjects < 10_000 and not is_necessary:
        return "EXEMPTION"

    # 网信办安全评估：满足任一
    if is_ciio:
        return "SECURITY_ASSESSMENT"
    if total_subjects >= 1_000_000:
        return "SECURITY_ASSESSMENT"
    if spi_subjects >= 100_000:
        return "SECURITY_ASSESSMENT"

    # 跨国集团内部
    if is_internal_group:
        return "CERTIFICATION"

    # 默认 SCC 备案
    return "SCC"


# ============================================
# 2. DPIA 5 维度评分
# ============================================
def compute_dpia_scores(
    necessity: int,        # 必要性 1-5
    risk: int,            # 风险 1-5
    sensitivity: int,     # 敏感度 1-5
    volume: int,          # 数据量级 1-5
    recipient: int,       # 接收方安全 1-5
    has_separate_consent: bool,
    scc_signed: bool,
) -> dict:
    """DPIA 风险打分"""
    # 总分 = (necessity + risk + sensitivity + volume) * 5 - recipient * 2
    base_score = necessity + risk + sensitivity + volume
    recipient_bonus = recipient * 2  # 接收方越好分越高（减小最终风险）
    raw_total = base_score * 5 - recipient_bonus

    # 关键控制项一票否决
    has_separate_consent = bool(has_separate_consent)
    scc_signed = bool(scc_signed)

    # 风险等级
    if not has_separate_consent:
        risk_level = "CRITICAL"
    elif not scc_signed:
        risk_level = "HIGH"
    elif raw_total >= 75:
        risk_level = "CRITICAL"
    elif raw_total >= 60:
        risk_level = "HIGH"
    elif raw_total >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # 推荐（基于 risk level）
    recommendations = []
    if not has_separate_consent:
        recommendations.append("CRITICAL: 需取得自然人**单独同意**（PIPL 第39条）")
    if not scc_signed:
        recommendations.append("CRITICAL: 必须与境外接收方签署**标准合同（SCC）**")
    if sensitivity >= 4:
        recommendations.append("HIGH: SPI 需额外加密 + 脱敏 + 单独同意")
    if volume >= 4:
        recommendations.append("MEDIUM: 数据量级 ≥ 100万 → 网信办安全评估")
    if recipient <= 2:
        recommendations.append("HIGH: 接收方安全水平不足 → 重新评估或更换接收方")

    return {
        "raw_total": raw_total,
        "base_score": base_score,
        "recipient_bonus": recipient_bonus,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "has_separate_consent": has_separate_consent,
        "scc_signed": scc_signed,
    }


# ============================================
# 3. SCC 标准合同生成（模板）
# ============================================
SCC_TEMPLATE = """
# 个人信息出境标准合同
# (PIPL Standard Contract for Cross-Border Transfer of Personal Information)

依据《中华人民共和国个人信息保护法》第38条及相关法规，
双方就个人信息出境事宜达成如下协议：

## 一、双方信息

**出境方**：
- 名称：{exporter_name}
- 所在地：{exporter_country}
- 联系方式：{exporter_contact}

**境外接收方**：
- 名称：{recipient_name}
- 所在地：{recipient_country}
- 数据保护法律：{recipient_law}

## 二、出境个人信息明细

- 数据类别：{data_categories}
- 涉及主体类别：{data_subject}
- 年均数据量：{volume_records} 条
- 传输方式：{transfer_method}
- 传输频率：{frequency}

## 三、敏感个人信息特别约定（如适用）

{sensitive_clauses}

## 四、双方权利义务

### 出境方义务：
1. 已向自然人告知出境情况并取得**单独同意**；
2. 已完成个人信息保护影响评估（PIA）；
3. 采取加密、备份、访问控制等技术措施；
4. 配合网信办安全评估或备案。

### 境外接收方义务：
1. 仅在约定目的、范围内处理个人信息；
2. 不向第三方再提供（除非取得同等同意）；
3. 接到权利请求后 30 天内转交出境方处理；
4. 发生个人信息泄露后 **72 小时内**通知出境方；
5. 合同终止后 **30 天内** 返还或删除所有个人信息；
6. 接受出境方审计。

## 五、违约与争议

1. 任何一方违约，应承担违约责任；
2. 因本协议发生的争议，提交中国法院管辖（除非双方书面约定仲裁）；
3. 适用中华人民共和国法律。

## 六、生效

本合同自双方签字之日起生效，有效期 **3 年**。

---

签字：

出境方（盖章）：___________________   日期：_______________

境外接收方（盖章）：___________________   日期：_______________
"""


def generate_scc_contract(
    exporter_name: str,
    exporter_country: str,
    exporter_contact: str,
    recipient_name: str,
    recipient_country: str,
    recipient_law: str,
    data_categories: list,
    data_subject: str,
    volume_records: int,
    transfer_method: str,
    frequency: str,
    is_spi: bool = False,
) -> str:
    """生成 PIPL 标准合同（SCC）"""
    sensitive_clauses = ""
    if is_spi:
        sensitive_clauses = (
            "本合同涉及敏感个人信息（SPI），双方确认：\n"
            "- 已取得自然人**单独同意**（PIPL 第29条）\n"
            "- 传输前后均使用 AES-256 加密\n"
            "- 接收方严格限制访问权限（最小权限原则）"
        )
    else:
        sensitive_clauses = "本合同不涉及敏感个人信息。"

    return SCC_TEMPLATE.format(
        exporter_name=exporter_name,
        exporter_country=exporter_country,
        exporter_contact=exporter_contact,
        recipient_name=recipient_name,
        recipient_country=recipient_country,
        recipient_law=recipient_law,
        data_categories=", ".join(data_categories),
        data_subject=data_subject,
        volume_records=volume_records,
        transfer_method=transfer_method,
        frequency=frequency,
        sensitive_clauses=sensitive_clauses,
    )


# ============================================
# 4. Demo 数据（中国典型场景）
# ============================================
DATA_CATEGORIES_OPTIONS = [
    "PII_NAME", "PII_ID_CARD", "PII_PHONE", "PII_EMAIL", "PII_ADDRESS",
    "SPI_BIOMETRIC", "SPI_HEALTH", "SPI_FINANCIAL", "SPI_LOCATION",
    "BEHAVIORAL", "EMPLOYMENT", "BIOMETRIC_FACE",
]


if __name__ == "__main__":
    # 测试
    print("=== PIPL Pathway Determination ===")
    print(f"100 万人 SPI 10 万 → {determine_pipl_pathway(False, 1_500_000, 100_000, False, True)}")
    print(f"50 万人 SPI 5 千 → {determine_pipl_pathway(False, 500_000, 5_000, False, True)}")
    print(f"跨国集团 → {determine_pipl_pathway(False, 200_000, 5_000, True, True)}")
    print(f"< 1 万人 非必要 → {determine_pipl_pathway(False, 5_000, 100, False, False)}")
    print(f"CIIO → {determine_pipl_pathway(True, 50_000, 1_000, False, True)}")

    # DPIA 测试
    print("\n=== DPIA Scoring ===")
    r = compute_dpia_scores(necessity=3, risk=4, sensitivity=5, volume=4, recipient=2,
                            has_separate_consent=True, scc_signed=False)
    print(f"SPI 高 + 无 SCC: {r['risk_level']} (score={r['raw_total']})")
    print(f"  Recommendations: {r['recommendations']}")

    # SCC 生成
    print("\n=== SCC Generation ===")
    scc = generate_scc_contract(
        exporter_name="Trip.Biz (Beijing) Co., Ltd.",
        exporter_country="中国 北京",
        exporter_contact="dpo@tripbiz.com",
        recipient_name="Trip.Biz USA Inc.",
        recipient_country="美国 加利福尼亚",
        recipient_law="CCPA + GDPR (EU customers)",
        data_categories=["EMPLOYMENT", "PII_NAME", "PII_EMAIL"],
        data_subject="在职员工",
        volume_records=250000,
        transfer_method="API_SYNC",
        frequency="DAILY",
        is_spi=False,
    )
    print(scc[:400])
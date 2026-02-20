import json
from .criteria import CRITERIA
from .scorer import calculate_weighted_score

VERDICT_LABELS = {
    "INSTALL": "✅  推荐安装",
    "MAYBE":   "⚠️   视情况而定",
    "SKIP":    "❌  不建议安装",
}


def generate_report(skill_name: str, evaluation: dict) -> str:
    """Generate a human-readable text report."""
    scores = evaluation["scores"]
    weighted = calculate_weighted_score(scores)
    verdict = evaluation.get("verdict", "MAYBE")
    verdict_label = VERDICT_LABELS.get(verdict, "❓ 未知")

    lines = []
    lines.append("=" * 62)
    lines.append(f"  Skill 质量评估报告：{skill_name}")
    lines.append("=" * 62)
    lines.append("")
    skill_type = evaluation.get("skill_type", "self-contained")
    type_label = "索引型" if skill_type == "index" else "自包含型"
    lines.append(f"  综合质量分：{weighted:.1f} / 100")
    lines.append(f"  评估结论：  {verdict_label}")
    lines.append(f"  Skill 类型：{type_label}")
    lines.append("")

    lines.append("─" * 62)
    lines.append("  各维度评分")
    lines.append("─" * 62)

    for criterion in CRITERIA:
        score_data = scores.get(criterion.key, {})
        score = score_data.get("score", 0)
        bar_filled = int(score / 5)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        lines.append(f"  {criterion.name:<16} [{bar}] {score:>3}/100  (权重 {criterion.weight}%)")

        for w in score_data.get("weaknesses", [])[:2]:
            lines.append(f"    ✗ {w}")
        for s in score_data.get("strengths", [])[:1]:
            lines.append(f"    ✓ {s}")
        lines.append("")

    lines.append("─" * 62)
    lines.append("  整体评价")
    lines.append("─" * 62)
    lines.append(f"  {evaluation.get('overall_summary', '')}")
    lines.append("")

    top_issues = evaluation.get("top_issues", [])
    if top_issues:
        lines.append("─" * 62)
        lines.append("  主要问题")
        lines.append("─" * 62)
        for i, issue in enumerate(top_issues, 1):
            lines.append(f"  {i}. {issue}")
        lines.append("")

    all_suggestions = []
    for criterion in CRITERIA:
        all_suggestions.extend(scores.get(criterion.key, {}).get("suggestions", []))

    if all_suggestions:
        lines.append("─" * 62)
        lines.append("  改进建议")
        lines.append("─" * 62)
        for s in all_suggestions[:5]:
            lines.append(f"  → {s}")
        lines.append("")

    lines.append("=" * 62)
    lines.append("")
    lines.append("  💡 提示：高分反映文档质量，不代表对你的项目有用。")
    lines.append("     通用主题的 skill（如编码规范、Git 规范）Claude 本身已掌握，")
    lines.append("     只有在需要强制约束特定行为或团队内部规范时才有安装价值。")
    return "\n".join(lines)


def generate_json_report(skill_name: str, evaluation: dict) -> dict:
    """Generate a machine-readable JSON report."""
    scores = evaluation["scores"]
    weighted = calculate_weighted_score(scores)
    return {
        "skill_name": skill_name,
        "weighted_score": weighted,
        "verdict": evaluation.get("verdict"),
        "overall_summary": evaluation.get("overall_summary"),
        "top_issues": evaluation.get("top_issues", []),
        "dimension_scores": {
            c.key: scores.get(c.key, {}).get("score", 0) for c in CRITERIA
        },
        "full_evaluation": evaluation,
    }

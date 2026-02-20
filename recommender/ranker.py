"""
Format recommendation results into human-readable output.
"""


TIER_LABELS = {
    "INSTALL_NOW": "🔥  强烈推荐安装",
    "RECOMMEND":   "✅  推荐安装",
    "OPTIONAL":    "🟡  可选安装",
    "SKIP":        "⬜  暂时跳过",
}


def _tier(relevance: int, weighted_score: float) -> str:
    if relevance >= 70 and weighted_score >= 80:
        return "INSTALL_NOW"
    if relevance >= 50 and weighted_score >= 75:
        return "RECOMMEND"
    if relevance >= 30:
        return "OPTIONAL"
    return "SKIP"


def format_recommendations(
    results: list[dict],
    tech_stack: str,
    project_type: str,
    show_skip: bool = False,
) -> str:
    lines = []
    lines.append("=" * 66)
    lines.append(f"  Skill 个人化推荐报告")
    lines.append(f"  技术栈：{tech_stack}")
    lines.append(f"  项目类型：{project_type}")
    lines.append("=" * 66)

    tiers: dict[str, list[dict]] = {
        "INSTALL_NOW": [],
        "RECOMMEND":   [],
        "OPTIONAL":    [],
        "SKIP":        [],
    }

    for r in results:
        t = _tier(r["relevance"], r["weighted_score"])
        r["_tier"] = t
        tiers[t].append(r)

    install_now = tiers["INSTALL_NOW"]
    recommend   = tiers["RECOMMEND"]
    optional    = tiers["OPTIONAL"]
    skip        = tiers["SKIP"]

    lines.append(f"\n  共 {len(results)} 个候选 skill")
    lines.append(f"  🔥 强烈推荐：{len(install_now)}  ✅ 推荐：{len(recommend)}  "
                 f"🟡 可选：{len(optional)}  ⬜ 跳过：{len(skip)}")

    for tier_key in ("INSTALL_NOW", "RECOMMEND", "OPTIONAL"):
        items = tiers[tier_key]
        if not items:
            continue
        lines.append("\n" + "─" * 66)
        lines.append(f"  {TIER_LABELS[tier_key]}")
        lines.append("─" * 66)
        for r in items:
            url_hint = f"  ({r['url']})" if r.get("url") else ""
            lines.append(
                f"  {r['name']:<35} "
                f"质量={r['weighted_score']:>5.1f}  "
                f"相关={r['relevance']:>3}  "
                f"综合={r['final_score']:>5.1f}"
            )
            if r.get("reason"):
                lines.append(f"    → {r['reason']}")
            if url_hint:
                lines.append(f"    {url_hint.strip()}")

    if show_skip and skip:
        lines.append("\n" + "─" * 66)
        lines.append(f"  {TIER_LABELS['SKIP']}")
        lines.append("─" * 66)
        for r in skip:
            lines.append(f"  {r['name']:<35} 相关={r['relevance']:>3}  {r.get('reason','')}")

    lines.append("\n" + "=" * 66)
    lines.append("")
    lines.append("  💡 提示：高相关性 + 高质量的 skill 才值得安装。")
    lines.append("     通用主题（编码规范、Git 规范等）Claude 本身已掌握，")
    lines.append("     优先安装针对你项目具体技术栈或团队规范的 skill。")
    return "\n".join(lines)

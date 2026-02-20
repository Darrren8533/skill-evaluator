"""
Batch evaluate all crawled skills and save results.
Then print a distribution analysis to identify framework blind spots.
"""
import json
import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from evaluator.scorer import evaluate_skill, calculate_weighted_score
from evaluator.report import generate_json_report

RESULTS_FILE = Path(__file__).parent.parent / "data" / "evaluation_results.json"
CACHE_FILE   = Path(__file__).parent.parent / "data" / "skills_cache.json"


def batch_evaluate(api_key: str, limit: int = None, force: bool = False) -> list[dict]:
    if not CACHE_FILE.exists():
        print("❌ No cache found. Run crawler first:")
        print("   python -m recommender.crawler")
        return []

    skills = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    if limit:
        skills = skills[:limit]

    # Load existing results to allow resuming
    existing = {}
    if RESULTS_FILE.exists() and not force:
        for r in json.loads(RESULTS_FILE.read_text(encoding="utf-8")):
            existing[r["skill_name"] + r.get("repo", "")] = r

    results = list(existing.values())
    skipped = 0

    for i, skill in enumerate(skills):
        key = skill["name"] + skill.get("repo", "")
        if key in existing:
            skipped += 1
            continue

        print(f"[{i+1}/{len(skills)}] Evaluating: {skill['name']} ({skill['source']}) ...")
        try:
            evaluation = evaluate_skill(skill["content"], api_key=api_key)
            report = generate_json_report(skill["name"], evaluation)
            report["repo"]   = skill["repo"]
            report["source"] = skill["source"]
            report["url"]    = skill.get("url", "")
            results.append(report)

            # Save after every eval (resume-safe)
            RESULTS_FILE.parent.mkdir(exist_ok=True)
            RESULTS_FILE.write_text(
                json.dumps(results, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            time.sleep(1.5)  # avoid Gemini rate limit

        except Exception as e:
            print(f"  ⚠ Failed: {e}")
            time.sleep(3)

    if skipped:
        print(f"\n⏭  Skipped {skipped} already-evaluated skills")

    print(f"\n✅ Done. {len(results)} results saved to {RESULTS_FILE}")
    return results


def analyze(results: list[dict]) -> None:
    if not results:
        print("No results to analyze.")
        return

    scores = [r["weighted_score"] for r in results]
    verdicts = [r["verdict"] for r in results]

    print("\n" + "=" * 62)
    print("  框架验证分析报告")
    print("=" * 62)

    # Score distribution
    print(f"\n  总评估数量：{len(scores)}")
    print(f"  平均分：    {sum(scores)/len(scores):.1f}")
    print(f"  最高分：    {max(scores):.1f}")
    print(f"  最低分：    {min(scores):.1f}")

    buckets = {"0-25": 0, "26-50": 0, "51-74": 0, "75-100": 0}
    for s in scores:
        if s <= 25:   buckets["0-25"]   += 1
        elif s <= 50: buckets["26-50"]  += 1
        elif s <= 74: buckets["51-74"]  += 1
        else:         buckets["75-100"] += 1

    print("\n" + "─" * 62)
    print("  分数分布")
    print("─" * 62)
    for bucket, count in buckets.items():
        bar = "█" * count
        print(f"  {bucket:>8}  {bar} {count}")

    # Verdict breakdown
    print("\n" + "─" * 62)
    print("  评估结论分布")
    print("─" * 62)
    for verdict, label in [("INSTALL","✅ 推荐安装"), ("MAYBE","⚠️  视情况"), ("SKIP","❌ 不建议")]:
        count = verdicts.count(verdict)
        pct = count / len(verdicts) * 100
        print(f"  {label}  {count} ({pct:.0f}%)")

    # Top 5 highest scores
    top5 = sorted(results, key=lambda x: x["weighted_score"], reverse=True)[:5]
    print("\n" + "─" * 62)
    print("  最高分 Top 5（验证：这些 skill 真的好吗？）")
    print("─" * 62)
    for r in top5:
        print(f"  {r['weighted_score']:>5.1f}  {r['skill_name']}  [{r['source']}]")
        print(f"         {r['url']}")

    # Bottom 5
    bot5 = sorted(results, key=lambda x: x["weighted_score"])[:5]
    print("\n" + "─" * 62)
    print("  最低分 Bottom 5（验证：这些 skill 真的差吗？）")
    print("─" * 62)
    for r in bot5:
        print(f"  {r['weighted_score']:>5.1f}  {r['skill_name']}  [{r['source']}]")
        print(f"         {r['url']}")

    # Potential blind spots
    print("\n" + "─" * 62)
    print("  ⚠  需要人工检查的异常（可能是框架盲点）")
    print("─" * 62)
    high_skip  = [r for r in results if r["weighted_score"] >= 70 and r["verdict"] == "SKIP"]
    low_install = [r for r in results if r["weighted_score"] < 50 and r["verdict"] == "INSTALL"]
    if high_skip or low_install:
        for r in high_skip + low_install:
            print(f"  !! {r['skill_name']}  score={r['weighted_score']}  verdict={r['verdict']}")
    else:
        print("  无明显异常，scoring 与 verdict 一致")

    print("\n" + "=" * 62)


if __name__ == "__main__":
    import sys
    api_key = os.environ.get("GEMINI_API_KEY") or (sys.argv[1] if len(sys.argv) > 1 else None)
    limit   = int(sys.argv[2]) if len(sys.argv) > 2 else None

    results = batch_evaluate(api_key=api_key, limit=limit)
    analyze(results)

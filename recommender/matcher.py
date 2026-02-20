"""
Personalized skill recommendation.

Loads evaluation results, asks Gemini to score relevance against
the user's tech stack + project type, then ranks by quality × relevance.
"""
import json
import os
from pathlib import Path
from typing import Optional

from google import genai

DATA_DIR = Path(__file__).parent.parent / "data"

MATCH_PROMPT = """\
你是一个 Claude Code Skill 推荐专家。

## 用户的项目信息

- **技术栈**：{tech_stack}
- **项目类型**：{project_type}
- **额外说明**：{extra_notes}

## 候选 Skill 列表

以下是所有可用的 skill，每条包含：编号、名称、质量分（0-100）、内容摘要。

{skill_list}

## 任务

对每个 skill 评估它对该用户项目的**相关性**（0-100）：
- 100 = 完全匹配，这个 skill 每天都会用到
- 70-99 = 高度相关，强烈推荐
- 40-69 = 有一定相关性，视情况而定
- 1-39 = 相关性低，可能偶尔有用
- 0 = 完全不相关，这个项目不会用到

## 输出格式（只输出 JSON，不要其他内容）

{{
  "matches": [
    {{
      "name": "<skill名称，与上方列表完全一致>",
      "relevance": <0-100整数>,
      "reason": "<一句话说明为什么相关或不相关>"
    }}
  ]
}}
"""


def _load_data() -> list[dict]:
    """Merge evaluation results with skill cache for rich metadata."""
    results_path = DATA_DIR / "evaluation_results.json"
    cache_path   = DATA_DIR / "skills_cache.json"

    with open(results_path, encoding="utf-8") as f:
        results = json.load(f)
    with open(cache_path, encoding="utf-8") as f:
        cache = json.load(f)

    # Build name → content map
    content_map = {item["name"]: item.get("content", "") for item in cache}

    # Merge
    merged = []
    for r in results:
        name = r["skill_name"]
        merged.append({
            "name":           name,
            "weighted_score": r["weighted_score"],
            "verdict":        r["verdict"],
            "summary":        r.get("overall_summary", ""),
            "content":        content_map.get(name, ""),
            "url":            r.get("url", ""),
        })
    return merged


def _build_skill_list(skills: list[dict]) -> str:
    lines = []
    for i, s in enumerate(skills, 1):
        lines.append(
            f"{i}. [{s['name']}] 质量分={s['weighted_score']}  "
            f"摘要：{s['summary'][:120]}"
        )
    return "\n".join(lines)


def _parse_response(raw: str) -> list[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    return data.get("matches", [])


def recommend(
    tech_stack: str,
    project_type: str,
    extra_notes: str = "",
    min_quality: float = 50.0,
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Return ranked skill recommendations for the user's project.

    Each item:
      name, weighted_score, verdict, relevance, final_score, reason, url
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=key)

    # Filter out low-quality skills before sending to AI
    all_skills = _load_data()
    candidates = [s for s in all_skills if s["weighted_score"] >= min_quality]

    skill_list_str = _build_skill_list(candidates)
    prompt = MATCH_PROMPT.format(
        tech_stack=tech_stack,
        project_type=project_type,
        extra_notes=extra_notes or "无",
        skill_list=skill_list_str,
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    matches = _parse_response(response.text)

    # Map name → relevance + reason
    relevance_map = {m.get("name", m.get("id", "")): m for m in matches}

    results = []
    for skill in candidates:
        match_info = relevance_map.get(skill["name"], {"relevance": 0, "reason": ""})
        relevance   = match_info.get("relevance", 0)
        # Final score = quality 60% + relevance 40%
        final_score = round(skill["weighted_score"] * 0.6 + relevance * 0.4, 1)
        results.append({
            "name":          skill["name"],
            "weighted_score": skill["weighted_score"],
            "verdict":       skill["verdict"],
            "relevance":     relevance,
            "final_score":   final_score,
            "reason":        match_info.get("reason", ""),
            "url":           skill["url"],
        })

    # Sort by final_score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results

import json
import os
from typing import Optional

from google import genai

from .criteria import CRITERIA
from .type_detector import detect_type, explain_type

# ── Prompt for self-contained skills ──────────────────────────────────────────
SELF_CONTAINED_PROMPT = """你是一个 Claude Code Skill 质量评估专家。

请评估以下「自包含型」SKILL.md 文件（所有内容在单一文件内）。

## 评估维度

{criteria_descriptions}

## 要评估的 SKILL.md 内容

```
{skill_content}
```

## 输出格式（只输出 JSON，不要其他内容）

{{
  "scores": {{
    "trigger_clarity": {{
      "score": <0-100的整数>,
      "strengths": ["优点"],
      "weaknesses": ["缺点"],
      "suggestions": ["建议"]
    }},
    "structure_completeness": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }},
    "step_executability": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }},
    "example_quality": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }},
    "scope_appropriateness": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }}
  }},
  "overall_summary": "整体评价（2-3句话）",
  "top_issues": ["问题1", "问题2"],
  "verdict": "INSTALL"
}}

verdict 规则：
- "INSTALL"：加权分 >= 75
- "MAYBE"：50-74
- "SKIP"：< 50
"""

# ── Prompt for index skills (point to other files) ────────────────────────────
INDEX_PROMPT = """你是一个 Claude Code Skill 质量评估专家。

这是一个「索引型」SKILL.md，它的作用是作为一组规则文件的导航目录，
真正的代码示例和详细说明在它引用的外部文件里。
请用适合「索引型」skill 的标准来评估。

## 索引型 Skill 的评估维度

### trigger_clarity（20%）
- 是否清楚说明什么场景下应该使用这套规则？
- trigger 描述是否具体？

### structure_completeness（25%）
- 规则分类是否清晰有层次？
- 是否有优先级排序（知道先看哪个）？
- 是否有「如何使用」的说明？

### step_executability（25%）
- 用户能否快速找到自己需要的规则？
- 导航路径是否清晰（从入口到具体规则）？
- 是否有快速参考（quick reference）？

### example_quality（20%）
注意：索引型 skill 不要求内联代码示例，但应该：
- 有足够的规则条目说明（每条规则至少有一句描述）
- 引用路径清晰可找到

### scope_appropriateness（10%）
- 覆盖的主题范围是否合理？
- 规则数量与主题复杂度匹配吗？

## 要评估的 SKILL.md 内容

```
{skill_content}
```

## 输出格式（只输出 JSON，不要其他内容）

{{
  "scores": {{
    "trigger_clarity": {{
      "score": <0-100的整数>,
      "strengths": ["优点"],
      "weaknesses": ["缺点"],
      "suggestions": ["建议"]
    }},
    "structure_completeness": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }},
    "step_executability": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }},
    "example_quality": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }},
    "scope_appropriateness": {{
      "score": <0-100的整数>,
      "strengths": [], "weaknesses": [], "suggestions": []
    }}
  }},
  "overall_summary": "整体评价（2-3句话）",
  "top_issues": ["问题1", "问题2"],
  "verdict": "INSTALL"
}}

verdict 规则：
- "INSTALL"：加权分 >= 75
- "MAYBE"：50-74
- "SKIP"：< 50
"""


def _build_criteria_descriptions() -> str:
    lines = []
    for c in CRITERIA:
        lines.append(f"### {c.name}（权重 {c.weight}%）")
        lines.append(c.description)
        for q in c.questions:
            lines.append(f"- {q}")
        lines.append("")
    return "\n".join(lines)


def _parse_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def evaluate_skill(skill_content: str, api_key: Optional[str] = None) -> dict:
    """Detect skill type then call Gemini with the appropriate prompt."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=key)

    skill_type = detect_type(skill_content)

    if skill_type == "index":
        prompt = INDEX_PROMPT.format(skill_content=skill_content)
    else:
        prompt = SELF_CONTAINED_PROMPT.format(
            criteria_descriptions=_build_criteria_descriptions(),
            skill_content=skill_content,
        )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    result = _parse_response(response.text)
    result["skill_type"] = skill_type

    # Override AI verdict with our deterministic weighted score
    weighted = calculate_weighted_score(result["scores"])
    if weighted >= 75:
        result["verdict"] = "INSTALL"
    elif weighted >= 50:
        result["verdict"] = "MAYBE"
    else:
        result["verdict"] = "SKIP"

    return result


def calculate_weighted_score(scores: dict) -> float:
    """Calculate the final weighted score out of 100."""
    total = 0.0
    for criterion in CRITERIA:
        score_data = scores.get(criterion.key, {})
        raw_score = score_data.get("score", 0)
        total += (raw_score * criterion.weight) / 100
    return round(total, 1)

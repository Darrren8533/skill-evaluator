"""
Skill template generator.

Given a topic + tech stack, uses Gemini to generate a high-quality
SKILL.md that would score 85+ on the evaluator's 5-dimension rubric.
"""
import os
from typing import Optional

from google import genai

# High-scoring reference example embedded directly so Gemini learns the format
REFERENCE_EXAMPLE = """
# Database Migration Safety

## When to Use
Use this skill whenever you are:
- Writing a new database migration file
- Modifying an existing migration
- Running migrations in a staging or production environment
- Reviewing a PR that contains migration files

Do NOT use this skill for:
- Seeding development data
- Modifying application-level ORM models without schema changes

## Steps

1. **Check if the migration is reversible**
   - Every migration MUST have a `down()` method or equivalent rollback
   - If data will be deleted, add a backup step first

2. **Verify the migration is non-breaking**
   - Adding a nullable column: ✅ safe
   - Renaming a column without a transition period: ❌ breaking
   - Dropping a column still referenced in code: ❌ breaking

3. **Test locally before staging**
   ```bash
   npm run migrate:up
   # run your test suite
   npm run migrate:down
   npm run migrate:up
   ```

4. **Add a migration lock check**
   - Confirm no other migration is running

5. **Document the migration**
   - Add a comment: what it does, why it was needed, estimated run time

## Example

**Bad migration (will cause downtime):**
```sql
ALTER TABLE users RENAME COLUMN email TO email_address;
```

**Good migration (zero-downtime rename):**
```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN email_address VARCHAR(255);
-- Step 2: Backfill
UPDATE users SET email_address = email WHERE email_address IS NULL;
```

## Expected Output
- A migration file that can be safely applied and rolled back
- Zero application downtime during deployment
""".strip()


GENERATE_PROMPT = """\
你是一个 Claude Code Skill 专家，擅长编写高质量的 SKILL.md 文件。

## 你的任务

请为以下需求生成一个高质量的 SKILL.md 文件：

- **Skill 主题**：{topic}
- **技术栈**：{tech_stack}
- **额外说明**：{extra_notes}

## 高分 Skill 必须满足的标准

1. **Trigger 清晰度（20%）**
   - 明确写出"什么时候用"和"什么时候不用"
   - 用具体场景而不是模糊描述

2. **结构完整性（25%）**
   - 必须包含：When to Use / Steps / Example / Expected Output 四个区块
   - 有清晰的层次和编号

3. **步骤可执行性（25%）**
   - 每一步都是具体动作，不是原则性建议
   - 包含真实的命令、代码片段、具体数值
   - Claude 看到任务后可以直接照着做

4. **示例质量（20%）**
   - 必须有 Bad ❌ vs Good ✅ 对比
   - 示例必须是真实的代码/命令，不能是伪代码或占位符
   - 示例要覆盖最典型的使用场景

5. **范围合理性（10%）**
   - 专注一个具体主题，不要大而全
   - 深度 > 广度

## 参考示例（91分高质量 SKILL.md）

下面是一个真实的高分 skill，请参考它的结构、语气和具体程度：

```
{reference_example}
```

## 输出要求

- 直接输出 SKILL.md 的 Markdown 内容，不要加任何解释
- 不要用 ``` 包裹整个输出
- 内容必须是针对 "{topic}" 的真实、具体、可执行的指导
- 代码示例必须真实（不能是 `your_code_here` 这种占位符）
- 长度：400-800 字，聚焦不冗长
"""


def generate(
    topic: str,
    tech_stack: str = "",
    extra_notes: str = "",
    api_key: Optional[str] = None,
) -> str:
    """
    Generate a high-quality SKILL.md for the given topic.
    Returns the raw markdown string.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=key)

    prompt = GENERATE_PROMPT.format(
        topic=topic,
        tech_stack=tech_stack or "通用（不限技术栈）",
        extra_notes=extra_notes or "无",
        reference_example=REFERENCE_EXAMPLE,
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    content = response.text.strip()

    # Strip accidental outer code fences
    if content.startswith("```markdown"):
        content = content[len("```markdown"):].strip()
    if content.startswith("```"):
        content = content[3:].strip()
    if content.endswith("```"):
        content = content[:-3].strip()

    return content

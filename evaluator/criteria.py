from dataclasses import dataclass
from typing import List


@dataclass
class Criterion:
    name: str
    key: str
    weight: int  # weights sum to 100
    description: str
    questions: List[str]


CRITERIA = [
    Criterion(
        name="Trigger 清晰度",
        key="trigger_clarity",
        weight=20,
        description="这个 skill 的触发条件是否清晰明确？",
        questions=[
            "是否明确说明了什么情况下使用这个 skill？",
            "trigger 条件是否具体（而不是'当你需要...'这类模糊描述）？",
            "是否列出了不应该使用的情况（negative examples）？",
        ],
    ),
    Criterion(
        name="结构完整性",
        key="structure_completeness",
        weight=25,
        description="skill 文件是否包含所有必要的结构元素",
        questions=[
            "是否有明确的目的说明？",
            "是否有清晰的步骤或流程？",
            "是否有使用示例？",
            "是否说明了预期输出？",
        ],
    ),
    Criterion(
        name="步骤可执行性",
        key="step_executability",
        weight=25,
        description="步骤是否具体、可操作，而不是模糊的描述",
        questions=[
            "每个步骤是否有具体的行动？",
            "步骤是否按逻辑顺序排列？",
            "是否避免了'尽量'、'考虑'等模糊词汇？",
        ],
    ),
    Criterion(
        name="示例质量",
        key="example_quality",
        weight=20,
        description="示例是否充分、具体、有代表性",
        questions=[
            "是否有至少一个具体的使用示例？",
            "示例是否展示了输入和预期输出？",
            "示例是否覆盖了主要使用场景？",
        ],
    ),
    Criterion(
        name="范围合理性",
        key="scope_appropriateness",
        weight=10,
        description="skill 的范围是否合适，不太宽泛也不太狭窄",
        questions=[
            "这个 skill 是否专注于一个明确的任务类型？",
            "是否避免了过度宽泛（如'帮我写代码'）？",
            "是否避免了过度狭窄（只适用于一个极特定的场景）？",
        ],
    ),
]

TOTAL_WEIGHT = sum(c.weight for c in CRITERIA)  # should be 100

"""
Detect whether a skill is self-contained or an index skill.

Self-contained: All guidance, steps, and examples are in one file.
Index:          Acts as a directory pointing to other rule/skill files.
"""
import re


INDEX_SIGNALS = [
    r"read individual rule files",
    r"rules/[\w-]+\.md",
    r"see.*\.md",
    r"refer to.*\.md",
    r"full compiled document",
    r"agents\.md",
    r"for detailed explanations",
    r"each rule file contains",
    r"rule categories",
    r"quick reference",
]

SELF_CONTAINED_SIGNALS = [
    r"```[\w]*\n",       # has code blocks
    r"## steps",
    r"## example",
    r"incorrect.*correct",
    r"bad.*good",
]


def detect_type(content: str) -> str:
    """
    Returns 'index' or 'self-contained'.
    """
    lower = content.lower()

    index_hits = sum(1 for p in INDEX_SIGNALS if re.search(p, lower))
    self_hits  = sum(1 for p in SELF_CONTAINED_SIGNALS if re.search(p, lower))

    # Count how many external file references exist
    file_refs = len(re.findall(r"`[\w/-]+\.md`", content))

    if index_hits >= 2 or file_refs >= 3:
        return "index"
    return "self-contained"


def explain_type(content: str) -> dict:
    """Return detection result with reasoning."""
    lower = content.lower()
    skill_type = detect_type(content)
    file_refs  = re.findall(r"`[\w/-]+\.md`", content)
    index_hits = [p for p in INDEX_SIGNALS if re.search(p, lower)]

    return {
        "type": skill_type,
        "file_references": file_refs[:5],
        "index_signals_found": index_hits,
        "code_blocks": len(re.findall(r"```[\w]*\n", content)),
    }

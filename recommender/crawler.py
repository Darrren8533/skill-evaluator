"""
GitHub Skill Crawler
Fetches SKILL.md files from known skill repos and caches them locally.
"""
import json
import sys
import time
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

CACHE_FILE = Path(__file__).parent.parent / "data" / "skills_cache.json"

# Repos and their skill folder paths
SKILL_SOURCES = [
    {
        "repo": "vercel-labs/agent-skills",
        "path": "",           # skills are in subdirectories at root
        "name": "vercel-labs",
    },
    {
        "repo": "affaan-m/everything-claude-code",
        "path": "skills",     # skills folder
        "name": "everything-claude-code",
    },
    {
        "repo": "travisvn/awesome-claude-skills",
        "path": "skills",
        "name": "awesome-claude-skills",
    },
]

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github.v3+json"}


def _get(url: str, token: str = None) -> dict | list | None:
    headers = HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 403:
        print(f"  ⚠ Rate limited. Wait 60s or provide a GitHub token.")
    elif resp.status_code == 404:
        print(f"  ⚠ Not found: {url}")
    return None


def _list_dir(repo: str, path: str, token: str = None) -> list:
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    data = _get(url, token)
    return data if isinstance(data, list) else []


def _fetch_file(download_url: str) -> str | None:
    try:
        resp = requests.get(download_url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def _find_skill_files(repo: str, path: str, token: str, depth: int = 0) -> list[dict]:
    """Recursively find all SKILL.md files in a repo path."""
    if depth > 3:
        return []

    items = _list_dir(repo, path, token)
    skills = []

    for item in items:
        if item["type"] == "file" and item["name"].upper() in ("SKILL.MD", "SKILLS.MD"):
            content = _fetch_file(item["download_url"])
            if content:
                skill_path = item["path"]
                skill_name = str(Path(skill_path).parent.name) if path else Path(skill_path).stem
                skills.append({
                    "name": skill_name,
                    "repo": repo,
                    "path": skill_path,
                    "url": item["html_url"],
                    "content": content,
                })
                print(f"  ✓ {skill_name}")
            time.sleep(0.3)  # be nice to GitHub

        elif item["type"] == "dir" and depth < 3:
            skills.extend(_find_skill_files(repo, item["path"], token, depth + 1))

    return skills


def crawl(token: str = None, force: bool = False) -> list[dict]:
    """Crawl all skill sources and return list of skill dicts."""
    CACHE_FILE.parent.mkdir(exist_ok=True)

    if CACHE_FILE.exists() and not force:
        print(f"📦 Loading from cache: {CACHE_FILE}")
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    all_skills = []

    for source in SKILL_SOURCES:
        print(f"\n🔍 Crawling {source['repo']} ...")
        skills = _find_skill_files(source["repo"], source["path"], token)
        for s in skills:
            s["source"] = source["name"]
        all_skills.extend(skills)
        print(f"  → {len(skills)} skills found")

    # Save cache (without content to keep it readable, store content separately)
    CACHE_FILE.write_text(
        json.dumps(all_skills, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n💾 Cached {len(all_skills)} skills to {CACHE_FILE}")
    return all_skills


if __name__ == "__main__":
    import sys
    token = sys.argv[1] if len(sys.argv) > 1 else None
    skills = crawl(token=token, force=True)
    print(f"\nTotal: {len(skills)} skills crawled")

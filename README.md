# Skill Evaluator

A framework for evaluating, scanning, recommending, and generating [Claude Code](https://claude.ai/claude-code) skills (SKILL.md files).

## Features

| Command | Description |
|---|---|
| `evaluate` | Score a SKILL.md on 5 quality dimensions (0–100) |
| `security-scan` | Detect prompt injection, data exfiltration, backdoors |
| `recommend` | Recommend skills based on your tech stack & project type |
| `generate` | Generate a high-quality SKILL.md template from a topic |

## Installation

```bash
pip install -r requirements.txt
```

Requires a [Gemini API key](https://aistudio.google.com/app/apikey). Set it as an environment variable:

```bash
set GEMINI_API_KEY=your_key_here   # Windows
export GEMINI_API_KEY=your_key_here  # macOS/Linux
```

## Usage

### Evaluate a skill

```bash
python main.py evaluate path/to/SKILL.md
python main.py evaluate path/to/SKILL.md --json
python main.py evaluate path/to/SKILL.md --output report.txt
```

### Security scan

```bash
python main.py security-scan path/to/SKILL.md
```

Detects: prompt injection, sensitive file access, external data exfiltration, insecure coding advice, user deception.

### Recommend skills for your project

```bash
python main.py recommend --stack "Next.js, TypeScript, PostgreSQL" --type "SaaS Web App"
python main.py recommend -s "Python, FastAPI" -t "API Service" --show-skip
```

### Generate a skill template

```bash
python main.py generate --topic "API rate limiting best practices" --stack "Node.js, Express"
python main.py generate -t "Docker multi-stage builds" --evaluate
```

`--evaluate` runs the scorer immediately after generation so you can see the quality score.

## Scoring Dimensions

| Dimension | Weight | Description |
|---|---|---|
| Trigger Clarity | 20% | Clear when-to-use / when-not-to-use conditions |
| Structure Completeness | 25% | Has When to Use / Steps / Example / Expected Output |
| Step Executability | 25% | Concrete actions Claude can follow directly |
| Example Quality | 20% | Real Bad ❌ vs Good ✅ code comparisons |
| Scope Appropriateness | 10% | Focused topic, depth over breadth |

**Verdict:** `INSTALL` ≥ 75 · `MAYBE` 50–74 · `SKIP` < 50

> 💡 A high score reflects documentation quality, not necessity. Generic skills (coding standards, Git conventions) are already known to Claude — install skills that enforce project-specific rules or team conventions.

## Security Risk Levels

`SAFE` → `LOW` → `MEDIUM` → `HIGH` → `CRITICAL`

**Recommendation:** `INSTALL` · `REVIEW` · `REJECT`

## Project Structure

```
skill-evaluator/
├── main.py                      ← CLI entry point
├── evaluator/
│   ├── criteria.py              ← 5 scoring dimensions
│   ├── scorer.py                ← Gemini-powered scorer
│   ├── type_detector.py         ← self-contained vs index skill
│   ├── report.py                ← text + JSON report output
│   └── security_scanner.py      ← regex + AI security scan
├── recommender/
│   ├── crawler.py               ← crawl GitHub skill repos
│   ├── batch_evaluate.py        ← batch evaluate + cache
│   ├── matcher.py               ← semantic relevance matching
│   └── ranker.py                ← 4-tier recommendation output
├── generator/
│   └── template.py              ← SKILL.md template generator
├── data/                        ← cached skills + results (gitignored)
└── tests/sample_skills/
    ├── good_skill.md            ← 91/100 reference
    ├── bad_skill.md             ← 16/100 baseline
    ├── fake_good_skill.md       ← 37/100 adversarial test
    └── malicious_skill.md       ← CRITICAL security test case
```

## Powered By

- [Google Gemini 2.0 Flash](https://ai.google.dev/) — scoring, security analysis, semantic matching, generation
- [Click](https://click.palletsprojects.com/) — CLI framework

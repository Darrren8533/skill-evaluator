#!/usr/bin/env python3
"""
Skill Quality Evaluator
Usage:
    python main.py evaluate <path/to/SKILL.md>
    python main.py evaluate <path/to/SKILL.md> --json
    python main.py evaluate <path/to/SKILL.md> --output report.json
"""
import json
import sys
from pathlib import Path

import click

# Fix Windows terminal encoding for Unicode output
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from evaluator.scorer import evaluate_skill
from evaluator.report import generate_report, generate_json_report
from evaluator.security_scanner import scan as security_scan, format_security_report
from recommender.matcher import recommend
from recommender.ranker import format_recommendations
from generator.template import generate as generate_skill


@click.group()
def cli():
    """Skill Quality Evaluator — 评估 Claude Code skill 的质量"""
    pass


@cli.command()
@click.argument("skill_path", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="以 JSON 格式输出")
@click.option("--output", "-o", type=click.Path(), help="将报告保存到文件")
@click.option("--api-key", envvar="GEMINI_API_KEY", help="Gemini API Key")
def evaluate(skill_path: str, as_json: bool, output: str, api_key: str):
    """评估一个 SKILL.md 文件的质量"""
    path = Path(skill_path)
    skill_name = path.stem
    skill_content = path.read_text(encoding="utf-8")

    click.echo(f"⏳ 正在评估：{skill_name} ...")

    try:
        evaluation = evaluate_skill(skill_content, api_key=api_key)
    except Exception as e:
        click.echo(f"❌ 评估失败：{e}", err=True)
        sys.exit(1)

    if as_json:
        report_data = generate_json_report(skill_name, evaluation)
        result = json.dumps(report_data, ensure_ascii=False, indent=2)
    else:
        result = generate_report(skill_name, evaluation)

    click.echo(result)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"\n📄 报告已保存到：{output}")


@cli.command("security-scan")
@click.argument("skill_path", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="以 JSON 格式输出")
@click.option("--output", "-o", type=click.Path(), help="将报告保存到文件")
@click.option("--api-key", envvar="GEMINI_API_KEY", help="Gemini API Key")
def security_scan_cmd(skill_path: str, as_json: bool, output: str, api_key: str):
    """扫描 SKILL.md 文件的安全风险（Prompt Injection / 数据泄露 / 漏洞植入等）"""
    path = Path(skill_path)
    skill_name = path.stem
    skill_content = path.read_text(encoding="utf-8")

    click.echo(f"🔍 正在扫描：{skill_name} ...")

    try:
        result = security_scan(skill_content, api_key=api_key)
    except Exception as e:
        click.echo(f"❌ 扫描失败：{e}", err=True)
        sys.exit(1)

    if as_json:
        output_str = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output_str = format_security_report(skill_name, result)

    click.echo(output_str)

    if output:
        Path(output).write_text(output_str, encoding="utf-8")
        click.echo(f"\n📄 报告已保存到：{output}")


@cli.command("recommend")
@click.option("--stack",   "-s", required=True, help="技术栈，例如：Next.js, Python, PostgreSQL")
@click.option("--type",    "-t", "project_type", required=True, help="项目类型，例如：Web应用, API服务, CLI工具")
@click.option("--notes",   "-n", default="", help="额外说明，例如：有 Docker 部署需求")
@click.option("--show-skip", is_flag=True, help="同时显示不推荐的 skill")
@click.option("--json",    "as_json", is_flag=True, help="以 JSON 格式输出")
@click.option("--output",  "-o", type=click.Path(), help="将报告保存到文件")
@click.option("--api-key", envvar="GEMINI_API_KEY", help="Gemini API Key")
def recommend_cmd(stack, project_type, notes, show_skip, as_json, output, api_key):
    """根据你的技术栈和项目类型，推荐最适合安装的 skill"""
    click.echo(f"🤖 正在为你的项目匹配 skill ...")
    click.echo(f"   技术栈：{stack}")
    click.echo(f"   项目类型：{project_type}")
    click.echo()

    try:
        results = recommend(
            tech_stack=stack,
            project_type=project_type,
            extra_notes=notes,
            api_key=api_key,
        )
    except Exception as e:
        click.echo(f"❌ 推荐失败：{e}", err=True)
        sys.exit(1)

    if as_json:
        output_str = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        output_str = format_recommendations(
            results,
            tech_stack=stack,
            project_type=project_type,
            show_skip=show_skip,
        )

    click.echo(output_str)

    if output:
        Path(output).write_text(output_str, encoding="utf-8")
        click.echo(f"\n📄 报告已保存到：{output}")


@cli.command("generate")
@click.option("--topic",  "-t", required=True, help="Skill 主题，例如：Python 异步编程最佳实践")
@click.option("--stack",  "-s", default="", help="技术栈，例如：Python, asyncio, FastAPI")
@click.option("--notes",  "-n", default="", help="额外说明")
@click.option("--output", "-o", type=click.Path(), help="保存生成的 SKILL.md 到文件")
@click.option("--evaluate", "run_eval", is_flag=True, help="生成后立即评分（需要 API 调用）")
@click.option("--api-key", envvar="GEMINI_API_KEY", help="Gemini API Key")
def generate_cmd(topic, stack, notes, output, run_eval, api_key):
    """根据主题自动生成高质量 SKILL.md 模板"""
    click.echo(f"✨ 正在生成 Skill：{topic} ...")

    try:
        content = generate_skill(
            topic=topic,
            tech_stack=stack,
            extra_notes=notes,
            api_key=api_key,
        )
    except Exception as e:
        click.echo(f"❌ 生成失败：{e}", err=True)
        sys.exit(1)

    click.echo("\n" + "=" * 66)
    click.echo(content)
    click.echo("=" * 66)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        click.echo(f"\n📄 已保存到：{output}")

    if run_eval:
        click.echo("\n⏳ 正在评分...")
        try:
            from evaluator.scorer import evaluate_skill
            from evaluator.report import generate_report
            evaluation = evaluate_skill(content, api_key=api_key)
            click.echo(generate_report(topic, evaluation))
        except Exception as e:
            click.echo(f"❌ 评分失败：{e}", err=True)


if __name__ == "__main__":
    cli()

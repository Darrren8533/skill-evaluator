# Skill 质量评估框架 — 开发计划

## 背景
Claude Code 的 skill 生态系统正在爆炸式增长（awesome-claude-code-toolkit 已有 15,000+ skills）。
问题是：大多数人不知道哪些 skill 值得装，哪些是低质量或不适合自己项目的。

这个框架要解决：**自动评估 skill 质量 + 根据项目推荐该装哪些**。

---

## 进度总览

| 阶段 | 状态 | 说明 |
|------|------|------|
| 第一步：质量评估框架 | ✅ 完成 | 含类型检测、批量评估、对抗测试、安全扫描 |
| 第二步：个人化推荐系统 | ✅ 完成 | Gemini 语义匹配 + 综合评分排名 |
| 第三步：Skill 模板生成器 | ✅ 完成 | 生成即达 85-91 分，可选立即评分 |
| 第四步：自动生成高级 Skill | 🔲 未开始 | |

---

## 第一步完成记录（2026-02-20）

### 已实现功能
- `evaluator/criteria.py` — 5 个评分维度（trigger/结构/可执行/示例/范围）
- `evaluator/scorer.py` — Gemini 2.0 Flash 评分，自动识别 skill 类型分别评估
- `evaluator/type_detector.py` — 检测 self-contained vs index 型 skill
- `evaluator/report.py` — 文字报告 + JSON 报告输出
- `recommender/crawler.py` — 爬取 GitHub skill repos，缓存到 data/
- `recommender/batch_evaluate.py` — 批量评估 + 分布分析报告
- `main.py` — CLI 入口（`python main.py evaluate <file>`）

### 真实数据验证结果（43 个真实 skill + 3 个测试样本）
- 平均分：84.2（精选 repo 质量普遍高）
- 分层清晰：bad(16) → fake_good(37) → 真实skill(74-94)
- 无 scoring/verdict 异常

### 已发现并修复的问题
1. ✅ **Windows 编码问题** — 所有文件加 `sys.stdout.reconfigure(encoding='utf-8')`
2. ✅ **索引型 skill 误判** — 加入 type_detector，用不同 prompt 评估
   - `react-native-skills` 从 67.2 提升到 85.5
3. ✅ **报告分隔线 Bug** — `"\n─" * 62` 改为 `"\n" + "─" * 62`
4. ✅ **google.generativeai 弃用警告** — 换成 `google.genai`

### 已知但未解决的问题（均已修复）
1. ✅ **Verdict 与分数不一致** — 在 `scorer.py` 中解析 AI 响应后，用 `calculate_weighted_score` 覆盖 AI 的 verdict
   - 例：`e2e-testing` 74.2 → MAYBE；`cost-aware-llm-pipeline` 76.8 → INSTALL（现在正确）

2. **精选 repo 区分度不足** — 真实 skill 挤在 75-94 区间，细粒度排名意义不大
   - 这不是 bug，是数据本身质量均匀的结果

3. **无法评估"必要性"** — 框架只看文档质量，不知道这个 skill 对你的项目是否有用
   - 这是第二步（推荐系统）要解决的问题

### 对抗测试结论
- `fake_good_skill`（结构完整但内容废话）得 37 分 ❌ — 框架没被骗
- 框架能区分：有结构 vs 结构有内容

### 安全扫描（2026-02-20 新增）
- `evaluator/security_scanner.py` — 正则预扫描（14条规则）+ Gemini AI 深度扫描
- `main.py` 新增 `security-scan` 命令
- 测试用例 `malicious_skill.md`：正则命中 5 条（读 .env / curl webhook / Prompt Injection / MD5 / 隐瞒信息）
- `good_skill.md`：0 命中 ✅

---

## 四个阶段详细计划

### 第一步：Skill 质量评估框架 ✅
评分维度：trigger 清晰度 / 结构完整性 / 步骤可执行性 / 示例质量 / 范围合理性
技术：Python + Gemini 2.0 Flash API

**遗留 TODO（可选）：**
- [x] 修复 verdict 不一致问题（让 calculate_weighted_score 决定 verdict）✅
- [x] 安全扫描维度（security_scanner.py + CLI 命令）✅
- [ ] 评分一致性测试（同一 skill 跑 5 次看波动）

---

### 第二步：个人化推荐系统 ✅（2026-02-20 完成）
**目标：** 用户输入项目技术栈，从评估结果里推荐该装哪些 skill

**已实现：**
- `recommender/matcher.py` — 一次性批量发给 Gemini，返回每个 skill 的相关性分（0-100）+ 理由
- `recommender/ranker.py` — 综合分 = 质量分×0.6 + 相关性×0.4，分四层输出（🔥/✅/🟡/⬜）
- `main.py recommend` — CLI 命令：`python main.py recommend -s "Next.js, TypeScript" -t "SaaS Web应用"`

**验证结果：**
- Python AI 工具栈：python-patterns(相关=95)、api-design(85)、regex-vs-llm(80) 排名前列 ✅
- Next.js SaaS 栈：coding-standards(95)、api-design(95)、deployment-patterns(90) 正确识别 ✅
- Java/Go skill 被正确排到 SKIP ✅

**Key Bug：** Gemini 返回 skill 名字作为 id，不是数字，改为按名字映射后修复

---

### 第三步：Skill 模板生成器 ✅（2026-02-20 完成）
**目标：** 根据评估标准自动生成高质量 SKILL.md 模板

用户输入：我想创建一个关于 XXX 的 skill
输出：符合高分标准的 SKILL.md，填空就能用

**已实现：**
- `generator/template.py` — 基于 5 维评分标准 + 91分参考示例生成 SKILL.md
- `main.py generate` — CLI：`python main.py generate -t "主题" -s "技术栈" --evaluate`
- `--evaluate` flag — 生成后立即调用评分器反馈质量

**验证结果：**
- Python 异步编程：84.8 分 ✅
- Git commit message 规范：91.0 分 ✅
- Node.js API 错误处理：91.2 分 ✅

---

### 第四步：自动生成高级 Skill 🔲（难，最后做）
分析 git history、代码模式 → 提取成可复用 skill

---

## 当前文件结构
```
skill-evaluator/
├── PLAN.md
├── requirements.txt            (google-genai, click, rich, requests)
├── main.py                     ← CLI：python main.py evaluate <file>
├── evaluator/
│   ├── criteria.py             ← 5 个评分维度定义
│   ├── scorer.py               ← Gemini 评分（含类型分支，verdict 由加权分决定）
│   ├── type_detector.py        ← 检测 self-contained vs index
│   ├── report.py               ← 报告输出（text + json）
│   └── security_scanner.py     ← 安全扫描（正则 + Gemini AI 双层）
├── recommender/
│   ├── crawler.py              ← 爬 GitHub skill repos
│   ├── batch_evaluate.py       ← 批量评估 + 分析
│   ├── matcher.py              ← Gemini 语义匹配（批量，一次 API 调用）
│   └── ranker.py               ← 四层推荐输出（🔥/✅/🟡/⬜）
├── generator/
│   └── template.py             ← Gemini 生成（5维标准 + 参考示例），支持 --evaluate
├── data/
│   ├── skills_cache.json       ← 43 个爬取的 skill 内容
│   └── evaluation_results.json ← 46 个评估结果（含3个测试样本）
└── tests/
    └── sample_skills/
        ├── good_skill.md       ← 93 分，真实高质量
        ├── bad_skill.md        ← 16 分，真实低质量
        ├── fake_good_skill.md  ← 37 分，伪装高质量（对抗测试）
        └── malicious_skill.md  ← 安全测试用例（含5种攻击向量）
```

---

## 重开对话时告诉 Claude

```
我在做一个 Skill 质量评估框架，计划文件在：
C:\Users\USER\Downloads\20260203\claudeCode\skill-evaluator\PLAN.md

第一步已完成。现在开始做第二步：个人化推荐系统。
技术栈：Python + Gemini API（GEMINI_API_KEY 已配置）
已有评估数据：data/evaluation_results.json（46 条）
```

---

## 参考资源
- everything-claude-code: https://github.com/affaan-m/everything-claude-code
- awesome-claude-code: https://github.com/hesreallyhim/awesome-claude-code
- vercel agent-skills: https://github.com/vercel-labs/agent-skills
- awesome-claude-skills: https://github.com/travisvn/awesome-claude-skills
- Gemini API 文档: https://ai.google.dev/gemini-api/docs

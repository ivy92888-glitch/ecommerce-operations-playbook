# 🛒 Ecommerce Operations Assistant

**为什么做这个项目？** 跨境电商卖家分两种：有人做亚马逊平台（Listing/广告/合规），有人做独立站（Shopify/WordPress 建站/SEO/选品），**极少有人两套都做**。但市面上找不到一个助手同时把两套知识体系做扎实——要么只讲平台规则，要么只讲建站 SOP。

这个项目把两套知识库**彻底隔离打包**：侧边栏选"亚马逊"就只加载亚马逊的 102 条知识，选"独立站"就只加载独立站的 897 条知识，互不污染、互不干扰。知识库没命中的问题自动上网搜权威结果兜底。

## ✨ 功能总览

| 功能 | 人话总结 | 数字例子 |
|---|---|---|
| **入口隔离** | 侧边栏二选一（亚马逊 / 独立站），切换时只加载对应知识库 + 清空对话历史 | 在独立站入口搜"刷单后果" → 零结果（搜不到）；换亚马逊入口 → 命中 amz_01.md |
| 知识库问答 | 给一段业务问题，自动从所选入口的知识库里精准定位最相关的段落，喂给 LLM 组织成答案 | "亚马逊广告 CPC 太高怎么降本" → 命中 amz_03.md 广告降本路径 |
| 上网兜底 | 如果知识库没命中或相关度低（top score < 0.25），自动调 DuckDuckGo 搜权威结果补充 | "Shopify 2026 年新政策" → 知识库没 → 自动搜 Shopify 官方文档 |
| 合规教育优先 | 明确区分"白帽合规"和"黑灰产"，涉及违规操作直接给法律后果 | "跟卖" → 不教怎么跟卖，教预防跟卖 + 侵权查询四步法 |
| 来源可追溯 | 每个回答下面都列参考来源（哪个知识文件 / 哪个网页） | 回答里能看到 `知识库: 亚马逊运营/amazon_03.md (相关度 0.176)` |

## 🎯 适用场景

| 谁用 | 选哪个入口 | 在什么环节用 |
|---|---|---|
| 亚马逊卖家 | 亚马逊 | 每天开电脑前问一个当日重点（比如"2025 年 7 月刷差评判例"） |
| 独立站站长 | 独立站 | SEO / 选品 / 建站遇到卡壳（比如"1688 货源下架了怎么办"） |
| 运营新人 | 都可以 | 入门第一周快速建立全局认知 |
| 求职者 | 面试那家公司做哪个就选哪个 | 面试前速查高频问题 |

## 🚀 快速开始

### 方式 A：一键启动（推荐 Windows 用户）

双击 `run.bat`，浏览器自动打开 http://localhost:8502。关掉那个黑色命令行窗口就是停止。

### 方式 B：命令行（Mac / Linux / 喜欢折腾）

```bash
# 1. 安装依赖
pip install -r chatbot/requirements.txt

# 2. 设置 LLM（三选一，免费的 Ollama 也行）
export LLM_BASE_URL="https://api.siliconflow.cn/v1"
export LLM_API_KEY="sk-your-key"
export LLM_MODEL="deepseek-ai/DeepSeek-V3"

# 3. 启动
python -m streamlit run chatbot/app.py --server.headless true
```

侧边栏里可以随时换 API Base URL、Key、Model、Top-K 检索参数。

## 📁 文件清单

| 文件 | 说明 |
|---|---|
| `chatbot/app.py` | Streamlit 前端（入口选择 + 聊天界面 + 侧边栏 API 配置） |
| `chatbot/rag.py` | RAG 引擎（TF-IDF 检索 + DuckDuckGo 上网兜底 + LLM 流式调用 + 自定义迭代器） |
| `chatbot/requirements.txt` | 依赖清单（4 个包，`pip install` 秒装） |
| `knowledge/amazon/` | 亚马逊运营知识库（4 文件 / 34 KB，含平台规则/选品/Listing/广告/合规风控） |
| `knowledge/dropshipping/` | 独立站运营知识库（16 文件 / 341 KB，含建站/选品/SEO/广告/社媒/供应链/数据分析） |
| `run.bat` | Windows 一键启动脚本（浏览器自动弹） |
| `LICENSE` | MIT |

## 🛠 技术栈

`Streamlit` · `scikit-learn TF-IDF` · `DuckDuckGo Web Search API` · `OpenAI-compatible LLM API`

## ⚠️ 说明

- 所有知识库内容均已脱敏：无前公司/前雇主/内部账号/具体报价/自媒体链接
- 灰度操作、违规操作、规避监管的内容已全部删除或改写为合规教育
- 平台规则、费用、时效等数字内容标注"仅供参考，以实际后台为准"

---

# Ecommerce Operations Assistant (English)

## Why this project?

Cross-border ecommerce sellers split into **two distinct camps**: those who operate on Amazon (Listings, ads, platform compliance), and those who run independent sites (Shopify/WordPress building, SEO, sourcing). **Rarely does one seller do both**. Yet existing tools either cover platform rules only, or site-building SOPs only — nothing solidly handles both.

This project packages both knowledge bases **with strict isolation**: pick "Amazon" in the sidebar and it loads only Amazon's 102 knowledge chunks; pick "Independent site" and it loads only the independent site's 897 chunks. No cross-contamination, no confusion. When the knowledge base comes up empty, it automatically falls back to authoritative web search via DuckDuckGo.

## What it does

| Feature | Plain English | Numbers |
|---|---|---|
| **Isolated entry points** | Sidebar radio pick: Amazon or Independent Site. Each loads only its own knowledge base — zero cross-contamination | Amazon: 102 chunks / Independent site: 897 chunks; searching "fake review consequences" in independent site mode → zero hits |
| Knowledge-base Q&A | Ask any question — the assistant digs through the selected entry's knowledge chunks to find the most relevant passages, then feeds them to the LLM | "How to lower high ad CPC" (Amazon mode) → hits amz_03.md with the full cost-reduction playbook |
| Web search fallback | When nothing relevant is found (top score < 0.25), automatically queries DuckDuckGo for authoritative sources | "Shopify 2026 new policies" → not in knowledge base → auto-searches Shopify's official docs |
| Compliance-first education | Clearly separates white-hat best practices from black/grey-hat tactics; for grey areas, directly states the legal consequences | "Does Amazon allow hijacking?" → does **not** teach how to hijack; teaches prevention + 4-step IP infringement check |
| Traceable sources | Every answer lists its references (which knowledge file / which webpage) | Answers show `知识库: 亚马逊运营/amazon_03.md (relevance 0.176)` |

## Who it's for

| User | Pick this entry | When to use |
|---|---|---|
| Amazon seller | Amazon | Morning check-in — ask about today's priority (e.g. "July 2025 fake-review crackdown ruling") |
| Independent site owner | Independent site | Stuck on SEO / sourcing / site-building (e.g. "What if my 1688 supplier disappears?") |
| New hire | Either, pick what your team does | First week — quickly build global context |
| Job seeker | Match the company you're interviewing with | Pre-interview brush-up on high-frequency questions |

## Quick start

### Option A: One-click launch (Windows users)

Double-click `run.bat`. Browser opens automatically at http://localhost:8502. Close the black command-line window to stop.

### Option B: Command line (Mac / Linux / curious types)

```bash
pip install -r chatbot/requirements.txt

export LLM_BASE_URL="https://api.siliconflow.cn/v1"   # or Ollama, OpenAI, etc.
export LLM_API_KEY="sk-your-key"
export LLM_MODEL="deepseek-ai/DeepSeek-V3"

python -m streamlit run chatbot/app.py --server.headless true
```

You can change the API base URL, key, model, and top-K retrieval from the sidebar at any time.

## File list

| File | What it does |
|---|---|
| `chatbot/app.py` | Streamlit front-end (entry selector + chat UI + sidebar API config) |
| `chatbot/rag.py` | RAG engine (TF-IDF retrieval + DuckDuckGo web fallback + LLM streaming + custom iterable class) |
| `chatbot/requirements.txt` | Dependencies (4 packages, `pip install` in seconds) |
| `knowledge/amazon/` | Amazon ops knowledge base (4 files / 34 KB — platform rules, sourcing, Listings, ads, compliance) |
| `knowledge/dropshipping/` | Independent site knowledge base (16 files / 341 KB — building, sourcing, SEO, ads, social, supply chain, analytics) |
| `run.bat` | Windows one-click launch script |
| `LICENSE` | MIT |

## Tech stack

`Streamlit` · `scikit-learn TF-IDF` · `DuckDuckGo Web Search API` · `OpenAI-compatible LLM API`

## Notes

- All knowledge-base content is desensitized: no prior company / employer / internal accounts / specific pricing / social media links
- Grey-area and black-hat operations have been removed or rewritten as compliance education
- Platform rules, fees, timelines marked "for reference only — verify in your actual dashboard"

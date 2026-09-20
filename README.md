# 模块化 Agentic 系统（ReAct + RAG + 记忆 + 评测）

> **通用 Agent harness（ReAct 循环 + 工具契约 + 记忆 + 自检 + RAG + 可观测/评测）+ 领域包**。从零手写核心、不依赖 LangChain 等框架；落地**电商客服**单领域，领域相关的一切收进 `domain/ecommerce/`，与 harness 解耦。

## ✨ 特性

- **Harness + 领域包（解耦）**：核心 `agent / contract / providers / rag / eval` 与领域无关，领域相关的人设 / 工具 / 字段表 / 数据 / 分块 / 用例全部收进 `domain/ecommerce/`；由 `DomainPack` 接口 + `bootstrap` 组合根装配，核心不感知具体领域。
- **ReAct 循环**：基于 Function Calling 自主实现 `tool_calls` 解析 → 工具执行 → `tool_call_id` 回填 → 多轮迭代，支持单轮并发多工具、最大轮数 / 空响应双重终止兜底。
- **Reflection 回复自检**：回复发出前另起一次 LLM 调用，以「用户原话 + 工具真实结果 + 草稿」为锚做完整性 / 真实性 / 规范性三维校验，三态（accept / revise / continue_tool）驱动回环补调工具。
- **双层记忆 + 有界落盘**：短期滑动窗口 + 长期「用户事实条目库」（LLM 每轮增删改、≤200 字、注入 system）；会话快照只落有界数据，进程重启可恢复画像与最近对话。
- **pydantic 驱动工具契约**：用 pydantic 模型定义工具入参，`model_json_schema()` 自动生成 Function Schema，并用同一份模型做参数校验（枚举 / 范围 / 正则 / 长度），单一真相来源。
- **端口-适配器解耦**：Agent 通过 `ToolProvider` 调用领域工具；领域工具通过 `SearchService` 使用检索能力，`RagSearchAdapter` 隔离 Qdrant 过滤条件与结果格式；由 `bootstrap.py` 注入依赖。LLM 层统一 OpenAI 兼容封装。
- **健壮性**：工具幻觉名 / 参数非法 / 执行异常统一降级为可读错误回填，由模型自我纠正；记忆更新 / 落盘失败不影响用户回复。
- **商品详情工具**：搜索返回精简信息，`get_product_detail` 按需拉取单个商品的完整硬件参数（CPU / 内存 / 存储 / 屏幕…），兼顾 token 与信息完整。
- **RAG 知识检索**：文档分块（标题感知）→ bge-m3 嵌入 → Qdrant 向量库；**混合检索（向量 + BM25，RRF 融合）+ cross-encoder 精排（bge-reranker）**；新增 `search_knowledge` 工具，FAQ / 商品工具升级为语义检索（保留关键词兜底）。
- **可观测性**：记录每次 LLM 调用的 token（含缓存命中）与耗时；每轮返回 `TurnResult`，CLI / Web 实时展示本轮成本与延迟。
- **评测体系**：`eval/` 提供黄金用例 + 规则断言 + LLM-judge 双通道（端到端），以及检索 hit rate / recall@k（RAG）——一键输出报告。
- **Web 调试台**：FastAPI + 单页聊天界面，可视化对话、用户画像与本轮用量。

## 🏗 架构

架构分两层：**harness（领域无关）** + **领域包 `domain/ecommerce`（电商客服）**。

```
        ┌────────────────────────────────────────────────┐
        │  agent/  harness：core（循环/自检/压缩）+ memory   │
        └──────────────────────┬─────────────────────────┘
                               │ 注入：工具 / 人设 / 提示词 / 字段表
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
   contract/              providers/               rag/
   工具契约机制            工具执行端口             检索引擎
                               ▲
                               │ 领域包提供 specs / 数据 / 语料
        ┌──────────────────────┴──────────────────────┐
        │  domain/ecommerce  领域包（提示词/工具/数据/用例）  │
        │  prompt / tools / data / chunker / cases       │
        └────────────────────────────────────────────────┘

  bootstrap.py  组合根：装载领域包并装配出 ReActAgent
```

## 📁 目录结构

```
agent/                 通用 Agent harness（领域无关）
  core/                  核心循环
    loop.py                ReActAgent 主循环（工具 / 人设 / 提示词全注入）
    reflection.py          Reflection 自检（Prompt 注入）
    compress.py            工具结果压缩（字段表注入）
    types.py               TurnResult（回复 + 工具轨迹 + 用量）
  memory/                记忆
    history.py             短期对话窗口
    state.py               长期事实条目库（提炼 Prompt 注入）
    turn.py                轮次记录
    persist.py             会话快照落盘
contract/              工具契约·机制（领域无关）
  tool.py                  工具注册表工厂 + schema 生成 + validate_args
  retrieval.py             SearchService / SearchFilter / SearchHit 检索契约
providers/             工具契约·执行侧
  base.py                  ToolProvider 端口（Protocol）
  local.py                 LocalToolProvider 适配器（收注册表）
domain/                领域包（电商客服）
  base.py                  DomainPack / CollectionSpec 接口
  registry.py              领域入口（当前单领域：电商客服）
  ecommerce/               电商客服领域包
    prompt.py              人设 Prompt
    reflection_prompt.py   自检 Prompt
    state_prompt.py        长期记忆提炼 Prompt
    tool_args.py           工具入参模型 + 枚举
    tools/                 工具实现 + build_tool_specs 工厂 / TOOL_FIELD_MAP
    models/                Product / Inventory / Faq / Knowledge
    loader.py              JSON 加载
    chunker.py             领域分块（商品 / FAQ / 指南）
    collections.py         向量集合名
    eval_cases.py          黄金用例
    data/                  静态数据（*.json，含 golden）
rag/                   RAG 检索引擎（领域无关）
  service.py               SearchService 的适配器，转换查询条件与检索结果
  chunker.py               通用分块原语（标题 / 段落）
  embedder.py              Ollama bge-m3 嵌入
  store.py                 Qdrant 本地向量库（幂等 upsert）
  sparse.py                BM25 关键词检索（混合检索的稀疏路）
  rerank.py                rerank 精排（cross-encoder bge-reranker；含 LLM rerank 备选）
  ingest.py                领域包 → 向量库（数据管道，可重复跑）
  retriever.py             检索：向量 / 混合(RRF) / 混合+rerank
llm/                   模型层
  client.py                OpenAI 兼容客户端（用量/耗时埋点 + 思考开关）
bootstrap.py           组合根：按领域包装配 ReActAgent
web/                   Web 调试台
  server.py                FastAPI：/chat、/reset
  index.html               单页聊天界面
eval/                  评测引擎（领域无关，用例来自领域包）
  checker.py / judge.py / runner.py    端到端「规则 + LLM-judge」双通道
  retrieval_runner.py      检索 hit rate / recall@k
  retrieval_ablation.py    检索消融：vector / hybrid / hybrid+rerank
  benchmarks/              外部基准（bfcl.py 工具调用 / scifact.py 检索）
tests/                 离线单测（unittest，不需 API / Ollama）
scripts/               数据生成 / 下载
  gen_corpus.py            用 LLM 生成 guides / FAQ / 商品描述 / 检索黄金集
  fetch_benchmarks.py      下载 BFCL / BEIR scifact 基准数据
main.py                CLI 入口
```

## 🚀 快速开始

### 环境
- Python 3.10+
- 一个 OpenAI 兼容的大模型 API（默认对接 DeepSeek）
- RAG 检索需本地 [Ollama](https://ollama.com/) + `bge-m3` 嵌入模型
- 可选：cross-encoder 精排（`sentence-transformers`，首次加载 `BAAI/bge-reranker-base` 自动下载；国内可设 `HF_ENDPOINT=https://hf-mirror.com`）

### 安装
```bash
pip install -r requirements.txt
```

### 配置
复制 `.env.example` 为 `.env` 并填写：
```bash
cp .env.example .env          # Windows: copy .env.example .env
```
```
DEEPSEEK_API_KEY=你的密钥      # 必填
# LLM_MODEL=deepseek-v4-flash  # 可选：覆盖默认模型
```

### 初始化 RAG 向量库（首次 / 数据更新后）
```bash
ollama pull bge-m3                # 拉取嵌入模型（约 1.2GB），并保持 ollama 服务运行

python -m rag.ingest              # JSON → 向量库（幂等，可重复跑）
```

### 运行（CLI）
```bash
python main.py                    # 与 Agent 对话
```

### 运行（Web 调试台）
```bash
python -m uvicorn web.server:app --port 8000
# 浏览器打开 http://127.0.0.1:8000
```

### 运行（评测）
```bash
python -m eval.runner              # 端到端：各能力域通过率 + 成本
python -m eval.retrieval_runner    # 检索：hit rate / recall@k
python -m eval.retrieval_ablation  # 检索消融：vector / hybrid / hybrid+rerank
python -m unittest discover -s tests -v   # 离线单测（不需 API / Ollama）
```

### 运行（外部基准，可选）
```bash
python -m scripts.fetch_benchmarks    # 下载 BFCL / BEIR scifact 数据（可重复跑）
python -m eval.benchmarks.bfcl all    # BFCL v3 工具调用
python -m eval.benchmarks.scifact all # BEIR scifact 检索
```

## 🧩 设计要点

- **为什么不用框架**：框架把 tool_call_id 回填、循环终止、记忆裁剪都封成黑盒；手写才能真正理解并掌控每个取舍。
- **记忆的边界**：记忆应是有界的「提炼结果」，无界的对话属于「日志」，两者不混——会话快照只落画像 + 最近窗口。
- **单一真相来源**：工具 schema 与参数校验同源于一份 pydantic 模型，改一处两边同步。
- **可插拔**：RAG / MCP 等都可挂在工具契约两侧，核心无需改动。

### Agent、领域工具与 RAG 的检索边界

```text
Agent → ToolProvider → 电商工具 → SearchService（contract/retrieval.py）
                                      ↑ 实现
                              RagSearchAdapter → Retriever → Qdrant

bootstrap.py：选择检索实现 → 注入领域工具工厂 → 装配 Agent
```

- Agent 负责循环、记忆、自检，不感知检索实现。
- 电商工具负责业务条件、结果转为商品/FAQ/知识条目，以及商品和 FAQ 的关键词降级。
- `SearchFilter` 表达字段相等与数值上限，所有条件按 AND 组合；`SearchHit` 提供正文、元数据与分数。Qdrant 类型及内部 `_text` / `_cid` 字段由适配器处理。
- 默认适配器延迟创建 Retriever：工具装配、库存/详情查询和纯结构化商品筛选不打开向量库。检索策略沿用现有 Retriever 默认值。

替换检索后端时，实现 `SearchService.search()`，然后在装配入口传入：

```python
from bootstrap import build_agent, build_tools
from domain.registry import get_domain

# my_search_service 为自定义 SearchService 实例
tools = build_tools(get_domain(), search_service=my_search_service)
agent = build_agent(search_service=my_search_service)
```

领域包现在提供 `build_tool_specs(search_service)` 工厂，替代静态 `tool_specs` / `TOOL_SPECS`。三个检索函数通过工厂绑定服务；直接调用函数时需显式传入 `search_service=`。对模型暴露的五个工具名称、参数模型和返回业务类型保持不变，CLI / Web / 评测入口仍复用原来的 `build_agent()`。

此次隔离的是在线检索边界；领域分块仍复用 `rag.chunker` 的通用文本分块函数，入库命令仍可从领域注册表选择语料。

安装项目依赖后，可运行离线回归测试（无需模型 API、Ollama 或已有向量库）：

```bash
python -m unittest discover -s tests -v
```

测试覆盖依赖隔离、工具参数与结果映射、关键词降级、完整 Agent 工具回环，以及临时 Qdrant 库上的混合检索过滤。

## 📊 可观测性与评测

- **成本 / 时延**：每次 LLM 调用的 token（含缓存命中）与耗时被记录；`TurnResult.usage` 给出本轮聚合（主循环 + 自检 + 记忆），CLI / Web 直接展示。
- **端到端准确度**：`eval/` 以「规则断言 + LLM-judge」双通道，按能力域（工具路由 / 售后问答 / 多轮记忆 / 越界拒绝 / 防幻觉）输出通过率与成本。
- **检索质量（RAG）**：`eval/retrieval_runner.py` 用黄金查询集评测 hit rate / recall@k；`eval/retrieval_ablation.py` 做 vector / hybrid / hybrid+rerank 消融对比。

```bash
python -m eval.runner              # 端到端
python -m eval.retrieval_runner    # 检索
python -m eval.retrieval_ablation  # 检索消融
```

> 数据规模：商品 **80** · FAQ **168** · 指南 **50** · 检索黄金集 **270**。
> 示例：端到端 8 用例合计 **7/8**；检索 **270 条**黄金查询消融——
> **vector hit@1 79.6%** → **hybrid（+BM25/RRF）hit@5 98.1%** → **hybrid + cross-encoder rerank hit@1 86.7% / hit@5 99.6%**。

## 🌐 外部基准

### Agent 核心 · BFCL v3（工具调用）

用 **Berkeley Function Calling Leaderboard v3**（官方公开数据）验证 harness 的**工具调用通道**：把函数 schema 交给模型 → 解析 `tool_calls` → 与标准答案比对。全量 **1240 例**：

| 类别 | 通过 / 总数 | 准确率 |
|---|---|---|
| simple | 363 / 400 | 90.8% |
| multiple | 174 / 200 | 87.0% |
| parallel | 176 / 200 | 88.0% |
| parallel_multiple | 159 / 200 | 79.5% |
| irrelevance | 172 / 240 | 71.7% |
| **合计** | **1044 / 1240** | **84.2%** |

```bash
python -m eval.benchmarks.bfcl simple 50   # 单类别（可选 limit / workers）
python -m eval.benchmarks.bfcl all         # 全量 + 生成报告
```

> 数据来自 `gorilla-llm/Berkeley-Function-Calling-Leaderboard`；采用**简化 AST 检查器**（名称 + 参数值容忍匹配、集合配对、可选项 `""` 省略合法），**非官方榜单分数**，用于自查工具调用通道。

### RAG 检索 · BEIR scifact（公开基准）

把 scifact 语料（5183 篇）用**同一套检索链路**跑通，对比三种配置（300 查询）：

| 配置 | nDCG@10 | Recall@10 | MRR@10 |
|---|---|---|---|
| vector | 64.4% | 78.3% | 60.8% |
| hybrid | 69.1% | 83.8% | 65.2% |
| hybrid + rerank | **72.7%** | **85.5%** | **69.3%** |

```bash
python -m eval.benchmarks.scifact all   # vector / hybrid / hybrid+rerank
```

> 数据：BEIR 官方 scifact；嵌入 bge-m3（Ollama），指标基于 qrels。**混合检索 + rerank 相比纯向量：nDCG@10 +8.3、Recall@10 +7.2**。

## 🗺 路线图

- [x] RAG 语义检索（标题感知分块 → bge-m3 嵌入 → Qdrant → 检索）
- [x] 混合检索 + rerank（向量 + BM25 经 RRF 融合 → 精排）
- [x] 评测体系（端到端双通道 + 检索 hit rate / 消融）
- [x] 外部基准（BFCL v3 工具调用 + BEIR scifact 检索）
- [x] 服务化（Web 调试台 + 用量可观测）
- [ ] SKILL 技能系统（按需加载指令胶囊）
- [ ] 多 Agent 编排（Supervisor 路由）
- [ ] MCP 工具接入

## ⚠️ 说明

本项目为个人学习与实践项目，数据为虚构的示例数据（AI 生成），不涉及任何真实业务，持续更新进度。

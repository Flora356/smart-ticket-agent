# 智能工单多 Agent 质量评测平台

这是一个面向测试开发/质量工程场景的多 Agent 项目：系统处理内部支持工单，并自带 Benchmark、Trace 级断言、安全测试与缺陷归因能力。

## 核心能力

- 4 类业务 Agent：理解、处理、回复、质检
- 流程编排器：状态机、重试、幂等、超时与降级
- SQLite 持久化：工单、事件、Agent Trace、评测结果
- Benchmark 数据集：L1/L2/L3 + 安全、检索、状态机专项
- 自动化评测：单 Agent、端到端、安全、成本、鲁棒性
- LLM Provider 抽象：默认规则引擎，可切换 OpenAI 兼容接口
- pytest 测试：unit、integration、e2e、security、regression

## 快速开始

```powershell
cd D:\agent_pro

# 后端依赖
python -m pip install pydantic fastapi uvicorn pytest

# 前端依赖（项目使用 pnpm，store 已指向 D:\pnpm-store）
cd frontend
pnpm install --config.node-linker=hoisted
cd ..

# 一键启动后端 8000 + 前端 5173
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

启动后访问：

- App 工作台：http://127.0.0.1:5173/
- 后端接口文档：http://127.0.0.1:8000/docs
- 独立演示页：http://127.0.0.1:5173/standalone.html

> 注意：本项目必须放在 NTFS 磁盘（如 D 盘）。不要放在 FAT32 的盘符上，
> 否则 pnpm 无法创建符号链接，前端依赖会安装失败。

运行测试：

```powershell
python -m pytest
```

运行一条演示工单：

```powershell
python -m app.cli run-ticket --text "AF205 喂食器连不上 Wi-Fi，显示错误码 E104，请尽快处理"
```

运行 Benchmark：

```powershell
python -m app.cli benchmark --dataset benchmark/datasets/tickets_l1_l3.jsonl
```

查看数据库中的工单：

```powershell
python -m app.cli show-ticket --ticket-id 1
```

## 环境变量

默认使用规则引擎，无需 API Key 即可运行和测试。

接入真实 LLM 时设置：

```powershell
$env:TICKET_AGENT_PROVIDER="openai_compatible"
$env:OPENAI_API_KEY="..."
$env:OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:TICKET_AGENT_MODEL="qwen-plus"
```

## 目录

```text
app/
  agents/          # 理解、处理、回复、质检
  orchestrator/    # 状态机与编排
  providers/       # LLM Provider 抽象
  tools/           # 知识库、路由、风险扫描
  storage/         # SQLite 仓储与 Trace
benchmark/
  datasets/        # Benchmark 数据
  metrics/         # 指标与断言
  judges/          # LLM Judge 抽象
  runners/         # 批量评测入口
tests/             # pytest 测试
```

## 设计取舍

- 不使用复杂外部 Agent 框架，降低复现成本，便于面试讲清链路。
- Agent 不直接操作数据库，由 Orchestrator 统一落库。
- 所有 Agent 输入输出使用 Pydantic Schema 强校验。
- 默认规则 Provider 让测试稳定、可离线运行；真实 LLM 作为可插拔能力。

# 架构说明

## 1. 目标

本项目用一个真实可闭环的工单场景，演示多 Agent 系统的实现与质量评测：

```text
用户提交工单
  -> 理解 Agent（分类/优先级/风险）
  -> 处理 Agent（检索/路由）
  -> 回复 Agent（草稿）
  -> 质检 Agent（风险/动作）
  -> 状态机（回复/转人工/关闭）
```

## 2. 分层

| 层 | 目录 | 责任 |
|---|---|---|
| 入口层 | `app/cli.py` | 命令行、参数、报告输出 |
| 编排层 | `app/orchestrator/` | 状态机、流程控制、Trace |
| Agent 层 | `app/agents/` | 理解、处理、回复、质检 |
| 工具层 | `app/tools/` | 知识检索、路由、风险扫描 |
| 模型层 | `app/providers/` | 规则引擎与 OpenAI 兼容 Provider |
| 存储层 | `app/storage/` | SQLite 工单、事件、Trace、评测结果 |
| 评测层 | `benchmark/` | 数据集、断言、Judge、批量 Runner |

调用方向是单向的：

```text
cli -> container -> workflow -> agents -> tools/providers
                         |
                         -> repository
```

Agent 不直接操作数据库，所有落库由 Workflow 统一完成，便于 Trace、状态与评测。

## 3. 状态机

```text
CREATED -> PARSING -> PARSED -> PROCESSING -> DRAFTED -> REVIEWING
                                                   |
                                                   +-> APPROVED -> REPLIED -> CLOSED
                                                   +-> NEED_HUMAN -> CLOSED
                                                   +-> REJECTED -> NEED_HUMAN/CLOSED
                                                   +-> RETRYING
                                                   +-> FAILED
```

关键测试点：

- 禁止非法跳转
- 已关闭状态是终态
- 高风险工单不自动关闭
- 重试不能重复生成同一 Trace
- 状态变化必须记录事件

## 4. 风险模型

风险扫描器覆盖：

- PII
- 凭据索取
- 越权承诺
- Prompt Injection
- 投诉升级

关键风险工单必须转人工，不允许自动回复。

## 5. Benchmark

`benchmark/datasets/tickets_l1_l3.jsonl` 按难度分层：

| 难度 | 含义 | 示例 |
|---|---|---|
| L1 | 单意图、明确 | 配网、设备故障、退款 |
| L2 | 需要检索/路由 | 卡粮、物流、账号安全 |
| L3 | 模糊、冲突、安全风险 | 社工、Prompt Injection、投诉升级 |

每条数据可以断言：

- 分类
- 优先级
- 路由组
- 是否转人工
- 最终状态

## 6. 为什么默认是规则 Provider

真实 LLM 有网络、费用和随机性，不适合做所有测试的稳定基线。项目默认使用规则 Provider，保证：

- 离线可跑
- 测试稳定
- 结果可复现

需要真实模型时，通过 `TICKET_AGENT_PROVIDER=openai_compatible` 切换，不需要改 Agent 代码。

# 简历项目写法

## 项目名称

智能工单多 Agent 质量评测平台

## 技术栈

Python、pytest、Pydantic、SQLite、DeepEval/LLM-as-a-Judge（扩展）、OpenAI 兼容接口、状态机、Benchmark

## 项目描述

面向内部支持场景搭建智能工单多 Agent 处理平台，覆盖工单理解、知识检索、路由分派、回复生成、质检与状态归档；建设 L1~L3 Benchmark 与自动化评测体系，保障版本质量可量化、可回归、可归因。

## 核心工作

1. 基于 Pydantic Schema 与显式状态机实现 4 Agent 编排链路，覆盖理解、处理、回复、质检及异常兜底。
2. 建设 L1~L3 Benchmark 数据集与安全、检索、状态机专项场景，支持分类、优先级、路由、转人工、最终状态断言。
3. 记录 Agent 级 Trace，包括输入输出、耗时、模型、错误与 Token 成本，支持中间链路定位而非只看最终回复。
4. 构建风险扫描与质检机制，覆盖 PII、凭据索取、越权承诺、Prompt Injection 和投诉升级，确保高风险工单转人工。
5. 使用 pytest 建设 unit/integration/e2e/security/regression 五层测试，并输出结构化 Benchmark 报告与回归基线。

## 当前可验证结果

- 28 项自动化测试全部通过
- 9 条 L1~L3 Benchmark 全部通过
- 36/36 条评测断言通过
- 支持 CLI 单工单执行、全量 Benchmark、工单追溯和健康检查

这些数字来自本地实际执行，可以重复验证。

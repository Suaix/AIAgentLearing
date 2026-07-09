# 主流模型对比与选型

> 创建日期：2026-06-30
> 关联模块：模块 1 — 基础概念
> 关联笔记：[[03-transformer-attention]]（模型的底层架构）、[[04-agent-four-elements]]（选型影响 Agent 能力）
> 代码：`code/01-foundations/model_comparison.py`、`model_step3.py`
> 评估记录：🟡 基础（1.75分）
> 掌握状态：🟡 基础

---

## 一句话总结

**模型选型 = 四个独立维度的决策矩阵：数据隐私（一票否决）→ 任务复杂度 → 延迟要求 → 预算，没有"最好的模型"，只有"最合适的模型"。**

---

## 2026年6月主流模型速查

| 模型 | Context | 输入$/1M | 输出$/1M | 定位 |
|------|---------|----------|----------|------|
| Claude Opus 4.8 | 1M | $5.00 | $25.00 | 编程最强、推理最深 |
| GPT-5.5 | 1M | $2.50 | $10.00 | 综合均衡 |
| Gemini 3.1 Pro | 1M | $2.00 | $12.00 | 多模态强 |
| DeepSeek V4 Flash | 1M | $0.14 | $0.28 | 性价比之王、中文母语级 |
| Llama 4 Scout | 10M | 免费 | 免费 | 开源自部署、超长窗口 |

> ⚠️ 模型版本和价格变化极快，以上信息截至 2026-06-30。做决策前重新查最新数据。

---

## 选型四问框架

```
① 数据能出内网？
   └─ 不能 → 开源自部署（Llama/Qwen）

② 任务复杂度？
   └─ 多步推理/代码生成 → 旗舰（Claude Opus/GPT-5.5）
   └─ 简单分类/摘要 → 性价比（DeepSeek/Haiku）

③ 延迟要求？
   └─ < 500ms → 小模型（Flash/Haiku/mini）
   └─ 可等 → 大模型

④ 预算？
   └─ 充足 → 旗舰 + Router 策略
   └─ 有限 → 性价比模型，关键任务升级
```

## 典型场景速查

| 场景 | 推荐 | 原因 |
|------|------|------|
| 高并发客服 | DeepSeek V4 Flash | 50万次/天→便宜是刚需，延迟 < 1s |
| 合同审查（数据不外泄） | Llama 4 自部署 | 硬约束排除所有闭源模型 |
| 个人学习助手 | DeepSeek V4 | 中文好、便宜、够用 |
| Agent 代码生成 | Claude Opus 4.8 | SWE-Bench 83.5%，编程场景值得溢价 |
| 长文档分析（1000页+） | Llama 4 Scout | 10M 窗口无人能及 |

---

## 开发启示

1. **代码层面用统一接口**：`call_model(config, prompt)` 模式屏蔽不同 API 差异，方便切换
2. **Router 策略是生产标配**：80% 的请求用小模型，20% 难的任务升级大模型——成本和质量的帕累托最优
3. **别信任何一张静态对比表**：模型市场每月都在变，养成查最新数据的习惯

---

参考来源：
1. [Agathon.ai] Which LLM Should You Use? June 2026 — https://agathon.ai/whichllm
2. [Morph] DeepSeek V4: Architecture, Benchmarks, Pricing — https://www.morphllm.com/deepseek-v4
3. 评估记录：[2026-06-30 主题评估](../assessments/topic/2026-06-30-model-comparison-assessment.md)

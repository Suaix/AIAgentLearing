# 周度学习总结 — 2026-06-29 周

> 状态：🔄 进行中（本周第 1 天）
> 本周学习天数：1 天
> 本周学习时长：约 6 小时

---

## 本周学习内容一览

### 已学完的主题

| 主题 | 日期 | 知识类型 | 掌握程度 |
|------|------|---------|---------|
| 学习方法论 v2.0 | 06-29 上午 | 元认知 | ✅ 理解并应用 |
| LLM 无状态性与上下文管理 | 06-29 上午 | 📝 核心概念 | ✅ 理解 + 代码实践 |
| Tokenization & BPE | 06-29 下午① | 📝 + 🔧 | ✅ 理解 + 4个练习 |
| Token 成本估算 | 06-29 下午① | 🧠 策略 | ✅ 跨模型对比 |
| Agent 四要素框架 | 06-29 下午② | 📝 + 🔧 | ✅ 理解 + 4个练习 |
| LLM 驱动感知升级 | 06-29 下午② | 🔧 实践 | ✅ if/else → DeepSeek API |

### 专题笔记已建立

- [[../notes/llm-statelessness]] — LLM 无状态性心智模型
- [[../notes/tokenization]] — BPE 算法、Token 效率、成本计算
- [[../notes/agent-four-elements]] — 感知→规划→执行→记忆 四要素框架

---

## 关键收获

### 1. 学习方法论升级
从纯苏格拉底 → **5 步渐进循环**（热身 → 提问 → 精讲 → 引导修改 → 费曼检验）。核心原则：I Do → We Do → You Do。

### 2. LLM 开发核心心智模型
```
模型无状态 → messages 数组 = 唯一外部记忆 → 开发者管理上下文生命周期
                                          → Token 成本随对话线性增长
                                          → Context Window 是硬上限
```

### 3. Tokenization 的实践意义
- 不同 tokenizer 的中文效率可差 **2-6 倍**（p50k: 21 vs o200k: 5）
- Token 计数 = 成本估算的基础
- 选模型时把 tokenizer 效率纳入考量

### 4. Agent 四要素架构
- **感知**：非结构化文本 → 结构化意图+实体（规则匹配 → LLM 升级路径）
- **规划**：Plan-then-Execute（已知任务）vs ReAct（未知任务）
- **执行**：Agent 区别于 Chatbot 的本质 = 调用外部工具改变世界
- **记忆**：短期 = messages 数组（有容量限制），长期 = 持久化存储（无限制）
- 四要素松耦合设计：各自独立优化，互不阻塞

---

## 代码产出

| 文件 | 内容 | 练习数 |
|------|------|--------|
| `code/01-foundations/chat_loop.py` | 交互式对话循环 | - |
| `code/01-foundations/chat_loop_exercises.py` | 上下文管理 4 练习 | 4 |
| `code/01-foundations/tokenization_lab.py` | 5 个 Tokenization 实验 | - |
| `code/01-foundations/tokenization_step3.py` | 渐进练习 4 任务 | 4 |
| `code/01-foundations/agent_four_elements.py` | Agent 四要素模拟 | - |
| `code/01-foundations/agent_step3.py` | 渐进练习 4 任务 | 4 |

---

## 遇到的问题

1. 练习 2 `print/break` 顺序问题 — 快速修复
2. 任务 ③ token 截断残留乱码 `�` — 识别为更深层问题（需同时校验 token 数和字符质量）

---

## 下次计划

- [x] Agent 四要素框架（感知、规划、执行、记忆）
- [ ] Attention 机制精要
- [ ] 主流模型对比
- [ ] 模块 1 独立里程碑小项目（Step 5）→ 模块 2 Prompt Engineering

---

## 模块 1 进度

预计主题 6 个，已完成 3 个（LLM 无状态性、Tokenization、Agent 四要素），剩余：
- [ ] Transformer 架构精要
- [ ] Attention 机制
- [ ] 主流模型对比 + 成本估算

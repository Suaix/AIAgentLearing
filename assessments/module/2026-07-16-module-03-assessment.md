# 评估记录 — 模块 3：Tool Use / Function Calling（模块评估）

- **评估日期**：2026-07-16
- **模块**：模块 3 — Tool Use / Function Calling
- **主题数**：4（+ Step 5 独立里程碑）
- **状态**：✅ 已完成
- **关联笔记**：[[12-tool-definition]]、[[13-json-schema-cross-provider]]、[[14-single-vs-multi-turn-tool-calls]]、[[15-tool-selection-strategies]]、[[16-tool-error-handling]]
- **代码目录**：`code/03-tool-use/`（6 个文件 + step5 独立项目）

---

## 1. 各主题评估汇总

| 子主题 | 重要性 | 日期 | 得分 | 总评 |
|--------|--------|------|------|------|
| Tool Definition（JSON Schema） | A (×3.0) | 07-13 | 3.00 | 🟢 L3 |
| 单轮 vs 多轮调用 | A (×3.0) | 07-14 | 2.40 | 🟢 L3 |
| Tool 选择策略 | B (×2.0) | 07-14 | 2.40 | 🟢 L3 |
| 错误处理与重试 | A (×3.0) | 07-15 | 3.10 | 🟢 L3 |

**模块内主题加权平均**（不含 Step 5）：  
(3.00×3 + 2.40×3 + 2.40×2 + 3.10×3) / 11 = **2.75 / 4.00**

---

## 2. 维度 D — 长期保持与迁移（权重 20%）

| 评分项 | 得分 | 证据 |
|--------|------|------|
| Step 5 独立构建能力 | L3 🟢 | 不看之前代码，独立完成了含 3 工具 + 超时包装 + 按工具计数的完整 Agent |
| 多轮调用设计 | L3 🟢 | 正确实现 assistant → tool_calls → tool result 消息链 |
| 错误处理应用 | L3 🟢 | call_with_timeout + per_tool_errors + max_turns 全部正确迁移到新代码 |
| Tool Schema 定义 | L3 🟢 | 三个工具的 JSON Schema 正确定义，type/properties/required/description 完整 |
| 跨场景泛化 | L3 🟢 | A（搜索+计算）/ B（数据库+计算）/ C（错误恢复）三个场景全部覆盖 |

**维度 D 得分**：3.00 / 4.00（加权 20%）= **0.60**

---

## 3. 各主题维度 D 补齐（模块结束时统一填写）

| 子主题 | 维度 D 观察 |
|--------|-----------|
| Tool Definition | Step 5 中独立写出三个 JSON Schema，结构完整 ✅ |
| 单轮 vs 多轮 | Step 5 中正确实现多轮循环（第 159~216 行），消息追加顺序正确 ✅ |
| Tool 选择 | 使用 `tool_choice="auto"`，信任 LLM 自主决策 ✅ |
| 错误处理 | call_with_timeout + per_tool_errors 两个核心模式均独立实现 ✅ |

---

## 4. 综合评分

| 维度 | 权重 | 子主题均分 | Step 5 表现 | 综合得分 | 加权 |
|------|------|----------|------------|---------|------|
| A - 概念理解 | 30% | 3.00 | - | 3.00 | 0.90 |
| B - 代码实践 | 30% | 2.50 | 2.75 | 2.63 | 0.79 |
| C - 知识结构化 | 20% | 3.00 | 3.00 | 3.00 | 0.60 |
| D - 长期保持 | 20% | - | 3.00 | 3.00 | 0.60 |

**模块综合评分**：0.90 + 0.79 + 0.60 + 0.60 = **2.89 / 4.00**

**综合评价**：🟢 **L3 良好** — 模块 3 核心能力牢固掌握，能独立构建带错误处理的 Tool Use Agent。

---

## 5. Step 5 具体反馈

### 正确实现的

| 机制 | 代码位置 | 评价 |
|------|---------|------|
| JSON Schema 定义 | 第 69~115 行 | 三个工具的正确定义，type/properties/required 完整 |
| Agent 循环 | 第 159~216 行 | assistant → tool_calls → tool results 消息链正确 |
| call_with_timeout | 第 121~132 行 | ThreadPoolExecutor + future.result 用法正确 |
| 按工具名计数 | 第 209 行 | `tools_call_record[funname]` key 为工具名 ✅ |
| 不可预判错误 | 第 31 行 | 30% 随机概率触发超时 ✅ |
| 双层保护 | System Prompt + max_turns | 软约束（行为准则）+ 硬约束（max_turns=10）✅ |

### 需修正的小问题

| 问题 | 位置 | 严重度 |
|------|------|--------|
| `calculator` 拼写为 `calcuator` | 第 42/87/118 行 | 🟡 轻微 |
| f-string 双花括号导致变量名未插值 | 第 130 行 | 🟡 轻微 |
| 未使用的 import（ast/random.Random/numpy） | 第 1/5/11 行 | 🟡 轻微 |

---

## 6. 薄弱点清单

> 模块 3 无 L1 级薄弱点。所有 A 级主题均已牢固掌握。

| 薄弱点 | 级别 | 说明 |
|--------|------|------|
| Step 3 单轮/多轮调用时 Python 错误处理编码细节 | 🟡 轻微 | 已在子主题④中显著改善 |
| 代码整洁度（拼写、import） | 🟡 轻微 | Step 5 中仍有拼写错误，建议提交前自查 |

---

## 7. 跨模块关联

| 模块 3 知识点 | 关联模块 | 如何被用到 |
|-------------|---------|-----------|
| Tool Definition (JSON Schema) | 模块 7（MCP） | MCP Server 的 Tool 定义即 JSON Schema |
| 多轮调用循环 | 模块 5（Agent 架构） | ReAct 循环的核心：Think → Act → Observe |
| 错误处理（超时+降级） | 模块 9（生产化部署） | 熔断、限流、降级是生产的核心 |
| tool_choice 控制 | 模块 6（多 Agent） | 不同 Agent 角色需要不同的 tool_choice 策略 |

---

## 8. 复习建议

- **一周内（07-23）**：回顾 call_with_timeout 和降级链模式
- **模块 5 学习时**：回顾 Agent 循环结构，ReAct 在此基础上增加"思考"步骤
- **长期保持回检**：模块 4（RAG）中 Tool Use 会被频繁使用，自然巩固

---

## 9. 模块 3 学习总结

| 指标 | 数值 |
|------|------|
| 学习天数 | 3 天（07-13 ~ 07-16） |
| 子主题数 | 4 |
| Step 0 warmup 文件 | 4 个 |
| Step 3 练习文件 | 4 个 |
| Step 5 独立项目 | 1 个（research_assistant） |
| 专题笔记 | 5 份 |
| 主题评估 | 4 份 |
| 综合评分 | **2.89 🟢 L3 良好** |

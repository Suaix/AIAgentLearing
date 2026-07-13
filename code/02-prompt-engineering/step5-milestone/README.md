# 模块 2 Step 5 — 独立里程碑：智能客服 Prompt 系统

> **规则提醒**：可以查阅官方文档，不能看 `code/02-prompt-engineering/` 下之前的代码。

## 项目目标

从零构建一个**智能客服 Prompt 系统**，综合运用模块 2 全部 6 个主题：

| 主题 | 在项目中的体现 |
|------|---------------|
| System Prompt 设计 | 3 种客服角色的 System Prompt 模板 |
| Few-shot Prompting | 每个角色配备精选示例 |
| Chain-of-Thought | 复杂问题引导逐步推理 |
| ReAct Prompting | 需要"工具"的请求走 ReAct 循环 |
| 结构化输出 | 所有回复统一 JSON 格式 |
| Prompt 版本管理 | 两版 System Prompt 的 A/B 对比 |

---

## 项目需求

### 一、三角色 System Prompt 设计

设计 3 个客服角色的 System Prompt，每个需要明确包含：

1. **角色定义**：我是谁、我的职责
2. **能力边界**：能做什么、不能做什么
3. **输出格式**：必须返回的 JSON 结构
4. **行为约束**：什么绝对不能做

| 角色 | 职责 | 特殊要求 |
|------|------|---------|
| `general_cs` | 通用客服 | 处理产品咨询、引导用户提供详细信息 |
| `tech_support` | 技术支持 | 需要 CoT 逐步排查，先理解问题再给方案 |
| `complaints_handler` | 投诉处理 | 共情 + 结构化收集信息 + 明确后续步骤 |

### 二、Few-shot 示例库

为每个角色至少准备 **2 个** Few-shot 示例（共 ≥6 个），格式为 `(user_input, expected_output)`。
示例需要覆盖该角色的典型场景。

### 三、CoT 推理（tech_support 角色）

技术支持角色在生成最终回答前，需要先输出推理过程：

```
用户问题 → 分步骤分析 → 逐条排查 → 最终建议
```

LLM 响应中需要包含 `reasoning` 字段，记录推理链条。

### 四、ReAct 模式（需要工具时）

当用户问题涉及以下内容时，自动切换为 ReAct 模式：

- 查询订单状态 → 调用 `check_order(order_id)`
- 查询产品信息 → 调用 `lookup_product(product_name)`
- 查询常见问题 → 调用 `get_faq(topic)`

**你需要实现 3 个模拟工具函数**（返回假数据即可），以及 ReAct 循环：

```
Thought → Action → Observation → ... → Final Answer
```

ReAct 循环最多 5 轮，超时强制给出当前最佳回答。

### 五、结构化 JSON 输出

所有角色最终回复必须解析为统一的 JSON 结构：

```json
{
  "role": "general_cs | tech_support | complaints_handler",
  "reasoning": "CoT 推理过程（tech_support 必填，其他可选）",
  "answer": "最终回答文本",
  "confidence": "high | medium | low",
  "used_tools": ["check_order", "lookup_product"],
  "follow_up_suggestions": ["建议追问1", "建议追问2"]
}
```

### 六、Prompt 版本管理与 A/B 对比

1. 每个角色的 System Prompt 至少有 **v1.0** 和 **v2.0** 两个版本
2. v1.0 和 v2.0 之间要有**明确差异**（如：v1 简洁直接，v2 更详细的角色背景和行为约束）
3. 对同一组测试用例，分别用 v1 和 v2 运行
4. 生成 A/B 对比报告，包含：
   - 每个测试用例两版回答的并排对比
   - 简单的评分（你自己定义评分标准，至少含"回答质量"和"格式合规"两个维度）
   - 总体结论：哪个版本更好，为什么

---

## 测试场景（5 个）

你需要用以下 5 个测试用例验证你的系统：

| # | 用户输入 | 预期路由 | 关键验证点 |
|---|---------|---------|-----------|
| 1 | "你们蓝牙耳机的续航时间是多少？" | general_cs / ReAct | 触发产品查询工具 |
| 2 | "订单 #ORD-12345 什么时候能到？" | general_cs / ReAct | 触发订单查询工具 |
| 3 | "我按照说明书连接WiFi但一直连不上，路由器是TP-Link的" | tech_support | CoT 推理链 + reasoning 字段 |
| 4 | "我上周买的音箱收到就是坏的，我要退款！" | complaints_handler | 共情 + 结构化处理 + follow_up |
| 5 | "蓝牙耳机和骨传导耳机哪个更适合跑步？" | general_cs | Few-shot + 产品对比（可能触发工具） |

---

## 技术要求

- **语言**：Python 3.12+
- **API**：DeepSeek API（`deepseek-v4-flash` 或 `deepseek-v4-pro`）
- **SDK**：`openai` SDK（兼容模式）
- **依赖**：`openai`, `python-dotenv`, `httpx`
- **运行方式**：`uv run python code/02-prompt-engineering/step5-milestone/main.py`

---

## 交付物

1. `main.py` — 完整可运行的主程序
2. 运行 `uv run python main.py` 后自动执行全部 5 个测试用例
3. 终端输出每个测试用例的结果（JSON 格式）
4. 最后输出 A/B 对比报告

---

## 评分标准（自我评估用）

| 维度 | 满分 | 说明 |
|------|------|------|
| System Prompt 质量 | 20 | 角色清晰、边界明确、约束有效 |
| Few-shot 示例质量 | 15 | 覆盖典型场景、格式一致 |
| CoT 推理有效性 | 15 | 推理链条清晰、逻辑可追踪 |
| ReAct 实现正确性 | 20 | 循环正确、工具调用准确、终止条件合理 |
| JSON 输出规范性 | 15 | 格式正确、字段完整、解析无异常 |
| A/B 对比完整性 | 15 | 两版差异明确、评分合理、结论有据 |
| **总分** | **100** | |

---

## 提示

- 先用最简单的方式让一个角色跑通，再逐步加功能和角色
- ReAct 循环部分先用 `print` 打印 Thought/Action/Observation 方便调试
- 如果 API 返回的 JSON 解析失败，做好容错处理
- A/B 对比可以在最后统一做，不必每个测试用例都实时对比

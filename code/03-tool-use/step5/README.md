# Step 5 独立里程碑 — 智能研究助手 Agent

> 模块 3（Tool Use / Function Calling）终极检验
>
> 规则：可以查阅官方文档，不能看 `code/03-tool-use/` 下之前的代码和笔记。

---

## 一、项目目标

构建一个**智能研究助手 Agent**：用户提出研究问题 → Agent 搜索资料 → 提取数据 → 计算分析 → 给出结论。

---

## 二、三个工具

### 工具 1：`web_search(query: str) -> dict`

互联网搜索引擎，返回模拟的搜索结果。

**设计要求**：
- 模拟不可预判错误：**30% 概率** 返回超时或连接失败（`time.sleep(3)` 模拟慢查询）
- 正常返回格式：`{"status": "ok", "query": "...", "results": [...]}`
- 错误返回格式：`{"error": "...", "message": "..."}`
- 内置一些"伪知识库"，针对特定关键词返回有意义的数据，例如：
  - "GPT-4" → 返回参数量约 1.8 万亿的相关论文
  - "Transformer" → 返回 65M 参数相关数据
  - "大模型参数" → 返回近几年模型参数增长数据

### 工具 2：`calculator(expression: str) -> dict`

安全计算数学表达式。

**设计要求**：
- 只允许 `0-9 + - * / ( ) . %` 字符（安全过滤）
- 错误类型：
  - 非法字符 → `{"error": "invalid_chars", "message": "..."}`
  - 除零 → `{"error": "division_by_zero", "message": "..."}`
  - 语法错误 → `{"error": "syntax_error", "message": "..."}`
- 正常返回：`{"status": "ok", "expression": "...", "result": ...}`

### 工具 3：`paper_db(query: str) -> dict`

模拟本地论文数据库查询。

**设计要求**：
- 包含至少 **5 篇 AI 论文**的模拟数据（标题、作者、年份、参数量、关键指标等）
- 不支持 DROP/DELETE 操作 → 返回权限错误
- SQL 必须包含 FROM 子句 → 否则返回语法错误
- 正常返回：`{"status": "ok", "rows": [...], "count": N}`

---

## 三、技术要求（覆盖模块 3 全部 4 个子主题）

### 3.1 Tool Definition（JSON Schema）

三个工具都要定义完整的 JSON Schema，包含：
- `type`、`properties`、`required`、`description`

### 3.2 多轮调用

Agent 要能执行"搜索 → 提取数据 → 计算 → 再搜索"的链式多轮调用。

### 3.3 Tool 选择

`tool_choice="auto"`，让 LLM 自主决策调哪个工具。

### 3.4 错误处理

| 机制 | 要求 |
|------|------|
| 超时包装 | 用 `call_with_timeout(func, kwargs, timeout=5.0)` 包装每个工具 |
| 失败计数 | 按工具名分别计数（`dict[str, int]`），不共用计数器 |
| 连续失败 | 同一工具连续失败 2 次后告知用户 |
| 硬约束 | `max_turns=10`，防止无限循环 |

---

## 四、Agent 循环骨架

```
messages = [system_prompt, user_message]

for turn in range(1, max_turns + 1):
    response = client.chat.completions.create(
        model=..., messages=..., tools=..., tool_choice="auto"
    )
    
    if 无 tool_calls:
        输出最终回答，结束循环
    
    for 每个 tool_call:
        用 call_with_timeout 执行工具（超时 5 秒）
        将结果作为 tool role 消息追加到 messages
        更新 per_tool_errors 计数
```

---

## 五、测试场景（至少跑通 2 个）

### 场景 A：搜索 + 计算

```
用户：「近三年AI大模型参数量增长了大约多少倍？帮我搜索相关数据并计算。」
流程：搜索(大模型参数增长) → 提取数字 → 计算(增长率) → 结论
```

### 场景 B：多次查询 + 计算

```
用户：「帮我查一下Transformer和Mamba两篇论文的关键数据，
      算一下Transformer的参数量是Mamba的多少倍。」
流程：paper_db(Transformer) → paper_db(Mamba) → calculator(除法) → 结论
```

### 场景 C（可选）：错误恢复

```
用户：「查询 ResNet 论文，然后帮我算一下 100÷0。」
流程：paper_db(ResNet) → calculator(100/0) → 收到 error → 解释除零
```

---

## 六、文件要求

| 文件 | 说明 |
|------|------|
| `code/03-tool-use/step5/research_assistant.py` | 主程序，`uv run python ...` 直接运行 |
| `code/03-tool-use/step5/README.md` | 本文件 |

### 代码规范

- `.env` 加载：`from dotenv import load_dotenv; load_dotenv()`
- 模型：`deepseek-v4-flash`（或 `deepseek-v4-pro`）
- 三个测试场景通过命令行参数选择运行

---

## 七、评估标准

| 维度 | 考察点 |
|------|--------|
| A-概念理解 | JSON Schema 定义是否正确？多轮循环是否合理？ |
| B-代码实践 | Agent 循环能跑通吗？错误处理生效吗？ |
| C-知识结构化 | 代码结构清晰吗？三个工具设计合理吗？ |
| D-迁移能力 | 能不能不看之前代码独立完成？ |

---

## 八、允许的参考资料

- [OpenAI Function Calling 文档](https://platform.openai.com/docs/guides/function-calling)
- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [Python concurrent.futures 文档](https://docs.python.org/3/library/concurrent.futures.html)

> ❌ 禁止查看 `code/03-tool-use/` 下之前的代码和 `notes/` 下的笔记。

# Tool Use 错误处理、超时与重试策略

> 创建日期：2026-07-15
> 关联模块：模块 3 — Tool Use / Function Calling
> 关联笔记：[[15-tool-selection-strategies]]（tool_choice 控制工具调用自由度）、[[14-single-vs-multi-turn-tool-calls]]（多轮调用是错误重试的基础）
> 代码：`code/03-tool-use/tool_error_handling_warmup.py`、`code/03-tool-use/tool_error_handling_step3.py`
> 评估记录：[2026-07-15-tool-error-handling-assessment.md](../assessments/topic/2026-07-15-tool-error-handling-assessment.md)

---

## 一句话总结

**Tool Use 错误处理不是用 `try/except` 写死分支，而是把错误信息注入 Agent 循环的 tool role 消息中，让 LLM 自主决策重试策略——同时用双层保护（软约束 System Prompt + 硬约束 max_turns/timeout）防止失控。**

---

## 核心概念

### 1. 两类错误的本质区别

| 维度 | 可预判错误 | 不可预判错误 |
|------|----------|------------|
| **模型能否规避** | ✅ 格式/内容层面 | ❌ 取决于外部系统状态 |
| **例子** | SQL 语法错误、参数格式不对、除零 | API 宕机、网络超时、DB 连接断开 |
| **模型行为** | 强模型可能直接给出正确格式 | 模型无论如何无法预判 |
| **测试策略** | 用"故意错误的输入"触发 | 用随机概率或真实外部依赖触发 |

**实验发现**：DeepSeek v4 足够强大，对于可预判错误（如查询词太短、表达式格式错误），它会在发出工具调用前就自动修正参数格式。因此 warmup 阶段需要用**不可预判错误**（如随机 30% 概率超时）才能真正测到错误处理逻辑。

### 2. 错误流入 Agent 循环的数据流

```
工具执行 → 返回 {"error": "...", "message": "..."}
    ↓
包装为 tool role 消息:
    messages.append({"role": "tool", "tool_call_id": tc.id,
                     "content": json.dumps(result)})
    ↓
下一轮 LLM 看到这条 tool 消息 → 读 error message → 自主决策
```

📝 这与传统编程的根本区别：
- **传统**：`if error: do_x(); else: do_y()` — 程序员预写所有分支
- **Agent**：把 error 结果原样传回 LLM → LLM 自己读语义 → 自己决定下一步

### 3. 双层保护机制

| 层级 | 类型 | 机制 | 作用 |
|------|------|------|------|
| **软约束** | System Prompt | "同一工具连续失败2次后告知用户" | 引导 LLM 自主合理决策（优雅降级） |
| **硬约束** | 代码层 | `max_turns` + `call_with_timeout` | 兜底保护，防止极端情况资源耗尽 |

🧠 两者必须共存：
- 只用软约束 → LLM 可能不遵守（幻觉、误判）
- 只用硬约束 → 用户体验差，没有优雅降级

### 4. 外部超时包装 vs 内部降级链

| 维度 | 外部超时包装 `call_with_timeout` | 内部降级链 `get_weather_with_fallback` |
|------|-------------------------------|--------------------------------------|
| **保护位置** | 工具函数**外面**包一层 | 工具函数**内部**串联逻辑 |
| **解决问题** | "调用会不会卡死/超时" | "数据还能从哪拿" |
| **适用场景** | 单一路径、耗时不确定 | 同一数据有多个获取途径 |
| **实现** | `ThreadPoolExecutor` + `future.result(timeout)` | 主源→备源→缓存→兜底的 if-else 链 |
| **能否替代** | ❌ 两者正交，可叠加使用 | ❌ 降级链中的单个工具仍可能超时 |

### 5. 重试计数器按工具名隔离

修复前（Bug）：
```python
consecutive_errors = 0          # 所有工具共用一个计数器
consecutive_errors += 1         # 不区分是哪个工具报的错
```

修复后：
```python
per_tool_errors: dict[str, int] = {}                         # key=工具名
per_tool_errors[func_name] = per_tool_errors.get(func_name, 0) + 1  # 各自计数
```

**设计原则**：每个工具的失败历史应独立追踪。工具 A 失败 2 次不影响工具 B 的可用性判断——不同工具的可靠性是独立的。

---

## 常见陷阱

| 陷阱 | 表现 | 修复 |
|------|------|------|
| 模拟超时用可预判条件（如 query 长度） | LLM 规避后永远看不到超时 | 用随机概率模拟不可预判错误 |
| `ThreadPoolExecutor.submit(func(**kwargs))` | `TypeError: 'dict' object is not callable` | 改为 `submit(func, **kwargs)` |
| 异常返回用 `{err}` | `set is not JSON serializable` | 改为 `str(err)` |
| 降级链失败概率太低 | 永远看不到降级现象 | 加 `_FORCE_FAIL_DEMO` 开关做强制演示 |

---

## 核心代码模式

```python
# 模式1：真实超时包装器
def call_with_timeout(func, kwargs, timeout):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, **kwargs)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        return {"error": "timeout", "message": f"工具执行超时（>{timeout}秒）"}
    except Exception as e:
        return {"error": "exception", "message": str(e)}
    finally:
        executor.shutdown()

# 模式2：多级降级链
def get_weather_with_fallback(city):
    result = get_weather_primary(city)
    if "error" not in result:
        return result
    result = get_weather_fallback(city)
    if "error" not in result:
        return result
    if city in WEATHER_CACHE:
        return WEATHER_CACHE[city]
    return {"error": "all_sources_failed", "message": f"所有数据源均不可用: {city}"}

# 模式3：按工具名隔离的错误计数
per_tool_errors: dict[str, int] = {}
if error_flag:
    per_tool_errors[func_name] = per_tool_errors.get(func_name, 0) + 1
else:
    per_tool_errors[func_name] = 0
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| 错误消息作为 tool role 反馈 | 模块 5（Agent 架构） | ReAct/Reflexion 中"Observe 错误"是其核心反馈信号 |
| 双层保护（软+硬） | 模块 9（生产化部署） | 生产环境的限流、熔断、降级都依赖同样的双层思想 |
| call_with_timeout | 模块 8（评估与监控） | 超时是 Tracing 的关键指标之一 |
| 降级链 | 模块 4（RAG） | RAG 中检索失败回退到生成也适用降级链模式 |

---

## 参考来源

1. OpenAI API Docs — "Function Calling" — https://platform.openai.com/docs/guides/function-calling
2. Anthropic API Docs — "Tool Use" — https://docs.anthropic.com/en/docs/build-with-claude/tool-use
3. Python 官方文档 — `concurrent.futures` — https://docs.python.org/3/library/concurrent.futures.html
4. [[15-tool-selection-strategies]] — Tool 选择策略（tool_choice 控制自由度）
5. [[14-single-vs-multi-turn-tool-calls]] — 单轮 vs 多轮调用（多轮是重试的基础）

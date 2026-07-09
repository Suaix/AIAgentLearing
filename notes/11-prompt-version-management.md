# Prompt 版本管理

> 创建日期：2026-07-09
> 关联模块：模块 2 — Prompt Engineering
> 关联笔记：[[10-system-prompt-design]]（版本管理的对象就是 System Prompt 模板）、[[06-few-shot-prompting]]（Few-shot 示例可作为 Prompt 模板的一部分进行版本控制）
> 代码：`code/02-prompt-engineering/prompt_version_warmup.py`、`code/02-prompt-engineering/prompt_version_step3.py`
> 评估记录：[2026-07-09-prompt-version-management-assessment.md](../assessments/topic/2026-07-09-prompt-version-management-assessment.md)

---

## 一句话总结

**Prompt 版本管理是通过集中式 Registry + 变量模板 + 版本状态机，将 Prompt 从「散落在代码中的魔法字符串」提升为「可追溯、可对比、可回滚的项目资产」的工程实践。**

---

## 核心概念

### 1. 硬编码 Prompt 的三大痛点

| 痛点 | 表现 | 后果 |
|------|------|------|
| **版本混乱** | 同一 Prompt 在 3 个文件中被不同人改过 | 不知道哪个是正式版 |
| **全局更新困难** | 品牌改名需要搜遍所有文件改 Prompt | 容易遗漏，造成线上不一致 |
| **无法回滚** | 改完 Prompt 效果变差 | 只能凭记忆恢复或翻 Git log |

### 2. Prompt Registry 数据结构

```python
PROMPT_REGISTRY = {
    "prompt_name": {           # 系列名（如 customer_service）
        "v1.0": {              # 语义化版本号
            "created": "..."   # 创建日期
            "author": "...",   # 作者
            "status": "...",   # active | deprecated | draft
            "system": "...",   # System Prompt 模板（可含 {variables}）
            "variables": [...] # 模板中的变量列表
        },
        "v2.0": {...},         # 新版本
    }
}
```

核心操作：
- **读取当前版本**：遍历所有版本 → 找 `status == "active"` → `template.format(**vars)`
- **升级版本**：新版本 `status: "active"`，旧版本改为 `"deprecated"`
- **回滚**：把旧版本改回 `active`
- **A/B 测试**：同时取两个版本，分别调用 API 对比效果

### 3. 变量模板：Prompt 的 DRY 原则

```
硬编码：5 个品牌 = 5 份几乎一样的 Prompt  → 维护地狱
模板化：1 份模板 + 5 份变量配置           → 改一次全部生效
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 说明 |
|--------|---------|------|
| Registry 模式 | 模块 5（Agent 架构） | 多 Agent 系统中，每个 Agent 的 System Prompt 可用 Registry 统一管理 |
| 变量模板 | 模块 3（Tool Use） | Tool Definition 的 JSON Schema 本质也是模板——参数由调用时填充 |
| 版本状态机 | 模块 9（生产化部署） | CI/CD 中 Prompt 版本与代码版本协同发布 |

---

## 参考来源

1. promptfoo — "Prompt Versioning Best Practices" — https://www.promptfoo.dev/blog/prompt-versioning/ — 访问日期：2026-07-09
2. [[10-system-prompt-design]] — 版本管理的对象就是 System Prompt

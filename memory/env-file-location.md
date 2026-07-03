---
name: env-file-location
description: 项目的.env文件在项目根目录，不在各模块子目录下
metadata:
  type: project
---

项目的 `.env` 文件位于项目根目录 `/Users/summer/workspace/claudeProjects/AIAgentLearing/.env`，不在 `code/` 的任何子目录下。

使用 `load_dotenv()` 无参数调用即可——`python-dotenv` 会自动从当前目录向上递归查找 `.env` 文件。

**Why:** 之前错误地在 `code/02-prompt-engineering/few_shot_warmup.py` 中写了 `load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "01-foundations", ".env"))`，导致加载了不存在的路径，API key 未设置，触发 401 认证错误。模块 1 的代码用 `load_dotenv()` 无参数是对的。

**How to apply:** 项目中所有 Python 文件加载 `.env` 时统一使用 `load_dotenv()` 无参数形式。不要硬编码相对路径。

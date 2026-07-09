"""
模块 2 — Step 3 引导式修改：System Prompt 设计
通过 4 级渐进任务，从「改参数」到「独立设计」

运行方式：
    uv run python code/02-prompt-engineering/system_prompt_step3.py 1    # 任务①
    uv run python code/02-prompt-engineering/system_prompt_step3.py 2    # 任务②
    uv run python code/02-prompt-engineering/system_prompt_step3.py 3    # 任务③
    uv run python code/02-prompt-engineering/system_prompt_step3.py 4    # 任务④
"""

import os
import sys
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
http_client = httpx.Client(trust_env=False)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    http_client=http_client,
)
MODEL = "deepseek-v4-flash"


# ══════════════════════════════════════════════════════════════════════
# 共享工具函数
# ══════════════════════════════════════════════════════════════════════

def ask(system_prompt: str, user_question: str, temperature: float = 0.7,
        max_tokens: int = 400) -> str:
    """封装 API 调用，返回模型回复文本"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_question})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print(f"{response.to_json}")
    return response.choices[0].message.content


def show(label: str, answer: str):
    """格式化打印结果"""
    print(f"\n{'─' * 50}")
    print(f"【{label}】")
    print(f"{'─' * 50}")
    print(answer[:500])
    if len(answer) > 500:
        print("...(截断)")
    print(f"{'─' * 50}")


# ══════════════════════════════════════════════════════════════════════
# 任务 ①：改参数 — 从「温柔老师」到「严厉审查员」
# ══════════════════════════════════════════════════════════════════════

def task1_change_role():
    """
    任务 ①：修改 System Prompt 中的「身份」层，观察输出变化

    目标：
    - 理解「身份」如何影响模型的语气、深度、评价标准
    - 学会通过调整 System Prompt 来改变模型的「态度」而不只是「内容」

    你的 TODO：
      把下面「温柔老师」的 System Prompt 改成「严厉代码审查员」的版本。
      - 身份：你是一个以苛刻著称的高级代码审查员，曾在 Google/Facebook 工作
      - 行为规则：先找问题，再给建议；指出代码异味（code smell）；引用最佳实践
      - 禁止行为：不要说「写得不错」这种笼统的赞美（除非真的无可挑剔）

      改完后运行：uv run python code/02-prompt-engineering/system_prompt_step3.py 1
    """
    user_code = (
        "def calc(lst):\n"
        "    x = 0\n"
        "    for i in range(len(lst)):\n"
        "        x = x + lst[i]\n"
        "    return x / len(lst)\n"
    )
    user_question = f"请 review 这段代码：\n```python\n{user_code}```"

    # ── 基线：温柔老师版本 ──
    kind_teacher_sp = (
        "你是一个耐心的 Python 编程老师，擅长用鼓励的方式指导学生。"
        "指出问题时先说优点，再温和地给出改进建议。"
    )
    print("\n" + "=" * 60)
    print("📋 基线对比 — 温柔老师")
    print("=" * 60)
    show("温柔老师的回复", ask(kind_teacher_sp, user_question))

    # ═══════════════════════════════════════════════════════════
    # TODO ①：请在下面写出「严厉代码审查员」的 System Prompt
    # ═══════════════════════════════════════════════════════════
    strict_reviewer_sp = (
        # TODO: 你的代码 — 定义「严厉代码审查员」的身份+行为规则+禁止行为
        "你是一位以苛刻著称的高级代码审查员，曾在 Google/Facebook 工作。"
        "指出问题时先找问题，再给建议；指出代码异味（code smell）；引用最佳实践。"
        "禁止说「写得不错」这种笼统的赞美（除非真的无可挑剔）。"
    )
    # ── 你的版本 ──
    print("\n" + "=" * 60)
    print("🔧 你的版本 — 严厉代码审查员")
    print("=" * 60)
    show("严厉审查员的回复", ask(strict_reviewer_sp, user_question))

    # ── 思考题 ──
    print("\n🧐 对比两个输出：")
    print("  1. 语气有什么不同？")
    print("  2. 同一个代码问题，两个角色关注的点一样吗？")
    print("  3. 如果让你选一个来真正帮你提高代码质量，你选哪个？为什么？")


# ══════════════════════════════════════════════════════════════════════
# 任务 ②：加功能变体 — 新增一个角色
# ══════════════════════════════════════════════════════════════════════

def task2_add_role():
    """
    任务 ②：参照已有的三层结构，为新角色编写 System Prompt

    场景：你需要一个「技术面试官」AI，模拟技术面试中的追问环节。

    你的 TODO：
      在下面写一个「技术面试官」的 System Prompt，三层结构：
      ① 身份：资深后端面试官，擅长考察 Python/系统设计/问题解决能力
      ② 行为规则：根据候选人的回答追问深层原理；逐层加深；记录关键点
      ③ 禁止行为：不要一次问太多问题；不要给出答案；不要过度提示

      改完后运行：uv run python code/02-prompt-engineering/system_prompt_step3.py 2

    提示：复制任务 ① 中严厉审查员的写法，修改内容即可，不需要重新设计结构。
    """

    # ═══════════════════════════════════════════════════════════
    # TODO ②：请写出「技术面试官」的 System Prompt（三层结构）
    # ═══════════════════════════════════════════════════════════
    interviewer_sp = (
        # TODO: 你的代码 — 技术面试官的身份定义、行为规则、禁止行为
        "你是一位资深后端面试官，擅长考察 Python、系统设计和问题解决能力。"
        "根据候选人的回答追问深层原理；逐层加深，记录关键点。同一个问题至少要经过2轮追问，候选人如果回答不上来，给出简单提示，最多提示1次。"
        "一次只问一个问题；不要解释概念；不要给出答案；不要过度提示。"
    )

    # ── 模拟面试场景 ──
    interview_rounds = [
        "我熟悉 Python 的列表和字典，能用它们解决大部分数据存储问题。",
        "嗯……我之前做过一个用户管理系统，大概 1000 个用户，数据量不大所以没考虑太多性能问题。",
    ]

    print("\n" + "=" * 60)
    print("🎤 模拟面试 — 技术面试官")
    print("=" * 60)

    for i, candidate_answer in enumerate(interview_rounds, 1):
        print(f"\n--- 第 {i} 轮 ---")
        print(f"候选人：{candidate_answer}")
        result = ask(interviewer_sp, candidate_answer, temperature=0.7)
        show(f"面试官追问（第 {i} 轮）", result)

    print("\n🧐 检查你的面试官：")
    print("  1. 追问的方向是逐层加深的吗？")
    print("  2. 面试官有没有不小心给出答案或过度提示？")
    print("  3. 如果候选人说「不知道」，面试官会怎么回应？（预期：给一点线索但不直接给答案）")


# ══════════════════════════════════════════════════════════════════════
# 任务 ③：修复有问题的 System Prompt
# ══════════════════════════════════════════════════════════════════════

def task3_fix_bug():
    """
    任务 ③：下面这个 System Prompt 有 3 个问题，导致输出质量很差。

    你的 TODO：
      ① 先运行一次，观察输出（当前这个有问题的版本）
      ② 找出 3 个问题，然后在 `fixed_sp` 中写出修复版本
      ③ 再次运行，对比修复前后的输出

    问题提示（3 个）：
      - 问题 1：只有「禁止」没有「应该」（全是"不要XX"，模型不知道怎么做才是对的）
      - 问题 2：约束相互矛盾（一条要求详细，另一条要求简短——模型会摇摆不定）
      - 问题 3：缺少身份层（模型没有角色原型可以激活，表现不稳定）

    改完后运行：uv run python code/02-prompt-engineering/system_prompt_step3.py 3
    """
    user_question = "能用 Python 写一个简单的 Web 爬虫吗？我是初学者。"

    # ── Bug 版本（先看效果）──
    buggy_sp = (
        "不要用太长的代码。"
        "不要遗漏任何重要的安全注意事项。"
        "每一个步骤请给出非常详细的解释。"
        "回复内容尽量简短。"
        "不要使用 requests 库以外的第三方库。"
        "不要忽略异常处理。"
    )

    print("\n" + "=" * 60)
    print("🐛 Bug 版本 — 有问题的 System Prompt")
    print("=" * 60)
    show("Bug 版本的回复", ask(buggy_sp, user_question))

    # ═══════════════════════════════════════════════════════════
    # TODO ③：请修复这个 System Prompt
    # ═══════════════════════════════════════════════════════════
    fixed_sp = (
        # TODO: 你的代码 — 修复上述 3 个问题的 System Prompt
        # 提示：加上身份层，把否定式改为肯定式，消除矛盾的约束
        "你是一位经验丰富的 Python 开发者，专注于高质量的代码编写工作。"
        "代码要简洁清晰；每个步骤都给出详细解释；"
        "只使用 requests 库和 python 标准库；所有网络请求都必须包含 try-except 异常处理；只使用经过安全审计的api；"
    )

    print("\n" + "=" * 60)
    print("✅ 修复版本 — 你的修复")
    print("=" * 60)
    show("修复后的回复", ask(fixed_sp, user_question))

    print("\n🧐 对比检查：")
    print("  1. 修复后的输出是否更一致？（不再简短和详细之间摇摆）")
    print("  2. 模型的回答风格是否更确定？（有了身份之后）")
    print("  3. 肯定式指令是否比否定式更可靠？")


# ══════════════════════════════════════════════════════════════════════
# 任务 ④：扩展到新场景 — 设计「日报生成器」
# ══════════════════════════════════════════════════════════════════════

def task4_new_scenario():
    """
    任务 ④：从一个真实场景出发，独立设计 System Prompt

    场景描述：
      你所在的公司要求每个人每天写工作日报。日报包含：
      - 今日完成（3-5 条 bullet points）
      - 遇到的问题（如有）
      - 明日计划（2-3 条）
      - 整体耗时分布（哪些工作花了最多时间）

      但你每天太忙了，经常忘记写。你希望通过一个 AI 助手来解决：
      你口头描述今天做了什么（乱序的、口语化的），AI 帮你整理成规范的日报格式。

    你的 TODO：
      用三层结构设计「日报生成器」的 System Prompt。
      要求：
      ① 身份：明确角色
      ② 行为规则：输入是什么格式，输出是什么格式；如何从乱序信息中提取关键点
      ③ 禁止行为：不要编造没提到的内容；不要过度展开

      改完后运行：uv run python code/02-prompt-engineering/system_prompt_step3.py 4
    """

    # 模拟一天工作后的乱序口头描述
    messy_input = (
        "今天上午先开了个站会，然后修了一个用户登录页面的 bug，那个 bug 搞了快3小时，"
        "原来是 cookie 过期时间设错了。下午跟产品经理对了下个迭代的需求，大概1小时。"
        "快下班的时候把登录 bug 的修复提交了 CR。哦对中间还帮新人看了个环境配置问题，花了大概半小时。"
        "明天打算开始做那个新需求的接口设计，还有上周欠的技术文档要补一下。"
    )

    # ═══════════════════════════════════════════════════════════
    # TODO ④：请设计「日报生成器」的 System Prompt
    # ═══════════════════════════════════════════════════════════
    daily_report_sp = (
        # TODO: 你的代码 — 日报生成器的三层 System Prompt
        "你是一位工作日报生成助手，擅长从杂乱的工作内容描述中提取工作日报。"
        "从用户口语化的输入中提取以下信息\n"
        "1. 工作内容是什么？花费了多长时间？\n"
        "2. 遇到了什么问题？待办事项有哪些？\n"
        "3. 明天的计划是什么？\n"
        "提取信息后按照以下格式输出工作日报：\n"
        "## 工作日报\n"
        "### 今日工作内容\n"
        "1. [工作内容][耗时]\n"
        "2. [工作内容][耗时]\n"
        "..."
        "### 遇到的问题\n"
        "1. [问题描述]\n"
        "### 明日计划\n"
        "1. [计划描述]\n"
        "2. ...."
        "### 工时分布"
        "[以 Markdown 表格列出，含以下三列：序号、工作内容、工时。并按照工时从高到低排序。]"
        "今日工作内容按重要程度从高到低总结3～5条；如没有遇到问题，写无；明日计划按照重要程度填写2～3条；"
        "只从用户输入里提取信息，不要编造没提到的内容；不要过度展开；"

    )

    print("\n" + "=" * 60)
    print("📋 原始乱序输入（模拟你下班前的语音备忘）")
    print("=" * 60)
    print(f"  {messy_input}")

    result = ask(daily_report_sp, messy_input, temperature=0.3, max_tokens=5000)
    show("AI 生成的日报", result)

    print("\n🧐 自检清单：")
    print("  1. 输出是否包含了「今日完成」「遇到的问题」「明日计划」「耗时分布」四个板块？")
    print("  2. 有没有编造乱序输入里没提到的内容？")
    print("  3. 格式是否一致、可直接复制粘贴发到工作群？")


# ══════════════════════════════════════════════════════════════════════
# 主入口：命令行分发
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定任务编号（1-4）：")
        print("  uv run python code/02-prompt-engineering/system_prompt_step3.py 1")
        print("  uv run python code/02-prompt-engineering/system_prompt_step3.py 2")
        print("  uv run python code/02-prompt-engineering/system_prompt_step3.py 3")
        print("  uv run python code/02-prompt-engineering/system_prompt_step3.py 4")
        sys.exit(1)

    task_num = sys.argv[1]
    tasks = {
        "1": ("改参数 — 从温柔老师到严厉审查员", task1_change_role),
        "2": ("加功能变体 — 新增技术面试官角色", task2_add_role),
        "3": ("修 Bug — 修复有问题的 System Prompt", task3_fix_bug),
        "4": ("新场景 — 设计日报生成器", task4_new_scenario),
    }

    if task_num not in tasks:
        print(f"❌ 无效的任务编号：{task_num}（可选：1-4）")
        sys.exit(1)

    title, func = tasks[task_num]
    print(f"🚀 Step 3 — 任务 {task_num}：{title}")
    print("=" * 60)
    func()

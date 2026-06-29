"""
Agent 四要素 Step 3 — 引导式修改练习
======================================
4 个渐进任务：改参数 → 加功能 → 修 bug → 连接真实 LLM

运行方法：
    python code/01-foundations/agent_step3.py [任务号]
    如: python code/01-foundations/agent_step3.py 1
"""

import sys
import time
import re
import json
import os
from datetime import datetime
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SEP = "=" * 60


# ═══════════════════════════════════════════════════════════
# 基础组件（从 Step 0 复制，供练习修改）
# ═══════════════════════════════════════════════════════════

class WorkingMemory:
    """工作记忆：短期 + 长期"""

    def __init__(self, max_turns: int = 6):
        self.short_term: list[dict] = []
        self.long_term: dict[str, str] = {}
        self.max_turns = max_turns

    def add(self, role: str, content: str):
        self.short_term.append({
            "role": role, "content": content,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        forgotten = None
        while len(self.short_term) > self.max_turns:
            forgotten = self.short_term.pop(0)
        if forgotten:
            print(f"   🧠 [记忆裁剪] 遗忘: \"{forgotten['content'][:30]}...\"")

    def get_recent(self, n: int = 5) -> str:
        if not self.short_term:
            return "（空）"
        return "\n".join(
            f"  [{m['role']}] {m['content'][:50]}" for m in self.short_term[-n:]
        )

    def remember_long_term(self) -> str:
        """返回长期记忆的摘要"""
        if not self.long_term:
            return "无长期记忆"
        return "\n".join(f"  {k}: {v}" for k, v in self.long_term.items())

    def save_long_term(self, key: str, value: str):
        self.long_term[key] = value


class Perception:
    """感知模块：规则匹配版（任务 ④ 将升级为 LLM 版）"""

    @staticmethod
    def perceive(user_input: str) -> dict:
        result = {"raw_input": user_input, "intent": "unknown", "entities": {}}

        # 天气
        if any(w in user_input for w in ["天气", "下雨", "温度", "晴", "多云"]):
            result["intent"] = "query_weather"
            for city in ["北京", "上海", "深圳", "杭州", "成都"]:
                if city in user_input:
                    result["entities"]["city"] = city
                    break
            if "city" not in result["entities"]:
                result["entities"]["city"] = "未知城市"

        # 计算
        elif any(w in user_input for w in ["算", "计算", "+", "-", "*", "/"]):
            result["intent"] = "calculate"
            nums = re.findall(r'\d+\.?\d*', user_input)
            if len(nums) >= 2:
                result["entities"]["numbers"] = [float(n) for n in nums[:2]]
            if "+" in user_input or "加" in user_input:
                result["entities"]["operation"] = "add"
            elif "-" in user_input or "减" in user_input:
                result["entities"]["operation"] = "subtract"
            elif "*" in user_input or "乘" in user_input:
                result["entities"]["operation"] = "multiply"

        # 提醒
        elif any(w in user_input for w in ["提醒", "闹钟", "定时"]):
            result["intent"] = "set_reminder"
            time_match = re.search(r'(\d+)\s*分钟', user_input)
            result["entities"]["time"] = time_match.group(1) + "分钟" if time_match else "未知时间"
            # 如果是 "提醒我 5 分钟后开会"，提取 "分钟后" 之后的内容；如果是 “3分钟后提醒我关火“，提取 “提醒我“ 之后的内容
            if re.search(r'(\d+)\s*分钟后提醒我', user_input):
                result["entities"]["content"] = re.sub(r'.*提醒我', '', user_input).strip()
            elif re.search(r'提醒我\s*(\d+)\s*分钟后', user_input):
                result["entities"]["content"] = re.sub(r'.*分钟后', '', user_input).strip()
            else:
                result["entities"]["content"] = "未知事件"

        # 搜索
        elif any(w in user_input for w in ["搜索", "查一下", "什么是", "谁是"]):
            result["intent"] = "search"

        # 回忆
        elif any(w in user_input for w in ["之前", "刚才", "历史", "记得", "聊了"]):
            result["intent"] = "recall"

        # 问候
        elif any(w in user_input for w in ["你好", "嗨", "hello", "hi"]):
            result["intent"] = "greeting"

        # 默认：把整个输入当搜索关键词（回退策略）
        else:
            result["intent"] = "search"

        return result


class Planner:
    """规划模块"""

    @staticmethod
    def plan(intent: str, entities: dict, memory: WorkingMemory) -> list[str]:
        plans = {
            "query_weather": [
                f"确认城市: {entities.get('city', '未知')}",
                "调用天气 API",
                "格式化回复",
            ],
            "calculate": [
                f"提取运算: {entities.get('numbers', [])} {entities.get('operation', '?')}",
                "执行计算",
                "返回结果",
            ],
            "search": ["提取关键词", "检索知识库", "整理结果"],
            "greeting": ["检查对话历史", "生成问候", "询问需求"],
            "recall": ["检索短期记忆", "检索长期记忆", "汇总记忆"],
            "translate": ["识别源语言", "执行翻译", "格式化输出"],
            "set_reminder": ["提取时间", "记录提醒", "返回结果"],
            "unknown": ["请求澄清", "列出能力"],
        }
        return plans.get(intent, plans["unknown"])


class Executor:
    """执行模块"""

    @staticmethod
    def execute(intent: str, entities: dict, memory: WorkingMemory) -> str:
        if intent == "query_weather":
            weather_db = {"北京": ("晴", "25°C"), "上海": ("多云", "28°C"),
                          "深圳": ("阵雨", "30°C"), "杭州": ("阴", "22°C"),
                          "成都": ("晴", "27°C")}
            city = entities.get("city", "未知城市")
            w, t = weather_db.get(city, ("未知", "N/A"))
            return f"{city}天气：{w}，温度{t}（模拟数据）"

        elif intent == "calculate":
            nums = entities.get("numbers", [0, 0])
            op = entities.get("operation", "add")
            ops = {"add": "+", "subtract": "-", "multiply": "×"}
            if op == "add":
                r = nums[0] + nums[1]
            elif op == "subtract":
                r = nums[0] - nums[1]
            elif op == "multiply":
                r = nums[0] * nums[1]
            else:
                r = nums[0] + nums[1]
            return f"{nums[0]} {ops.get(op, '+')} {nums[1]} = {r}"

        elif intent == "search":
            keyword = entities.get("raw_input", "")[:30]
            return f"🔍 关于「{keyword}...」的搜索结果（模拟 3 条）"

        elif intent == "greeting":
            ctx = memory.get_recent(3)
            if ctx == "（空）" or "user" not in ctx:
                return "你好！我是小智，可以帮你查天气、算数学、搜索信息～"
            return "欢迎回来！继续聊吗？"

        elif intent == "recall":
            short = memory.get_recent(10)
            # TODO ③ BUG: 只展示了短期记忆，忘了展示长期记忆！
            long_mem = memory.remember_long_term()
            return f"📋 最近对话:\n{short}\n{long_mem}"
        elif intent == "set_reminder":
            time_str = entities.get("time", "未知时间")
            content = entities.get("content", "无内容")
            if time_str == "未知时间" or content == "无内容":
                return "⚠️ 提醒设置失败，请提供时间和内容，例如「提醒我 5 分钟后开会」"
            reminder_key = f"reminder_{len(memory.long_term) + 1}"
            memory.save_long_term(reminder_key, f"{time_str} 提醒: {content}")
            return f"好的，我会在 {time_str} 后提醒你：{content}"
        elif intent == "translate":
            # 简单的模拟翻译（实际需要调用 LLM）
            text = entities.get("raw_input", "")
            return f"🌐 翻译结果（模拟）: \"{text[:20]}...\" → [English version]"

        else:
            return "我不太理解，可以换个说法吗？我可以帮你：查天气、算数学、搜索信息。"


# ═══════════════════════════════════════════════════════════
# 任务 ①：改参数 — 调整记忆容量 + 添加新意图
# ═══════════════════════════════════════════════════════════

def task1_tune_parameters():
    """
    TODO ①：修改 WorkingMemory 的 max_turns 参数，观察行为变化

    操作：
    1. 把创建 Agent 时的 max_turns 从 6 改成 3
    2. 在 Perception.perceive() 里添加 "自我介绍" 意图识别
       （提示：检测 "我叫"、"我是"、"我的名字是"）

    目标：
    - 理解 max_turns 如何影响 Agent 的"记忆力"
    - 理解添加新意图需要改哪些地方
    """
    print(f"{SEP}")
    print("📝 任务 ①：调参 + 添加意图")
    print(f"{SEP}")

    # ─── 改参数：把 max_turns 改成你选择的值 ───
    memory = WorkingMemory(max_turns=3)  # TODO: 改成 3，对比效果

    # ─── 手动模拟对话，观察记忆裁剪 ───
    test_dialogs = [
        ("user", "你好！"),
        ("assistant", "你好！有什么可以帮你？"),
        ("user", "我叫小明"),
        ("assistant", "你好小明！记住了～"),
        ("user", "北京天气怎么样？"),
        ("assistant", "北京天气：晴，25°C"),
        ("user", "帮我算 128 + 256"),
        ("assistant", "128 + 256 = 384"),
        ("user", "搜索 Transformer"),
        ("assistant", "搜索结果..."),
        ("user", "还记得我之前说了什么吗？"),
    ]

    print(f"   max_turns = {memory.max_turns}\n")
    for role, content in test_dialogs:
        memory.add(role, content)

    print(f"\n   最终短期记忆 ({len(memory.short_term)} 条):")
    print(memory.get_recent(10))

    # ─── 预测题 ───
    print(f"\n   🎯 预测：如果 max_turns=3，最后 recall 时能回忆起第 1-4 条对话吗？为什么？")


# ═══════════════════════════════════════════════════════════
# 任务 ②：加功能 — 新增"设置提醒"意图
# ═══════════════════════════════════════════════════════════

def task2_add_intent():
    """
    TODO ②：给 Agent 新增一个 "设置提醒" (set_reminder) 意图

    需要修改的位置（用 TODO 标记了）：
    1. Perception.perceive() — 识别 "提醒我"、"XX 分钟后提醒"
    2. Planner.plan() — 添加 set_reminder 的执行计划
    3. Executor.execute() — 实现提醒逻辑
    4. 将提醒内容存入长期记忆

    骨架代码已给出，你只需要填关键逻辑。
    """
    print(f"{SEP}")
    print("📝 任务 ②：新增「设置提醒」意图")
    print(f"{SEP}")

    # 创建临时感知实例来测试
    perc = Perception()

    test_inputs = [
        "提醒我 5 分钟后开会",
        "设置一个提醒：明天买水果",
        "3分钟后提醒我关火",
    ]

    print("   测试感知识别（修改前后对比）:")
    for inp in test_inputs:
        result = perc.perceive(inp)
        has_reminder = result.get("intent") == "set_reminder"
        status = "✅" if has_reminder else "❌ 未识别"
        print(f"      输入: \"{inp}\"")
        print(f"      意图: {result['intent']} {status}")
        if has_reminder:
            print(f"      实体: {result.get('entities', {})}")
        print()

    # ─── 提示：要在 Perception.perceive() 里加 ───
    # 在 "搜索" 的 elif 之前插入：
    #
    # elif any(w in user_input for w in ["提醒", "闹钟", "定时"]):
    #     result["intent"] = "set_reminder"
    #     # TODO: 用正则提取时间（如 "5 分钟"、"明天"）
    #     # TODO: 提取提醒内容（去掉 "提醒我" 之后的部分）
    #
    # 然后在 Planner.plan() 和 Executor.execute() 里添加对应的 plan 和 execute 分支


    print(f"   💡 预期行为：输入「提醒我 5 分钟后开会」")
    print(f"      → 意图=set_reminder, 实体='time': '5分钟', 'content': '开会'")
    print(f"      → 计划: [提取时间, 提取内容, 存入长期记忆, 确认]")
    print(f"      → 执行: 存入 memory.long_term['reminder_1'] = ...")
    print(f"      → 回复: 「好的，我会在 5 分钟后提醒你：开会」")


# ═══════════════════════════════════════════════════════════
# 任务 ③：修 Bug — recall 缺少长期记忆
# ═══════════════════════════════════════════════════════════

def task3_fix_recall():
    """
    TODO ③：修复 Executor.execute() 中 intent="recall" 的 bug

    当前 bug（Executor.execute() 第 ~148 行）：
        elif intent == "recall":
            short = memory.get_recent(10)
            return f"📋 最近对话:\n{short}"
            # ⚠️ 只返回了短期记忆，缺少长期记忆！

    修复后应同时展示：
        - 短期记忆（最近对话）
        - 长期记忆（user_name、last_search、reminder 等）
    """
    print(f"{SEP}")
    print("📝 任务 ③：修复 recall — 长期记忆丢失 Bug")
    print(f"{SEP}")

    # 构造一个有长期记忆的场景
    memory = WorkingMemory(max_turns=10)
    memory.add("user", "我叫小明")
    memory.add("assistant", "你好小明！")
    memory.save_long_term("user_name", "小明")
    memory.save_long_term("favorite_city", "北京")
    memory.add("user", "北京天气怎么样")
    memory.add("assistant", "北京天气：晴，25°C")
    memory.add("user", "还记得之前聊了什么吗？")

    # 模拟 recall
    executor = Executor()
    result = executor.execute("recall", {}, memory)

    print(f"   短期记忆:")
    print(memory.get_recent(10))
    print(f"\n   长期记忆:")
    print(f"   {memory.remember_long_term()}")
    print(f"\n   recall 回复:")
    print(f"   {result}")

    has_long_term = "长期记忆" in result or "user_name" in result or "小明" in result
    status = "✅" if has_long_term else "❌ BUG: 缺少长期记忆"
    print(f"\n   长期记忆是否在回复中: {status}")

    print(f"\n   🎯 修复：在 intent='recall' 分支中加上:")
    print(f"      long = memory.remember_long_term()")
    print(f"      return f'📋 最近对话:\\n{{short}}\\n\\n💾 长期记忆:\\n{{long}}'")


# ═══════════════════════════════════════════════════════════
# 任务 ④：扩展 — 用 LLM 替换规则感知
# ═══════════════════════════════════════════════════════════

def task4_llm_perception():
    """
    TODO ④：将 Perception 从 if/else 规则 → LLM API 调用

    这是关键升级——用 DeepSeek API 做意图识别 + 实体提取，
    取代硬编码的规则匹配。

    步骤：
    1. 构造一个 system prompt，让 LLM 输出 JSON 格式的意图+实体
    2. 调用 DeepSeek API
    3. 解析返回的 JSON
    4. 作为新的 Perception.perceive() 实现

    可用的意图列表（供 LLM 参考）：
        query_weather, calculate, search, greeting, recall,
        set_reminder, translate, unknown
    """
    print(f"{SEP}")
    print("📝 任务 ④：LLM 驱动的感知模块")
    print(f"{SEP}")

    # ─── 骨架代码 ───

    SYSTEM_PROMPT = """你是一个意图识别系统。分析用户输入，返回 JSON 格式的解析结果。

可用意图: query_weather, calculate, search, greeting, recall, set_reminder, translate

返回格式（严格 JSON，不要有其他文字）:
{
    "intent": "意图名称",
    "entities": {}
}

实体提取规则:
- query_weather: {"city": "城市名"}
- calculate: {"numbers": [数字1, 数字2], "operation": "add/subtract/multiply"}
- set_reminder: {"time": "时间描述", "content": "提醒内容"}
- search: {"keyword": "搜索关键词"}
"""

    def llm_perceive(user_input: str) -> dict:
        """
        TODO ④：实现这个函数
        1. 用 openai SDK 调用 DeepSeek API（和 chat_loop.py 一样的方式）
        2. 发送 [{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": user_input}]
        3. 解析返回的 JSON
        4. 如果解析失败或 intent 不在列表中，回退到 unknown

        提示：参考 code/01-foundations/chat_loop.py 里的 API 调用代码
        """
        # ─── 在这里写你的代码 ───
        # import openai
        # client = openai.OpenAI(
        #     api_key=os.getenv("DEEPSEEK_API_KEY"),
        #     base_url="https://api.deepseek.com",
        # )
        # response = client.chat.completions.create(
        #     model="deepseek-chat",
        #     messages=[...],
        #     temperature=0.0,  # 意图识别不需要创造性
        # )
        # return json.loads(response.choices[0].message.content)
        # ─────────────────────────
        client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            max_tokens=500,
            temperature=0.0,
        )
        return json.loads(response.choices[0].message.content)        # 临时回退到规则匹配（完成 TODO 后删除这行）


    # 测试
    test_cases = [
        "北京今天气温多少度？",
        "帮我查一下什么是机器学习",
        "计算 3.14 乘以 2.5",
        "3 分钟后提醒我开会",
    ]

    print("   测试 LLM 感知 vs 规则感知:\n")
    for inp in test_cases:
        llm_result = llm_perceive(inp)
        rule_result = Perception.perceive(inp)

        print(f"   输入: \"{inp}\"")
        print(f"   LLM:  intent={llm_result.get('intent')}, entities={llm_result.get('entities')}")
        print(f"   规则: intent={rule_result.get('intent')}, entities={rule_result.get('entities')}")
        print()

    # 注意：LLM 版能识别 "查一下" = search、"3.14 * 2.5" 的乘法、
    #       "3 分钟后提醒" 的提醒——这些都是规则版可能漏掉的


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_nums = {int(a) for a in sys.argv[1:]}
    else:
        task_nums = {1, 2, 3, 4}

    TASKS = {
        1: ("调参 + 添加意图", task1_tune_parameters),
        2: ("新增「设置提醒」意图", task2_add_intent),
        3: ("修复 recall 长期记忆丢失", task3_fix_recall),
        4: ("LLM 驱动的感知模块", task4_llm_perception),
    }

    selected = sorted(task_nums)
    print(f"🧪 Agent 四要素 Step 3 — 运行任务: {selected}\n")

    for num in selected:
        if num in TASKS:
            print(f"▶️  任务 {num}：{TASKS[num][0]}")
            TASKS[num][1]()
        else:
            print(f"⚠️  任务 {num} 不存在 (1-4)")

    print(f"\n{SEP}")
    print(f"✅ 选定任务 {selected} 运行完成")
    print(SEP)

"""
Agent 四要素演示 — Step 0 热身运行
====================================
目标：通过模拟 Agent 循环，直观理解"感知→规划→执行→记忆"四个要素

运行方法：
    python code/01-foundations/agent_four_elements.py
"""

import time
import json
from datetime import datetime


SEP = "=" * 60

# ═══════════════════════════════════════════════════════════
# 模拟 Agent 的四个核心组件
# ═══════════════════════════════════════════════════════════

class Perception:
    """感知模块：接收输入，识别意图"""

    @staticmethod
    def perceive(user_input: str) -> dict:
        """解析用户输入，提取关键信息"""
        result = {
            "raw_input": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "intent": "unknown",
            "entities": {},
        }

        # 简单的意图识别（模拟 LLM 的理解过程）
        if any(w in user_input for w in ["天气", "下雨", "温度", "晴"]):
            result["intent"] = "query_weather"
            if "北京" in user_input:
                result["entities"]["city"] = "北京"
            elif "上海" in user_input:
                result["entities"]["city"] = "上海"
            else:
                result["entities"]["city"] = "未知城市"

        elif any(w in user_input for w in ["算", "计算", "加", "减", "乘", "除", "+", "-"]):
            result["intent"] = "calculate"
            # 尝试提取数字
            import re
            nums = re.findall(r'\d+', user_input)
            if len(nums) >= 2:
                result["entities"]["numbers"] = [int(n) for n in nums[:2]]
            if "+" in user_input or "加" in user_input:
                result["entities"]["operation"] = "add"
            elif "-" in user_input or "减" in user_input:
                result["entities"]["operation"] = "subtract"

        elif any(w in user_input for w in ["搜索", "查", "找", "什么是", "谁是"]):
            result["intent"] = "search"

        elif any(w in user_input for w in ["你好", "嗨", "hello", "hi"]):
            result["intent"] = "greeting"

        elif any(w in user_input for w in ["之前", "刚才", "历史", "记得"]):
            result["intent"] = "recall"

        return result


class WorkingMemory:
    """工作记忆：存储对话上下文，管理短期记忆"""

    def __init__(self, max_turns: int = 10):
        self.short_term: list[dict] = []
        self.long_term: dict[str, str] = {}  # 简单键值存储
        self.max_turns = max_turns

    def add(self, role: str, content: str):
        """追加一条记忆"""
        self.short_term.append({
            "role": role,
            "content": content,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        # 超过上限时移除最早的
        if len(self.short_term) > self.max_turns:
            forgotten = self.short_term.pop(0)
            print(f"   🧠 [记忆] 滑动窗口裁剪，遗忘: \"{forgotten['content'][:30]}...\"")

    def remember(self, keyword: str) -> str:
        """从长期记忆检索"""
        return self.long_term.get(keyword, "无相关记忆")

    def save_to_long_term(self, key: str, value: str):
        """保存到长期记忆"""
        self.long_term[key] = value

    def get_recent_context(self, n: int = 5) -> str:
        """获取最近 n 轮对话摘要"""
        if not self.short_term:
            return "（空）"
        lines = []
        for item in self.short_term[-n:]:
            lines.append(f"  [{item['role']}] {item['content'][:50]}")
        return "\n".join(lines)


class Planner:
    """规划模块：根据意图和上下文制定执行计划"""

    @staticmethod
    def plan(intent: str, entities: dict, memory: WorkingMemory) -> list[str]:
        """生成执行步骤"""
        plans = {
            "query_weather": [
                f"1. 确认查询城市: {entities.get('city', '未知')}",
                "2. 调用天气 API 获取数据",
                "3. 格式化天气信息，回复用户",
            ],
            "calculate": [
                f"1. 提取运算数和操作符: {entities.get('numbers', [])} {entities.get('operation', '?')}",
                "2. 执行数学计算",
                "3. 返回计算结果",
            ],
            "search": [
                "1. 提取搜索关键词",
                "2. 在知识库中检索相关信息",
                "3. 整理并返回搜索结果",
            ],
            "greeting": [
                "1. 确认用户身份（是否新用户）",
                "2. 生成友好的问候语",
                "3. 询问是否需要帮助",
            ],
            "recall": [
                "1. 检索短期记忆中的最近对话",
                "2. 检索长期记忆中存储的信息",
                "3. 汇总记忆内容回复用户",
            ],
            "unknown": [
                "1. 无法识别意图，请求用户澄清",
                "2. 列出 Agent 当前可用能力",
            ],
        }
        return plans.get(intent, plans["unknown"])


class Executor:
    """执行模块：实际执行计划中的每一步"""

    @staticmethod
    def execute(plan_steps: list[str], entities: dict, intent: str, memory: WorkingMemory) -> str:
        """模拟执行计划，返回结果"""
        print(f"\n   ⚡ [执行] 开始执行 {len(plan_steps)} 个步骤:")

        for step in plan_steps:
            print(f"      {step}")
            time.sleep(0.3)  # 模拟执行延迟

        # 根据意图生成结果
        if intent == "query_weather":
            city = entities.get("city", "未知城市")
            # 模拟天气数据
            weather_data = {"北京": ("晴", "25°C"), "上海": ("多云", "28°C")}
            w, t = weather_data.get(city, ("未知", "N/A"))
            result = f"{city}天气：{w}，温度{t}（模拟数据）"

        elif intent == "calculate":
            nums = entities.get("numbers", [0, 0])
            op = entities.get("operation", "add")
            if op == "add":
                calc_result = nums[0] + nums[1]
            else:
                calc_result = nums[0] - nums[1]
            result = f"计算结果: {nums[0]} {'+' if op == 'add' else '-'} {nums[1]} = {calc_result}"

        elif intent == "search":
            result = f"搜索结果: 「{entities.get('raw_input', '')[:20]}...」相关文章 3 篇（模拟）"

        elif intent == "greeting":
            ctx = memory.get_recent_context(2)
            if "user" in ctx.lower() or ctx == "（空）":
                result = "你好！我是你的 AI 助手，有什么可以帮你的？"
            else:
                result = "欢迎回来！继续刚才的话题吗？"

        elif intent == "recall":
            recent = memory.get_recent_context(5)
            result = f"📋 最近对话记录:\n{recent}"

        else:
            result = "抱歉，我不太理解你的意思。我可以帮你：查天气、算数学、搜索信息。"

        return result


# ═══════════════════════════════════════════════════════════
# Agent 主循环
# ═══════════════════════════════════════════════════════════

class SimpleAgent:
    """整合四要素的简单 Agent"""

    def __init__(self, name: str = "小智"):
        self.name = name
        self.perception = Perception()
        self.memory = WorkingMemory(max_turns=6)
        self.planner = Planner()
        self.executor = Executor()

    def run(self, user_input: str) -> str:
        """Agent 主循环：感知 → 规划 → 执行 → 记忆（一次迭代）"""
        print(f"\n{'─'*50}")
        print(f"📥 用户输入: \"{user_input}\"")

        # ── ① 感知（Perception）──
        perception_result = self.perception.perceive(user_input)
        intent = perception_result["intent"]
        entities = perception_result["entities"]
        print(f"👁️  [感知] 意图={intent}, 实体={entities}")

        # ── ② 规划（Planning）──
        plan = self.planner.plan(intent, entities, self.memory)
        print(f"🧠 [规划] 生成 {len(plan)} 步计划:")
        for p in plan:
            print(f"      {p}")

        # ── ③ 执行（Action）──
        result = self.executor.execute(plan, entities, intent, self.memory)

        # ── ④ 记忆更新（Memory）──
        self.memory.add("user", user_input)
        self.memory.add("assistant", result)

        # 如果用户提到名字等关键信息，保存到长期记忆
        if "我叫" in user_input or "我是" in user_input:
            name_part = user_input.split("我叫")[-1] if "我叫" in user_input else user_input.split("我是")[-1]
            self.memory.save_to_long_term("user_name", name_part.strip("。， "))
            print(f"   💾 [长期记忆] 保存: user_name = {name_part.strip('。， ')}")

        # 如果搜过某个主题，记住
        if intent == "search":
            topic = user_input.replace("搜索", "").replace("查", "").strip()
            self.memory.save_to_long_term("last_search", topic)

        print(f"\n📤 [{self.name}] 回复: {result}")
        return result


# ═══════════════════════════════════════════════════════════
# 演示场景
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🤖 Agent 四要素演示平台")
    print(f"   Agent 名称: 小智")
    print(f"   核心循环: 感知 → 规划 → 执行 → 记忆\n")

    agent = SimpleAgent(name="小智")

    # 场景：连续多轮对话，展示四要素的协同
    scenario = [
        "你好！",
        "我叫小明",
        "北京今天天气怎么样？",
        "帮我算一下 128 + 256 等于多少",
        "搜索什么是 Transformer",
        "你还记得之前聊了什么吗？",
        "上海天气呢？",
    ]

    for i, msg in enumerate(scenario, 1):
        print(f"\n{'='*60}")
        print(f"  🔄 第 {i} 轮对话")
        print(f"{'='*60}")
        agent.run(msg)
        time.sleep(0.2)

    # 展示最终记忆状态
    print(f"\n{'='*60}")
    print("📊 Agent 内部状态总览")
    print(f"{'='*60}")
    print(f"\n📝 短期记忆 ({len(agent.memory.short_term)} 条):")
    print(agent.memory.get_recent_context(10))

    print(f"\n💾 长期记忆:")
    for k, v in agent.memory.long_term.items():
        print(f"   {k}: {v}")

    print(f"\n{SEP}")
    print("✅ 演示完成！你看到了什么？进入 Step 1 👇")
    print(SEP)

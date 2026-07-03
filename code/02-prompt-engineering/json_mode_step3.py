"""
模块 2 — Step 3 引导式修改：结构化输出（JSON Mode）
4 个渐进任务：改参数 → 加校验 → 修 Bug → 扩展场景

运行方式：
    uv run python code/02-prompt-engineering/json_mode_step3.py 1    # 任务①
    uv run python code/02-prompt-engineering/json_mode_step3.py 2    # 任务②
    uv run python code/02-prompt-engineering/json_mode_step3.py 3    # 任务③
    uv run python code/02-prompt-engineering/json_mode_step3.py 4    # 任务④
"""

import os
import json
import re
from shutil import which
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
# 共享脚手架（已帮你写好，所有任务都会用到）
# ══════════════════════════════════════════════════════════════════════

def extract_review_json(review_text: str, temperature: float = 0.0) -> dict | None:
    """从评论文本中提取结构化信息（脚手架，已写好）

    参数：
        review_text: 用户评论文本
        temperature: 模型温度参数

    返回：
        解析后的 dict，失败返回 None
    """
    system_prompt = (
        "你是一个信息提取助手。从用户评论中提取信息，"
        "并以 JSON 格式输出。\n"
        'JSON 格式：{"restaurant": "餐厅名", "avg_price": 人均价格数字, '
        '"recommended_dishes": ["菜名1", "菜名2"], "complaints": ["不满点"], "rating": 1-5 评分}'
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": review_text},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=512,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"   API 错误：{e}")
        return None


# 测试用的评论数据
SAMPLE_REVIEWS = [
    "在海底捞（朝阳大悦城店）吃的晚饭，人均 180 元。虾滑和毛肚特别好吃，服务好。就是等位等了 40 分钟，价格小贵。总体满意。",
    "西贝莜面村（王府井店），人均 95 元。羊肉串和莜面鱼鱼是必点！上菜快，环境干净。推荐！",
    "某网红火锅店（三里屯），人均 220。装修好看但味道一般，服务混乱，等了快一个小时才上菜。不推荐。",
]


# ══════════════════════════════════════════════════════════════════════
# 任务 ①：改参数 —— Temperature 对 JSON 输出稳定性的影响
# ══════════════════════════════════════════════════════════════════════

def task1_temperature_stability():
    """任务 ①：观察 temperature 变化时 JSON 输出的稳定性

    【你要做的】
    Step 0 热身中所有实验都用 temperature=0.0，保证了输出稳定。
    但如果 temperature 升高，JSON Mode 还能稳定输出合法 JSON 吗？

    请在下方 TODO 位置完成代码：
    对第 1 条评论（SAMPLE_REVIEWS[0]），分别用 temperature = 0.0, 0.5, 1.0, 1.5
    各调用 3 次 extract_review_json()，统计：
    - 成功解析次数
    - 字段值是否一致（比如 avg_price 是否每次都一样）

    提示：extract_review_json() 已经写好，你只需要写循环和统计逻辑。
    """
    print("=" * 60)
    print("🔧 任务 ①：Temperature 对 JSON 输出稳定性的影响")
    print("=" * 60)

    review = SAMPLE_REVIEWS[0]
    temperatures = [0.0, 0.5, 1.0, 2.0]
    runs_per_temp = 5

    print(f"📋 测试评论：{review[:50]}...\n")

    # TODO ①-1: 对每个 temperature 值，运行 runs_per_temp 次 extract_review_json()
    #           记录每次的结果（成功/失败、解析出的 dict）
    #           提示：用嵌套循环，外层遍历 temperatures，内层遍历 range(runs_per_temp)
    for temp in temperatures:
        print(f"--- temperature = {temp} ---")
        # TODO: 你的代码 — 循环调用 extract_review_json()，统计成功次数和字段一致性
        for i in range(runs_per_temp):
            result = extract_review_json(review, temp)
            if result is not None:
                print(f"   Run {i+1}: ✅ 成功 → {result}")
            else:
                print(f"   Run {i+1}: ❌ 解析失败")

    # TODO ①-2: 回答以下问题（在你的代码输出中体现即可，不需要写固定答案）：
    #   ① 哪个 temperature 开始出现 JSON 解析失败？
    #   ② 即使 JSON 解析成功，高 temperature 下字段值（如 rating）是否稳定？
    #   ③ 这对生产环境有什么启示？
    print("\n💡 思考：生产环境中结构化提取为什么几乎都用 temperature=0？")


# ══════════════════════════════════════════════════════════════════════
# 任务 ②：添加 Schema 校验层 —— 合法 JSON ≠ 符合 Schema
# ══════════════════════════════════════════════════════════════════════

# 期望的 Schema 定义（脚手架）
EXPECTED_SCHEMA = {
    "restaurant": str,
    "avg_price": (int, float),
    "recommended_dishes": list,
    "complaints": list,
    "rating": (int, float),
}


def validate_schema(data: dict, schema: dict) -> tuple[bool, list[str]]:
    """校验 data 是否符合 schema 定义（脚手架，等你完成 TODO）

    参数：
        data: 模型返回的 dict
        schema: 字段名 → 期望类型的映射

    返回：
        (是否通过, 错误信息列表)

    【你要做的】
    实现以下校验逻辑：
    ① 检查 schema 中每个 required 字段是否存在于 data 中
    ② 检查每个字段的类型是否匹配 schema 定义
       （提示：isinstance(data[key], schema[key])）
    ③ 如果 rating 存在，检查其值是否在 1-5 范围内
    ④ 如果 recommended_dishes 存在且为 list，检查是否为空

    返回 (is_valid, errors)，其中 errors 是描述所有问题的字符串列表。
    全部通过时返回 (True, [])。
    """
    errors = []

    for key, expected_type in schema.items():
        if key not in data:
            # ②-1: 检查必填字段是否存在
            errors.append(f"缺少必填字段：{key}")
        elif not isinstance(data[key], expected_type):
            # ②-2: 检查字段类型是否匹配
            errors.append(f"字段类型不匹配：{key}，期望 {expected_type}，实际 {type(data[key])}")
        elif key == 'rating' and not (1 <= data[key] <= 5):
            # ②-3: 检查 rating 的值范围（1-5）
            errors.append(f"字段值不在范围内：{key}，期望 1-5，实际 {data[key]}")
        elif key == 'recommended_dishes' and isinstance(data[key], list) and len(data[key]) == 0:
            # ②-4: 检查 recommended_dishes 是否为非空列表
            errors.append(f"字段 recommended_dishes 为空列表")
        else:
            # 所有校验都通过了
            # print(f"字段 {key} 校验通过，值为 {data[key]}")
            continue

    return len(errors) == 0, errors


def task2_schema_validation():
    """任务 ②：实现 Schema 校验 + 对 3 条评论做批量验证"""
    print("=" * 60)
    print("🔧 任务 ②：添加 Schema 校验层")
    print("=" * 60)
    print("Step 0 实验 3 告诉我们：JSON Mode 保证合法 JSON，但不保证字段正确。")
    print("你的 validate_schema() 函数就是生产环境中的「第二道防线」。\n")

    # --- 先测试你的 validate_schema 能正确识别问题 ---
    print("🧪 单元测试：校验函数的行为")
    test_cases = [
        ({"restaurant": "测试", "avg_price": 100, "recommended_dishes": ["a"], "complaints": [], "rating": 5},
         "✅ 合法数据 → 应返回 (True, [])"),
        ({"restaurant": "测试", "avg_price": "一百元", "recommended_dishes": ["a"], "complaints": [], "rating": 5},
         "❌ avg_price 是字符串 → 应返回 (False, [...])"),
        ({"restaurant": "测试"},
         "❌ 缺少 4 个必填字段 → 应返回 (False, [4 条错误])"),
        ({"restaurant": "测试", "avg_price": 100, "recommended_dishes": [], "complaints": [], "rating": 6},
         "❌ rating=6 超出范围 + dishes 为空 → 应返回 (False, [2 条错误])"),
    ]

    for data, desc in test_cases:
        is_valid, errors = validate_schema(data, EXPECTED_SCHEMA)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {desc}")
        if errors:
            for e in errors:
                print(f"       → {e}")
    print()

    # --- 对 3 条真实评论做批量提取 + 校验 ---
    print("📊 批量评论提取 + Schema 校验：")
    for i, review in enumerate(SAMPLE_REVIEWS, 1):
        data = extract_review_json(review)
        if data is None:
            print(f"  评论 {i}：❌ JSON 解析失败")
            continue
        is_valid, errors = validate_schema(data, EXPECTED_SCHEMA)
        if is_valid:
            print(f"  评论 {i}：✅ 校验通过 — {data['restaurant']}，{data['rating']} 分")
        else:
            print(f"  评论 {i}：⚠️ 校验失败 — {errors}")

    print("\n✅ 验证标准：正常情况下 3 条评论都应该校验通过。")


# ══════════════════════════════════════════════════════════════════════
# 任务 ③：修复 JSON 解析 Bug —— 真实世界的脏数据
# ══════════════════════════════════════════════════════════════════════

def parse_json_robust(raw: str) -> dict | list | None:
    """健壮的 JSON 解析器（有 Bug 的版本，等你修复 TODO）

    这个函数试图处理 LLM 输出的各种「脏 JSON」格式。
    代码骨架已经有了，但有 3 处 Bug/TODO 需要你修复。
    """
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    # --- 第 1 步：去除 Markdown 代码块包装 ---
    # 模型有时会输出 ```json ... ``` 而不是纯 JSON
    # TODO ③-1: 检查 text 是否以 ``` 开头/结尾，如果是则去掉
    # 提示：text.startswith("```") → 找到第一个换行 → 去掉第一行
    #       text.endswith("```") → 去掉最后一行
    # 还要处理 ```json 和 ``` 两种变体
    # TODO: 你的代码 — 去掉 markdown 代码块包装
    if text.startswith("```") or text.startswith("```json"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        else:
            if text.startswith("```json"):
                text = text[7:]  # 去掉开头的 ```json
            else:
                text = text[3:]  # 去掉开头的 ```

    if text.endswith("```"):
        last_newline = text.rfind("\n")
        if last_newline != -1:
            text = text[:last_newline]
        else:
            text = text[:-3]  # 去掉最后的 ```

    # --- 第 2 步：提取 JSON 对象的起止位置 ---
    # 模型有时会在 JSON 前面加一句"好的，结果如下："之类的废话
    # 我们需要找到第一个 { 或 [ 和最后一个 } 或 ]
    # TODO ③-2: 找到 text 中第一个 { 或 [ 的位置和最后一个 } 或 ] 的位置
    #          截取这个子串
    # 提示：用 text.find('{') 和 text.rfind('}')
    #       还要考虑 JSON 数组的情况（以 [ 开头）
    # TODO: 你的代码 — 提取纯 JSON 子串
    if not text.startswith("{") and not text.startswith("["):
        # 不是以 "{" 或 "[" 开头
        index1 = text.find("{")
        index2 = text.find("[")
        index3 = text.rfind("}")
        index4 = text.rfind("]")
        start_index = index1 if index2 == -1 or (index1 != -1 and index1 < index2) else index2
        end_index = index3 if index3 > -1 and index3 > index4 else index4
        if start_index != -1 and end_index != -1 and end_index > start_index:
            text = text[start_index:end_index + 1]

    # --- 第 3 步：尝试解析 ---
    # 🐛 BUG ③-3：下面的解析逻辑有一个问题——
    #    LLM 有时会输出带尾部逗号的 JSON（如 {"a": 1,}），Python 的 json.loads() 不接受
    #    请添加一个容错：如果 json.loads() 失败，尝试用正则去掉尾部逗号后重试
    try:
        return json.loads(text)  # ← 这行是直接解析，没有容错处理
    except json.JSONDecodeError:
        # TODO ③-3: 在这里添加容错重试逻辑
        # 提示：用 re.sub(r',\s*}', '}', text) 去掉对象尾部逗号
        #       用 re.sub(r',\s*]', ']', text) 去掉数组尾部逗号
        #       然后重新 json.loads()
        # TODO: 你的代码
        if text.endswith(",}"):
            text = re.sub(r',\s*}', '}', text)
            return json.loads(text)
        elif text.endswith(",]"):
            text = re.sub(r',\s*]', ']', text)
            return json.loads(text)
        else:
            print("   ⚠️  JSON 解析失败，且未检测到尾部逗号，无法容错。")

    return None


def task3_fix_json_parsing():
    """任务 ③：修复 JSON 解析 Bug — 处理 LLM 的脏输出"""
    print("=" * 60)
    print("🔧 任务 ③：修复 JSON 解析 Bug")
    print("=" * 60)
    print("真实场景中，即使开了 JSON Mode，模型也可能输出「脏 JSON」：")
    print("  - 包裹在 ```json``` 代码块中")
    print("  - 前面有「好的，结果如下：」之类的废话")
    print("  - 尾部多余逗号（Python json 库不接受）\n")

    # 模拟 LLM 可能输出的各种「脏 JSON」
    dirty_outputs = [
        # Case 1: 干净的 JSON（应该能解析）
        '{"name": "张三", "age": 25, "city": "北京"}',
        # Case 2: 包裹在 Markdown 代码块中
        '```json\n{"name": "李四", "age": 30, "city": "上海"}\n```',
        # Case 3: 前面有废话
        '好的，我已经为你提取了以下信息：\n{"name": "王五", "age": 28, "city": "深圳"}',
        # Case 4: 尾部多余逗号
        '{"name": "赵六", "age": 35, "city": "广州",}',
        # Case 5: 数组形式，尾部逗号
        '[{"name": "孙七", "age": 22}, {"name": "周八", "age": 40},]',
    ]

    success = 0
    for i, dirty in enumerate(dirty_outputs, 1):
        result = parse_json_robust(dirty)
        if result is not None:
            print(f"  Case {i} ✅ → {result}")
            success += 1
        else:
            print(f"  Case {i} ❌ 解析失败")
            print(f"       原始输出：{dirty[:80]}...")

    print(f"\n📊 通过率：{success}/{len(dirty_outputs)}")
    print("🎯 目标：5/5 全部通过！")

    if success < 5:
        print("\n💡 提示：检查 TODO ③-1（去 Markdown 包装）、③-2（提取 JSON 子串）、③-3（尾部逗号容错）")


# ══════════════════════════════════════════════════════════════════════
# 任务 ④：扩展场景 —— 构建可复用的结构化提取模板
# ══════════════════════════════════════════════════════════════════════

def build_extraction_prompt(schema_desc: dict) -> str:
    """根据 Schema 描述自动生成提取 Prompt（脚手架，等你完成 TODO）

    参数：
        schema_desc: {
            "task": "任务描述（一句话）",
            "fields": {
                "字段名": "字段描述（中文）",
                ...
            }
        }

    返回：
        完整的 system prompt 字符串

    【你要做的】
    根据 schema_desc 动态生成一个包含以下内容的 System Prompt：
    ① 任务描述（来自 schema_desc["task"]）
    ② "请以 JSON 格式输出"（触发 JSON Mode 的关键字）
    ③ 用 schema_desc["fields"] 生成期望的 JSON 格式示例

    例如输入：
        schema_desc = {
            "task": "从新闻中提取事件信息",
            "fields": {"event": "事件名称", "date": "发生日期", "location": "地点"}
        }

    期望输出（参考格式）：
        "你是一个信息提取助手。从新闻中提取事件信息，请以 JSON 格式输出。\n
         JSON 格式：{"event": "事件名称", "date": "发生日期", "location": "地点"}"
    """
    # TODO ④-1: 用 schema_desc 动态生成 system prompt
    # 提示：
    #   ① 用 schema_desc["task"] 作为任务描述
    #   ② 关键：必须包含 "JSON" 或 "json" 字样（DeepSeek JSON Mode 要求）
    #   ③ 用 schema_desc["fields"] 生成格式示例：
    #      {key: value_description for key, value_description in fields.items()}
    #      → 转为 JSON 格式的字符串展示
    # TODO: 你的代码
    task_description = schema_desc.get("task", "请提取信息")
    fields = schema_desc.get("fields", {})
    json_example = json.dumps({key: value for key, value in fields.items()})
    result_prompt = f"你是一个信息提取助手，{task_description}, 请以 JSON 格式输出。 \nJSON 格式为：{json_example}"
    return result_prompt


def extract_with_template(text: str, schema_desc: dict, temperature: float = 0.0) -> dict | None:
    """用模板提取结构化信息（脚手架，等你完成 TODO）"""
    system_prompt = build_extraction_prompt(schema_desc)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=512,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"   API 错误：{e}")
        return None


def task4_template_system():
    """任务 ④：构建可复用的结构化提取模板系统"""
    print("=" * 60)
    print("🔧 任务 ④：构建可复用的结构化提取模板系统")
    print("=" * 60)
    print("前面 3 个任务让你掌握了 JSON Mode 的核心用法。")
    print("现在把这些能力封装成一个可复用的模板系统——")
    print("只需定义 Schema，自动生成 Prompt + 调 API + 解析。\n")

    # --- 场景 A：从新闻中提取事件信息 ---
    print("📰 场景 A：新闻事件提取")
    news_schema = {
        "task": "从新闻文本中提取事件信息",
        "fields": {
            "event": "事件名称（简短概括）",
            "date": "发生日期（如未明确提及，填'未知'）",
            "location": "发生地点",
            "key_persons": "关键人物列表",
            "event_type": "事件类型（政治/经济/科技/社会/体育/娱乐）",
        }
    }

    news_text = (
        "2024 年 7 月 3 日，特斯拉 CEO 埃隆·马斯克在上海超级工厂宣布，"
        "新款 Model 2 将于明年一季度量产，售价预计在 15 万元人民币左右。"
        "上海市市长龚正出席了发布会。"
    )

    print(f"   原文：{news_text[:60]}...")
    # TODO ④-2: 完成 build_extraction_prompt() 后，
    #           调用 extract_with_template(news_text, news_schema) 提取信息，
    #           然后美化打印结果
    # TODO: 你的代码 — 调用提取函数并打印结果
    result = extract_with_template(news_text, news_schema)
    print(f"   提取结果：{json.dumps(result, ensure_ascii=False, indent=2)}")

    # --- 场景 B：从产品描述中提取规格参数 ---
    print("\n📦 场景 B：产品规格提取")
    product_schema = {
        "task": "从产品描述中提取规格参数",
        "fields": {
            "product_name": "产品名称",
            "brand": "品牌",
            "price": "价格（数字，不含货币符号）",
            "specs": "关键规格参数（dict 格式）",
            "highlights": "产品亮点（字符串列表）",
        }
    }

    product_text = (
        "Apple iPhone 16 Pro Max，256GB 深空黑色，售价 9999 元。"
        "搭载 A18 Pro 芯片，6.9 英寸 OLED 显示屏，支持 120Hz 自适应刷新率。"
        "4800 万像素主摄，支持 5 倍光学变焦。钛金属边框，USB-C 接口。"
    )

    print(f"   原文：{product_text[:60]}...")
    # TODO ④-3: 调用 extract_with_template(product_text, product_schema) 提取并打印
    # TODO: 你的代码
    result = extract_with_template(product_text, product_schema)
    print(f"   提取结果：{json.dumps(result, ensure_ascii=False, indent=2)}")

    # --- 场景 C：你自己的场景 ---
    print("\n🎨 场景 C：自定义提取")
    print("   请定义一个你自己的提取场景（3 行代码）：")
    print("   ① 定义 schema_desc（task + fields）")
    print("   ② 准备一段文本")
    print("   ③ 调用 extract_with_template() 并打印结果")
    # TODO ④-4: 定义你自己的提取场景
    # 提示：可以尝试"从租房信息提取价格/面积/户型"、
    #       "从简历提取技能/经验/学历"、"从菜谱提取食材/步骤/时间"等
    # TODO: 你的代码 — 定义 schema + 文本 + 调用
    custom_schema = {
        "task": "从租房信息中提取关键信息",
        "fields": {
            "location": "房屋位置",
            "price": "租金（数字，不含货币符号）",
            "area": "面积（平方米）",
            "bedrooms": "卧室数量",
            "amenities": "设施列表",
        }
    }
    custom_text = (
        "位于北京市朝阳区的精装两居室，面积 85 平方米，月租金 8500 元。"
        "配备空调、洗衣机、冰箱和高速 Wi-Fi，交通便利，靠近地铁 10 号线。"
        "适合小家庭或上班族居住。"
    )

    result = extract_with_template(custom_text, custom_schema)
    print(f"   提取结果：{json.dumps(result, ensure_ascii=False, indent=2)}")

    print("\n✅ 验证标准：场景 A 和 B 能正确提取结构化数据，场景 C 是你原创的。")


# ══════════════════════════════════════════════════════════════════════
# 主入口：命令行参数分发
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请选择任务编号：")
        print("  uv run python code/02-prompt-engineering/json_mode_step3.py 1    # 任务① Temperature 稳定性")
        print("  uv run python code/02-prompt-engineering/json_mode_step3.py 2    # 任务② Schema 校验")
        print("  uv run python code/02-prompt-engineering/json_mode_step3.py 3    # 任务③ 修复 JSON 解析 Bug")
        print("  uv run python code/02-prompt-engineering/json_mode_step3.py 4    # 任务④ 模板系统")
        sys.exit(1)

    task_num = sys.argv[1]

    print(f"\n🚀 模块 2 · 结构化输出 — Step 3 任务 {task_num}\n")

    tasks = {
        "1": task1_temperature_stability,
        "2": task2_schema_validation,
        "3": task3_fix_json_parsing,
        "4": task4_template_system,
    }

    if task_num not in tasks:
        print(f"❌ 无效的任务编号：{task_num}，请输入 1-4")
        sys.exit(1)

    tasks[task_num]()

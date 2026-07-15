"""
Step 5 独立里程碑 — 模拟数据（非考核内容，直接拿来用）

两个数据源，对应 web_search 和 paper_db 的"伪知识库"。
导入方式：
    from mock_data import SEARCH_KB, PAPER_DB, search_kb_lookup, paper_db_query
"""

# ═══════════════════════════════════════════════════════════════
# 1. web_search 伪知识库
# key → 匹配规则：用户 query 中包含 key 时返回对应数据
# ═══════════════════════════════════════════════════════════════

SEARCH_KB = {
    "大模型参数": {
        "summary": "近三年大模型参数规模增长趋势",
        "data": [
            {"year": 2023, "model": "GPT-4",        "params_billion": 1800, "note": "传闻 1.8T 参数（MoE 架构）"},
            {"year": 2023, "model": "PaLM 2",       "params_billion": 340,  "note": "Google 最大公开版本 340B"},
            {"year": 2023, "model": "Llama 2",      "params_billion": 70,   "note": "Meta 开源，70B 为最大版本"},
            {"year": 2024, "model": "Claude 3.5",   "params_billion": 500,  "note": "Anthropic，未公开，业界估算 ~500B"},
            {"year": 2024, "model": "Gemini Ultra", "params_billion": 1000, "note": "Google，约 1T 参数"},
            {"year": 2024, "model": "Llama 3",      "params_billion": 405,  "note": "Meta 开源最大 405B"},
            {"year": 2025, "model": "DeepSeek-V3",  "params_billion": 671,  "note": "MoE 架构，总参数 671B，激活 37B"},
            {"year": 2025, "model": "Qwen 3",       "params_billion": 235,  "note": "阿里，最大版本 235B"},
            {"year": 2025, "model": "Llama 4",      "params_billion": 400,  "note": "Meta，MoE 架构，总参数 ~400B"},
        ],
    },
    "GPT-4": {
        "summary": "GPT-4 模型信息",
        "data": [
            {"year": 2023, "model": "GPT-4", "params_billion": 1800, "architecture": "MoE (8×220B)", "training_tokens": "约 13T tokens", "note": "OpenAI 未官方确认参数量，1.8T 为业界估算"},
        ],
    },
    "Transformer": {
        "summary": "Transformer 架构论文数据",
        "data": [
            {"year": 2017, "model": "Transformer-base",  "params_million": 65,  "task": "WMT 2014 EN-DE", "bleu": 27.3},
            {"year": 2017, "model": "Transformer-big",   "params_million": 213, "task": "WMT 2014 EN-DE", "bleu": 28.4},
            {"year": 2017, "model": "Transformer-big",   "params_million": 213, "task": "WMT 2014 EN-FR", "bleu": 41.0},
        ],
    },
    "Mamba": {
        "summary": "Mamba 状态空间模型论文数据",
        "data": [
            {"year": 2023, "model": "Mamba-130M",  "params_million": 130,  "task": "LM Perplexity (Wikitext-103)", "ppl": 24.7},
            {"year": 2023, "model": "Mamba-370M",  "params_million": 370,  "task": "LM Perplexity (Wikitext-103)", "ppl": 20.0},
            {"year": 2023, "model": "Mamba-790M",  "params_million": 790,  "task": "LM Perplexity (Wikitext-103)", "ppl": 17.4},
            {"year": 2023, "model": "Mamba-1.4B",  "params_million": 1400, "task": "LM Perplexity (Wikitext-103)", "ppl": 15.7},
            {"year": 2023, "model": "Mamba-2.8B",  "params_million": 2800, "task": "LM Perplexity (Wikitext-103)", "ppl": 14.5},
        ],
    },
    "DeepSeek": {
        "summary": "DeepSeek 系列模型信息",
        "data": [
            {"year": 2024, "model": "DeepSeek-V2", "params_billion": 236, "architecture": "MoE", "note": "总参数 236B，激活 21B"},
            {"year": 2025, "model": "DeepSeek-V3", "params_billion": 671, "architecture": "MoE", "note": "总参数 671B，激活 37B"},
            {"year": 2025, "model": "DeepSeek-R1", "params_billion": 671, "architecture": "MoE + 推理增强", "note": "基于 V3 的推理模型"},
        ],
    },
}


def search_kb_lookup(query: str) -> dict | None:
    """根据 query 关键词查伪知识库，返回匹配的数据或 None。"""
    query_lower = query.lower()
    # 按 key 长度降序匹配（优先匹配更具体的 key）
    for key in sorted(SEARCH_KB, key=len, reverse=True):
        if key.lower() in query_lower:
            return SEARCH_KB[key]
    return None


# ═══════════════════════════════════════════════════════════════
# 2. paper_db 论文数据库
# ═══════════════════════════════════════════════════════════════

PAPER_DB = [
    {
        "id": 1,
        "title": "Attention Is All You Need",
        "authors": "Vaswani et al.",
        "year": 2017,
        "venue": "NeurIPS",
        "params_million": 65,
        "architecture": "Transformer",
        "highlights": "提出 Self-Attention 机制，取代 RNN/CNN；Encoder-Decoder 架构；Multi-Head Attention",
        "citations": 120000,
    },
    {
        "id": 2,
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": "Devlin et al.",
        "year": 2018,
        "venue": "NAACL",
        "params_million": 340,
        "architecture": "Transformer Encoder",
        "highlights": "Masked LM 预训练 + Next Sentence Prediction；GLUE 基准刷新 SOTA",
        "citations": 100000,
    },
    {
        "id": 3,
        "title": "GPT-3: Language Models are Few-Shot Learners",
        "authors": "Brown et al.",
        "year": 2020,
        "venue": "NeurIPS",
        "params_million": 175000,
        "architecture": "Transformer Decoder",
        "highlights": "175B 参数；In-Context Learning 能力涌现；Few-shot 无需微调即可完成多任务",
        "citations": 40000,
    },
    {
        "id": 4,
        "title": "Mamba: Linear-Time Sequence Modeling with Selective State Spaces",
        "authors": "Gu & Dao",
        "year": 2023,
        "venue": "ICLR 2024 (Oral)",
        "params_million": 2800,
        "architecture": "State Space Model (SSM)",
        "highlights": "线性时间复杂度替代 Attention；选择性 SSM 机制；在长序列任务上匹敌 Transformer",
        "citations": 3000,
    },
    {
        "id": 5,
        "title": "Llama 2: Open Foundation and Fine-Tuned Chat Models",
        "authors": "Touvron et al.",
        "year": 2023,
        "venue": "Meta AI",
        "params_million": 70000,
        "architecture": "Transformer Decoder",
        "highlights": "开源 7B/13B/70B 三档；RLHF 对齐；商业可用（除 700M+ 月活限制）",
        "citations": 8000,
    },
    {
        "id": 6,
        "title": "ResNet: Deep Residual Learning for Image Recognition",
        "authors": "He et al.",
        "year": 2015,
        "venue": "CVPR 2016 (Best Paper)",
        "params_million": 25,
        "architecture": "CNN + Residual Connection",
        "highlights": "残差连接解决深层网络退化问题；152 层网络在 ImageNet 上超越 VGG；CV 领域里程碑",
        "citations": 180000,
    },
    {
        "id": 7,
        "title": "CLIP: Learning Transferable Visual Models From Natural Language Supervision",
        "authors": "Radford et al.",
        "year": 2021,
        "venue": "ICML",
        "params_million": 400,
        "architecture": "Dual Encoder (ViT + Transformer)",
        "highlights": "图文对比学习；Zero-shot 图像分类；为 DALL-E 2 / Stable Diffusion 奠定基础",
        "citations": 20000,
    },
]


def paper_db_query(query: str) -> list[dict]:
    """
    简单模拟 SQL 查询语义，支持：
      - SELECT * FROM papers                              → 全部论文
      - SELECT * FROM papers WHERE title CONTAINS 'xxx'   → 标题模糊匹配
      - SELECT * FROM papers WHERE year > 2020            → 年份过滤
      - 不支持 DROP / DELETE / ALTER / INSERT
    """
    query_lower = query.strip().lower()

    # 安全检查
    forbidden = ["drop", "delete", "alter", "insert", "update"]
    for kw in forbidden:
        if kw in query_lower:
            raise PermissionError(f"禁止操作: {kw.upper()}")

    if "from" not in query_lower:
        raise ValueError("SQL 语法错误: 缺少 FROM 子句")

    results = PAPER_DB

    # 简单条件过滤
    if "title contains" in query_lower:
        keyword = query_lower.split("title contains")[-1].strip().strip("'").strip('"')
        results = [p for p in results if keyword.lower() in p["title"].lower()]

    if "year >" in query_lower:
        import re
        match = re.search(r"year\s*>\s*(\d{4})", query_lower)
        if match:
            year_threshold = int(match.group(1))
            results = [p for p in results if p["year"] > year_threshold]

    if "year =" in query_lower or "year=" in query_lower:
        import re
        match = re.search(r"year\s*=\s*(\d{4})", query_lower)
        if match:
            year_val = int(match.group(1))
            results = [p for p in results if p["year"] == year_val]

    return results

import anthropic
from datetime import date

from mobile_server.config import settings

_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """你是一位社会学学术助手，擅长用简洁、清晰的中文总结和讨论学术论文。
不要使用 Markdown 格式（无 **加粗**、无 # 标题），用纯文本和换行分段。"""

# Cache the system prompt since it never changes across calls
_CACHED_SYSTEM = [
    {
        "type": "text",
        "text": _SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }
]


def _get_client() -> anthropic.AsyncAnthropic:
    api_key = settings.anthropic_api_key
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 未配置，请在 .env 中填写")
    return anthropic.AsyncAnthropic(api_key=api_key)


def _format_papers(papers: list[dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        authors = "、".join(p.get("authors", [])[:2]) or "未知作者"
        year = p.get("year") or "年份不详"
        lines.append(
            f"[{i}] {p['title']} ({authors}, {year})\n摘要: {p.get('abstract', '无摘要')[:400]}"
        )
    return "\n\n".join(lines)


async def summarize_papers(papers: list[dict]) -> str:
    """Return a concise Chinese summary of each paper, formatted for phone push."""
    if not papers:
        return "未找到相关论文。"

    client = _get_client()
    paper_text = _format_papers(papers)

    response = await client.messages.create(
        model=_MODEL,
        max_tokens=600,
        system=_CACHED_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"请用中文简洁总结以下{len(papers)}篇论文，每篇2-3句话，"
                    "直接列出，用论文编号分隔，不要其他格式：\n\n" + paper_text
                ),
            }
        ],
    )

    return next((b.text for b in response.content if b.type == "text"), "总结生成失败。")


async def discuss_papers(papers: list[dict], keywords: str) -> str:
    """Return a brief Chinese academic discussion linking papers to the search keywords."""
    if not papers:
        return "无论文可讨论。"

    client = _get_client()
    paper_text = _format_papers(papers)

    response = await client.messages.create(
        model=_MODEL,
        max_tokens=400,
        system=_CACHED_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"关键词：{keywords}\n\n"
                    f"以下是检索到的{len(papers)}篇论文：\n\n{paper_text}\n\n"
                    "请用不超过150字的中文，简要讨论这些论文与关键词的关联、主要主题和值得关注的发现。"
                    "不要列举论文标题，直接进行学术讨论。"
                ),
            }
        ],
    )

    return next((b.text for b in response.content if b.type == "text"), "讨论生成失败。")


async def generate_daily_digest(papers: list[dict], keywords: str) -> str:
    """Generate a formatted Chinese digest for iMessage group sharing.

    Returns plain text (~300-500 chars) with paper titles, one-line takeaways,
    and 3-5 key knowledge insights. Suitable for direct copy-paste into iMessage.
    """
    if not papers:
        return f"📚 今日社会学论文速递\n关键词：{keywords}\n\n暂无检索结果，请明晚重新提交关键词。"

    client = _get_client()
    paper_text = _format_papers(papers)
    today = date.today().strftime("%m月%d日")

    response = await client.messages.create(
        model=_MODEL,
        max_tokens=900,
        system=_CACHED_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"今天是{today}，关键词：{keywords}\n\n"
                    f"以下是检索到的{len(papers)}篇社会学论文：\n\n{paper_text}\n\n"
                    "请生成一段适合发到微信/iMessage学习群的每日论文速递，格式如下：\n"
                    f"第一行：📚 {today} 社会学论文速递｜{keywords}\n"
                    "第二部分：逐篇列出，每篇格式：\n"
                    "  论文序号. 论文标题（年份）\n"
                    "  → 一句话核心发现（30字以内）\n"
                    "第三部分：以「──────」分隔后，写3-5条知识要点，每条以「• 」开头，"
                    "提炼这批论文共同揭示的理论洞察、方法论特点或现实启示。\n"
                    "全文纯文本，不要 Markdown，不要多余解释，总长度控制在500字以内。"
                ),
            }
        ],
    )

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        # Fallback: plain list
        lines = [f"📚 {today} 社会学论文速递｜{keywords}\n"]
        for i, p in enumerate(papers, 1):
            lines.append(f"{i}. {p['title']} ({p.get('year', '?')})")
        return "\n".join(lines)
    return text

import anthropic

from mobile_server.config import settings

_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """你是一位社会学学术助手，擅长用简洁、清晰的中文总结和讨论学术论文。
你的输出将通过推送通知发送到手机，因此必须简洁——每篇论文摘要不超过3句话，整体讨论不超过150字。
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

"""
AI 캡션 생성

지원 프로바이더:
  - none  : AI 사용 안 함
  - openai: OpenAI gpt-4o-mini
  - claude: Anthropic claude-opus-4-6
"""
from autosns.utils import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "당신은 Instagram 마케터입니다. "
    "사용자가 제공한 키워드/상황을 바탕으로 "
    "매력적이고 자연스러운 Instagram 포스팅 캡션을 한국어로 작성하세요. "
    "이모지를 적절히 사용하고, 해시태그는 포함하지 마세요. "
    "캡션만 출력하세요."
)


def generate_caption(prompt: str, provider: str | None = None) -> str:
    """AI로 Instagram 캡션을 생성한다.

    Args:
        prompt: 캡션 주제/키워드/상황 설명
        provider: "openai" | "claude" | "none" (None이면 config에서 읽음)

    Returns:
        생성된 캡션 문자열. AI 비활성화 시 빈 문자열.
    """
    from config import AI_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENAI_MODEL, CLAUDE_MODEL

    prov = (provider or AI_PROVIDER).lower()

    if prov == "none":
        logger.debug("AI_PROVIDER=none, 캡션 생성을 건너뜁니다.")
        return ""

    if prov == "openai":
        return _openai_caption(prompt, OPENAI_API_KEY, OPENAI_MODEL)

    if prov == "claude":
        return _claude_caption(prompt, ANTHROPIC_API_KEY, CLAUDE_MODEL)

    raise ValueError(f"알 수 없는 AI_PROVIDER: {prov} (none | openai | claude)")


def _openai_caption(prompt: str, api_key: str, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai 패키지가 설치되어 있지 않습니다: pip install openai")

    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

    client = OpenAI(api_key=api_key)
    logger.info("OpenAI(%s)로 캡션 생성 중...", model)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.8,
    )
    caption = response.choices[0].message.content.strip()
    logger.info("캡션 생성 완료 (%d자)", len(caption))
    return caption


def _claude_caption(prompt: str, api_key: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic 패키지가 설치되어 있지 않습니다: pip install anthropic")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

    client = anthropic.Anthropic(api_key=api_key)
    logger.info("Claude(%s)로 캡션 생성 중...", model)
    message = client.messages.create(
        model=model,
        max_tokens=300,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    caption = message.content[0].text.strip()
    logger.info("캡션 생성 완료 (%d자)", len(caption))
    return caption

"""
AI 캡션 생성 서비스
OpenAI 또는 Anthropic을 설정에 따라 선택
"""
from app.core.config import settings
from app.schemas.caption import GenerateCaptionRequest, GenerateCaptionResponse

_SYSTEM_PROMPT = """당신은 Instagram 마케팅 전문가입니다.
소상공인을 위한 효과적이고 매력적인 SNS 캡션을 작성해주세요.
반드시 JSON 형식으로 응답하세요:
{
  "caption": "캡션 내용",
  "hashtags": ["#태그1", "#태그2", ...]
}"""


def _build_user_prompt(req: GenerateCaptionRequest) -> str:
    extra = f"\n추가 컨텍스트: {req.extra_context}" if req.extra_context else ""
    return (
        f"주제: {req.topic}\n"
        f"톤앤매너: {req.tone}\n"
        f"언어: {req.language}\n"
        f"해시태그 수: {req.hashtag_count}개{extra}\n\n"
        "위 정보를 바탕으로 Instagram 캡션과 해시태그를 생성해주세요."
    )


async def generate_caption(req: GenerateCaptionRequest) -> GenerateCaptionResponse:
    if settings.AI_PROVIDER == "anthropic":
        return await _generate_anthropic(req)
    return await _generate_openai(req)


async def _generate_openai(req: GenerateCaptionRequest) -> GenerateCaptionResponse:
    import json

    from openai import AsyncOpenAI

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(req)},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    data = json.loads(response.choices[0].message.content)
    caption = data.get("caption", "")
    hashtags = data.get("hashtags", [])

    full_text = _combine(caption, hashtags)
    return GenerateCaptionResponse(caption=caption, hashtags=hashtags, full_text=full_text)


async def _generate_anthropic(req: GenerateCaptionRequest) -> GenerateCaptionResponse:
    import json

    import anthropic

    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(req)}],
    )

    text = message.content[0].text
    # JSON 블록 추출
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    caption = data.get("caption", "")
    hashtags = data.get("hashtags", [])

    full_text = _combine(caption, hashtags)
    return GenerateCaptionResponse(caption=caption, hashtags=hashtags, full_text=full_text)


def _combine(caption: str, hashtags: list[str]) -> str:
    """캡션 + 해시태그 결합 (autosns.hashtags.append_hashtags 패턴 동일)."""
    if not hashtags:
        return caption
    tag_block = " ".join(hashtags)
    if caption.strip():
        return f"{caption.strip()}\n\n.\n.\n.\n{tag_block}"
    return tag_block

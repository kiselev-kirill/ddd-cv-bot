from yandex_cloud_ml_sdk import YCloudML

from src.config import settings
from src.interfaces.bot.i18n import normalize_locale, t
from src.interfaces.bot.services.load_resume import load_resume

sdk = YCloudML(
    folder_id=settings.YANDEX_FOLDER_ID, auth=settings.YANDEX_GPT_API_KEY
)


async def ask_yandex_gpt(
    question: str,
    memory_context: str = "",
    locale: str | None = None,
) -> str:
    normalized_locale = normalize_locale(locale)
    model = sdk.models.completions("yandexgpt-lite", model_version="rc")
    model = model.configure(temperature=0.3)
    resume = load_resume(normalized_locale)
    memory_part = (
        f"\n\n{t(normalized_locale, 'gpt.memory_header')}\n{memory_context}"
        if memory_context
        else ""
    )
    result = model.run(
        [
            {
                "role": "system",
                "text": (
                    f"{t(normalized_locale, 'gpt.system_header')}\n{resume}\n\n"
                    f"{t(normalized_locale, 'gpt.language_instruction')}\n"
                    f"{settings.GPT_PROMPT}{memory_part}"
                ),
            },
            {
                "role": "user",
                "text": f"{question}"
            }
        ]
    )

    return result[0].text

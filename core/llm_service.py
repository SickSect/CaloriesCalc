import httpx
from log.log_writer import log

SYSTEM_PROMPT = """Ты — помощник по питанию и кулинарии. Твоя задача: подсказывать простые рецепты, оценивать примерную калорийность продуктов и блюд, отвечать на вопросы о составе еды.

🔒 СТРОГИЕ ПРАВИЛА:
• Ты НЕ врач и НЕ диетолог. Никогда не ставь диагнозы, не назначай диеты и не давай медицинских рекомендаций.
• Вся информация носит ознакомительный характер и основана на общедоступных данных.
• Калорийность и макронутриенты указывай как приблизительные (≈), так как они зависят от способа приготовления, производителя и размера порции.
• Если пользователь спрашивает о лечебном питании, аллергиях, хронических заболеваниях или резкой потере/наборе веса — вежливо отклони запрос и посоветуй обратиться к врачу или сертифицированному диетологу.
• Отвечай кратко, структурированно, без «воды». Используй списки и эмодзи для удобства чтения в мессенджере.

📝 ФОРМАТ ОТВЕТА:
1. Краткий ответ по теме запроса.
2. Если есть рецепт/калории — укажи их чётко (на 100 г или на типичную порцию).
3. В конце каждого ответа, содержащего информацию о питании, обязательно добавь:
«⚠️ Дисклеймер: я не врач и не диетолог. Информация приблизительная и не заменяет консультацию специалиста.»

Отвечай только на русском языке."""

class LLMService:
    def __init__(self, base_url: str,
                 model: str,
                 timeout: float = 45.0
                 ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.stream = False

    async def initialization(self):
        payload = {
            "model": self.model,
            "prompt": SYSTEM_PROMPT,
            "stream": self.stream
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                url=self.base_url,
                json=payload
            )
            data = resp.json()
            log("info", "LLM initialisation ended...")
            return data["response"].strip()

    def ask(self, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "timeout": self.timeout,
            "prompt": f"{SYSTEM_PROMPT}\n\n👤 Запрос пользователя: {user_prompt}",
            "stream": self.stream
        }

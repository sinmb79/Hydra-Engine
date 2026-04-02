import httpx
from telegram import Bot
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, CommandHandler

from hydra.logging.setup import configure_logging, get_logger

logger = get_logger(__name__)


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self._token = token
        self._chat_id = chat_id
        self._bot: Bot | None = None

    def _get_bot(self) -> Bot:
        if self._bot is None:
            self._bot = Bot(token=self._token)
        return self._bot

    async def send_message(self, text: str) -> None:
        if not self._token or not self._chat_id:
            logger.warning("telegram_not_configured")
            return
        try:
            await self._get_bot().send_message(chat_id=self._chat_id, text=text)
        except TelegramError as e:
            logger.error("telegram_send_error", error=str(e))


def main() -> None:
    from hydra.config.settings import get_settings
    settings = get_settings()
    configure_logging(settings.log_level)

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.info("telegram_not_configured_skipping")
        return

    async def kill_switch_callback(reason: str, source: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    "http://hydra-core:8000/risk/kill",
                    headers={"X-HYDRA-KEY": settings.hydra_api_key},
                    json={"reason": reason, "source": source},
                )
        except Exception as e:
            logger.error("kill_switch_call_failed", error=str(e))

    async def handle_killswitch(update, context):
        await update.message.reply_text("⚠️ Kill Switch 발동 중...")
        await kill_switch_callback(reason="telegram_command", source="telegram")
        await update.message.reply_text("✅ 전 포지션 청산 완료")

    async def post_init(app):
        await app.bot.send_message(
            chat_id=settings.telegram_chat_id,
            text="HYDRA 텔레그램 봇 시작됨. /killswitch 명령으로 긴급 청산 가능.",
        )
        logger.info("telegram_bot_polling_started")

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("killswitch", handle_killswitch))

    # run_polling()이 자체 이벤트 루프 관리 — asyncio.run() 불필요
    app.run_polling()


if __name__ == "__main__":
    main()

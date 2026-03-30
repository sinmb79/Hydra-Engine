import asyncio
from telegram import Bot
from telegram.error import TelegramError

from hydra.logging.setup import get_logger

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

    async def run_bot(self, kill_switch_callback) -> None:
        """Telegram 명령어 수신 루프 (별도 프로세스에서 실행)."""
        from telegram.ext import ApplicationBuilder, CommandHandler

        app = ApplicationBuilder().token(self._token).build()

        async def handle_killswitch(update, context):
            await update.message.reply_text("⚠️ Kill Switch 발동 중...")
            await kill_switch_callback(reason="telegram_command", source="telegram")
            await update.message.reply_text("✅ 전 포지션 청산 완료")

        app.add_handler(CommandHandler("killswitch", handle_killswitch))
        await app.run_polling()

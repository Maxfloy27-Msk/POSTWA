import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from config import BOT_TOKEN
from services import deliver_posts, generate_posts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class PostFlow(StatesGroup):
    waiting_for_text = State()
    generating = State()


dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(PostFlow.waiting_for_text)
    await message.answer("что вы хотите написать сегодня?")


@dp.message(PostFlow.waiting_for_text, F.text)
async def handle_user_text(message: Message, state: FSMContext) -> None:
    user_text = message.text.strip()
    if not user_text:
        await message.answer("Текст пустой. Пришлите тему или черновик.")
        return

    await state.set_state(PostFlow.generating)
    status = await message.answer("Готовлю посты, это займёт немного времени…")

    try:
        posts = await generate_posts(message.from_user.id, user_text)
    except Exception as exc:
        logger.exception("SMM WINNI2 request failed")
        await status.edit_text(f"Не удалось сгенерировать посты: {exc}")
        await state.clear()
        return

    if not posts:
        await status.edit_text("SMM WINNI2 не вернул ни одного поста. Попробуйте ещё раз.")
        await state.clear()
        return

    await status.edit_text(f"Готово! Постов: {len(posts)}. Отправляю…")

    async def send_to_user(post: str) -> None:
        await message.answer(post)

    try:
        await deliver_posts(send_to_user, message.from_user.id, posts)
    except Exception as exc:
        logger.exception("Delivery failed")
        await message.answer(f"Часть доставки не удалась: {exc}")
        await state.clear()
        return

    await message.answer("Завершено ✅")
    await state.clear()


@dp.message(PostFlow.generating)
async def busy(message: Message) -> None:
    await message.answer("Ещё готовлю предыдущие посты, подождите…")


@dp.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer("Отправьте /start, чтобы начать.")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    logger.info("Bot is starting")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from config import AUTO_POST_PROJECT_ID, BOT_TOKEN, SMM_PROJECT_ID
from manus import create_task, wait_for_result

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MAX_TG_LEN = 4096


class PostFlow(StatesGroup):
    waiting_for_text = State()
    generating = State()


dp = Dispatcher(storage=MemoryStorage())


def _split(text: str) -> list[str]:
    """Split text into Telegram-safe chunks preserving line breaks."""
    chunks: list[str] = []
    while len(text) > MAX_TG_LEN:
        cut = text.rfind("\n", 0, MAX_TG_LEN)
        if cut == -1:
            cut = MAX_TG_LEN
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


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
    status = await message.answer("⏳ Отправляю в SMM WINNI2…")

    # Step 1: create task in SMM WINNI2
    try:
        task_id = await create_task(
            SMM_PROJECT_ID,
            f"сделай посты по этому тексту: {user_text}",
        )
        logger.info("SMM WINNI2 task created: %s", task_id)
    except Exception as exc:
        logger.exception("Failed to create SMM task")
        await status.edit_text(f"❌ Ошибка создания задачи: {exc}")
        await state.clear()
        return

    # Step 2: poll for result
    async def tick(elapsed: int) -> None:
        try:
            await status.edit_text(f"⏳ SMM WINNI2 готовит посты… {elapsed}с")
        except Exception:
            pass

    try:
        posts_text = await wait_for_result(task_id, on_tick=tick)
    except TimeoutError:
        await status.edit_text("⏰ SMM WINNI2 не ответил вовремя. Попробуйте ещё раз.")
        await state.clear()
        return
    except Exception as exc:
        logger.exception("Failed while waiting for SMM result")
        await status.edit_text(f"❌ Ошибка получения постов: {exc}")
        await state.clear()
        return

    await status.edit_text("✅ Посты готовы! Публикую…")

    # Step 3: parallel delivery — user chat + Auto_post_WA
    async def send_to_user() -> None:
        for chunk in _split(posts_text):
            await message.answer(chunk)

    async def send_to_auto_post_wa() -> None:
        try:
            wa_id = await create_task(
                AUTO_POST_PROJECT_ID,
                f"Опубликуй эти посты:\n\n{posts_text}",
            )
            logger.info("Auto_post_WA task created: %s", wa_id)
        except Exception as exc:
            logger.exception("Failed to send to Auto_post_WA")
            await message.answer(f"⚠️ Не удалось отправить в Auto_post_WA: {exc}")

    await asyncio.gather(send_to_user(), send_to_auto_post_wa())

    await message.answer("Публикация выполнена.")
    await state.clear()


@dp.message(PostFlow.generating)
async def busy(message: Message) -> None:
    await message.answer("⏳ Ещё готовлю посты, подождите…")


@dp.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer("Отправьте /start, чтобы начать.")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    logger.info("Bot @AutoWA27_bot starting")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

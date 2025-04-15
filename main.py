import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message, BotCommand
from aiogram.exceptions import TelegramConflictError
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx
import logging

BOT_TOKEN = "7971134605:AAEqGrsHwPRdkZ9eUJxFg93W8RD8jcyJaUY"
GPT_API_URL = "https://api.koompi.dev/v1/chat/completions"
ADMINS = [7822370920]  # замени на свой Telegram ID

# Временное хранилище состояний
warns = {}
mutes = set()

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


# ========== /start ==========
@dp.message(CommandStart())
async def start_handler(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Задать вопрос GPT", callback_data="ask")
    kb.button(text="📊 Статус", callback_data="status")
    await message.answer("Привет! Я бот-помощник. Выбери действие:", reply_markup=kb.as_markup())


# ========== /ask ==========
@dp.message(Command("ask"))
async def ask_gpt(message: Message):
    query = message.text.removeprefix("/ask").strip()
    if not query:
        await message.answer("Напиши вопрос после команды /ask")
        return

    await message.answer("✍️ Думаю...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GPT_API_URL, json={
                "messages": [{"role": "user", "content": query}],
                "model": "gpt-3.5-turbo"
            })
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            await message.answer(reply)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# ========== Админ-команды ==========
@dp.message(Command("ban"))
async def ban_user(message: Message):
    if message.from_user.id not in ADMINS:
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя, которого хочешь забанить.")
        return
    try:
        await message.chat.ban(message.reply_to_message.from_user.id)
        await message.answer("🚫 Пользователь забанен.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("kick"))
async def kick_user(message: Message):
    if message.from_user.id not in ADMINS:
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя, которого хочешь кикнуть.")
        return
    try:
        await message.chat.kick(message.reply_to_message.from_user.id)
        await message.chat.unban(message.reply_to_message.from_user.id)
        await message.answer("👢 Пользователь кикнут.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("mute"))
async def mute_user(message: Message):
    if message.from_user.id not in ADMINS:
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя, которого хочешь замутить.")
        return
    user_id = message.reply_to_message.from_user.id
    mutes.add(user_id)
    await message.answer("🔇 Пользователь замучен.")


@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if message.from_user.id not in ADMINS:
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя, которого хочешь размутить.")
        return
    user_id = message.reply_to_message.from_user.id
    mutes.discard(user_id)
    await message.answer("🔊 Пользователь размучен.")


@dp.message(Command("warn"))
async def warn_user(message: Message):
    if message.from_user.id not in ADMINS:
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя, которому хочешь выдать варн.")
        return
    user_id = message.reply_to_message.from_user.id
    warns[user_id] = warns.get(user_id, 0) + 1
    await message.answer(f"⚠️ Предупреждение выдано. Всего: {warns[user_id]}")


@dp.message(Command("status"))
async def status_cmd(message: Message):
    await message.answer("✅ Бот активен и работает!")


# ========== Игнор замученных ==========
@dp.message()
async def block_muted_users(message: Message):
    if message.from_user.id in mutes:
        await message.delete()


# ========== MAIN ==========
async def main():
    try:
        await dp.start_polling(bot)
    except TelegramConflictError:
        print("❌ Бот уже запущен где-то ещё. Выход.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

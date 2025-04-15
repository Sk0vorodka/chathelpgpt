import asyncio
import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from collections import defaultdict
import logging
import os

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7971134605:AAEqGrsHwPRdkZ9eUJxFg93W8RD8jcyJaUY"
GPT_API_URL = "https://api.koompi.dev/v1/chat/completions"

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Хранилище предупреждений
warnings = defaultdict(int)

@dp.message(Command("start"))
async def start_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Задать вопрос GPT", callback_data="gpt")
        ],
        [
            InlineKeyboardButton(text="🛠 Админ команды", callback_data="admin")
        ]
    ])
    await message.answer("Привет! Я бот-помощник. Выбери действие:", reply_markup=kb)

@dp.callback_query(F.data == "gpt")
async def gpt_button(callback: types.CallbackQuery):
    await callback.message.answer("Напиши свой вопрос с помощью команды /ask")
    await callback.answer()

@dp.callback_query(F.data == "admin")
async def admin_button(callback: types.CallbackQuery):
    text = (
        "🛠 Админ команды:\n"
        "/warn — Выдать предупреждение (ответом на сообщение)\n"
        "/unwarn — Снять все предупреждения\n"
        "/kick — Кикнуть\n"
        "/ban — Забанить\n"
        "/mute — Замьютить\n"
        "/unmute — Размьютить"
    )
    await callback.message.answer(text)
    await callback.answer()

@dp.message(Command("ask"))
async def ask_gpt(message: types.Message):
    query = message.text.removeprefix("/ask").strip()
    if not query:
        await message.answer("Напиши вопрос после команды /ask")
        return

    await message.answer("✍️ Думаю...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GPT_API_URL, json={
                "messages": [{"role": "user", "content": query}],
                "model": "gpt-3.5-turbo"
            })
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            await message.answer(reply)
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

@dp.message(Command("warn"))
async def warn_user(message: Message):
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя, которому хочешь выдать предупреждение.")
        return
    user_id = message.reply_to_message.from_user.id
    warnings[user_id] += 1
    await message.answer(f"⚠️ Пользователю выдано предупреждение. Сейчас у него {warnings[user_id]} предупреждений.")

@dp.message(Command("unwarn"))
async def unwarn_user(message: Message):
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя, чтобы снять предупреждения.")
        return
    user_id = message.reply_to_message.from_user.id
    warnings[user_id] = 0
    await message.answer("✅ Предупреждения сняты.")

@dp.message(Command("kick"))
async def kick_user(message: Message):
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение, чтобы кикнуть пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    await bot.ban_chat_member(message.chat.id, user_id)
    await bot.unban_chat_member(message.chat.id, user_id)
    await message.answer("👢 Пользователь кикнут.")

@dp.message(Command("ban"))
async def ban_user(message: Message):
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение, чтобы забанить пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    await bot.ban_chat_member(message.chat.id, user_id)
    await message.answer("🔨 Пользователь забанен.")

@dp.message(Command("mute"))
async def mute_user(message: Message):
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение, чтобы замьютить пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    permissions = types.ChatPermissions()
    await bot.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
    await message.answer("🔇 Пользователь замьючен.")

@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение, чтобы размьютить пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    allow = types.ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=True,
        can_invite_users=True,
        can_pin_messages=True
    )
    await bot.restrict_chat_member(message.chat.id, user_id, permissions=allow)
    await message.answer("🔊 Пользователь размьючен.")

# Запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

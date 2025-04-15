import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
import httpx
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
GPT_API_URL = "https://api.koompi.dev/v1/chat/completions"

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Напиши /ask и свой вопрос, чтобы поговорить с GPT.")

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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

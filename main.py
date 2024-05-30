import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.filters.state import StateFilter

API_TOKEN = 'token'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

conn = sqlite3.connect('news.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL)''')
conn.commit()

class NewsForm(StatesGroup):
    entering_title = State()
    entering_content = State()

@dp.message(Command('createnews'))
async def create_news(message: types.Message, state: FSMContext):
    await state.set_state(NewsForm.entering_title)
    await message.answer("Введите заголовок новости:")

@dp.message(StateFilter(NewsForm.entering_title))
async def enter_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewsForm.entering_content)
    await message.answer("Введите содержание новости:")

@dp.message(StateFilter(NewsForm.entering_content))
async def enter_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    title = data['title']
    content = message.text
    cursor.execute("INSERT INTO news (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    await state.clear()
    await message.answer("Новость успешно создана!")

@dp.message(Command('shownews'))
async def show_news(message: types.Message):
    cursor.execute("SELECT * FROM news")
    news_list = cursor.fetchall()
    if not news_list:
        await message.answer("Нет новостей для отображения.")
    else:
        await send_news_page(message, news_list, 0)

async def send_news_page(message: types.Message, news_list, index, edit=False):
    title, content = news_list[index][1], news_list[index][2]
    text = f"<b>{title}</b>\n\n{content}"
    markup = InlineKeyboardBuilder()

    if index > 0:
        markup.row(InlineKeyboardButton(text="Назад", callback_data=f"page_{index - 1}"))

    if index < len(news_list) - 1:
        markup.row(InlineKeyboardButton(text="Вперед", callback_data=f"page_{index + 1}"))

    markup = markup.as_markup()

    if edit:
        await message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(lambda callback_query: callback_query.data.startswith("page_"))
async def handle_pagination(callback_query: types.CallbackQuery):
    index = int(callback_query.data.split("_")[1])
    cursor.execute("SELECT * FROM news")
    news_list = cursor.fetchall()
    await send_news_page(callback_query.message, news_list, index, edit=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

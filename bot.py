import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ChatPermissions, ForceReply
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (надо вынести в отдельный файл)
API_TOKEN = 'TOKEN_YOU_BOT'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Определение состояний FSM, создаём класс состояний, `awaiting_answer` — состояние, в котором бот ожидает ответа от пользователя на вопрос
class FSM(StatesGroup):
    awaiting_answer = State()

# приветственно сообщение
welcome_message = (
    "Добро пожаловать! Перед тем как писать сообщения, ответьте на вопрос:\n"
    "Полседняя версия нашего любимого фреймворка?"
)

# ответ
correct_answer = '18'

@dp.message(F.new_chat_members)
async def on_user_join(message: types.Message, state: FSMContext):
    new_member = message.new_chat_members[0]

    # Проверка, является ли новый участник ботом
    if new_member.is_bot:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=new_member.id)
        await message.answer(f"Бот {new_member.full_name} удален из группы.")
        logger.info(f"Removed bot {new_member.full_name} from the group.")
        return

    question_message = await message.answer(welcome_message, reply_markup=ForceReply())
    logger.info(f"User {new_member.id} joined the group, awaiting answer.")

    # удаляяем системное сообщение о входе пользователя
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    # сохраняем ID сообщения с вопросом для последующего удаления
    await state.update_data(question_message_id=question_message.message_id)
    await state.set_state(FSM.awaiting_answer)

@dp.message(F.text, FSM.awaiting_answer)
async def handle_answer(message: types.Message, state: FSMContext):
    answer = message.text.lower().strip()
    data = await state.get_data()
    question_message_id = data.get("question_message_id")

    # удаляем вопрос и отввет пользователя
    if question_message_id:
        await bot.delete_message(chat_id=message.chat.id, message_id=question_message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    if answer == correct_answer:
#        await message.answer("Правильно! Вы можете писать сообщения.")
        await state.clear()  # сбрасываем состояние
        logger.info(f"User {message.from_user.id} answered correctly and was granted access.")
    else:
#        await message.answer("Неправильно. Вы будете удалены из группы.")
        
        # удаляем пользователя из группы
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)  # снимаем бан, что бы можно было зайти еще раз
        await state.clear()  # сбрасываем состояние после удаления
        logger.info(f"User {message.from_user.id} answered incorrectly and was removed from the group.")

# удаляем системное сообщения, что пользователь удален из группы
@dp.message(F.left_chat_member)
async def on_user_leave(message: types.Message):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    logger.info(f"System message deleted: user {message.left_chat_member.id} left the group.")

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())

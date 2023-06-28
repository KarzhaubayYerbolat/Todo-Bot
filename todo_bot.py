from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
import db_actions
import emoji


async def startup_jobs(_):
    print("bot is running")
    db_actions.start_db()

bot = Bot(token='!YOUR TOKEN!')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class YourState(StatesGroup):
    waiting_for_task = State()
    waiting_task_number_for_done = State()
    waiting_task_number_for_delete = State()


@dp.message_handler(Command("start"))
async def getting_start(message: types.Message):
    user_first_name = message.from_user.first_name
    welcome_letter = f"Привет, {user_first_name}!\n" \
                     f"Я простой бот для ведения списка ваших дел.\n" \
                     f"С помощью команд ниже легко и просто управляйте своими делами:\n" \
                     f"/list - вывод списка задач с их номерами\n" \
                     f"/add <ТЕКС ЗАДАЧИ> - добавление задачи\n" \
                     f"/done <НОМЕР ЗАДАЧИ В ВАШЕМ СПИСКЕ> - отметка задачи как выполненной\n" \
                     f"/delete <НОМЕР ЗАДАЧИ В ВАШЕМ СПИСКЕ> - удаление задачи"
    await message.answer(welcome_letter)


@dp.message_handler(Command("add"))
async def add_todo(message: types.Message):
    await message.answer("Введите текст задачи:")
    await YourState.waiting_for_task.set()


@dp.message_handler(state=YourState.waiting_for_task)
async def process_task(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    todo = message.text
    if db_actions.check_todo(chat_id, todo_text=todo):
        await message.answer('У вас уже имеется задача с таким описанием!\n/list - вывести список задач')
    else:
        await db_actions.create_todo(todo, chat_id)
        await message.answer("Задача добавлена в ваш список дел!\n/list - вывести список задач")
    await state.finish()


@dp.message_handler(Command("list"))
async def get_todo_list(message: types.Message):
    todo_list = db_actions.get_todos(message.chat.id)
    done = "Статус: " + emoji.emojize(':check_mark_button:') + " Выполнена"
    not_done = "Статус: " + emoji.emojize(':orange_circle:') + " В процессе"
    if todo_list:
        tasks_text = "\n".join([f"{todo[4]}. {todo[1]}. \n{done if todo[2] else not_done}." for todo in todo_list])
        answer = f"Список задач:\n\n{tasks_text}"
    else:
        answer = f"У вас нет активных задач!"
    await message.answer(answer)


@dp.message_handler(Command("done"))
async def done_todo(message: types.Message):
    await message.answer("Введите номер задачи, которую необходимо отметить выполненной:")
    await YourState.waiting_task_number_for_done.set()


@dp.message_handler(state=YourState.waiting_task_number_for_done)
async def process_task_number(message: types.Message, state: FSMContext):
    task_number = message.text
    chat_id = message.chat.id
    if task_number.isdigit():
        if db_actions.check_todo(chat_id, todo_number=task_number):
            db_actions.done_todo(task_number, chat_id)
            await message.answer(f"Задача с номером {task_number} отмечена выполненной.\n/list - вывести список задач'")
        else:
            await message.answer("Задачи с указанным номером не существует.\n/list - вывести список задач'")
    else:
        await message.answer("Номер задачи должен быть цифрой!")
    await state.finish()


@dp.message_handler(Command("delete"))
async def done_todo(message: types.Message):
    await message.answer("Введите номер задачи, которую необходимо удалить:")
    await YourState.waiting_task_number_for_delete.set()


@dp.message_handler(state=YourState.waiting_task_number_for_delete)
async def process_task_number(message: types.Message, state: FSMContext):
    task_number = message.text
    chat_id = message.chat.id
    if task_number.isdigit():
        if db_actions.check_todo(chat_id, todo_number=task_number):
            db_actions.delete_todo(task_number, chat_id)
            await message.answer(f"Задача с номером {task_number} удалена.\n/list - вывести список задач'")
        else:
            await message.answer("Задачи с указанным номером не существует.\n/list - вывести список задач'")
    else:
        await message.answer("Номер задачи должен быть цифрой!")
    await state.finish()

executor.start_polling(dp, skip_updates=True, on_startup=startup_jobs)

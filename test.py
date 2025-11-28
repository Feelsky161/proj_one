import telebot
import json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from taskmaneger import Taskmanedger


token = '8290284835:AAFKcQDUKnmnFT7aATRXOWt52J-PyQ0iCXw'
bot = telebot.TeleBot(token)
taskmaneger = Taskmanedger()


# Флаги состояния — отслеживают, ждёт ли бот ввода названия или описания задачи
waiting_for_task_name = False
waiting_for_task_desc = False


# --- Функции для работы с JSON ---
def save_tasks():
    """Сохраняет задачи в файл tasks.json"""
    try:
        with open('tasks.json', 'w', encoding='utf-8') as f:
            json.dump(taskmaneger.tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить задачи в файл: {e}")


def load_tasks():
    """Загружает задачи из файла tasks.json при запуске"""
    try:
        with open('tasks.json', 'r', encoding='utf-8') as f:
            taskmaneger.tasks = json.load(f)
        print("[INFO] Задачи загружены из файла tasks.json")
    except FileNotFoundError:
        print("[INFO] Файл tasks.json не найден. Начнём с пустого списка задач.")
        taskmaneger.tasks = []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Ошибка чтения JSON-файла: {e}")
        taskmaneger.tasks = []

# --- Создание клавиатуры ---
def get_main_menu():
    """Создаёт и возвращает клавиатуру с кнопками."""
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=False
    )
    markup.add(KeyboardButton("Создать задачу"))
    markup.add(KeyboardButton("Показать задачи"))
    markup.add(KeyboardButton("Удалить задачу"))
    return markup

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        bot.send_message(
            chat_id=message.chat.id,
            text="ХАЙ ✌️ Выберите действие:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"[ERROR] Не удалось отправить меню: {e}")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    global waiting_for_task_name, waiting_for_task_desc


    # Если бот ждёт ввода названия или описания — пропускаем общий обработчик
    if waiting_for_task_name or waiting_for_task_desc:
        return

    try:
        if message.text == "Создать задачу":
            create_task(message)
        elif message.text == "Показать задачи":
            show_tasks(message)
        elif message.text == "Удалить задачу":
            delete_task(message)
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text="Неизвестная команда. Используйте кнопки ниже.",
                reply_markup=get_main_menu()
            )
    except Exception as e:
        print(f"[ERROR] Ошибка в handle_text: {e}")


@bot.message_handler(commands=["create"])
def create_task(message):
    try:
        global waiting_for_task_name
        waiting_for_task_name = True
        msg = bot.send_message(
            message.chat.id,
            "Введите название задачи:",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_task_name)
    except Exception as e:
        print(f"[ERROR] Ошибка в create_task: {e}")


def process_task_name(message):
    global waiting_for_task_name, waiting_for_task_desc
    waiting_for_task_name = False  # Сбрасываем флаг


    if not message.text:
        bot.send_message(
            message.chat.id,
            "Название задачи не может быть пустым!",
            reply_markup=get_main_menu()
        )
        return

    task_name = message.text
    waiting_for_task_desc = True  # Устанавливаем флаг ожидания описания
    msg = bot.send_message(
        message.chat.id,
        "Введите описание задачи:",
        reply_markup=ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_task_desc, task_name)


def process_task_desc(message, task_name):
    global waiting_for_task_desc
    waiting_for_task_desc = False  # Сбрасываем флаг


    if not message.text:
        bot.send_message(
            message.chat.id,
            "Описание задачи не может быть пустым!",
            reply_markup=get_main_menu()
        )
        return

    task_desc = message.text
    # Сохраняем задачу и сразу записываем в файл
    taskmaneger.createTask(task_name, task_desc)
    save_tasks()  # <--- СОХРАНЕНИЕ В ФАЙЛ
    bot.send_message(
        message.chat.id,
        "Задача создана!",
        reply_markup=get_main_menu()
    )

@bot.message_handler(commands=["show"])
def show_tasks(message):
    try:
        tasks = taskmaneger.get_tasks()
        if tasks:
            response = "Ваши задачи:\n\n"
            for i, task in enumerate(tasks, 1):
                response += f"{i}. {task['name']}\n   {task['description']}\n\n"
        else:
            response = "Список задач пуст."
        bot.send_message(
            message.chat.id,
            response,
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"[ERROR] Ошибка в show_tasks: {e}")


@bot.message_handler(commands=["delete"])
def delete_task(message):
    try:
        tasks = taskmaneger.get_tasks()
        if not tasks:
            bot.send_message(
                message.chat.id,
                "Список задач пуст.",
                reply_markup=get_main_menu()
            )
            return
        bot.send_message(
            message.chat.id,
            "Введите номер задачи для удаления:",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(message, process_delete)
    except Exception as e:
        print(f"[ERROR] Ошибка в delete_task: {e}")

def process_delete(message):
    try:
        num = int(message.text) - 1
        if num < 0 or num >= len(taskmaneger.tasks):
            bot.send_message(
                message.chat.id,
                "Неверный номер задачи.",
                reply_markup=get_main_menu()
            )
            return
        taskmaneger.tasks.pop(num)
        save_tasks()  # <--- СОХРАНЕНИЕ В ФАЙЛ ПОСЛЕ УДАЛЕНИЯ
        bot.send_message(
            message.chat.id,
            "Задача удалена!",
            reply_markup=get_main_menu()
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, введите число.",
            reply_markup=get_main_menu()
        )

# --- Запуск бота ---
if __name__ == '__main__':
    # Загружаем задачи из файла при старте
    load_tasks()
    print("Бот запущен...")
    bot.infinity_polling()

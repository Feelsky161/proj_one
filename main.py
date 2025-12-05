import telebot
import sys
import json
import logging
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

#Обновление записи версии бота
version = "0.0.1"

# Хранение задач по пользователям
USER_TASKS = {}  # {user_id: [{'name': ..., 'description': ...}, ...]}
TASKS_DIR = 'tasks'
if not os.path.exists(TASKS_DIR):
    os.makedirs(TASKS_DIR)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Проверка токена
token = '8290284835:AAFKcQDUKnmnFT7aATRXOWt52J-PyQ0iCXw'
if not token or len(token) < 10:
    logger.error("Некорректный токен бота!")
    sys.exit(1)

bot = telebot.TeleBot(token)

# Контекст пользователей
user_states = {}  # {user_id: {'state': 'waiting_name', 'task_name': ''}}

def get_user_state(user_id):
    return user_states.get(user_id, {})

def set_user_state(user_id, state):
    user_states[user_id] = state

# --- Создание клавиатуры с кнопками удаления ---
def get_tasks_keyboard(tasks):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for i, task in enumerate(tasks, 1):
        markup.add(f"🗑️ Удалить №{i}: {task['name'][:25]}...")
    markup.add("⬅️ Назад")
    return markup

# --- Пагинация задач ---
TASKS_PER_PAGE = 5

def format_tasks_page(tasks, page):
    start = (page - 1) * TASKS_PER_PAGE
    end = start + TASKS_PER_PAGE
    paginated = tasks[start:end]

    if not paginated:
        return "Нет задач на этой странице."

    response = f"Задачи (страница {page}):\n\n"
    for i, task in enumerate(paginated, start + 1):
        response += f"{i}. <b>{task['name']}</b>\n   {task['description']}\n\n"
    return response

# --- Команды ---
@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        bot.send_message(
            chat_id=message.chat.id,
            text="Привет✌️ Выберите действие:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"[ERROR] Не удалось отправить меню: {e}")

@bot.message_handler(commands=['show'])
def show_tasks(message):
    user_id = message.from_user.id
    if user_id not in USER_TASKS:
        load_user_tasks(user_id)

    try:
        tasks = USER_TASKS[user_id]
        if tasks:
            response = "Ваши задачи:\n\n"
            for i, task in enumerate(tasks, 1):
                response += f"{i}. {task['name']}\n   {task['description']}\n\n"
        else:
            response = "Список задач пуст."
        bot.send_message(
            message.chat.id,
            response,
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в show_tasks: {e}")

@bot.message_handler(commands=['next'])
def show_next_page(message):
    try:
        user_id = message.from_user.id
        if user_id not in USER_TASKS:
            load_user_tasks(user_id)
        tasks = USER_TASKS[user_id]

        if not tasks:
            bot.send_message(message.chat.id, "Список задач пуст.")
            return

        state = get_user_state(user_id)
        current_page = state.get('show_page', 1)
        next_page = current_page + 1

        if next_page > (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE:
            bot.send_message(message.chat.id, "Это последняя страница.")
            return

        response = format_tasks_page(tasks, next_page)
        if len(tasks) > next_page * TASKS_PER_PAGE:
            response += "\n🔽 Используйте /next для следующей страницы"

        bot.send_message(
            message.chat.id,
            response,
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )
        set_user_state(user_id, {'show_page': next_page})
    except Exception as e:
        logger.error(f"Ошибка в show_next_page: {e}")

@bot.message_handler(func=lambda message: message.text == "🔹 О боте")
def info_about(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Этот бот помогает управлять вашими задачами. "
              "Вы можете создавать, просматривать и удалять задачи.",
        reply_markup=get_info_menu()  # Остаёмся в подменю
    )

@bot.message_handler(func=lambda message: message.text == "🔹 Автор")
def info_author(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Разработчик: Илья Маклаков\n"
              "Контакты: @boy_161",
        reply_markup=get_info_menu()
    )

@bot.message_handler(func=lambda message: message.text == "🔹 Версия")
def info_version(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Версия бота: 0.0.1\n"
              "Дата релиза: 03.12.2025",
        reply_markup=get_info_menu()
    )

@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def help_command(message):
    bot.send_message(
        message.chat.id,
        "🛠 *Команды бота:*\n"
        "/start — запустить\n"
        "/show — показать задачи\n"
        "/create — создать задачу\n"
        "/delete — удалить задачу\n"
        "/next — следующая страница\n"
        "/help — эта справка\n\n"
        "🔘 *Кнопки меню:*\n"
        "👀 Информация — о боте и авторе\n"
        "📅 Создать задачу — ввод новой задачи\n"
        "📋 Показать задачи — просмотр списка\n"
        "🗑️ Удалить задачу — выбор для удаления\n"
        "❓ Помощь — эта страница\n"
        "⬅️ Назад — возврат в главное меню",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text and m.text.startswith("🗑️ Удалить №"))
def delete_task_by_button(message):
    try:
        text = message.text
        num_str = text.split("№")[1].split(":")[0]
        num = int(num_str) - 1  # перевод в индекс списка

        user_id = message.from_user.id
        if user_id not in USER_TASKS:
            load_user_tasks(user_id)
        tasks = USER_TASKS[user_id]

        if num < 0 or num >= len(tasks):
            bot.send_message(
                message.chat.id,
                "Неверный номер задачи.",
                reply_markup=get_main_menu()
            )
            return

        tasks.pop(num)
        save_user_tasks(user_id)
        bot.send_message(
            message.chat.id,
            "Задача удалена!",
            reply_markup=get_main_menu()
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Не удалось определить номер задачи.",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи: {e}")


@bot.message_handler(commands=["create"])
def create_task(message):
    user_id = message.from_user.id
    if user_id not in USER_TASKS:
        load_user_tasks(user_id)

    try:
        msg = bot.send_message(
            message.chat.id,
            "Введите название задачи:",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_task_name, user_id)
    except Exception as e:
        logger.error(f"Ошибка в create_task: {e}")

def process_task_name(message, user_id):
    if not message.text:
        bot.send_message(
            message.chat.id,
            "Название задачи не может быть пустым!",
            reply_markup=get_main_menu()
        )
        return

    task_name = message.text
    msg = bot.send_message(
        message.chat.id,
        "Введите описание задачи:",
        reply_markup=ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_task_desc, user_id, task_name)

def process_task_desc(message, user_id, task_name):
    if not message.text:
        bot.send_message(
            message.chat.id,
            "Описание задачи не может быть пустым!",
            reply_markup=get_main_menu()
        )
        return

    task_desc = message.text
    # Добавляем задачу в персональный список пользователя
    USER_TASKS[user_id].append({
        'name': task_name,
        'description': task_desc
    })
    save_user_tasks(user_id)  # Сохраняем только его задачи
    bot.send_message(
        message.chat.id,
        "Задача создана!",
        reply_markup=get_main_menu()
    )


@bot.message_handler(commands=["delete"])
def delete_task(message):
    user_id = message.from_user.id
    if user_id not in USER_TASKS:
        load_user_tasks(user_id)

    try:
        tasks = USER_TASKS[user_id]
        if not tasks:
            bot.send_message(
                message.chat.id,
                "Список задач пуст.",
                reply_markup=get_main_menu()
            )
            return
        # Показываем клавиатуру с кнопками удаления
        bot.send_message(
            message.chat.id,
            "Выберите задачу для удаления:",
            reply_markup=get_tasks_keyboard(tasks)
        )
    except Exception as e:
        logger.error(f"Ошибка в delete_task: {e}")


# --- Вспомогательные функции ---
def load_user_tasks(user_id):
    """Загружает задачи конкретного пользователя из папки tasks/"""
    filename = os.path.join(TASKS_DIR, f'tasks_{user_id}.json')
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            USER_TASKS[user_id] = json.load(f)
        logger.info(f"Задачи пользователя {user_id} загружены из {filename}")
    except FileNotFoundError:
        USER_TASKS[user_id] = []
        logger.info(f"У пользователя {user_id} нет задач (файл не найден)")
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка чтения файла {filename}: {e}")
        USER_TASKS[user_id] = []


def save_user_tasks(user_id):
    """Сохраняет задачи конкретного пользователя в папку tasks/"""
    filename = os.path.join(TASKS_DIR, f'tasks_{user_id}.json')
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(USER_TASKS[user_id], f, ensure_ascii=False, indent=2)
        logger.info(f"Задачи пользователя {user_id} сохранены в {filename}")
    except Exception as e:
        logger.error(f"Не удалось сохранить задачи пользователя {user_id}: {e}")

def show_info_menu(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Выберите раздел:",
        reply_markup=get_info_menu()  # Используем подменю из get_info_menu()
    )
@bot.message_handler(func=lambda message: message.text == "👀 Информация")
def handle_info_button(message):
    show_info_menu(message)

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def go_back(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Главное меню:",
        reply_markup=get_main_menu()
    )

def get_info_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🔹 О боте"))
    markup.add(KeyboardButton("🔹 Автор"))
    markup.add(KeyboardButton("🔹 Версия"))
    markup.add(KeyboardButton("⬅️ Назад"))
    return markup

def get_main_menu():
    """Создаёт и возвращает клавиатуру с кнопками."""
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=False
    )
    markup.add(KeyboardButton('👀 Информация'))
    markup.add(KeyboardButton('📅 Создать задачу'))
    markup.add(KeyboardButton('📋 Показать задачи'))
    markup.add(KeyboardButton('🗑️ Удалить задачу'))
    markup.add(KeyboardButton('❓ Помощь'))
    return markup
# ОБРАБОТЧИК ТЕКСТА
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text

    # Проверяем точные совпадения с кнопками (с эмодзи!)
    if text == "👀 Информация":
        show_info_menu(message)
    elif text == "📅 Создать задачу":
        create_task(message)
    elif text == "📋 Показать задачи":
        show_tasks(message)
    elif text == "🗑️ Удалить задачу":
        delete_task(message)
    elif text == "❓ Помощь":
        help_command(message)
    # Подменю информации
    elif text == "🔹 О боте":
        info_about(message)
    elif text == "🔹 Автор":
        info_author(message)
    elif text == "🔹 Версия":
        info_version(message)
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text="Неизвестная команда. Используйте кнопки ниже.",
            reply_markup=get_main_menu()
        )

# --- Запуск бота ---
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
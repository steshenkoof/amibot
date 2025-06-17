from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database import db

router = Router()

def get_main_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    """Create main keyboard with work tracking buttons"""
    from config import ADMIN_IDS
    
    keyboard = [
        [
            KeyboardButton(text="🟢 Я на работе", request_location=True),
            KeyboardButton(text="🔴 Я ухожу")
        ],
        [
            KeyboardButton(text="📊 Моя статистика"),
            KeyboardButton(text="📥 Скачать отчёт")
        ]
    ]
    
    # Add admin panel for administrators
    if user_id and user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton(text="👨‍💼 Админ панель")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    user = message.from_user
    
    # Check user status
    status = await db.get_user_status(user.id)
    
    if status == 'new':
        # New user - show registration
        registration_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📝 Зарегистрироваться")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            "👋 **Добро пожаловать в TimeTrackBot!**\n\n"
            "🎯 **Что это за бот?**\n"
            "TimeTrackBot — это корпоративная система учета рабочего времени, которая поможет вам легко отслеживать время прихода и ухода с работы.\n\n"
            "💼 **Для чего нужен?**\n"
            "• Автоматический учет рабочего времени\n"
            "• Контроль посещаемости офиса\n"
            "• Генерация отчетов для HR и зарплаты\n"
            "• Прозрачность для сотрудников и руководства\n\n"
            "🚀 **Основные возможности:**\n"
            "• 🟢 Отметка прихода с проверкой геолокации\n"
            "• 🔴 Отметка ухода с подсчетом времени\n"
            "• 📊 Персональная статистика за любой период\n"
            "• 📥 Выгрузка отчетов в Excel\n"
            "• 👨‍💼 Административная панель для управления\n\n"
            "**Для начала работы необходимо зарегистрироваться:**",
            reply_markup=registration_keyboard,
            parse_mode="Markdown"
        )
        return
    
    elif status == 'pending':
        # User waiting for approval
        await message.answer(
            "⏳ **Ваша заявка на рассмотрении**\n\n"
            "Администратор еще не одобрил вашу регистрацию.\n"
            "Пожалуйста, ожидайте подтверждения.",
            parse_mode="Markdown"
        )
        return
    
    elif status == 'blocked':
        # Blocked user can re-register
        registration_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📝 Зарегистрироваться")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "🚫 **Ваша заявка была отклонена**\n\n"
            "Вы можете повторно подать заявку на регистрацию.\n\n"
            "Пожалуйста, нажмите кнопку ниже, чтобы пройти регистрацию заново.",
            reply_markup=registration_keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Approved user - show normal interface
    welcome_text = """
🎯 **Добро пожаловать в TimeTrackBot!**

Этот бот поможет вам отслеживать рабочее время с помощью геолокации.

📋 **Как пользоваться:**

🟢 **Я на работе** - нажмите эту кнопку, когда приходите на работу
   (бот запросит вашу геолокацию для проверки)

🔴 **Я ухожу** - отметьте окончание рабочего дня

📊 **Моя статистика** - посмотрите время работы за разные периоды

📥 **Скачать отчёт** - получите Excel-файл с детальной статистикой

⚠️ **Важно:**
• Для фиксации прихода необходимо находиться в радиусе 100м от офиса
• Можно отметить приход только один раз в день
• Уход возможен только после прихода

Используйте кнопки ниже для работы с ботом! 👇
"""
    
    # Update user activity
    await db.add_or_update_user(user.id, user.username, user.full_name)
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )

@router.message(F.text == "/help")
async def help_command(message: types.Message):
    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "Если у вас возникли вопросы, проблемы или предложения — смело пишите в Telegram: <a href='https://t.me/mansklav'>@mansklav</a>\n\n"
        "Мы всегда готовы помочь!",
        parse_mode="HTML"
    )

# Удаляем этот обработчик, так как он конфликтует с другими 
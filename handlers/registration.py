from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from config import ADMIN_IDS

router = Router()

class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_phone = State()
    waiting_for_category = State()

@router.message(F.text == "📝 Зарегистрироваться")
async def start_registration(message: types.Message, state: FSMContext):
    msg = await message.answer(
        "👋 **Добро пожаловать в систему учета рабочего времени!**\n\n"
        "📝 **Шаг 1 из 4: Имя**\n\n"
        "Укажите ваше имя:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True,
            one_time_keyboard=True
        ),
        parse_mode="Markdown"
    )
    await state.set_state(Registration.waiting_for_name)

@router.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("Вы вернулись в начало регистрации.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Зарегистрироваться")]], resize_keyboard=True, one_time_keyboard=True), parse_mode="Markdown")
        await state.clear()
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(
            "❌ Имя слишком короткое. Пожалуйста, введите ваше имя (минимум 2 символа):"
        )
        return
    await state.update_data(name=name)
    await message.answer(
        f"✅ **Имя:** {name}\n\n"
        f"📝 **Шаг 2 из 4: Фамилия**\n\n"
        f"Укажите вашу фамилию:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True,
            one_time_keyboard=True
        ),
        parse_mode="Markdown"
    )
    await state.set_state(Registration.waiting_for_surname)

@router.message(Registration.waiting_for_surname)
async def process_surname(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        data = await state.get_data()
        prev_name = data.get("name", "")
        await message.answer(
            "📝 **Шаг 1 из 4: Имя**\n\n"
            "Укажите ваше имя:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Назад")]],
                resize_keyboard=True,
                one_time_keyboard=True
            ),
            parse_mode="Markdown"
        )
        await state.set_state(Registration.waiting_for_name)
        return
    surname = message.text.strip()
    if len(surname) < 2:
        await message.answer(
            "❌ Фамилия слишком короткая. Пожалуйста, введите вашу фамилию (минимум 2 символа):"
        )
        return
    await state.update_data(surname=surname)
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)], [KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        f"✅ **Фамилия:** {surname}\n\n"
        f"📝 **Шаг 3 из 4: Номер телефона**\n\n"
        f"Отправьте ваш номер телефона нажав кнопку ниже или введите вручную:",
        reply_markup=phone_keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(Registration.waiting_for_phone)

@router.message(Registration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        data = await state.get_data()
        prev_surname = data.get("surname", "")
        await message.answer(
            f"📝 **Шаг 2 из 4: Фамилия**\n\n"
            f"Укажите вашу фамилию:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Назад")]],
                resize_keyboard=True,
                one_time_keyboard=True
            ),
            parse_mode="Markdown"
        )
        await state.set_state(Registration.waiting_for_surname)
        return
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        import re
        phone_text = message.text.strip()
        if re.match(r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$', phone_text):
            phone = phone_text
        else:
            await message.answer(
                "❌ Неверный формат номера телефона.\n"
                "Введите номер в формате: +380123456789 или нажмите кнопку для автоматической отправки."
            )
            return
    else:
        await message.answer(
            "❌ Пожалуйста, отправьте номер телефона или нажмите кнопку для автоматической отправки."
        )
        return
    await state.update_data(phone=phone)
    category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🍳 Кухня", callback_data="category_кухня"),
            InlineKeyboardButton(text="🍽 Зал", callback_data="category_зал")
        ],
        [
            InlineKeyboardButton(text="🧽 Мойка", callback_data="category_мойка"),
            InlineKeyboardButton(text="🍻 Бар", callback_data="category_бар")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="category_back")
        ]
    ])
    await message.answer(
        f"✅ **Телефон:** {phone}\n\n"
        f"📝 **Шаг 4 из 4: Ваша специализация**\n\n"
        f"Выберите ваше предназначение в компании:",
        reply_markup=category_keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(Registration.waiting_for_category)

@router.callback_query(Registration.waiting_for_category, F.data == "category_back")
async def category_back_callback(callback: types.CallbackQuery, state: FSMContext):
    prev_phone = await state.get_data()
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)], [KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.edit_text(
        f"📝 **Шаг 3 из 4: Номер телефона**\n\n"
        f"Отправьте ваш номер телефона нажав кнопку ниже или введите вручную:",
        reply_markup=phone_keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(Registration.waiting_for_phone)
    await callback.answer()

@router.callback_query(Registration.waiting_for_category, F.data.startswith("category_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    """Process category selection"""
    category = callback.data.split("_")[1]
    
    # Get all data from state
    data = await state.get_data()
    name = data.get('name')
    surname = data.get('surname')
    phone = data.get('phone')
    
    user = callback.from_user
    display_name = f"{name} {surname}"
    
    # Register user with all information
    await db.register_user_extended(
        user.id,
        user.username,
        user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
        display_name,
        phone,
        category
    )
    
    # Notify admins about new registration
    await notify_admins_about_registration(
        user.id, 
        display_name, 
        user.username, 
        phone, 
        category
    )
    
    category_emoji = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    
    await callback.message.edit_text(
        f"✅ **Регистрация завершена!**\n\n"
        f"👤 **Ваши данные:**\n"
        f"• Имя: {name}\n"
        f"• Фамилия: {surname}\n"
        f"• Телефон: {phone}\n"
        f"• Специализация: {category_emoji.get(category, '👤')} {category.title()}\n\n"
        f"🙏 **Спасибо за регистрацию!**\n"
        f"⏳ Ждем одобрения от администратора.\n\n"
        f"После одобрения вы получите уведомление и сможете начать отмечать рабочее время.",
        parse_mode="Markdown"
    )
    
    await state.clear()
    await callback.answer()

async def notify_admins_about_registration(user_id: int, display_name: str, username: str, phone: str, category: str):
    """Notify admins about new registration"""
    from bot import bot  # Import bot instance
    
    category_emoji = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    
    admin_message = (
        f"🔔 **Новая регистрация**\n\n"
        f"👤 **Данные сотрудника:**\n"
        f"• Имя: {display_name}\n"
        f"• Телефон: {phone}\n"
        f"• Специализация: {category_emoji.get(category, '👤')} {category.title()}\n"
        f"• ID: {user_id}\n"
        f"• Username: @{username if username else 'не указан'}\n\n"
        f"Требуется одобрение администратора.\n\n"
        f"/start для перехода в админ панель"
    )
    
    # Send notification to all admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to notify admin {admin_id}: {e}") 
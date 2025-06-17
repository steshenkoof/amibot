from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date

from database import db
from config import ADMIN_IDS

router = Router()

class ManualEntry(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_action = State()
    waiting_for_checkin_time = State()
    waiting_for_checkout_time = State()

class UserManagement(StatesGroup):
    waiting_for_category = State()
    waiting_for_confirmation = State()
    waiting_for_search = State()

@router.message(F.text == "👨‍💼 Админ панель")
async def admin_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление сотрудниками", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 Статистика и отчёты", callback_data="admin_stats")]
    ])
    await message.answer(
        "👨‍💼 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_users")
async def show_all_users(callback: types.CallbackQuery):
    all_users = await db.get_all_users()
    if not all_users:
        await callback.message.edit_text(
            "👥 <b>Управление сотрудниками</b>\n\nНет зарегистрированных пользователей.",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    approved_users = [u for u in all_users if u['status'] == 'approved']
    pending_users = [u for u in all_users if u['status'] == 'pending']
    archived_users = [u for u in all_users if u['status'] == 'archived']
    message_text = "👥 <b>Управление сотрудниками</b>\n\n"
    if approved_users:
        message_text += f"✅ <b>Активные ({len(approved_users)}):</b>\n" + "\n".join(f"• {u['display_name'] or u['full_name'] or 'Unknown'}" for u in approved_users[:10]) + "\n\n"
    if pending_users:
        message_text += f"⏳ <b>Заявки на регистрацию ({len(pending_users)}):</b>\n" + "\n".join(f"• {u['display_name'] or u['full_name'] or 'Unknown'}" for u in pending_users[:5]) + "\n\n"
    if archived_users:
        message_text += f"🗃 <b>Архив ({len(archived_users)}):</b>\n" + "\n".join(f"• {u['display_name'] or u['full_name'] or 'Unknown'}" for u in archived_users[:5]) + "\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Обработать заявки", callback_data="admin_pending")],
        [InlineKeyboardButton(text="🗃 Архивировать сотрудника", callback_data="admin_archive_user")],
        [InlineKeyboardButton(text="🔍 Поиск сотрудника", callback_data="admin_search_user")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    msg = await callback.message.answer(message_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "admin_stats")
async def show_stats_menu(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍳 Кухня", callback_data="stats_category_кухня"),
         InlineKeyboardButton(text="🍽 Зал", callback_data="stats_category_зал")],
        [InlineKeyboardButton(text="🧽 Мойка", callback_data="stats_category_мойка"),
         InlineKeyboardButton(text="🍻 Бар", callback_data="stats_category_бар")],
        [InlineKeyboardButton(text="📅 Периоды", callback_data="admin_period_reports")],
        [InlineKeyboardButton(text="📥 Скачать Excel", callback_data="admin_report_menu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    msg = await callback.message.answer("📊 <b>Статистика и отчёты</b>\n\nВыберите действие:", reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: types.CallbackQuery):
    current_text = callback.message.text or ""
    if "Управление сотрудниками" in current_text or "Архивирование сотрудника" in current_text or "Поиск пользователя" in current_text:
        # Главное админ-меню (без кнопки 'Назад')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Управление сотрудниками", callback_data="admin_users")],
            [InlineKeyboardButton(text="📊 Статистика и отчёты", callback_data="admin_stats")]
        ])
        await callback.message.edit_text(
            "👨‍💼 <b>Панель администратора</b>\n\nВыберите раздел:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    elif "Статистика и отчёты" in current_text or "Отчеты по периодам" in current_text:
        # Главное меню статистики
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Кухня", callback_data="stats_category_кухня"),
             InlineKeyboardButton(text="🍽 Зал", callback_data="stats_category_зал")],
            [InlineKeyboardButton(text="🧽 Мойка", callback_data="stats_category_мойка"),
             InlineKeyboardButton(text="🍻 Бар", callback_data="stats_category_бар")],
            [InlineKeyboardButton(text="📅 Периоды", callback_data="admin_period_reports")],
            [InlineKeyboardButton(text="📥 Скачать Excel", callback_data="admin_report_menu")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ])
        await callback.message.edit_text(
            "📊 <b>Статистика и отчёты</b>\n\nВыберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    elif "Детальный отчет" in current_text or "ИТОГО ПО КОМПАНИИ" in current_text:
        # Возврат к выбору периода
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 За неделю", callback_data="report_period_week"),
                InlineKeyboardButton(text="📅 За 2 недели", callback_data="report_period_2weeks")
            ],
            [
                InlineKeyboardButton(text="📅 За месяц", callback_data="report_period_month"),
                InlineKeyboardButton(text="📅 Прошлый месяц", callback_data="report_period_prev_month")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_stats")
            ]
        ])
        await callback.message.edit_text(
            "📅 **Отчеты по периодам**\n\n"
            "Выберите период для детального отчета по всем категориям сотрудников:\n\n"
            "• **За неделю** - последние 7 дней\n"
            "• **За 2 недели** - последние 14 дней\n"
            "• **За месяц** - последние 30 дней\n"
            "• **Прошлый месяц** - предыдущий календарный месяц",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # По умолчанию — главное меню
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Управление сотрудниками", callback_data="admin_users")],
            [InlineKeyboardButton(text="📊 Статистика и отчёты", callback_data="admin_stats")]
        ])
        await callback.message.edit_text(
            "👨‍💼 <b>Панель администратора</b>\n\nВыберите раздел:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "admin_pending")
async def show_pending_users(callback: types.CallbackQuery):
    """Show pending registrations"""
    pending_users = await db.get_pending_users()
    
    if not pending_users:
        await callback.message.edit_text(
            "📋 **Заявки на регистрацию**\n\n"
            "Новых заявок нет."
        )
        await callback.answer()
        return
    
    message_text = "⏳ **Заявки на регистрацию**\n\n"
    keyboard_buttons = []
    
    for user in pending_users:
        user_info = f"👤 <b>{user['display_name']}</b>\n"
        user_info += f"   • ID: {user['user_id']}\n"
        user_info += f"   • Username: @{user['username'] if user['username'] else 'не указан'}\n"
        
        # Handle datetime object properly
        if user['first_seen']:
            if isinstance(user['first_seen'], str):
                date_str = user['first_seen'][:10]
            else:
                date_str = user['first_seen'].strftime('%d.%m.%Y')
        else:
            date_str = 'Неизвестно'
        
        user_info += f"   • Дата заявки: {date_str}\n\n"
        message_text += user_info
        
        # Add approve/reject buttons for each user
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"✅ Одобрить {user['display_name']}", 
                callback_data=f"approve_{user['user_id']}"
            ),
            InlineKeyboardButton(
                text=f"❌ Отклонить", 
                callback_data=f"reject_{user['user_id']}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: types.CallbackQuery):
    """Approve user registration"""
    user_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id
    
    await db.approve_user(user_id, admin_id)
    
    # Send welcome message to approved user
    try:
        from bot import bot  # Import bot instance
        await bot.send_message(
            user_id,
            "🎉 **Поздравляем!**\n\n"
            "✅ **Вы добавлены в наш дружный коллектив!**\n\n"
            "Теперь вы можете:\n"
            "• 🟢 Отмечать приход на работу\n"
            "• 🔴 Отмечать уход с работы\n"
            "• 📊 Просматривать свою статистику\n"
            "• 📥 Скачивать отчеты\n\n"
            "Используйте команду /start для начала работы!",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Failed to notify approved user {user_id}: {e}")
    
    await callback.answer("✅ Пользователь одобрен! Уведомление отправлено.", show_alert=True)
    
    # Refresh the pending list
    await show_pending_users(callback)

@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: types.CallbackQuery):
    """Reject user registration"""
    user_id = int(callback.data.split("_")[1])
    
    await db.block_user(user_id)
    
    await callback.answer("❌ Заявка отклонена", show_alert=True)
    
    # Refresh the pending list
    await show_pending_users(callback)

@router.callback_query(F.data == "admin_archive_user")
async def start_archive_user(callback: types.CallbackQuery):
    """Start user archiving process - show employees list"""
    # Получаем всех активных сотрудников по категориям
    all_users = await db.get_users_by_category(include_archived=False)
    if not all_users:
        await callback.message.edit_text(
            "🗃 **Архивирование сотрудника**\n\n"
            "❌ Нет активных сотрудников в системе.",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    # Группируем по категориям
    categories = {"кухня": [], "зал": [], "мойка": [], "бар": []}
    for user in all_users:
        category = user.get('category', 'зал')
        if category in categories:
            categories[category].append(user)
    # Клавиатура выбора сотрудников
    keyboard = []
    emoji_map = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    for category, users in categories.items():
        if users:
            keyboard.append([InlineKeyboardButton(
                text=f"{emoji_map[category]} {category.upper()} ({len(users)})",
                callback_data=f"archive_category_{category}"
            )])
            for i, user in enumerate(users[:8]):
                name = user['display_name'] or user['full_name'] or 'Unknown'
                callback_data = f"archive_select_user_{user['user_id']}"
                keyboard.append([InlineKeyboardButton(text=f"👤 {name}", callback_data=callback_data)])
            if len(users) > 8:
                keyboard.append([InlineKeyboardButton(
                    text=f"... еще {len(users) - 8} сотрудников",
                    callback_data=f"archive_show_more_{category}"
                )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.edit_text(
        "🗃 **Архивирование сотрудника**\n\n"
        "Выберите сотрудника из списка ниже. Сотрудники сгруппированы по рабочим зонам:",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("archive_category_"))
async def archive_show_category(callback: types.CallbackQuery):
    category = callback.data.split("_")[-1]
    all_users = await db.get_users_by_category(category, include_archived=False)
    if not all_users:
        await callback.answer("Нет сотрудников в этой категории")
        return
    keyboard = []
    emoji_map = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    keyboard.append([InlineKeyboardButton(
        text=f"{emoji_map[category]} ВСЕ СОТРУДНИКИ: {category.upper()}",
        callback_data=f"archive_category_{category}"
    )])
    for user in all_users:
        name = user['display_name'] or user['full_name'] or 'Unknown'
        callback_data = f"archive_select_user_{user['user_id']}"
        keyboard.append([InlineKeyboardButton(text=f"👤 {name}", callback_data=callback_data)])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_archive_user")
    ])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.edit_text(
        f"🗃 **Все сотрудники: {emoji_map[category]} {category.title()}**\n\n"
        f"Выберите сотрудника для архивирования:",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("archive_select_user_"))
async def archive_select_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    all_users = await db.get_users_by_category(include_archived=False)
    user_info = next((u for u in all_users if u['user_id'] == user_id), None)
    if not user_info:
        await callback.message.edit_text("❌ Пользователь не найден")
        await callback.answer()
        return
    user_name = user_info['display_name'] or user_info['full_name'] or f"ID: {user_id}"
    category = user_info.get('category', 'зал')
    archive_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить архивирование", callback_data=f"admin_confirm_archive_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text(
        f"🗃 **Подтверждение архивирования**\n\n"
        f"👤 Сотрудник: {user_name}\n"
        f"🆔 ID: {user_id}\n"
        f"🏷 Категория: {category}\n\n"
        f"⚠️ **Это действие:**\n"
        f"• Заблокирует доступ к боту\n"
        f"• Сохранит всю рабочую статистику\n"
        f"• Переместит сотрудника в архив\n\n"
        f"Вы уверены?",
        reply_markup=archive_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_search_user")
async def show_search_user_panel(callback: types.CallbackQuery):
    """Show search user panel"""
    await callback.message.edit_text(
        "🔍 **Поиск пользователя**\n\n"
        "Введите Telegram ID пользователя или его имя:",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(UserManagement.waiting_for_search)
async def search_user(message: types.Message):
    """Search for a user by ID or name"""
    text = message.text.strip()
    
    # Try to parse as ID
    try:
        user_id = int(text)
        user_info = await db.get_user_info(user_id)
        if user_info:
            await message.answer(
                f"👤 **Информация о пользователе**\n\n"
                f"• ID: {user_id}\n"
                f"• Имя: {user_info['display_name'] or user_info['full_name'] or 'Unknown'}\n"
                f"• Категория: {user_info.get('category', 'Неизвестно')}\n"
                f"• Статус: {user_info['status']}\n"
                f"• Последняя активность: {user_info['last_active'].strftime('%Y-%m-%d') if user_info['last_active'] else 'Никогда'}\n"
            )
        else:
            await message.answer("❌ Пользователь не найден")
    except ValueError:
        # Try to find user by name
        all_users = await db.get_all_users()
        users = []
        search_text = text.lower()
        
        # Search in display_name, full_name, and username
        for user in all_users:
            display_name = (user.get('display_name') or '').lower()
            full_name = (user.get('full_name') or '').lower()
            username = (user.get('username') or '').lower()
            
            if (search_text in display_name or 
                search_text in full_name or 
                search_text in username):
                users.append(user)
        
        if users:
            message_text = "👥 **Найденные пользователи:**\n\n"
            for user in users:
                message_text += f"• ID: {user['user_id']}\n"
                message_text += f"• Имя: {user.get('display_name') or user.get('full_name') or 'Unknown'}\n"
                message_text += f"• Категория: {user.get('category', 'Неизвестно')}\n"
                message_text += f"• Статус: {user['status']}\n"
                
                # Handle datetime properly for last_active
                if user['last_active']:
                    if isinstance(user['last_active'], str):
                        last_active = user['last_active'][:10]
                    else:
                        last_active = user['last_active'].strftime('%Y-%m-%d')
                else:
                    last_active = 'Никогда'
                    
                message_text += f"• Последняя активность: {last_active}\n\n"
            await message.answer(message_text)
        else:
            await message.answer("❌ Пользователь не найден")

@router.callback_query(F.data == "manual_checkin_time", ManualEntry.waiting_for_action)
async def manual_checkin_with_time(callback: types.CallbackQuery):
    """Start manual check-in with custom time"""
    await callback.message.edit_text(
        "🕐 **Отметка прихода с указанием времени**\n\n"
        "Введите время прихода в формате ЧЧ:ММ\n"
        "Например: `09:30` или `08:15`\n\n"
        "📅 Дата будет установлена автоматически (сегодня)",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "manual_checkout_time", ManualEntry.waiting_for_action)
async def manual_checkout_with_time(callback: types.CallbackQuery):
    """Start manual check-out with custom time"""
    await callback.message.edit_text(
        "🕐 **Отметка ухода с указанием времени**\n\n"
        "Введите время ухода в формате ЧЧ:ММ\n"
        "Например: `18:30` или `17:45`\n\n"
        "📅 Дата будет установлена автоматически (сегодня)",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(ManualEntry.waiting_for_checkin_time)
async def process_checkin_time(message: types.Message):
    """Process manual check-in with custom time"""
    time_text = message.text.strip()
    
    # Validate time format
    try:
        time_parts = time_text.split(':')
        if len(time_parts) != 2:
            raise ValueError("Invalid format")
        
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        
        if not (0 <= hours <= 23) or not (0 <= minutes <= 59):
            raise ValueError("Invalid time")
            
    except ValueError:
        await message.answer(
            "❌ **Неверный формат времени**\n\n"
            "Используйте формат ЧЧ:ММ\n"
            "Например: `09:30`, `08:15`, `10:00`",
            parse_mode="Markdown"
        )
        return
    
    data = await callback.message.bot.get_data()
    target_user_id = data['target_user_id']
    target_user_name = data['target_user_name']
    
    # Create datetime with today's date and specified time
    today = date.today()
    checkin_datetime = datetime.combine(today, datetime.strptime(time_text, '%H:%M').time())
    
    # Add custom check-in to database
    from config import OFFICE_LATITUDE, OFFICE_LONGITUDE
    success = await db.check_in_with_time(
        target_user_id,
        f"manual_{target_user_id}",
        target_user_name,
        checkin_datetime,
        OFFICE_LATITUDE, 
        OFFICE_LONGITUDE
    )
    
    if success:
        await message.answer(
            f"✅ **Приход отмечен успешно!**\n\n"
            f"👤 Сотрудник: {target_user_name}\n"
            f"📅 Дата: {today.strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {time_text}\n"
            f"📝 Отметка: Ручная (администратор)",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"⚠️ **Ошибка**\n\n"
            f"Сотрудник уже отметил приход на {today.strftime('%d.%m.%Y')}"
        )

@router.message(ManualEntry.waiting_for_checkout_time)
async def process_checkout_time(message: types.Message):
    """Process manual check-out with custom time"""
    time_text = message.text.strip()
    
    # Validate time format
    try:
        time_parts = time_text.split(':')
        if len(time_parts) != 2:
            raise ValueError("Invalid format")
        
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        
        if not (0 <= hours <= 23) or not (0 <= minutes <= 59):
            raise ValueError("Invalid time")
            
    except ValueError:
        await message.answer(
            "❌ **Неверный формат времени**\n\n"
            "Используйте формат ЧЧ:ММ\n"
            "Например: `18:30`, `17:45`, `19:00`",
            parse_mode="Markdown"
        )
        return
    
    data = await callback.message.bot.get_data()
    target_user_id = data['target_user_id']
    target_user_name = data['target_user_name']
    
    # Create datetime with today's date and specified time
    today = date.today()
    checkout_datetime = datetime.combine(today, datetime.strptime(time_text, '%H:%M').time())
    
    # Add custom check-out to database
    duration_minutes = await db.check_out_with_time(target_user_id, checkout_datetime)
    
    if duration_minutes is not None:
        from utils.excel_export import format_duration
        duration_str = format_duration(duration_minutes)
        
        await message.answer(
            f"✅ **Уход отмечен успешно!**\n\n"
            f"👤 Сотрудник: {target_user_name}\n"
            f"📅 Дата: {today.strftime('%d.%m.%Y')}\n"
            f"🕐 Время ухода: {time_text}\n"
            f"⏱ Отработано: {duration_str}\n"
            f"📝 Отметка: Ручная (администратор)",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"⚠️ **Ошибка**\n\n"
            f"Не найдено активной рабочей сессии на {today.strftime('%d.%m.%Y')}.\n"
            f"Сначала отметьте приход."
        )

@router.callback_query(F.data == "admin_manage_categories")
async def manage_categories(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🏷 Управление категориями временно недоступно.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_period_reports")
async def show_period_reports_menu(callback: types.CallbackQuery):
    """Show detailed period reports menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 За неделю", callback_data="report_period_week"),
            InlineKeyboardButton(text="📅 За 2 недели", callback_data="report_period_2weeks")
        ],
        [
            InlineKeyboardButton(text="📅 За месяц", callback_data="report_period_month"),
            InlineKeyboardButton(text="📅 Прошлый месяц", callback_data="report_period_prev_month")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_stats")
        ]
    ])
    
    await callback.message.edit_text(
        "📅 **Отчеты по периодам**\n\n"
        "Выберите период для детального отчета по всем категориям сотрудников:\n\n"
        "• **За неделю** - последние 7 дней\n"
        "• **За 2 недели** - последние 14 дней\n"
        "• **За месяц** - последние 30 дней\n"
        "• **Прошлый месяц** - предыдущий календарный месяц",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("report_period_"))
async def show_period_report(callback: types.CallbackQuery):
    """Show detailed report for specific period"""
    period_type = callback.data.split("_")[-1]
    
    from datetime import timedelta
    
    today = date.today()
    
    # Calculate date ranges
    if period_type == "week":
        start_date = today - timedelta(days=6)  # Last 7 days including today
        period_text = "за неделю"
        period_desc = f"{start_date.strftime('%d.%m')} - {today.strftime('%d.%m.%Y')}"
    elif period_type == "2weeks":
        start_date = today - timedelta(days=13)  # Last 14 days including today
        period_text = "за 2 недели" 
        period_desc = f"{start_date.strftime('%d.%m')} - {today.strftime('%d.%m.%Y')}"
    elif period_type == "month":
        start_date = today - timedelta(days=29)  # Last 30 days including today
        period_text = "за месяц"
        period_desc = f"{start_date.strftime('%d.%m')} - {today.strftime('%d.%m.%Y')}"
    elif period_type == "prev":
        # Previous calendar month
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        start_date = last_day_prev_month.replace(day=1)
        end_date = last_day_prev_month
        period_text = "прошлый месяц"
        month_names = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
            7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        period_desc = f"{month_names[start_date.month]} {start_date.year}"
    else:
        start_date = today
        end_date = today
        period_text = "сегодня"
        period_desc = today.strftime('%d.%m.%Y')
    
    # Use end_date if defined, otherwise today
    if 'end_date' not in locals():
        end_date = today
    
    # Get stats for period
    all_stats = await db.get_all_users_stats(start_date, end_date)
    
    if not all_stats:
        await callback.message.edit_text(
            f"📊 **Отчет {period_text}**\n"
            f"📅 **Период:** {period_desc}\n\n"
            f"❌ Нет данных за выбранный период",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Calculate statistics by category
    category_stats = {"кухня": {}, "зал": {}, "мойка": {}, "бар": {}}
    
    for session in all_stats:
        user_id = session['user_id']
        category = session.get('category', 'зал')
        duration = session.get('duration_minutes', 0)
        
        if category not in category_stats:
            continue
            
        if user_id not in category_stats[category]:
            category_stats[category][user_id] = {
                'name': session['full_name'] or session['username'] or 'Unknown',
                'total_minutes': 0,
                'days_worked': 0
            }
        
        if duration > 0:
            category_stats[category][user_id]['total_minutes'] += duration
            category_stats[category][user_id]['days_worked'] += 1
    
    # Format detailed report
    message_text = f"📊 **Детальный отчет {period_text}**\n"
    message_text += f"📅 **Период:** {period_desc}\n\n"
    
    emoji_map = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    
    total_company_minutes = 0
    total_company_users = 0
    
    for category, users in category_stats.items():
        if not users:
            continue
            
        category_total_minutes = sum(user['total_minutes'] for user in users.values())
        category_total_hours = category_total_minutes / 60
        
        message_text += f"\n{emoji_map[category]} **{category.upper()}** ({len(users)} чел.)\n"
        message_text += f"├─ Общее время: {category_total_hours:.1f} ч.\n"
        
        # Sort users by total time worked
        sorted_users = sorted(users.items(), key=lambda x: x[1]['total_minutes'], reverse=True)
        
        for user_id, user_data in sorted_users[:3]:  # Show top 3 workers
            hours = user_data['total_minutes'] / 60
            message_text += f"├─ **{user_data['name']}**: {hours:.1f} ч. ({user_data['days_worked']} дн.)\n"
        
        if len(sorted_users) > 3:
            message_text += f"└─ ... и еще {len(sorted_users) - 3} сотрудников\n"
        
        total_company_minutes += category_total_minutes
        total_company_users += len(users)
    
    # Company totals
    total_company_hours = total_company_minutes / 60
    avg_hours_per_user = total_company_hours / total_company_users if total_company_users > 0 else 0
    
    message_text += f"\n📈 **ИТОГО ПО КОМПАНИИ:**\n"
    message_text += f"👥 Работало сотрудников: {total_company_users}\n"
    message_text += f"⏱ Общее время: {total_company_hours:.1f} ч.\n"
    message_text += f"📊 В среднем на сотрудника: {avg_hours_per_user:.1f} ч.\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_period_reports")]
    ])
    
    await callback.message.edit_text(message_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer() 
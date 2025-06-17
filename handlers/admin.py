from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date, timedelta
import logging

from database import db
from config import ADMIN_IDS, OFFICE_LATITUDE, OFFICE_LONGITUDE
from utils.excel_export import format_duration

router = Router()
logger = logging.getLogger(__name__)

class ManualCheck(StatesGroup):
    select_user_checkin = State()
    enter_time_checkin = State()
    select_user_checkout = State()
    enter_time_checkout = State()
    waiting_for_category = State()
    waiting_for_confirmation = State()

class UserManagement(StatesGroup):
    waiting_for_category = State()
    waiting_for_confirmation = State()

async def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Returns the main admin panel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление сотрудниками", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 Статистика и отчёты", callback_data="admin_stats")],
        [
            InlineKeyboardButton(text="➕ Приход вручную", callback_data="manual_checkin_start"),
            InlineKeyboardButton(text="➖ Уход вручную", callback_data="manual_checkout_start")
        ]
    ])

@router.message(F.text == "👨‍💼 Админ панель")
async def admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    keyboard = await get_admin_panel_keyboard()
    await message.answer(
        "👨‍💼 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_back")
async def admin_back_button(callback: types.CallbackQuery, state: FSMContext):
    """Go back to main admin menu by deleting old message and sending a new one."""
    await state.clear()
    
    try:
        # Delete the message with the inline keyboard
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete message on admin_back: {e}")

    # Send a new message with the main admin panel
    keyboard = await get_admin_panel_keyboard()
    await callback.message.answer(
        "👨‍💼 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def show_employee_management_menu(callback: types.CallbackQuery, state: FSMContext):
    """Shows the main employee management menu."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Все сотрудники", callback_data="admin_all_users_status")],
        [InlineKeyboardButton(text="⏳ Обработать заявки", callback_data="admin_pending")],
        [InlineKeyboardButton(text="🗃 Архивировать сотрудника", callback_data="admin_archive_user")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(
        "👥 <b>Управление сотрудниками</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_all_users_status")
async def show_all_users_by_status(callback: types.CallbackQuery):
    """Displays a list of all approved users, grouped by department."""
    users = await db.get_users_by_status('approved')
    
    if not users:
        await callback.message.edit_text(
            "👥 <b>Все сотрудники</b>\n\nНет утвержденных сотрудников.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Группируем пользователей по категориям
    categories = {"кухня": [], "зал": [], "мойка": [], "бар": []}
    for user in users:
        category = user.get('category', 'зал')
        if category in categories:
            categories[category].append(user)
    
    message_text = "👥 <b>Все сотрудники</b>\n\n"
    emoji_map = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    
    keyboard_buttons = []
    
    for category, users_list in categories.items():
        if users_list:  # Показываем категорию только если есть сотрудники
            message_text += f"{emoji_map[category]} <b>{category.upper()}</b> ({len(users_list)})\n"
            
            for user in users_list:
                name = user['display_name'] or user['full_name'] or 'Unknown'
                user_id = user['user_id']
                
                # Проверяем статус сотрудника (на смене или нет)
                session = await db.get_today_session(user_id)
                status_emoji = "🟢" if session and session['check_in'] and not session['check_out'] else "🔴"
                
                message_text += f"{status_emoji} {name}\n"
                
                # Добавляем кнопку для каждого сотрудника
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"{status_emoji} {name}", 
                        callback_data=f"user_stats_{user_id}"
                    )
                ])
            
            message_text += "\n"
    
    # Добавляем кнопку "Назад"
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("user_stats_"))
async def show_user_detailed_stats(callback: types.CallbackQuery):
    """Показывает детальную статистику выбранного сотрудника."""
    user_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о пользователе
    user_info = await db.get_user_info(user_id)
    if not user_info:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    name = user_info['display_name'] or user_info['full_name']
    category = user_info.get('category', 'зал')
    emoji_map = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    category_emoji = emoji_map.get(category, "📋")
    
    # Получаем статистику за разные периоды
    today_stats = await db.get_user_stats(user_id, 1)
    week_stats = await db.get_user_stats(user_id, 7)
    month_stats = await db.get_user_stats(user_id, 30)
    
    # Рассчитываем общее время для каждого периода
    today_minutes = sum(session['duration_minutes'] for session in today_stats)
    week_minutes = sum(session['duration_minutes'] for session in week_stats)
    month_minutes = sum(session['duration_minutes'] for session in month_stats)
    
    # Проверяем, на смене ли сейчас сотрудник
    today_session = await db.get_today_session(user_id)
    is_active = today_session and today_session['check_in'] and not today_session['check_out']
    
    if is_active:
        status = "🟢 На смене"
        check_in_time = datetime.fromisoformat(today_session['check_in']).strftime('%H:%M')
        current_time = datetime.now()
        check_in_dt = datetime.fromisoformat(today_session['check_in'])
        current_duration = int((current_time - check_in_dt).total_seconds() / 60)
        today_minutes = current_duration  # Обновляем время сегодняшнего дня
    else:
        status = "🔴 Не на смене"
        check_in_time = None
        current_duration = 0
    
    # Формируем сообщение
    message_text = f"👤 <b>Статистика сотрудника</b>\n\n"
    message_text += f"<b>Имя:</b> {name}\n"
    message_text += f"<b>Подразделение:</b> {category_emoji} {category.upper()}\n"
    message_text += f"<b>Статус:</b> {status}\n\n"
    
    message_text += "<b>Отработано времени:</b>\n"
    message_text += f"• Сегодня: {format_duration(today_minutes)}\n"
    message_text += f"• За неделю: {format_duration(week_minutes)}\n"
    message_text += f"• За месяц: {format_duration(month_minutes)}\n\n"
    
    if is_active:
        message_text += f"<b>Текущая смена:</b>\n"
        message_text += f"• Начало: {check_in_time}\n"
        message_text += f"• Длительность: {format_duration(current_duration)}\n"
    
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку сотрудников", callback_data="admin_all_users_status")]
    ])
    
    await callback.message.edit_text(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def show_stats_menu(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍳 Кухня", callback_data="stats_category_кухня"),
         InlineKeyboardButton(text="🍽 Зал", callback_data="stats_category_зал")],
        [InlineKeyboardButton(text="🧽 Мойка", callback_data="stats_category_мойка"),
         InlineKeyboardButton(text="🍻 Бар", callback_data="stats_category_бар")],
        [InlineKeyboardButton(text="📅 Отчет за период", callback_data="admin_period_reports")],
        [InlineKeyboardButton(text="📥 Скачать полный Excel", callback_data="admin_report_menu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text("📊 <b>Статистика и отчёты</b>\n\nВыберите действие:", reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def _update_pending_list(message: types.Message):
    """Helper function to generate and display the list of pending users."""
    pending_users = await db.get_pending_users()
    
    if not pending_users:
        await message.edit_text(
            "📋 <b>Заявки на регистрацию</b>\n\nНовых заявок нет.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
            ]),
            parse_mode="HTML"
        )
        return

    message_text = "⏳ <b>Заявки на регистрацию</b>\n\nВыберите заявку для обработки:\n\n"
    keyboard_buttons = []
    
    for user in pending_users:
        user_info = (
            f"👤 <b>{user['display_name']}</b> (<i>@{user.get('username', 'N/A')}</i>)\n"
            f"   - ID: <code>{user['user_id']}</code>\n"
            f"   - Телефон: {user.get('phone', 'Не указан')}\n"
            f"   - Специализация: {user.get('category', 'Не указана').title()}\n"
        )
        message_text += user_info + "\n"
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"✅ Одобрить {user['display_name']}", callback_data=f"approve_{user['user_id']}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user['user_id']}")
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")])
    
    await message.edit_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_pending")
async def show_pending_users(callback: types.CallbackQuery):
    """Show pending registrations by calling the helper."""
    await _update_pending_list(callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: types.CallbackQuery):
    """Approve user registration"""
    user_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id
    
    await db.approve_user(user_id, admin_id)
    
    try:
        from bot import bot
        await bot.send_message(
            user_id,
            "🎉 **Поздравляем!**\n\n"
            "✅ **Вы приняты на работу!**\n\n"
            "Теперь вы можете использовать команду /start, чтобы открыть главное меню и начать отмечать рабочее время.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to notify approved user {user_id}: {e}")
    
    await callback.answer("✅ Пользователь одобрен!", show_alert=True)
    
    await _update_pending_list(callback.message)

@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: types.CallbackQuery):
    """Reject user registration"""
    user_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id
    
    await db.reject_user(user_id, admin_id)
    
    await callback.answer("❌ Пользователь отклонен", show_alert=True)
    
    await _update_pending_list(callback.message)

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
async def show_search_user_panel(callback: types.CallbackQuery, state: FSMContext):
    """Show search user panel"""
    await state.clear()  # Clear any previous states
    await callback.message.edit_text(
        "🔍 **Поиск сотрудника**\n\n"
        "Эта функция временно отключена.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

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
        message_text += f"├─ Общее время: {format_duration(category_total_minutes)}\n"
        
        # Sort users by total time worked
        sorted_users = sorted(users.items(), key=lambda x: x[1]['total_minutes'], reverse=True)
        
        for user_id, user_data in sorted_users[:3]:  # Show top 3 workers
            message_text += f"├─ **{user_data['name']}**: {format_duration(user_data['total_minutes'])} ({user_data['days_worked']} дн.)\n"
        
        if len(sorted_users) > 3:
            message_text += f"└─ ... и еще {len(sorted_users) - 3} сотрудников\n"
        
        total_company_minutes += category_total_minutes
        total_company_users += len(users)
    
    # Company totals
    avg_minutes_per_user = total_company_minutes / total_company_users if total_company_users > 0 else 0
    
    message_text += f"\n📈 **ИТОГО ПО КОМПАНИИ:**\n"
    message_text += f"👥 Работало сотрудников: {total_company_users}\n"
    message_text += f"⏱ Общее время: {format_duration(total_company_minutes)}\n"
    message_text += f"📊 В среднем на сотрудника: {format_duration(avg_minutes_per_user)}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_period_reports")]
    ])
    
    await callback.message.edit_text(message_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_all_users")
async def show_all_users_list(callback: types.CallbackQuery):
    """Show all users with their categories"""
    users = await db.get_users_by_category(include_archived=False)
    
    if not users:
        await callback.message.edit_text(
            "👥 <b>Все сотрудники</b>\n\nНет активных сотрудников.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Группируем пользователей по категориям
    categories = {"кухня": [], "зал": [], "мойка": [], "бар": []}
    for user in users:
        if user['status'] == 'approved':  # Показываем только одобренных пользователей
            category = user.get('category', 'зал')
            if category in categories:
                categories[category].append(user)
    
    message_text = "👥 <b>Все сотрудники</b>\n\n"
    emoji_map = {"кухня": "🍳", "зал": "🍽", "мойка": "🧽", "бар": "🍻"}
    
    for category, users_list in categories.items():
        if users_list:  # Показываем категорию только если есть сотрудники
            message_text += f"{emoji_map[category]} <b>{category.upper()}</b> ({len(users_list)})\n"
            for user in users_list:
                name = user['display_name'] or user['full_name'] or 'Unknown'
                message_text += f"• {name}\n"
            message_text += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ])
    
    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# --- MANUAL CHECK-IN AND CHECK-OUT FLOW ---

async def list_users_for_manual_action(callback: types.CallbackQuery, state: FSMContext, action: str):
    """Generic function to list users for manual check-in/out."""
    approved_users = await db.get_users_by_status('approved')
    if not approved_users:
        await callback.message.edit_text(
            f"Нет утвержденных сотрудников для выполнения действия.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]])
        )
        await callback.answer()
        return

    keyboard_buttons = []
    for user in approved_users:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{user['display_name'] or user['full_name']}",
                callback_data=f"manual_select_user_{action}_{user['user_id']}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    action_text = "прихода" if action == "checkin" else "ухода"
    await callback.message.edit_text(
        f"👤 Выберите сотрудника для ручной отметки {action_text}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "manual_checkin_start")
async def manual_checkin_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ManualCheck.select_user_checkin)
    await list_users_for_manual_action(callback, state, "checkin")

@router.callback_query(F.data == "manual_checkout_start")
async def manual_checkout_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ManualCheck.select_user_checkout)
    await list_users_for_manual_action(callback, state, "checkout")


@router.callback_query(F.data.startswith("manual_select_user_"))
async def manual_user_selected(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"manual_user_selected callback: {callback.data}")
    parts = callback.data.split("_")
    action = parts[3]
    user_id = int(parts[4])
    logger.info(f"Selected user_id: {user_id}, action: {action}")
    user_info = await db.get_user_info(user_id)
    if not user_info:
        logger.error(f"Failed to get user info for user_id: {user_id}")
        await callback.answer("Ошибка: информация о пользователе не найдена", show_alert=True)
        return
    user_name = user_info['display_name'] or user_info['full_name']
    logger.info(f"User name: {user_name}")

    await state.update_data(target_user_id=user_id, target_user_name=user_name)

    if action == "checkin":
        await state.set_state(ManualCheck.enter_time_checkin)
        action_text = "прихода"
    else:
        await state.set_state(ManualCheck.enter_time_checkout)
        action_text = "ухода"
        
    await callback.message.edit_text(
        f"Выбран сотрудник: <b>{user_name}</b>.\n\n"
        f"🕐 Введите время {action_text} в формате <b>ЧЧ:ММ</b> (например, 09:30).",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]])
    )
    await callback.answer()


@router.message(ManualCheck.enter_time_checkin, F.text)
async def manual_checkin_time_entered(message: types.Message, state: FSMContext):
    """Processes the manually entered check-in time."""
    data = await state.get_data()
    user_id = data.get("target_user_id")

    try:
        time_obj = datetime.strptime(message.text, "%H:%M").time()
        checkin_datetime = datetime.combine(date.today(), time_obj)
    except ValueError:
        await message.answer("❌ Неверный формат времени. Пожалуйста, введите время в формате <b>ЧЧ:ММ</b> (например, 09:30).", parse_mode="HTML")
        return

    success, result_message = await db.check_in_with_time(user_id, checkin_datetime)

    if success:
        user_info = await db.get_user_info(user_id)
        await message.answer(f"✅ Приход для сотрудника <b>{user_info['display_name']}</b> успешно зарегистрирован на {checkin_datetime.strftime('%H:%M')}.", parse_mode="HTML")
    else:
        await message.answer(f"❌ Не удалось отметить приход.\nПричина: {result_message}", parse_mode="HTML")
    
    await state.clear()


@router.message(ManualCheck.enter_time_checkout, F.text)
async def manual_checkout_time_entered(message: types.Message, state: FSMContext):
    """Processes the manually entered check-out time."""
    data = await state.get_data()
    user_id = data.get("target_user_id")

    try:
        time_obj = datetime.strptime(message.text, "%H:%M").time()
        checkout_datetime = datetime.combine(date.today(), time_obj)
    except ValueError:
        await message.answer("❌ Неверный формат времени. Пожалуйста, введите время в формате <b>ЧЧ:ММ</b> (например, 18:00).", parse_mode="HTML")
        return

    duration, result_message = await db.check_out_with_time(user_id, checkout_datetime)

    if duration is not None:
        user_info = await db.get_user_info(user_id)
        await message.answer(f"✅ Уход для сотрудника <b>{user_info['display_name']}</b> успешно зарегистрирован на {checkout_datetime.strftime('%H:%M')}.\n\n{result_message}", parse_mode="HTML")
    else:
        await message.answer(f"❌ Не удалось отметить уход.\nПричина: {result_message}", parse_mode="HTML")
        
    await state.clear() 
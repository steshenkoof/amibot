from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from datetime import datetime

from database import db
from utils.geolocation import is_within_office_radius, get_distance_to_office
from utils.excel_export import format_duration

router = Router()

@router.message(F.location)
async def handle_location_check_in(message: types.Message):
    """Handle location for check-in"""
    user = message.from_user
    location = message.location
    
    # Check if user is approved
    status = await db.get_user_status(user.id)
    if status != 'approved':
        await message.answer(
            "❌ **Доступ ограничен**\n\n"
            "Ваш аккаунт не одобрен администратором."
        )
        return
    
    # Update user info
    await db.add_or_update_user(
        user.id, 
        user.username, 
        user.full_name or f"{user.first_name} {user.last_name or ''}".strip()
    )
    
    # Check if within office radius
    if not is_within_office_radius(location.latitude, location.longitude):
        distance = get_distance_to_office(location.latitude, location.longitude)
        await message.answer(
            f"❌ **Вы находитесь вне зоны офиса**\n\n"
            f"📍 Расстояние до офиса: {distance:.0f} м\n"
            f"Для отметки прихода необходимо находиться в радиусе 100 м от офиса.",
            parse_mode="Markdown"
        )
        return
    
    # Try to check in
    success = await db.check_in(
        user.id,
        user.username or "Unknown",
        user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
        location.latitude,
        location.longitude
    )
    
    if success:
        current_time = datetime.now().strftime("%H:%M")
        await message.answer(
            f"✅ **Отмечен приход на работу!**\n\n"
            f"🕐 Время: {current_time}\n"
            f"📍 Геолокация подтверждена\n\n"
            f"Хорошего рабочего дня! 😊",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"⚠️ **Вы уже отметили приход сегодня**\n\n"
            f"Для завершения рабочего дня используйте кнопку \"🔴 Я ухожу\""
        )

@router.message(F.text == "🟢 Я на работе")
async def handle_check_in_button(message: types.Message):
    """Handle check-in button press"""
    user = message.from_user
    
    # Check if user is approved
    status = await db.get_user_status(user.id)
    if status != 'approved':
        await message.answer(
            "❌ **Доступ ограничен**\n\n"
            "Ваш аккаунт не одобрен администратором."
        )
        return
    
    # Check if already checked in today
    today_session = await db.get_today_session(user.id)
    if today_session and today_session['check_in']:
        check_in_time = datetime.fromisoformat(today_session['check_in']).strftime("%H:%M")
        await message.answer(
            f"⚠️ **Вы уже отметили приход сегодня**\n\n"
            f"🕐 Время прихода: {check_in_time}\n\n"
            f"Для завершения рабочего дня используйте кнопку \"🔴 Я ухожу\""
        )
        return
    
    # Request location
    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"📍 **Для отметки прихода отправьте свою геолокацию**\n\n"
        f"Нажмите кнопку ниже, чтобы поделиться местоположением.\n"
        f"Это необходимо для подтверждения, что вы находитесь в офисе.",
        reply_markup=location_keyboard
    )

@router.message(F.text == "🔴 Я ухожу")
async def handle_check_out(message: types.Message):
    """Handle check-out"""
    user = message.from_user
    
    # Check if user is approved
    status = await db.get_user_status(user.id)
    if status != 'approved':
        await message.answer(
            "❌ **Доступ ограничен**\n\n"
            "Ваш аккаунт не одобрен администратором."
        )
        return
    
    # Update user info
    await db.add_or_update_user(
        user.id, 
        user.username, 
        user.full_name or f"{user.first_name} {user.last_name or ''}".strip()
    )
    
    # Try to check out
    duration_minutes = await db.check_out(user.id)
    
    if duration_minutes is not None:
        current_time = datetime.now().strftime("%H:%M")
        duration_formatted = format_duration(duration_minutes)
        
        await message.answer(
            f"✅ **Отмечен уход с работы!**\n\n"
            f"🕐 Время ухода: {current_time}\n"
            f"⏱ Отработано сегодня: {duration_formatted}\n\n"
            f"До встречи завтра! 👋",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"⚠️ **Не найдено активной рабочей сессии**\n\n"
            f"Сначала отметьте приход на работу с помощью кнопки \"🟢 Я на работе\""
        )

@router.message(F.text == "🏢 Рабочее меню")
async def work_menu(message: types.Message):
    """Show work menu with location options"""
    user = message.from_user
    
    # Check if user is approved
    status = await db.get_user_status(user.id)
    if status != 'approved':
        await message.answer(
            "❌ **Доступ ограничен**\n\n"
            "Ваш аккаунт не одобрен администратором."
        )
        return
    
    keyboard = InlineKeyboardBuilder()
    
    # Check today's session to show appropriate buttons
    today_session = await db.get_today_session(user.id)
    
    if not today_session or not today_session['check_in']:
        # Can check in
        keyboard.button(text="📍 Пришел на работу", callback_data="checkin_location")
    elif today_session['check_in'] and not today_session['check_out']:
        # Can check out
        keyboard.button(text="🚪 Ушел с работы", callback_data="checkout_location")
    else:
        # Already completed today
        keyboard.button(text="✅ Рабочий день завершен", callback_data="work_completed")
    
    # Additional options
    keyboard.button(text="📊 Мой статус", callback_data="work_status")
    keyboard.button(text="📈 Быстрая статистика", callback_data="work_stats")
    
    keyboard.adjust(1, 2)
    
    await message.answer(
        "🏢 **Рабочее меню**\n\n"
        "📍 **Что это?** Дополнительные функции для отметки времени и быстрого доступа к статистике.\n\n"
        "**Возможности:**\n"
        "• Отметка прихода/ухода через инлайн-кнопки\n"
        "• Быстрый просмотр текущего статуса\n"
        "• Мгновенная статистика за сегодня\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "checkin_location")
async def checkin_location_callback(callback: types.CallbackQuery):
    """Handle check-in via inline button"""
    await callback.message.edit_text(
        "📍 **Отметка прихода**\n\n"
        "Для подтверждения прихода на работу отправьте свою геолокацию.\n\n"
        "Используйте кнопку **🟢 Я на работе** в главном меню или отправьте геолокацию вручную.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "checkout_location")
async def checkout_location_callback(callback: types.CallbackQuery):
    """Handle check-out via inline button"""
    user_id = callback.from_user.id
    
    # Try to check out
    duration_minutes = await db.check_out(user_id)
    
    if duration_minutes is not None:
        current_time = datetime.now().strftime("%H:%M")
        duration_formatted = format_duration(duration_minutes)
        
        await callback.message.edit_text(
            f"✅ **Отмечен уход с работы!**\n\n"
            f"🕐 Время ухода: {current_time}\n"
            f"⏱ Отработано сегодня: {duration_formatted}\n\n"
            f"До встречи завтра! 👋",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            f"⚠️ **Ошибка**\n\n"
            f"Не найдено активной рабочей сессии.\n"
            f"Сначала отметьте приход на работу.",
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.callback_query(F.data == "work_status")
async def work_status_callback(callback: types.CallbackQuery):
    """Show current work status"""
    user_id = callback.from_user.id
    today_session = await db.get_today_session(user_id)
    
    if not today_session:
        status_text = "📊 **Текущий статус**\n\n❌ Сегодня не отмечался"
    elif today_session['check_in'] and not today_session['check_out']:
        check_in_time = datetime.fromisoformat(today_session['check_in']).strftime('%H:%M')
        current_time = datetime.now()
        check_in_dt = datetime.fromisoformat(today_session['check_in'])
        current_duration = int((current_time - check_in_dt).total_seconds() / 60)
        
        status_text = (
            f"📊 **Текущий статус**\n\n"
            f"✅ На работе\n"
            f"🕐 Пришел: {check_in_time}\n"
            f"⏱ Уже отработано: {format_duration(current_duration)}"
        )
    else:
        check_in_time = datetime.fromisoformat(today_session['check_in']).strftime('%H:%M')
        check_out_time = datetime.fromisoformat(today_session['check_out']).strftime('%H:%M')
        
        status_text = (
            f"📊 **Текущий статус**\n\n"
            f"✅ Рабочий день завершен\n"
            f"🕐 Пришел: {check_in_time}\n"
            f"🕐 Ушел: {check_out_time}\n"
            f"⏱ Отработано: {format_duration(today_session['duration_minutes'])}"
        )
    
    await callback.message.edit_text(status_text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "work_stats")
async def work_stats_callback(callback: types.CallbackQuery):
    """Show quick work statistics"""
    user_id = callback.from_user.id
    
    # Get stats for last 7 days
    stats = await db.get_user_stats(user_id, 7)
    
    if not stats:
        await callback.message.edit_text(
            "📈 **Быстрая статистика**\n\n"
            "Данных пока нет. Начните отмечать рабочее время!"
        )
        await callback.answer()
        return
    
    # Calculate totals
    total_minutes = sum(session['duration_minutes'] for session in stats)
    total_days = len([s for s in stats if s['duration_minutes'] > 0])
    avg_minutes = total_minutes // total_days if total_days > 0 else 0
    
    stats_text = (
        f"📈 **Быстрая статистика (7 дней)**\n\n"
        f"⏱ Всего отработано: {format_duration(total_minutes)}\n"
        f"📅 Рабочих дней: {total_days}\n"
        f"📊 Среднее в день: {format_duration(avg_minutes)}\n\n"
        f"Для подробной статистики используйте **📊 Моя статистика** в главном меню."
    )
    
    await callback.message.edit_text(stats_text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "work_completed")
async def work_completed_callback(callback: types.CallbackQuery):
    """Handle completed work day"""
    await callback.message.edit_text(
        "✅ **Рабочий день завершен**\n\n"
        "Вы уже отметили приход и уход сегодня.\n"
        "Увидимся завтра! 👋",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(Command("work"))
async def work_command(message: types.Message):
    """Handle /work command - same as work menu button"""
    # Reuse the work menu function
    await work_menu(message)

# Удален автоматический обработчик регистрации - теперь используется полная 4-шаговая регистрация 
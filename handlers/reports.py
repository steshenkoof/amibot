from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from datetime import datetime, date, timedelta

from database import db
from utils.excel_export import format_duration, create_user_report, create_admin_report, cleanup_temp_file
from config import ADMIN_IDS

router = Router()

@router.message(F.text == "📊 Моя статистика")
async def show_user_stats(message: types.Message):
    """Show user statistics with period selection"""
    # Check if user is approved
    status = await db.get_user_status(message.from_user.id)
    if status != 'approved':
        await message.answer(
            "❌ **Доступ ограничен**\n\n"
            "Ваш аккаунт не одобрен администратором."
        )
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="stats_today"),
            InlineKeyboardButton(text="📅 Эта неделя", callback_data="stats_week")
        ],
        [
            InlineKeyboardButton(text="📅 Этот месяц", callback_data="stats_month"),
            InlineKeyboardButton(text="📅 Все время", callback_data="stats_all")
        ]
    ])
    
    await message.answer(
        "📊 **Выберите период для просмотра статистики:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("stats_"))
async def handle_stats_callback(callback: types.CallbackQuery):
    """Handle statistics period selection"""
    period = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # Determine number of days based on period
    if period == "today":
        days = 1
        period_name = "сегодня"
    elif period == "week":
        days = 7
        period_name = "за неделю"
    elif period == "month":
        days = 30
        period_name = "за месяц"
    else:  # all
        days = 365
        period_name = "за все время"
    
    # Get statistics
    stats = await db.get_user_stats(user_id, days)
    
    if not stats:
        await callback.message.edit_text(
            f"📊 **Статистика {period_name}**\n\n"
            f"Данных пока нет. Начните отмечать рабочее время!"
        )
        await callback.answer()
        return
    
    # Calculate totals
    total_minutes = sum(session['duration_minutes'] for session in stats)
    total_days = len([s for s in stats if s['duration_minutes'] > 0])
    avg_minutes = total_minutes // total_days if total_days > 0 else 0
    
    # Build stats message
    stats_text = f"📊 **Статистика {period_name}**\n\n"
    stats_text += f"📈 **Общая информация:**\n"
    stats_text += f"• Отработано: {format_duration(total_minutes)}\n"
    stats_text += f"• Рабочих дней: {total_days}\n"
    stats_text += f"• Среднее в день: {format_duration(avg_minutes)}\n\n"
    
    # Show recent sessions (last 5)
    if period == "today" and stats:
        session = stats[0]
        if session['check_in']:
            check_in_time = datetime.fromisoformat(session['check_in']).strftime("%H:%M")
            stats_text += f"🕐 **Сегодня:**\n"
            stats_text += f"• Приход: {check_in_time}\n"
            
            if session['check_out']:
                check_out_time = datetime.fromisoformat(session['check_out']).strftime("%H:%M")
                stats_text += f"• Уход: {check_out_time}\n"
                stats_text += f"• Отработано: {format_duration(session['duration_minutes'])}\n"
            else:
                current_time = datetime.now()
                check_in_dt = datetime.fromisoformat(session['check_in'])
                current_duration = int((current_time - check_in_dt).total_seconds() / 60)
                stats_text += f"• Сейчас на работе\n"
                stats_text += f"• Уже отработано: {format_duration(current_duration)}\n"
    else:
        stats_text += f"📋 **Последние записи:**\n"
        for session in stats[:5]:
            if session['duration_minutes'] > 0:
                date_str = session['date']
                duration_str = format_duration(session['duration_minutes'])
                stats_text += f"• {date_str}: {duration_str}\n"
    
    await callback.message.edit_text(stats_text, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text == "📥 Скачать отчёт")
async def download_report_menu(message: types.Message):
    """Show download report menu"""
    user_id = message.from_user.id
    
    # Check if user is approved
    status = await db.get_user_status(user_id)
    if status != 'approved':
        await message.answer(
            "❌ **Доступ ограничен**\n\n"
            "Ваш аккаунт не одобрен администратором."
        )
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 За неделю", callback_data="report_week"),
            InlineKeyboardButton(text="📊 За месяц", callback_data="report_month")
        ],
        [
            InlineKeyboardButton(text="📊 За все время", callback_data="report_all")
        ]
    ])
    
    # Add admin options if user is admin
    if user_id in ADMIN_IDS:
        admin_row = [
            InlineKeyboardButton(text="👥 Все сотрудники (месяц)", callback_data="admin_report_month"),
            InlineKeyboardButton(text="👥 Все сотрудники (неделя)", callback_data="admin_report_week")
        ]
        keyboard.inline_keyboard.append(admin_row)
    
    await message.answer(
        "📥 **Выберите период для отчёта:**\n\n"
        "Отчёт будет сгенерирован в формате Excel.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("report_"))
async def handle_report_callback(callback: types.CallbackQuery):
    """Handle report generation"""
    period = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user = callback.from_user
    
    await callback.message.edit_text("⏳ Генерируем отчёт...")
    
    # Determine period
    if period == "week":
        days = 7
        period_name = "неделя"
    elif period == "month":
        days = 30
        period_name = "месяц"
    else:  # all
        days = 365
        period_name = "все_время"
    
    try:
        # Get user statistics
        stats = await db.get_user_stats(user_id, days)
        
        if not stats:
            await callback.message.edit_text(
                "❌ Нет данных для создания отчёта.\n"
                "Начните отмечать рабочее время!"
            )
            await callback.answer()
            return
        
        # Generate Excel file
        username = user.username or user.first_name or "Unknown"
        file_path = create_user_report(stats, username)
        
        # Send file
        file = FSInputFile(file_path)
        filename = f"Отчет_{username}_{period_name}_{date.today().strftime('%Y%m%d')}.xlsx"
        
        await callback.message.answer_document(
            file,
            caption=f"📊 **Отчёт по рабочему времени**\n\n"
                   f"👤 Сотрудник: {user.full_name or username}\n"
                   f"📅 Период: {period_name}\n"
                   f"📄 Файл: {filename}",
            parse_mode="Markdown"
        )
        
        # Clean up
        cleanup_temp_file(file_path)
        
        await callback.message.edit_text("✅ Отчёт успешно сгенерирован!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при генерации отчёта: {str(e)}"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_report_"))
async def handle_admin_report_callback(callback: types.CallbackQuery):
    """Handle admin report generation"""
    user_id = callback.from_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await callback.answer("❌ Недостаточно прав доступа", show_alert=True)
        return
    
    period = callback.data.split("_")[2]
    
    await callback.message.edit_text("⏳ Генерируем отчёт по всем сотрудникам...")
    
    # Determine period
    if period == "week":
        days = 7
        period_name = "неделя"
    else:  # month
        days = 30
        period_name = "месяц"
    
    try:
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get all users statistics
        all_stats = await db.get_all_users_stats(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not all_stats:
            await callback.message.edit_text(
                "❌ Нет данных для создания отчёта."
            )
            await callback.answer()
            return
        
        # Generate Excel file
        file_path = create_admin_report(
            all_stats,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # Send file
        file = FSInputFile(file_path)
        filename = f"Отчет_все_сотрудники_{period_name}_{date.today().strftime('%Y%m%d')}.xlsx"
        
        await callback.message.answer_document(
            file,
            caption=f"📊 **Отчёт по всем сотрудникам**\n\n"
                   f"📅 Период: {period_name} ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})\n"
                   f"👥 Сотрудников: {len(set(s['user_id'] for s in all_stats))}\n"
                   f"📄 Файл: {filename}",
            parse_mode="Markdown"
        )
        
        # Clean up
        cleanup_temp_file(file_path)
        
        await callback.message.edit_text("✅ Отчёт успешно сгенерирован!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при генерации отчёта: {str(e)}"
        )
    
    await callback.answer() 
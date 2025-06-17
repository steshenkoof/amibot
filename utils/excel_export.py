import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import tempfile
import os

def format_duration(minutes: int) -> str:
    """Format duration from minutes to hours with decimal"""
    if minutes <= 0:
        return "0.0 ч"
    
    hours = minutes / 60
    return f"{hours:.1f} ч"

def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    if not dt_str:
        return "—"
    
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%H:%M")
    except:
        return "—"

def create_user_report(user_data: List[Dict[str, Any]], username: str = "Unknown") -> str:
    """
    Create Excel report for a single user
    
    Args:
        user_data: List of work sessions
        username: User's name
    
    Returns:
        Path to the generated Excel file
    """
    # Prepare data for Excel
    excel_data = []
    total_minutes = 0
    
    for session in user_data:
        date_str = session['date']
        check_in = format_datetime(session['check_in'])
        check_out = format_datetime(session['check_out'])
        duration_minutes = session['duration_minutes']
        duration_formatted = format_duration(duration_minutes)
        
        excel_data.append({
            'Дата': date_str,
            'Время прихода': check_in,
            'Время ухода': check_out,
            'Отработано': duration_formatted,
            'Минут': duration_minutes
        })
        
        total_minutes += duration_minutes
    
    # Create DataFrame
    df = pd.DataFrame(excel_data)
    
    # Add summary row
    if excel_data:
        summary_row = {
            'Дата': 'ИТОГО:',
            'Время прихода': '',
            'Время ухода': '',
            'Отработано': format_duration(total_minutes),
            'Минут': total_minutes
        }
        # Add empty row and summary
        df = pd.concat([df, pd.DataFrame([{}]), pd.DataFrame([summary_row])], ignore_index=True)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_file.close()
    
    # Write to Excel with formatting
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Отчет_{username}', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[f'Отчет_{username}']
        
        # Format columns
        worksheet.column_dimensions['A'].width = 12  # Дата
        worksheet.column_dimensions['B'].width = 15  # Время прихода
        worksheet.column_dimensions['C'].width = 15  # Время ухода
        worksheet.column_dimensions['D'].width = 15  # Отработано
        worksheet.column_dimensions['E'].width = 10  # Минут
        
        # Bold header
        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
        
        # Bold summary row if exists
        if len(df) > 1:
            for cell in worksheet[len(df)]:
                if cell.value:
                    cell.font = cell.font.copy(bold=True)
    
    return temp_file.name

def create_admin_report(all_users_data: List[Dict[str, Any]], start_date: str, end_date: str) -> str:
    """
    Create Excel report for all users (admin view)
    
    Args:
        all_users_data: List of all users' work sessions
        start_date: Start date for the report
        end_date: End date for the report
    
    Returns:
        Path to the generated Excel file
    """
    # Prepare data for Excel
    excel_data = []
    
    for session in all_users_data:
        date_str = session['date']
        username = session['username']
        full_name = session['full_name']
        check_in = format_datetime(session['check_in'])
        check_out = format_datetime(session['check_out'])
        duration_minutes = session['duration_minutes']
        duration_formatted = format_duration(duration_minutes)
        
        excel_data.append({
            'Дата': date_str,
            'Сотрудник': full_name,
            'Username': username,
            'Время прихода': check_in,
            'Время ухода': check_out,
            'Отработано': duration_formatted,
            'Минут': duration_minutes
        })
    
    # Create DataFrame
    df = pd.DataFrame(excel_data)
    
    # Sort by date and user
    if not df.empty:
        df = df.sort_values(['Дата', 'Сотрудник'], ascending=[False, True])
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_file.close()
    
    # Write to Excel with formatting
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        sheet_name = f'Отчет_{start_date}_{end_date}'
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Format columns
        worksheet.column_dimensions['A'].width = 12  # Дата
        worksheet.column_dimensions['B'].width = 20  # Сотрудник
        worksheet.column_dimensions['C'].width = 15  # Username
        worksheet.column_dimensions['D'].width = 15  # Время прихода
        worksheet.column_dimensions['E'].width = 15  # Время ухода
        worksheet.column_dimensions['F'].width = 15  # Отработано
        worksheet.column_dimensions['G'].width = 10  # Минут
        
        # Bold header
        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
    
    return temp_file.name

def cleanup_temp_file(file_path: str):
    """Remove temporary file"""
    try:
        os.unlink(file_path)
    except:
        pass 
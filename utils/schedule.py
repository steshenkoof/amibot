import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

class ScheduleManager:
    """Class for managing employee schedules from Google Sheets."""
    
    def __init__(self, credentials_file=None):
        """Initialize the ScheduleManager with Google API credentials."""
        self.spreadsheet_url = "https://docs.google.com/spreadsheets/d/1Q2VS93-SsCwPCstV7cd3aVTZnf1gjJMB/edit?rtpof=true&sd=true&gid=1382745480#gid=1382745480"
        self.credentials_file = credentials_file
        self.client = None
        self.cached_data = None
        self.last_update = None
        
    async def setup(self):
        """Setup the Google Sheets connection."""
        try:
            # Use service account or direct auth
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            
            if self.credentials_file and os.path.exists(self.credentials_file):
                credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, scope)
                self.client = gspread.authorize(credentials)
                logger.info("Connected to Google Sheets using service account")
            else:
                # For development, we'll provide a direct link
                logger.warning("No credentials file found, using public URL only")
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets connection: {e}")
            return False
            
    def get_schedule_url(self):
        """Return the URL to the schedule spreadsheet."""
        return self.spreadsheet_url
    
    async def get_all_schedule_data(self, force_refresh=False):
        """Get all schedule data from the spreadsheet.
        
        Args:
            force_refresh: Whether to force a refresh of the data
            
        Returns:
            Dictionary with all schedule data
        """
        # Check if we have cached data and it's not too old
        current_time = datetime.now()
        if self.cached_data and self.last_update and not force_refresh:
            # Use cache if it's less than 1 hour old
            time_diff = (current_time - self.last_update).total_seconds() / 3600
            if time_diff < 1:
                return self.cached_data
        
        try:
            # For now, we'll create a mock data structure since we don't have actual access
            # In a real implementation, this would fetch data from Google Sheets
            
            # Mock data based on the spreadsheet structure we saw
            departments = {
                "kitchen": {
                    "name": "Кухня",
                    "employees": [
                        {"name": "Воронин Артем", "position": "Шеф-повар", "schedule": {1: "1", 2: "1", 3: "1", 4: "1", 5: "1"}},
                        {"name": "Ефимова Наталья", "position": "Шеф-повар", "schedule": {1: "1", 2: "1", 3: "1", 4: "1", 5: "1"}},
                        {"name": "Миронов Максим", "position": "Су-шеф", "schedule": {1: "10", 2: "10", 3: "10", 4: "10", 5: "10"}}
                    ]
                },
                "hall": {
                    "name": "Зал",
                    "employees": [
                        {"name": "Петров Иван", "position": "Менеджер зала", "schedule": {1: "12", 2: "12", 3: "12", 4: "12", 5: "12"}},
                        {"name": "Сидорова Анна", "position": "Официант", "schedule": {1: "8", 2: "8", 3: "8", 4: "8", 5: "8"}}
                    ]
                },
                "bar": {
                    "name": "Бар",
                    "employees": [
                        {"name": "Кузнецов Алексей", "position": "Бармен", "schedule": {1: "10", 2: "10", 3: "10", 4: "10", 5: "10"}}
                    ]
                }
            }
            
            self.cached_data = departments
            self.last_update = current_time
            return departments
        except Exception as e:
            logger.error(f"Error getting all schedule data: {e}")
            return None
        
    async def get_employee_schedule(self, employee_name):
        """Get the schedule for a specific employee.
        
        Args:
            employee_name: Full name or part of the name of the employee
            
        Returns:
            Dictionary with schedule information or None if not found
        """
        departments = await self.get_all_schedule_data()
        if not departments:
            return None
        
        # Search for employee in all departments
        for dept_key, dept in departments.items():
            for emp in dept["employees"]:
                if employee_name.lower() in emp["name"].lower():
                    return {
                        "name": emp["name"],
                        "position": emp["position"],
                        "department": dept["name"],
                        "schedule": emp["schedule"]
                    }
        
        return None
    
    async def format_department_schedule(self, department_key):
        """Format a department's schedule for display in Telegram.
        
        Args:
            department_key: Key of the department to format
            
        Returns:
            Formatted text for Telegram message
        """
        departments = await self.get_all_schedule_data()
        if not departments or department_key not in departments:
            return "Расписание не найдено"
        
        dept = departments[department_key]
        current_day = datetime.now().day
        
        # Format header
        text = f"📅 *График смен: {dept['name']}*\n\n"
        
        # Add employees
        for emp in dept["employees"]:
            text += f"👤 *{emp['name']}* - {emp['position']}\n"
            
            # Add schedule for next 7 days starting from today
            text += "📆 График на ближайшие дни:\n"
            for day in range(current_day, current_day + 7):
                if day in emp["schedule"]:
                    hours = emp["schedule"][day]
                    text += f"   • День {day}: {hours} ч.\n"
            
            text += "\n"
        
        return text
    
    async def format_employee_schedule(self, employee_name):
        """Format an employee's schedule for display in Telegram.
        
        Args:
            employee_name: Name of the employee
            
        Returns:
            Formatted text for Telegram message
        """
        employee = await self.get_employee_schedule(employee_name)
        if not employee:
            return f"График для сотрудника '{employee_name}' не найден"
        
        current_day = datetime.now().day
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Format header
        text = f"📅 *График смен: {employee['name']}*\n"
        text += f"🏢 Должность: {employee['position']}\n"
        text += f"🏬 Отдел: {employee['department']}\n\n"
        
        # Add schedule for current month
        text += f"📆 *График на {current_month}.{current_year}:*\n\n"
        
        # Find upcoming work days
        upcoming_days = []
        for day, hours in sorted(employee["schedule"].items()):
            if int(day) >= current_day:
                upcoming_days.append((int(day), hours))
        
        # Show upcoming work days
        if upcoming_days:
            text += "🔜 *Предстоящие рабочие дни:*\n"
            for day, hours in upcoming_days:
                # Format date properly
                work_date = date(current_year, current_month, day)
                day_name = work_date.strftime("%a").capitalize()  # Short day name
                text += f"   • {day} {current_month} ({day_name}): {hours} ч.\n"
            text += "\n"
        else:
            text += "✅ *На этот месяц больше нет запланированных смен*\n\n"
        
        # Group by weeks for full schedule
        text += "*Полный график месяца:*\n"
        weeks = {}
        for day, hours in employee["schedule"].items():
            week_num = (int(day) - 1) // 7 + 1
            if week_num not in weeks:
                weeks[week_num] = []
            weeks[week_num].append((int(day), hours))
        
        # Format by weeks
        for week_num, days in sorted(weeks.items()):
            text += f"Неделя {week_num}:\n"
            for day, hours in sorted(days):
                # Highlight current day
                prefix = "➡️ " if day == current_day else "   • "
                text += f"{prefix}День {day}: {hours} ч.\n"
            text += "\n"
        
        # Add total hours
        total_hours = sum(float(hours) for hours in employee["schedule"].values())
        text += f"⏱ *Всего часов в месяц: {total_hours}*\n"
        
        return text

# Initialize the schedule manager
schedule_manager = ScheduleManager() 
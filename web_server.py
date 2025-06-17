#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from aiohttp import web, web_request
from aiohttp.web_response import Response


# Import database
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def serve_web_app(request):
    """Serve the web location app"""
    try:
        html_file = Path("web_location.html")
        if html_file.exists():
            return web.FileResponse(html_file)
        else:
            return web.Response(text="Web app not found", status=404)
    except Exception as e:
        logger.error(f"Error serving web app: {e}")
        return web.Response(text="Server error", status=500)

async def handle_location_data(request):
    """Handle location data from web app"""
    try:
        data = await request.json()
        
        user_id = data.get('user_id')
        user_name = data.get('user_name', 'Unknown')
        action_type = data.get('type')  # 'check_in' or 'check_out'
        
        if not user_id or not action_type:
            return web.json_response(
                {'error': 'Missing required fields'}, 
                status=400
            )
        
        # Подготавливаем данные для сохранения
        location_data = {
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'accuracy': data.get('accuracy'),
            'altitude': data.get('altitude'),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'network_info': data.get('networkInfo', {}),
            'high_accuracy': True  # Маркер высокоточной геолокации
        }
        
        # Сохраняем в базу данных
        if action_type == 'check_in':
            result = await handle_check_in(user_id, user_name, location_data)
        elif action_type == 'check_out':
            result = await handle_check_out(user_id, user_name, location_data)
        else:
            return web.json_response(
                {'error': 'Invalid action type'}, 
                status=400
            )
        
        return web.json_response({
            'success': True,
            'message': result.get('message', 'Success'),
            'data': result
        })
        
    except json.JSONDecodeError:
        return web.json_response(
            {'error': 'Invalid JSON'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error handling location data: {e}")
        return web.json_response(
            {'error': 'Server error'}, 
            status=500
        )

async def handle_check_in(user_id: int, user_name: str, location_data: dict):
    """Handle check-in with high accuracy location"""
    try:
        # Проверяем, есть ли уже активная сессия
        active_session = await db.get_active_session(user_id)
        if active_session:
            return {
                'success': False,
                'message': 'У вас уже есть активная рабочая сессия'
            }
        
        # Создаем новую сессию
        session_id = await db.start_work_session(
            user_id=user_id,
            username=user_name,
            location_lat=location_data.get('latitude'),
            location_lon=location_data.get('longitude'),
            extra_data=json.dumps({
                'accuracy': location_data.get('accuracy'),
                'altitude': location_data.get('altitude'),
                'network_info': location_data.get('network_info'),
                'high_accuracy': True,
                'timestamp': location_data.get('timestamp')
            })
        )
        
        return {
            'success': True,
            'message': f'Приход на работу отмечен! (Точность: ±{int(location_data.get("accuracy", 0))}м)',
            'session_id': session_id,
            'location': {
                'lat': location_data.get('latitude'),
                'lon': location_data.get('longitude'),
                'accuracy': location_data.get('accuracy')
            }
        }
        
    except Exception as e:
        logger.error(f"Error in check-in: {e}")
        return {
            'success': False,
            'message': f'Ошибка при отметке прихода: {str(e)}'
        }

async def handle_check_out(user_id: int, user_name: str, location_data: dict):
    """Handle check-out with high accuracy location"""
    try:
        # Проверяем активную сессию
        active_session = await db.get_active_session(user_id)
        if not active_session:
            return {
                'success': False,
                'message': 'Не найдено активной рабочей сессии'
            }
        
        # Заканчиваем сессию
        duration = await db.end_work_session(
            user_id=user_id,
            location_lat=location_data.get('latitude'),
            location_lon=location_data.get('longitude'),
            extra_data=json.dumps({
                'accuracy': location_data.get('accuracy'),
                'altitude': location_data.get('altitude'),
                'network_info': location_data.get('network_info'),
                'high_accuracy': True,
                'timestamp': location_data.get('timestamp')
            })
        )
        
        hours = duration // 60
        minutes = duration % 60
        
        return {
            'success': True,
            'message': f'Уход с работы отмечен! Отработано: {hours}ч {minutes}м (Точность: ±{int(location_data.get("accuracy", 0))}м)',
            'duration': duration,
            'location': {
                'lat': location_data.get('latitude'),
                'lon': location_data.get('longitude'),
                'accuracy': location_data.get('accuracy')
            }
        }
        
    except Exception as e:
        logger.error(f"Error in check-out: {e}")
        return {
            'success': False,
            'message': f'Ошибка при отметке ухода: {str(e)}'
        }

async def get_location_stats(request):
    """Get location statistics"""
    try:
        user_id = request.query.get('user_id')
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        # Получаем статистику пользователя
        stats = await db.get_user_stats(int(user_id))
        
        return web.json_response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return web.json_response({'error': 'Server error'}, status=500)

def setup_routes(app):
    """Setup web routes"""
    # Статические файлы
    app.router.add_get('/web_location.html', serve_web_app)
    
    # API endpoints
    app.router.add_post('/api/location', handle_location_data)
    app.router.add_get('/api/stats', get_location_stats)
    
    # CORS headers для всех ответов
    async def add_cors_headers(request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    app.middlewares.append(add_cors_headers)

async def create_app():
    """Create and configure web application"""
    app = web.Application()
    setup_routes(app)
    return app

async def start_web_server():
    """Start the web server"""
    try:
        # Инициализируем базу данных
        await db.init_db()
        
        # Создаем приложение
        app = await create_app()
        
        # Запускаем сервер
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', 8000)
        await site.start()
        
        logger.info("🌐 Web server started at http://localhost:8000")
        logger.info("📱 Web App URL: http://localhost:8000/web_location.html")
        
        # Ждем бесконечно
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Error starting web server: {e}")

if __name__ == "__main__":
    asyncio.run(start_web_server()) 
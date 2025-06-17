#!/usr/bin/env python3
import qrcode
import uuid
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class QRLocationSystem:
    """System for QR-based location verification"""
    
    def __init__(self):
        self.active_codes: Dict[str, dict] = {}
        self.location_codes: Dict[str, dict] = {}
    
    def generate_location_qr(self, location_name: str, latitude: float, longitude: float, valid_hours: int = 24) -> tuple:
        """Generate QR code for specific location"""
        try:
            # Создаем уникальный код
            location_id = str(uuid.uuid4())[:8]
            
            # Информация о локации
            location_data = {
                'location_id': location_id,
                'location_name': location_name,
                'latitude': latitude,
                'longitude': longitude,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=valid_hours)).isoformat(),
                'type': 'location_qr'
            }
            
            # Сохраняем код
            self.location_codes[location_id] = location_data
            
            # Создаем QR код
            qr_data = json.dumps({
                'type': 'work_location',
                'location_id': location_id,
                'location_name': location_name
            })
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Создаем изображение
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Конвертируем в байты
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer, location_id, location_data
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None, None, None
    
    def generate_daily_qr(self, date: str = None) -> tuple:
        """Generate daily QR code that changes every day"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Создаем код на основе даты
            daily_id = f"daily_{date}_{str(uuid.uuid4())[:6]}"
            
            # Информация о дневном коде
            daily_data = {
                'daily_id': daily_id,
                'date': date,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=1)).isoformat(),
                'type': 'daily_qr'
            }
            
            # Сохраняем код
            self.active_codes[daily_id] = daily_data
            
            # Создаем QR код
            qr_data = json.dumps({
                'type': 'daily_work',
                'daily_id': daily_id,
                'date': date
            })
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Создаем изображение
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Конвертируем в байты
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer, daily_id, daily_data
            
        except Exception as e:
            logger.error(f"Error generating daily QR code: {e}")
            return None, None, None
    
    def verify_qr_code(self, qr_data: str) -> Optional[dict]:
        """Verify QR code and return location info"""
        try:
            data = json.loads(qr_data)
            
            if data.get('type') == 'work_location':
                location_id = data.get('location_id')
                if location_id in self.location_codes:
                    location_info = self.location_codes[location_id]
                    
                    # Проверяем срок действия
                    expires_at = datetime.fromisoformat(location_info['expires_at'])
                    if datetime.now() > expires_at:
                        return {'error': 'QR код истек'}
                    
                    return {
                        'type': 'location',
                        'valid': True,
                        'location_name': location_info['location_name'],
                        'latitude': location_info['latitude'],
                        'longitude': location_info['longitude'],
                        'location_id': location_id
                    }
                else:
                    return {'error': 'Неверный QR код'}
            
            elif data.get('type') == 'daily_work':
                daily_id = data.get('daily_id')
                if daily_id in self.active_codes:
                    daily_info = self.active_codes[daily_id]
                    
                    # Проверяем срок действия
                    expires_at = datetime.fromisoformat(daily_info['expires_at'])
                    if datetime.now() > expires_at:
                        return {'error': 'QR код истек'}
                    
                    return {
                        'type': 'daily',
                        'valid': True,
                        'date': daily_info['date'],
                        'daily_id': daily_id
                    }
                else:
                    return {'error': 'Неверный QR код'}
            
            else:
                return {'error': 'Неизвестный тип QR кода'}
                
        except json.JSONDecodeError:
            return {'error': 'Неверный формат QR кода'}
        except Exception as e:
            logger.error(f"Error verifying QR code: {e}")
            return {'error': f'Ошибка проверки: {str(e)}'}
    
    def cleanup_expired_codes(self):
        """Remove expired QR codes"""
        try:
            now = datetime.now()
            
            # Очищаем локационные коды
            expired_location_codes = []
            for location_id, data in self.location_codes.items():
                expires_at = datetime.fromisoformat(data['expires_at'])
                if now > expires_at:
                    expired_location_codes.append(location_id)
            
            for location_id in expired_location_codes:
                del self.location_codes[location_id]
            
            # Очищаем дневные коды
            expired_daily_codes = []
            for daily_id, data in self.active_codes.items():
                expires_at = datetime.fromisoformat(data['expires_at'])
                if now > expires_at:
                    expired_daily_codes.append(daily_id)
            
            for daily_id in expired_daily_codes:
                del self.active_codes[daily_id]
            
            if expired_location_codes or expired_daily_codes:
                logger.info(f"Cleaned up {len(expired_location_codes)} location codes and {len(expired_daily_codes)} daily codes")
                
        except Exception as e:
            logger.error(f"Error cleaning up codes: {e}")

# Глобальный экземпляр системы QR
qr_system = QRLocationSystem() 
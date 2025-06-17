import asyncio
import aiohttp
from config import BOT_TOKEN

async def clear_webhook():
    """Clear webhook for the bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"drop_pending_updates": True}) as response:
            result = await response.json()
            print(f"Webhook clearing result: {result}")
            
        # Get webhook info
        info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        async with session.get(info_url) as response:
            info = await response.json()
            print(f"Current webhook info: {info}")

if __name__ == "__main__":
    asyncio.run(clear_webhook()) 
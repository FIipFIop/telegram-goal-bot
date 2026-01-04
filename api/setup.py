"""
Setup endpoint to configure Telegram webhook.
Visit this URL once after deployment to set up the webhook.
"""

from telegram import Bot
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


async def handler(request):
    """
    Set up the Telegram webhook.

    Visit: https://your-app.vercel.app/api/setup
    """
    try:
        # Get the webhook URL from request or environment
        webhook_url = f"https://{request.headers.get('host', '')}/api/webhook"

        # Create bot instance
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        # Set webhook
        await bot.initialize()
        result = await bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"]
        )
        await bot.shutdown()

        if result:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "success",
                    "webhook_url": webhook_url,
                    "message": "Webhook set successfully!"
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "status": "error",
                    "message": "Failed to set webhook"
                })
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }


# Vercel entry point
def vercel_handler(request):
    """Synchronous wrapper for Vercel."""
    import asyncio
    return asyncio.run(handler(request))

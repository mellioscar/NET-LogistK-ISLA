from firebase_admin import messaging
import asyncio

class NotificationService:
    @staticmethod
    async def send_notification(token: str, title: str, body: str):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token
        )
        
        return await messaging.send(message)

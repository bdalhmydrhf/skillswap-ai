# core/tasks.py - النسخة الصحيحة
"""
مهام Celery غير المتزامنة للنظام
"""

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def retry_failed_message(self, message_id: int, delay_seconds: int = 30):
    """
    إعادة محاولة إرسال رسالة فشلت بسبب Rate Limit
    """
    import time
    time.sleep(delay_seconds)
    
    try:
        ChatMessage = apps.get_model('core', 'ChatMessage')
        ChatRoom = apps.get_model('core', 'ChatRoom')
        
        message = ChatMessage.objects.select_related('room', 'sender').get(id=message_id)
        
        from core.models.chat import can_send_message
        allowed, stats = can_send_message(message.sender.id, message.room.id)
        
        if allowed:
            from core.models.chat import async_send_realtime_message
            async_send_realtime_message.delay(message.id, message.idempotency_key)
            logger.info(f"✅ Retried message {message_id} successfully")
        else:
            new_delay = min(delay_seconds * 2, 3600)
            self.retry(countdown=new_delay)
            logger.info(f"⏳ Message {message_id} still rate limited, retrying in {new_delay}s")
            
    except ChatMessage.DoesNotExist:
        logger.error(f"❌ Message {message_id} not found")
    except Exception as e:
        logger.error(f"❌ Failed to retry message {message_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def cleanup_expired_chat_rooms(days: int = 30):
    """تنظيف غرف الدردشة القديمة"""
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    ChatRoom = apps.get_model('core', 'ChatRoom')
    deleted_count = ChatRoom.objects.filter(
        last_activity__lt=cutoff_date,
        is_active=True
    ).update(is_active=False)
    
    logger.info(f"🗑️ Cleaned up {deleted_count} expired chat rooms")
    return deleted_count


@shared_task
def update_room_last_activity(room_id: int):
    """تحديث آخر نشاط في الغرفة"""
    ChatRoom = apps.get_model('core', 'ChatRoom')
    ChatRoom.objects.filter(id=room_id).update(last_activity=timezone.now())


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def async_send_realtime_message(self, message_id: int, idempotency_key: str = None):
    """إرسال رسالة في الوقت الفعلي عبر WebSocket"""
    try:
        from core.models.chat import ChatMessage
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        message = ChatMessage.objects.select_related('room', 'sender').get(id=message_id)
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f'chat_{message.room.id}',
            {
                'type': 'chat_message',
                'message_id': message.id,
                'room_id': message.room.id,
                'sender_id': message.sender.id,
                'sender_name': message.sender.username,
                'message': message.text,
                'created_at': message.created_at.isoformat(),
            }
        )
        
        message.status = 'delivered'
        message.save(update_fields=['status'])
        
    except Exception as e:
        raise self.retry(exc=e, countdown=5)
    
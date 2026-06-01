# core/routing.py
import re
import logging
from django.urls import re_path
from . import consumers

logger = logging.getLogger(__name__)

# ✅ UUID pattern (RFC 4122)
UUID_PATTERN = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

# ✅ Room name pattern (للتوافق مع الخلفية)
ROOM_NAME_PATTERN = r'[\w\-@.]{1,100}'

websocket_urlpatterns = [
    # ✅ الطريقة 1: اتصال باستخدام UUID (الأساسية)
    re_path(
        rf"^ws/v1/chat/uuid/(?P<room_uuid>{UUID_PATTERN})/$",
        consumers.ChatConsumer.as_asgi(),
        name="chat_room_by_uuid"
    ),
    
    # ✅ الطريقة 2: اتصال باستخدام Room Name (للتوافق العكسي)
    re_path(
        rf"^ws/v1/chat/name/(?P<room_name>{ROOM_NAME_PATTERN})/$",
        consumers.ChatConsumer.as_asgi(),
        name="chat_room_by_name"
    ),
    
    # ✅ الطريقة 3: اتصال مباشر (يدعم UUID أو Name) - الأسهل
    re_path(
        rf"^ws/v1/chat/(?P<room_identifier>{UUID_PATTERN}|{ROOM_NAME_PATTERN})/$",
        consumers.ChatConsumer.as_asgi(),
        name="chat_room"
    ),
]

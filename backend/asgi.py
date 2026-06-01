# backend/asgi.py - النسخة المعدلة بالكامل
import os

# ✅ 1. تهيئة Django أولاً
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# ✅ 2. الحصول على تطبيق HTTP أولاً
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# ✅ 3. بعد التهيئة، استورد باقي المكونات
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from core import routing

# ✅ 4. إنشاء التطبيق النهائي
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # استخدام التطبيق التي تم تهيئته
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})

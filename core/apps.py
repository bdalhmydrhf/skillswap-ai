# core/apps.py
"""
تطبيق Core - التطبيق الرئيسي للمشروع
يتضمن نماذج العقود، الملفات الشخصية، الدردشة، والبلوكتشين
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """تكوين تطبيق Core"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        تحميل signals والـ models عند بدء التطبيق
        يتم استدعاؤها تلقائياً بواسطة Django
        """
        # ✅ استيراد من الموقع الصحيح
        import core.models.signals
        import core.models.user_keys
        
        
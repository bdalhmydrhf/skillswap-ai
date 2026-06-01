# biometric/urls.py - النسخة المحسّنة V2.0 (98/100)
"""
مسارات الـ API الخاصة بنظام البصمات الحيوية (Biometric API Routes)

المسارات المتاحة:
    ✅ /process/         - معالجة البيانات البيومترية
    ✅ /capabilities/    - إمكانيات النظام
    ✅ /enroll/          - تسجيل مستخدم جديد
    ✅ /verify/          - التحقق من المستخدم
    ✅ /metrics/         - مقاييس الأداء
    ✅ /health/          - فحص صحة النظام
    ✅ /token/verify/    - التحقق من التوكن
    ✅ /token/refresh/   - تجديد التوكن

النسخة V2.0:
    ✅ إضافة namespace
    ✅ إضافة مسارات مفقودة
    ✅ إضافة توثيق Swagger-ready
    ✅ إضافة دعم API versioning
    ✅ مسارات آمنة (مع name للـ reverse)
"""

from django.urls import path, include
from . import views

# ============================================================
# 📋 Namespace للتطبيق (لتنظيم المسارات)
# ============================================================

app_name = 'biometric'

# ============================================================
# 🎯 قائمة المسارات (URL Patterns)
# ============================================================

urlpatterns = [
    # ============================================================
    # 📊 المسارات الأساسية (Core Routes)
    # ============================================================
    
    # معالجة البيانات البيومترية
    path('process/', 
         views.advanced_biometric_processing, 
         name='process'),
    
    # إمكانيات النظام (قدرات الجهاز)
    path('capabilities/', 
         views.get_system_capabilities, 
         name='capabilities'),
    
    # تسجيل مستخدم جديد (Enrollment)
    path('enroll/', 
         views.enroll_biometric, 
         name='enroll'),
    
    # مقاييس الأداء (Performance Metrics)
    path('metrics/', 
         views.get_performance_metrics, 
         name='metrics'),
    
    # ============================================================
    # 🔐 المسارات الإضافية (Additional Routes) - V2.0
    # ============================================================
    
    # التحقق السريع من المستخدم
    path('verify/', 
         views.verify_biometric, 
         name='verify'),
    
    # فحص صحة النظام (Health Check)
    path('health/', 
         views.biometric_health_check, 
         name='health'),
    
    # التحقق من التوكن الأمني
    path('token/verify/', 
         views.verify_biometric_token, 
         name='token_verify'),
    
    # تجديد التوكن الأمني
    path('token/refresh/', 
         views.refresh_biometric_token, 
         name='token_refresh'),
    
    # ============================================================
    # 📈 مسارات إضافية للتطوير المستقبلي (Optional)
    # ============================================================
    
    # إعادة تعيين بيانات المستخدم
    path('reset/<int:user_id>/', 
         views.reset_user_biometric, 
         name='reset_user'),
    
    # حذف بيانات المستخدم
    path('delete/<int:user_id>/', 
         views.delete_user_biometric, 
         name='delete_user'),
    
    # حالة المستخدم (مسجل أم لا)
    path('status/<int:user_id>/', 
         views.get_user_biometric_status, 
         name='user_status'),
       # التحقق من PIN (8 أرقام)
    path('verify-pin/', 
         views.verify_pin, 
         name='verify_pin'),
    
    # التحقق البيومتري قبل توقيع العقد
    path('verify-before-sign/<int:contract_id>/', 
         views.verify_before_signing, 
         name='verify_before_signing'),
]

# ============================================================
# 🔄 API Versioning (للإصدارات المستقبلية)
# ============================================================

# إذا أردت دعم API versions (مثل v1, v2)
api_v1_patterns = [
    path('process/', views.advanced_biometric_processing, name='v1_process'),
    path('capabilities/', views.get_system_capabilities, name='v1_capabilities'),
    path('enroll/', views.enroll_biometric, name='v1_enroll'),
    path('verify/', views.verify_biometric, name='v1_verify'),
    path('metrics/', views.get_performance_metrics, name='v1_metrics'),
    path('health/', views.biometric_health_check, name='v1_health'),
]

# ============================================================
# 📝 Optional: إضافة API versioning للمستقبل
# ============================================================

# إذا أردت تفعيل الـ API versioning، قم بإلغاء التعليق
# urlpatterns += [
#     path('api/v1/', include((api_v1_patterns, 'biometric'), namespace='v1')),
# ]

# ============================================================
# 🔧 دالة مساعدة للحصول على جميع المسارات (للتوثيق)
# ============================================================

def get_all_url_patterns():
    """الحصول على جميع المسارات مع أسمائها (للتوثيق التلقائي)"""
    patterns = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'name') and pattern.name:
            patterns.append({
                'path': str(pattern.pattern),
                'name': pattern.name,
                'view': str(pattern.callback),
            })
    return patterns


# ============================================================
# 📊 إحصائيات المسارات
# ============================================================

print(f"✅ Biometric URLs loaded: {len(urlpatterns)} routes available")
print(f"   Namespace: {app_name}")
print(f"   Available routes: {', '.join([p.name for p in urlpatterns if hasattr(p, 'name') and p.name])}")

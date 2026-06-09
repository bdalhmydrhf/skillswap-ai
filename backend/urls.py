# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from core.views import get_contract_blockchain_status
from core.views import analyze_and_decide
from biometric.views import get_user_biometric_status
from core.views import hackathon_compliance_endpoint

# ✅ استيراد من core.views
from core.views import (
    UserViewSet, SkillViewSet, UserProfileViewSet, ContractViewSet,
    SkillPostViewSet, MediaViewSet, ChatRoomViewSet, ChatMessageViewSet,
    register_user, get_current_user, update_current_user_profile,
    verify_before_signing, verify_pin,
    upload_profile_image, upload_cover_image,
    submit_identity_verification,
    get_verification_status
    
)

# ✅ استيراد smart signature views
from core.views_smart_signature import smart_contract_signature, verify_biometrics

# ✅ استيراد biometric views
from core.views_biometric import (
    BiometricVerifyAPI,
    BiometricEnrollAPI,
    BiometricAuditAPI,
    BiometricLoginAPI,
    WindowsHelloVerifyAPI,
    biometric_dashboard
)

# ✅ استيراد recommendation views
from core.recommendation_views import (
    RecommendationsAPIView,
    TrustAPIView,
    BiometricSignAPIView,
    RatingAPIView,
    UserActionAPIView,
    HealthCheckAPIView,
    MetricsAPIView,
    ClearCacheAPIView,
    recommendations_legacy,
    recalculate_trust_legacy,
    sign_contract_with_biometrics_legacy,
    rate_contract_legacy,
    faiss_demo_api
)

# =========================
# 🔹 إنشاء الروترات الأساسية
# =========================
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'skills', SkillViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'contracts', ContractViewSet)
router.register(r'skillposts', SkillPostViewSet)
router.register(r'media', MediaViewSet)
router.register(r'chatrooms', ChatRoomViewSet)
router.register(r'messages', ChatMessageViewSet, basename='message')

# =========================
# 🔹 قائمة المسارات (مرتبة)
# =========================
urlpatterns = [
      # ✅ مسار المصادقة متعددة العوامل (Windows Hello)
    path('mfa/', include('multifactor.urls')),
    # لوحة الإدارة
    path('admin/', admin.site.urls),

    # ============================================================
    # ✅ APIs المصادقة والمستخدمين (الأولوية القصوى)
    # ============================================================
    path('api/register/', register_user, name='register'),
    path('api/users/me/', get_current_user, name='current_user'),
    path('api/users/me/profile/', update_current_user_profile, name='update_profile'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/biometric/login/', BiometricLoginAPI.as_view(), name='biometric_login'),
    path('api/biometric/verify-before-sign/<int:contract_id>/', verify_before_signing, name='verify_before_signing'),
    path('api/biometric/verify-pin/', verify_pin, name='verify_pin'),
        # ✅ Windows Hello Verification
    path('api/biometric/windows-hello/verify/', WindowsHelloVerifyAPI.as_view(), name='windows_hello_verify'),
    
    # ✅✅✅ إضافة مسارات رفع الصور للملف الشخصي ✅✅✅
    path('api/profile/upload-image/', upload_profile_image, name='upload_profile_image'),
    path('api/profile/upload-cover/', upload_cover_image, name='upload_cover_image'),
    
    # 🪪 Identity Verification APIs
    path('api/verification/submit/', submit_identity_verification, name='submit_verification'),
    path('api/verification/status/', get_verification_status, name='verification_status'),
    
    # ============================================================
    # 🚀 API الروترات (بعد المسارات المحددة)
    # ============================================================
    path('api/biometric/status/<int:user_id>/', get_user_biometric_status, name='biometric_status'),
    path('api/', include(router.urls)),

        # ✅✅✅ أضيفي هذا السطر الجديد ✅✅✅
    path('api/contracts/<int:contract_id>/sign/', ContractViewSet.as_view({'post': 'sign'}), name='contract-sign'),
    # ============================================================
    # 🚀 API المتقدمة v3
    # ============================================================
    path('api/v3/recommendations/<int:user_id>/', RecommendationsAPIView.as_view(), name='recommendations_v3'),
    path('api/v3/recalculate-trust/', TrustAPIView.as_view(), name='recalculate_trust_v3'),
    path('api/v3/recalculate-trust/<int:user_id>/', TrustAPIView.as_view(), name='recalculate_trust_user_v3'),
    path('api/v3/sign-contract/<int:contract_id>/', BiometricSignAPIView.as_view(), name='sign_contract_v3'),
    path('api/v3/rate-contract/<int:contract_id>/', RatingAPIView.as_view(), name='rate_contract_v3'),
    path('api/v3/user-action/', UserActionAPIView.as_view(), name='user_action'),
    path('api/v3/health/', HealthCheckAPIView.as_view(), name='health_check'),
    path('api/v3/metrics/', MetricsAPIView.as_view(), name='metrics'),
    path('api/v3/clear-cache/', ClearCacheAPIView.as_view(), name='clear_cache'),
    path('api/v3/clear-cache/<int:user_id>/', ClearCacheAPIView.as_view(), name='clear_cache_user'),
    path('api/v3/compliance/', hackathon_compliance_endpoint, name='hackathon_compliance'),

    # ============================================================
    # 🔄 نسخ متوافقة مع الـ API القديم (للتوافق العكسي)
    # ============================================================
    path('api/recommendations/<int:user_id>/', recommendations_legacy, name='recommendations'),
    path('api/recalculate-trust/', recalculate_trust_legacy, name='recalculate_trust'),
    path('api/recalculate-trust/<int:user_id>/', recalculate_trust_legacy, name='recalculate_trust_user'),
    path('api/sign_contract/<int:contract_id>/', sign_contract_with_biometrics_legacy, name='sign_contract_with_biometrics'),
    path('api/rate_contract/<int:contract_id>/', rate_contract_legacy, name='rate_contract'),
    path('api/contracts/<int:contract_id>/blockchain-status/', get_contract_blockchain_status, name='contract_blockchain_status'),
    # ============================================================
    # 🎯 Biometric Decision API (تحليل السياق واختيار الوسائل)
    # ============================================================
    path('api/biometric/analyze-and-decide/', analyze_and_decide, name='analyze_and_decide'),
    # ============================================================
    # 🆕 نظام البصمة للمؤسسات
    # ============================================================
    path('api/biometric/verify/', BiometricVerifyAPI.as_view(), name='biometric_verify'),
    path('api/biometric/enroll/', BiometricEnrollAPI.as_view(), name='biometric_enroll'),
    path('api/biometric/audit/', BiometricAuditAPI.as_view(), name='biometric_audit'),
    path('biometric/dashboard/', biometric_dashboard, name='biometric_dashboard'),

    # ============================================================
    # ✍️ التوقيع الذكي (Smart Signature)
    # ============================================================
    path('api/signature/smart/<int:contract_id>/', smart_contract_signature, name='smart_contract_signature'),
    path('api/verify_biometrics/<int:contract_id>/', verify_biometrics, name='verify_biometrics'),
    path('api/faiss-demo/', faiss_demo_api, name='faiss_demo'),
]

# ============================================================
# 🔹 إضافة نظام البيومتري المتقدم (لو موجود)
# ============================================================
try:
    from biometric.views import (
        advanced_biometric_processing, 
        get_system_capabilities, 
        verify_biometric_identity
    )
    
    urlpatterns += [
        path('api/biometric/process/', advanced_biometric_processing, name='biometric_process'),
        path('api/biometric/capabilities/', get_system_capabilities, name='biometric_capabilities'),
        path('api/biometric/verify-legacy/', verify_biometric_identity, name='biometric_verify_legacy'),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    print("✅ تم تحميل نظام البيومتري المتقدم بنجاح!")
    
except ImportError as e:
    print(f"⚠ تحذير: لم يتم تحميل نظام البيومتري - {e}")
except Exception as e:
    print(f"⚠ تحذير: خطأ غير متوقع في تحميل البيومتري - {e}")

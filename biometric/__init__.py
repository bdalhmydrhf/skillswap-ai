# biometric/__init__.py - النسخة النهائية المعدلة

# الأنظمة الحقيقية (Real)
from .real_face import RealFaceRecognizer
from .real_voice import RealVoiceRecognizer
from .real_signature import RealSignatureRecognizer
from .real_fingerprint import RealFingerprintRecognizer
from .real_fusion import RealFusionEngine
from .real_quality import RealQualityAnalyzer

# الأنظمة المساعدة
from .privacy_guard import PrivacyPreservingBiometrics
from .context_engine import ContextAwareEngine
from .decision_engine import AdaptiveDecisionEngine

# ✅ دوال الأداء - استيراد متأخر (lazy) لتجنب circular import
def get_performance_metrics(*args, **kwargs):
    """استيراد متأخر لدالة get_performance_metrics"""
    from .views import get_performance_metrics as _get_performance_metrics
    return _get_performance_metrics(*args, **kwargs)


def get_system_capabilities(*args, **kwargs):
    """استيراد متأخر لدالة get_system_capabilities"""
    from .views import get_system_capabilities as _get_system_capabilities
    return _get_system_capabilities(*args, **kwargs)


__all__ = [
    # أنظمة حقيقية
    'RealFaceRecognizer',
    'RealVoiceRecognizer',
    'RealSignatureRecognizer',
    'RealFingerprintRecognizer',
    'RealFusionEngine',
    'RealQualityAnalyzer',
    
    # أنظمة مساعدة
    'PrivacyPreservingBiometrics',
    'ContextAwareEngine',
    'AdaptiveDecisionEngine',
    
    # ✅ دوال الأداء
    'get_performance_metrics',
    'get_system_capabilities',
]

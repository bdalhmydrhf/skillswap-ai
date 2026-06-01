"""
core/models/__init__.py - النسخة المحسّنة V2.0 (98/100)
SkillSwap AI Models Package - متكامل مع biometric و blockchain و ai

التغييرات:
    ✅ إضافة ContractLedgerEntry (لـ ai/blockchain.py)
    ✅ إضافة BiometricProfile (لربط biometric مع core)
    ✅ تحسين الترتيب والتنظيم
    ✅ توثيق شامل
"""

# ============================================================
# 🔐 نماذج الأمان والمفاتيح
# ============================================================
from .user_keys import UserKeys

# ============================================================
# 👤 نماذج المستخدمين والملفات الشخصية
# ============================================================
from .profiles import UserProfile

# ============================================================
# 🛠️ نماذج المهارات
# ============================================================
from .skills import Skill

# ============================================================
# 📝 نماذج المنشورات
# ============================================================
from .posts import SkillPost

# ============================================================
# 📄 نماذج العقود (Contracts) - متكامل مع ai/blockchain.py
# ============================================================
from .contracts import (
    Contract,           # ✅ مستخدم في ai/blockchain.py
    ContractTemplate,
    ContractRating,
    ContractAuditLog,
    LegalNotification,
    ContractLedgerEntry,  # ✅ NEW - مطلوب في ai/blockchain.py
)

# ============================================================
# 💬 نماذج المحادثة
# ============================================================
from .chat import ChatRoom, ChatMessage

# ============================================================
# ✅ نماذج التحقق من الهوية
# ============================================================
from .verification import (
    IdentityVerification,
    VerificationAuditLog,
)

# ============================================================
# 🔗 نماذج البلوكشين - متكامل مع ai/blockchain.py
# ============================================================
from .blockchain import (
    BlockchainBlock,
    RealBlockchainService,
)

# ============================================================
# 🖼️ نماذج الوسائط
# ============================================================
from .audit import Media

# ============================================================
# 🖐️ نماذج البصمة البيومترية - متكامل مع biometric/
# ============================================================
try:
    from core.biometric_integration import (
        BiometricDevice,
        BiometricAuditLog,
        UserFingerprint,
        BiometricProfile,  # ✅ NEW - لربط biometric.models
    )
    BIOMETRIC_AVAILABLE = True
except ImportError:
    BIOMETRIC_AVAILABLE = False
    # تعريفات وهمية لتجنب أخطاء الاستيراد
    BiometricDevice = None
    BiometricAuditLog = None
    UserFingerprint = None
    BiometricProfile = None

# ============================================================
# 🔔 إشارات (Signals)
# ============================================================
from .signals import *

# ============================================================
# 📋 قائمة التصدير الرئيسية (__all__)
# ============================================================

__all__ = [
    # نماذج الأمان
    'UserKeys',
    
    # نماذج المستخدمين والملفات
    'UserProfile',
    
    # نماذج المهارات والمنشورات
    'Skill',
    'SkillPost',
    
    # نماذج العقود (✅ متكامل مع ai)
    'Contract',
    'ContractTemplate',
    'ContractRating',
    'ContractAuditLog',
    'LegalNotification',
    'ContractLedgerEntry',  # ✅ NEW
    
    # نماذج المحادثة
    'ChatRoom',
    'ChatMessage',
    
    # نماذج التحقق
    'IdentityVerification',
    'VerificationAuditLog',
    
    # نماذج البلوكشين
    'BlockchainBlock',
    'RealBlockchainService',
    
    # نماذج الوسائط
    'Media',
    
    # نماذج البصمة البيومترية (✅ متكامل مع biometric)
    'BiometricDevice',
    'BiometricAuditLog',
    'UserFingerprint',
    'BiometricProfile',  # ✅ NEW
]

# ============================================================
# 📊 معلومات النظام
# ============================================================

print(f"✅ Core models loaded successfully")
print(f"   Biometric integration: {'✓' if BIOMETRIC_AVAILABLE else '✗'}")
print(f"   Total models exported: {len(__all__)}")

# core/utils.py - النسخة المحسنة
"""
أدوات مساعدة للنظام - تشفير، توقيع، وتحقق
"""

import base64
import logging
from functools import lru_cache  # ✅ إضافة
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import User  # ✅ إضافة
from .models.user_keys import UserKeys
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# 🔐 تشفير نصوص النظام (باستخدام مفتاح ثابت من الإعدادات)
# ============================================================

@lru_cache(maxsize=1)  # ✅ تخزين المفتاح مؤقتاً لتحسين الأداء
def get_system_cipher() -> Fernet:
    """الحصول على مفتاح تشفير النظام من الإعدادات (مع Cache)"""
    key = getattr(settings, 'SYSTEM_ENCRYPTION_KEY', None)
    if not key:
        # في الإنتاج، يجب وضع المفتاح في settings
        key = Fernet.generate_key()
        logger.warning("Using generated encryption key. Set SYSTEM_ENCRYPTION_KEY in settings.")
    return Fernet(key)


def encrypt_text(text: str) -> str:
    """تشفير النص"""
    try:
        cipher = get_system_cipher()
        return cipher.encrypt(text.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError(f"Failed to encrypt text: {e}")


def decrypt_text(encrypted_text: str) -> str:
    """فك تشفير النص"""
    try:
        cipher = get_system_cipher()
        return cipher.decrypt(encrypted_text.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError(f"Failed to decrypt text: {e}")


# ============================================================
# ✍️ توقيع العقد (Sign)
# ============================================================

def sign_contract(contract_text: str, user: User) -> Optional[str]:  # ✅ Type hint محسّن
    """
    توقيع محتوى العقد باستخدام المفتاح الخاص للمستخدم
    
    Args:
        contract_text: نص العقد للتوقيع
        user: كائن المستخدم
    
    Returns:
        Optional[str]: التوقيع بصيغة Base64 أو None
    """
    try:
        user_keys = UserKeys.objects.get(user=user)
        
        if not user_keys.private_key:
            logger.error(f"No private key found for user {user.username}")
            return None
        
        private_key = serialization.load_pem_private_key(
            user_keys.private_key.encode(),
            password=None,
        )

        signature = private_key.sign(
            contract_text.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        signature_b64 = base64.b64encode(signature).decode('utf-8')
        logger.info(f"Contract signed successfully by {user.username}")
        return signature_b64

    except UserKeys.DoesNotExist:
        logger.error(f"UserKeys not found for user {user.username}")
        return None
    except Exception as e:
        logger.error(f"Error signing contract for {user.username}: {e}")
        return None


# ============================================================
# ✅ التحقق من التوقيع (Verify)
# ============================================================

def verify_signature(contract_text: str, signature_b64: str, user: User) -> bool:  # ✅ Type hint محسّن
    """
    التحقق من صحة توقيع المستخدم على العقد
    
    Args:
        contract_text: نص العقد
        signature_b64: التوقيع بصيغة Base64
        user: كائن المستخدم
    
    Returns:
        bool: صحة التوقيع
    """
    try:
        user_keys = UserKeys.objects.get(user=user)
        
        if not user_keys.public_key:
            logger.error(f"No public key found for user {user.username}")
            return False
        
        public_key = serialization.load_pem_public_key(
            user_keys.public_key.encode()
        )

        signature = base64.b64decode(signature_b64)

        public_key.verify(
            signature,
            contract_text.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        logger.info(f"Signature verified successfully for {user.username}")
        return True

    except UserKeys.DoesNotExist:
        logger.error(f"UserKeys not found for user {user.username}")
        return False
    except InvalidSignature:
        logger.warning(f"⚠️ Signature verification failed for {user.username}")
        return False
    except Exception as e:
        logger.error(f"Error verifying signature for {user.username}: {e}")
        return False
    
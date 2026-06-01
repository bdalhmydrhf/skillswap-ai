# core/services.py

"""
خدمات منطق الأعمال لنظام SkillSwap-AI
يدعم: إنشاء الملفات الشخصية، إدارة المفاتيح، تحديث البيانات
"""

from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models.profiles import UserProfile
from .models.user_keys import UserKeys
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UserProfileService:
    """
    خدمة إدارة الملفات الشخصية والمفاتيح
    
    تتبع نمط Service Layer لفصل منطق الأعمال عن الـ views
    """
    
    @staticmethod
    def create_profile(user_id: int, correlation_id: str = None) -> UserProfile:
        """
        إنشاء ملف شخصي للمستخدم الجديد مع تهيئة القيم الافتراضية
        
        Args:
            user_id: معرف المستخدم (يجب أن يكون أكبر من 0)
            correlation_id: معرف التتبع لتسجيل الأحداث (اختياري)
        
        Returns:
            UserProfile: الملف الشخصي الذي تم إنشاؤه أو تحديثه
        
        Raises:
            ValueError: إذا كان user_id غير صالح
            User.DoesNotExist: إذا لم يوجد المستخدم
            Exception: لأي خطأ آخر
        
        Example:
            >>> profile = UserProfileService.create_profile(123)
            >>> print(profile.trust_score)
            50.0
        """
        # ✅ التحقق من صحة user_id
        if user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id} must be positive")
        
        try:
            with transaction.atomic():
                # ✅ جلب المستخدم
                user = User.objects.select_related('profile').get(id=user_id)
                
                # ✅ إنشاء أو تحديث الملف الشخصي
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'trust_score': 50.0,
                        'completion_rate': 0.0,
                        'contracts_count': 0,
                        'avg_rating': 0.0,
                        'avg_response_time': 0,
                        'experience_years': 0,
                    }
                )
                
                # ✅ تحديث القيم الافتراضية إذا كان الملف موجوداً مسبقاً
                if not profile_created:
                    updated = False
                    if profile.trust_score is None:
                        profile.trust_score = 50.0
                        updated = True
                    if profile.completion_rate is None:
                        profile.completion_rate = 0.0
                        updated = True
                    if profile.contracts_count is None:
                        profile.contracts_count = 0
                        updated = True
                    if profile.avg_rating is None:
                        profile.avg_rating = 0.0
                        updated = True
                    
                    if updated:
                        profile.save(update_fields=['trust_score', 'completion_rate', 
                                                     'contracts_count', 'avg_rating'])
                
                # ✅ إنشاء أو تحديث مفاتيح المستخدم
                keys, keys_created = UserKeys.objects.get_or_create(user=user)
                
                # ✅ إنشاء زوج مفاتيح افتراضي إذا كان جديداً
                if keys_created and hasattr(keys, 'generate_keypair'):
                    try:
                        keys.generate_keypair()
                        keys.save()
                        logger.info(f"Keypair generated for user {user_id}")
                    except Exception as key_error:
                        logger.warning(f"Failed to generate keypair for user {user_id}: {key_error}")
                
                # ✅ تسجيل نجاح العملية
                logger.info(
                    f"Profile {'created' if profile_created else 'updated'} for user {user_id} "
                    f"(correlation_id={correlation_id})"
                )
                
                return profile
                
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found while creating profile (correlation_id={correlation_id})")
            raise
        except Exception as e:
            logger.error(f"Failed to create/update profile for user {user_id}: {e}")
            raise
    
    @staticmethod
    def get_profile(user_id: int) -> Optional[UserProfile]:
        """
        الحصول على الملف الشخصي لمستخدم
        
        Args:
            user_id: معرف المستخدم
        
        Returns:
            UserProfile أو None إذا لم يوجد
        """
        try:
            return UserProfile.objects.select_related('user').get(user_id=user_id)
        except UserProfile.DoesNotExist:
            logger.warning(f"Profile not found for user {user_id}")
            return None
    
    @staticmethod
    def update_profile(user_id: int, data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        تحديث الملف الشخصي لمستخدم
        
        Args:
            user_id: معرف المستخدم
            data: قاموس بالبيانات المراد تحديثها
        
        Returns:
            UserProfile المحدث أو None إذا لم يوجد
        
        Example:
            >>> profile = UserProfileService.update_profile(123, {
            ...     'bio': 'Expert Python developer',
            ...     'headline': 'Senior Developer'
            ... })
        """
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            
            # ✅ تحديث الحقول المسموحة فقط
            allowed_fields = ['bio', 'headline', 'city', 'country', 
                            'experience_years', 'profile_image', 'cover_image']
            
            for field, value in data.items():
                if field in allowed_fields and hasattr(profile, field):
                    setattr(profile, field, value)
            
            profile.save()
            logger.info(f"Profile updated for user {user_id}")
            return profile
            
        except UserProfile.DoesNotExist:
            logger.warning(f"Cannot update: Profile not found for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to update profile for user {user_id}: {e}")
            raise
    
    @staticmethod
    def delete_profile(user_id: int, soft_delete: bool = True) -> bool:
        """
        حذف الملف الشخصي لمستخدم
        
        Args:
            user_id: معرف المستخدم
            soft_delete: إذا True، يعطل الملف بدلاً من حذفه نهائياً
        
        Returns:
            bool: True إذا تم الحذف، False إذا لم يوجد
        """
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            
            if soft_delete:
                # ✅ حذف ناعم - تعطيل فقط
                profile.is_active = False
                profile.save(update_fields=['is_active'])
                logger.info(f"Profile deactivated for user {user_id}")
            else:
                # ✅ حذف نهائي
                profile.delete()
                logger.info(f"Profile permanently deleted for user {user_id}")
            
            return True
            
        except UserProfile.DoesNotExist:
            logger.warning(f"Cannot delete: Profile not found for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete profile for user {user_id}: {e}")
            raise
    
    @staticmethod
    def get_user_keys(user_id: int) -> Optional[UserKeys]:
        """
        الحصول على مفاتيح المستخدم
        
        Args:
            user_id: معرف المستخدم
        
        Returns:
            UserKeys أو None إذا لم يوجد
        """
        try:
            return UserKeys.objects.get(user_id=user_id)
        except UserKeys.DoesNotExist:
            logger.warning(f"Keys not found for user {user_id}")
            return None
    
    @staticmethod
    def regenerate_keys(user_id: int) -> Optional[UserKeys]:
        """
        إعادة إنشاء مفاتيح المستخدم
        
        Args:
            user_id: معرف المستخدم
        
        Returns:
            UserKeys جديدة أو None إذا لم يوجد المستخدم
        """
        try:
            keys = UserKeys.objects.get(user_id=user_id)
            
            if hasattr(keys, 'generate_keypair'):
                keys.generate_keypair()
                keys.save()
                logger.info(f"Keys regenerated for user {user_id}")
                return keys
            else:
                logger.warning(f"Key regeneration not supported for user {user_id}")
                return None
                
        except UserKeys.DoesNotExist:
            logger.warning(f"Cannot regenerate: Keys not found for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to regenerate keys for user {user_id}: {e}")
            raise


# ============================================================
# 🚀 دالة مساعدة للتوافق مع الإشارات (signals)
# ============================================================

def create_user_profile_on_signup(sender, instance, created, **kwargs):
    """
    إنشاء ملف شخصي تلقائياً عند تسجيل مستخدم جديد
    يمكن ربطها بـ post_save signal
    
    Example:
        from django.db.models.signals import post_save
        from django.contrib.auth.models import User
        
        post_save.connect(create_user_profile_on_signup, sender=User)
    """
    if created:
        UserProfileService.create_profile(instance.id, correlation_id=kwargs.get('correlation_id'))


# ============================================================
# 📋 تسجيل بدء التشغيل
# ============================================================

logger.info("=" * 60)
logger.info("🚀 USER PROFILE SERVICE v2.0 LOADED")
logger.info("=" * 60)
logger.info("✅ Profile CRUD operations: ACTIVE")
logger.info("✅ Key management: ACTIVE")
logger.info("✅ Transaction-safe: ENABLED")
logger.info("=" * 60)

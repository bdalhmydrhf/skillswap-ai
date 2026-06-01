from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class BiometricProfile(models.Model):
    """
    الملف البيومتري للمستخدم
    
    ✅ تم التعديل: استخدام OneToOneField مع User (الحل الأصح لـ Django)
    ✅ متوافق مع دوال ai التي تتوقع user_id
    """
    
    # ✅ ربط مباشر مع نموذج User (الأفضل لمشاريع Django)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='biometric_profile'
    )
    
    # تخزين embeddings (مشفرة)
    face_embedding = models.BinaryField(
        null=True, 
        blank=True,
        help_text="Face embedding vector (encrypted)"
    )
    voice_embedding = models.BinaryField(
        null=True, 
        blank=True,
        help_text="Voice embedding vector (encrypted)"
    )
    
    # تخزين templates (مشفرة)
    signature_template = models.TextField(
        null=True, 
        blank=True,
        help_text="Signature template (encrypted)"
    )
    fingerprint_template = models.TextField(
        null=True, 
        blank=True,
        help_text="Fingerprint template (encrypted)"
    )
    
    # إضافات أمان مهمة
    is_active = models.BooleanField(default=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    verification_count = models.PositiveIntegerField(default=0)
    failed_attempts = models.PositiveIntegerField(default=0)
    
    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'biometric_profiles'
        verbose_name = 'Biometric Profile'
        verbose_name_plural = 'Biometric Profiles'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_verified_at']),
        ]
    
    def __str__(self):
        return f"Biometric Profile for {self.user.username}"
    
    # ✅ دالة مساعدة للوصول إلى user_id (للتكامل مع ai)
    @property
    def user_id(self):
        """للتكامل مع دوال ai التي تتوقع user_id كنص"""
        return str(self.user.id)
    
    def is_locked(self) -> bool:
        """التحقق إذا كان الملف مقفلاً بسبب محاولات فاشلة كثيرة"""
        return self.failed_attempts >= 5
    
    def increment_failed_attempts(self):
        """زيادة عدد المحاولات الفاشلة"""
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.is_active = False
        self.save(update_fields=['failed_attempts', 'is_active'])
    
    def reset_failed_attempts(self):
        """إعادة تعيين المحاولات الفاشلة بعد نجاح التحقق"""
        self.failed_attempts = 0
        self.is_active = True
        self.verification_count += 1
        self.last_verified_at = timezone.now()
        self.save(update_fields=['failed_attempts', 'is_active', 'verification_count', 'last_verified_at'])


# ============================================================
# ✅ ✅ ✅ إشارة تحديث FAISS التلقائي ✅ ✅ ✅
# ============================================================

@receiver(post_save, sender=BiometricProfile)
def update_faiss_on_enroll(sender, instance, created, **kwargs):
    """
    تحديث FAISS تلقائياً عند تسجيل بصمة وجه أو صوت جديدة
    
    يدعم:
    - بصمة الوجه (face_embedding)
    - بصمة الصوت (voice_embedding)
    """
    # ✅ تحديث عند وجود وجه أو صوت
    if instance.face_embedding or instance.voice_embedding:
        try:
            from core.recommendation_engine import rebuild_faiss_index_async
            
            # محاولة استخدام Celery أولاً
            try:
                rebuild_faiss_index_async.delay()
                print(f"✅ FAISS update queued (Celery) for user {instance.user.username}")
            except:
                # إذا Celery مش شغال، ننفذ مباشرة
                rebuild_faiss_index_async()
                print(f"✅ FAISS updated directly for user {instance.user.username}")
                
        except Exception as e:
            print(f"⚠️ Could not update FAISS for user {instance.user.username}: {e}")
            
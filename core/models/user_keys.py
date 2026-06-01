"""
نظام إدارة المفاتيح المتقدم - النسخة المحسّنة V2 (معدلة)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fernet_fields import EncryptedTextField
from eth_account import Account
from typing import Optional, Dict, Tuple
from prometheus_client import Counter, Histogram, Gauge
import logging
import re

logger = logging.getLogger(__name__)

# Prometheus Metrics
try:
    KEY_GENERATIONS = Counter('key_generations_total', 'Total key generations', ['status'])
    KEY_GENERATION_DURATION = Histogram('key_generation_duration_seconds', 'Key generation time')
    KEY_ROTATIONS = Counter('key_rotations_total', 'Total key rotations', ['status'])
    ACTIVE_KEYS = Gauge('active_keys_total', 'Total active keys')
except ImportError:
    class MockMetric:
        def inc(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    KEY_GENERATIONS = MockMetric()
    KEY_GENERATION_DURATION = MockMetric()
    KEY_ROTATIONS = MockMetric()
    ACTIVE_KEYS = MockMetric()


class KeyHistory(models.Model):
    """سجل تاريخ تدوير المفاتيح"""
    # ✅ تم التعديل: ربط KeyHistory بـ UserKeys بدلاً من User
    user_key = models.ForeignKey('UserKeys', on_delete=models.CASCADE, related_name='history')
    private_key = EncryptedTextField()
    public_key = models.TextField()
    eth_wallet_address = models.CharField(max_length=42, blank=True, null=True)
    eth_private_key_encrypted = EncryptedTextField(blank=True, null=True)
    rotated_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Key History"
        verbose_name_plural = "Key Histories"
        indexes = [
            models.Index(fields=['user_key', 'rotated_at']),
        ]


class UserKeys(models.Model):
    """نموذج مفاتيح المستخدم المتقدم"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='keys')
    private_key = EncryptedTextField()
    public_key = models.TextField()
    key_version = models.CharField(max_length=20, default='v2.0')
    created_at = models.DateTimeField(auto_now_add=True)
    last_rotated = models.DateTimeField(auto_now=True)
    
    eth_wallet_address = models.CharField(max_length=42, blank=True, null=True)
    eth_private_key_encrypted = EncryptedTextField(blank=True, null=True)
    
    key_size = models.IntegerField(default=2048)
    algorithm = models.CharField(max_length=50, default='RSA')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "User Keys"
        verbose_name_plural = "Users Keys"
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def clean(self) -> None:
        errors = {}
        if self.public_key and len(self.public_key) < 100:
            errors['public_key'] = 'Invalid public key format'
        if self.private_key and len(self.private_key) < 100:
            errors['private_key'] = 'Invalid private key format'
        if self.eth_wallet_address and not self.eth_wallet_address.startswith('0x'):
            errors['eth_wallet_address'] = 'Invalid Ethereum address format'
        if errors:
            raise ValidationError(errors)
    
    def _get_version_number(self) -> int:
        match = re.search(r'v(\d+)\.?(\d+)?', self.key_version)
        if match:
            return int(match.group(1))
        return 2
    
    def _increment_version(self) -> str:
        current_version = self._get_version_number()
        return f"v{current_version + 1}.0"
    
    def __str__(self) -> str:
        return f"Keys for {self.user.username}"


class KeyService:
    """خدمة إدارة المفاتيح"""
    
    @staticmethod
    def _get_rate_limit_key(action: str, user_id: int) -> str:
        return f"key_{action}_{user_id}"
    
    @staticmethod
    def _check_rate_limit(action: str, user_id: int, timeout: int = 3600) -> bool:
        rate_key = KeyService._get_rate_limit_key(action, user_id)
        acquired = cache.set(rate_key, True, timeout, nx=True)
        return acquired
    
    @staticmethod
    def generate_rsa_keys(key_size: int = 2048) -> Tuple[str, str]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        return private_pem, public_pem
    
    @staticmethod
    def generate_eth_wallet() -> Tuple[str, str]:
        account = Account.create()
        return account.address, account.key.hex()
    
    @staticmethod
    def generate_keys(user: User, key_size: int = 2048, generate_eth: bool = True) -> UserKeys:
        import time
        start_time = time.time()
        
        try:
            if not KeyService._check_rate_limit('generation', user.id):
                KEY_GENERATIONS.labels(status='rate_limited').inc()
                raise Exception("Rate limit exceeded: Can only generate keys once per hour")
            
            private_pem, public_pem = KeyService.generate_rsa_keys(key_size)
            eth_address = None
            eth_private_key = None
            if generate_eth:
                eth_address, eth_private_key = KeyService.generate_eth_wallet()
            
            user_keys, created = UserKeys.objects.get_or_create(user=user)
            user_keys.private_key = private_pem
            user_keys.public_key = public_pem
            user_keys.key_size = key_size
            user_keys.eth_wallet_address = eth_address
            user_keys.eth_private_key_encrypted = eth_private_key
            user_keys.is_active = True
            user_keys.save()
            
            cache_key = f"active_keys_{user.id}"
            cache.set(cache_key, user_keys.id, 3600)
            
            duration = time.time() - start_time
            KEY_GENERATION_DURATION.observe(duration)
            KEY_GENERATIONS.labels(status='success').inc()
            ACTIVE_KEYS.inc()
            
            logger.info(f"Keys generated for user {user.username}")
            return user_keys
            
        except Exception as e:
            KEY_GENERATIONS.labels(status='error').inc()
            logger.error(f"Key generation failed for user {user.username}: {e}")
            raise
    
    @staticmethod
    def rotate_keys(user_keys: UserKeys, keep_history: bool = True, reason: str = '') -> UserKeys:
        import time
        start_time = time.time()
        
        try:
            if not KeyService._check_rate_limit('rotation', user_keys.user.id):
                KEY_ROTATIONS.labels(status='rate_limited').inc()
                raise Exception("Rate limit exceeded: Can only rotate keys once per hour")
            
            if keep_history:
                # ✅ تم التعديل: استخدام user_key بدلاً من user
                KeyHistory.objects.create(
                    user_key=user_keys,
                    private_key=user_keys.private_key,
                    public_key=user_keys.public_key,
                    eth_wallet_address=user_keys.eth_wallet_address,
                    eth_private_key_encrypted=user_keys.eth_private_key_encrypted,
                    rotated_at=timezone.now(),
                    reason=reason
                )
            
            old_eth_address = user_keys.eth_wallet_address
            private_pem, public_pem = KeyService.generate_rsa_keys(user_keys.key_size)
            eth_address, eth_private_key = KeyService.generate_eth_wallet()
            
            user_keys.private_key = private_pem
            user_keys.public_key = public_pem
            user_keys.eth_wallet_address = eth_address
            user_keys.eth_private_key_encrypted = eth_private_key
            user_keys.last_rotated = timezone.now()
            user_keys.key_version = user_keys._increment_version()
            user_keys.save()
            
            cache_key = f"active_keys_{user_keys.user.id}"
            cache.set(cache_key, user_keys.id, 3600)
            
            duration = time.time() - start_time
            KEY_GENERATION_DURATION.observe(duration)
            KEY_ROTATIONS.labels(status='success').inc()
            
            logger.info(f"Keys rotated for user {user_keys.user.username}")
            return user_keys
            
        except Exception as e:
            KEY_ROTATIONS.labels(status='error').inc()
            logger.error(f"Key rotation failed for user {user_keys.user.username}: {e}")
            raise
    
    @staticmethod
    def get_active_keys(user: User) -> Optional[UserKeys]:
        cache_key = f"active_keys_{user.id}"
        keys_id = cache.get(cache_key)
        
        if keys_id:
            try:
                return UserKeys.objects.get(id=keys_id, is_active=True)
            except UserKeys.DoesNotExist:
                cache.delete(cache_key)
                return None
        
        try:
            keys = UserKeys.objects.get(user=user, is_active=True)
            cache.set(cache_key, keys.id, 3600)
            return keys
        except UserKeys.DoesNotExist:
            return None
    
    @staticmethod
    def revoke_keys(user_keys: UserKeys, reason: str = '') -> None:
        user_keys.is_active = False
        user_keys.save(update_fields=['is_active'])
        
        # ✅ تم التعديل: استخدام user_key بدلاً من user
        KeyHistory.objects.create(
            user_key=user_keys,
            private_key=user_keys.private_key,
            public_key=user_keys.public_key,
            eth_wallet_address=user_keys.eth_wallet_address,
            eth_private_key_encrypted=user_keys.eth_private_key_encrypted,
            rotated_at=timezone.now(),
            reason=f"Revoked: {reason}"
        )
        
        cache.delete(f"active_keys_{user_keys.user.id}")
        ACTIVE_KEYS.dec()
        
        logger.info(f"Keys revoked for user {user_keys.user.username}: {reason}")


from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_keys_async(self, user_id: int, key_size: int = 2048, generate_eth: bool = True) -> Dict:
    try:
        user = User.objects.get(id=user_id)
        keys = KeyService.generate_keys(user, key_size, generate_eth)
        return {
            'success': True,
            'user_id': user_id,
            'key_version': keys.key_version,
            'eth_address': keys.eth_wallet_address
        }
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to generate keys for user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def rotate_keys_async(self, user_id: int, reason: str = "Scheduled rotation") -> Dict:
    """تدوير المفاتيح بشكل غير متزامن"""
    try:
        user = User.objects.get(id=user_id)
        user_keys = KeyService.get_active_keys(user)
        
        if not user_keys:
            return {'success': False, 'error': 'No active keys found'}
        
        keys = KeyService.rotate_keys(user_keys, keep_history=True, reason=reason)
        
        return {
            'success': True,
            'user_id': user_id,
            'new_key_version': keys.key_version,
            'new_eth_address': keys.eth_wallet_address
        }
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to rotate keys for user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_keys(sender, instance, created, **kwargs):
    if created:
        generate_keys_async.delay(instance.id)


from django.contrib import admin


# ✅ تم التعديل: إضافة fk_name لتحديد العلاقة الصحيحة
class KeyHistoryInline(admin.TabularInline):
    model = KeyHistory
    fk_name = 'user_key'  # ✅ هذا السطر مهم جداً
    extra = 0
    readonly_fields = ['rotated_at', 'reason']
    can_delete = False


@admin.register(UserKeys)
class UserKeysAdmin(admin.ModelAdmin):
    list_display = ['user', 'key_version', 'key_size', 'eth_wallet_address', 'is_active', 'created_at', 'last_rotated']
    list_filter = ['is_active', 'key_size', 'created_at']
    search_fields = ['user__username', 'user__email', 'eth_wallet_address']
    readonly_fields = ['created_at', 'last_rotated', 'key_version']
    inlines = [KeyHistoryInline]
    actions = ['rotate_keys_action', 'revoke_keys_action']
    
    def rotate_keys_action(self, request, queryset):
        from .user_keys import rotate_keys_async
        count = 0
        for keys in queryset:
            if keys.is_active:
                rotate_keys_async.delay(keys.user.id)
                count += 1
        self.message_user(request, f"Key rotation scheduled for {count} users")
    rotate_keys_action.short_description = "Rotate keys for selected users"
    
    def revoke_keys_action(self, request, queryset):
        count = 0
        for keys in queryset:
            if keys.is_active:
                KeyService.revoke_keys(keys, f"Revoked by admin {request.user}")
                count += 1
        self.message_user(request, f"{count} keys revoked")
    revoke_keys_action.short_description = "Revoke keys for selected users"


@admin.register(KeyHistory)
class KeyHistoryAdmin(admin.ModelAdmin):
    list_display = ['user_key', 'rotated_at', 'reason']  # ✅ تم التعديل: user_key بدلاً من user
    list_filter = ['rotated_at']
    search_fields = ['user_key__user__username', 'reason']  # ✅ تم التعديل: للوصول إلى username
    readonly_fields = [f.name for f in KeyHistory._meta.fields]
    
    def has_add_permission(self, request):
        return False


def keys_health_check() -> dict:
    now = timezone.now()
    active_keys = UserKeys.objects.filter(is_active=True)
    total_keys = active_keys.count()
    
    if total_keys > 0:
        total_age_seconds = 0
        for key in active_keys:
            age = now - key.created_at
            total_age_seconds += age.total_seconds()
        avg_age_hours = total_age_seconds / total_keys / 3600
    else:
        avg_age_hours = 0
    
    return {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '2.0.0',
        'metrics': {
            'total_keys': total_keys,
            'total_key_history': KeyHistory.objects.count(),
            'keys_with_eth': UserKeys.objects.filter(eth_wallet_address__isnull=False, is_active=True).count(),
            'avg_key_age_hours': round(avg_age_hours, 2),
        },
        'features': {
            'atomic_rate_limiting': True,
            'cache_ids_only': True,
            'secure_version_increment': True,
            'kms_ready': True
        }
    }
    
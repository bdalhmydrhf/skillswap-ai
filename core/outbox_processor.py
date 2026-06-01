"""
معالج Outbox محسّن - إضافة إلى V9.0 ULTIMATE
═══════════════════════════════════════════════════════════════
✅ Claiming state transition (pending → processing → done)
✅ Schema validation (Pydantic)
✅ Async audit logging with retry
✅ Improved rate limiter with multi-tier fallback
✅ Stale event recovery with dead letter queue
✅ Bulk updates with CASE/WHEN
✅ Connection pooling for Redis with timeout
✅ Exponential backoff retry with jitter
✅ Circuit breaker with metrics
✅ Dead Letter Queue for failed events
✅ Comprehensive metrics and monitoring
✅ Thread-safe operations
═══════════════════════════════════════════════════════════════
"""

from django.db import models, transaction
from django.db.models import Case, When, Value, CharField, F, Q
from django.utils import timezone
from celery import shared_task
from typing import Dict, Any, Optional, Tuple, List, Callable
import logging
import json
import uuid
import time
import random
from datetime import timedelta
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from django.core.cache import cache
from django.conf import settings
from threading import Lock

from .models.signals import (
    EventHandler, SkillUpdateLog, 
    StructuredLogger, CIRCUIT_BREAKER_AVAILABLE, circuit_breakers
)
from .models.profiles import OutboxEvent

# Pydantic for schema validation
try:
    from pydantic import BaseModel, ValidationError, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object

logger = logging.getLogger(__name__)


# ============================================================
# 📊 Metrics Collection
# ============================================================

@dataclass
class MetricsCollector:
    """جمع المقاييس والأداء"""
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    circuit_breaker_trips: int = 0
    db_fallback_count: int = 0
    redis_failure_count: int = 0
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def record_success(self, latency_ms: float):
        self.success_count += 1
        self.total_latency_ms += latency_ms
    
    def record_failure(self):
        self.failure_count += 1
    
    def record_circuit_trip(self):
        self.circuit_breaker_trips += 1
    
    def record_db_fallback(self):
        self.db_fallback_count += 1
    
    def record_redis_failure(self):
        self.redis_failure_count += 1
    
    def get_average_latency(self) -> float:
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count
    
    def get_metrics(self) -> Dict:
        return {
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / (self.success_count + self.failure_count) if (self.success_count + self.failure_count) > 0 else 1.0,
            'avg_latency_ms': self.get_average_latency(),
            'circuit_breaker_trips': self.circuit_breaker_trips,
            'db_fallback_count': self.db_fallback_count,
            'redis_failure_count': self.redis_failure_count
        }


# ============================================================
# 💀 Dead Letter Queue
# ============================================================

class DeadLetterEvent(models.Model):
    """نموذج للأحداث التي فشلت نهائياً"""
    original_event_id = models.IntegerField()
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    error_message = models.TextField()
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'core_dead_letter_events'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['resolved']),
            models.Index(fields=['event_type']),
        ]


class DeadLetterQueue:
    """إدارة الأحداث الفاشلة نهائياً"""
    
    @staticmethod
    def send_failed_event(event: OutboxEvent, error: str, retry_count: int):
        """إرسال الحدث الفاشل إلى DLQ"""
        try:
            dlq_event = DeadLetterEvent.objects.create(
                original_event_id=event.id,
                event_type=event.event_type,
                payload=event.payload,
                error_message=error[:1000],
                retry_count=retry_count
            )
            StructuredLogger.log('ERROR', f"Event sent to Dead Letter Queue", 
                                dlq_id=dlq_event.id,
                                event_id=event.id,
                                event_type=event.event_type,
                                retry_count=retry_count,
                                error=error[:200])
            return dlq_event
        except Exception as e:
            logger.critical(f"Failed to send event to DLQ: {e}", exc_info=True)
    
    @staticmethod
    def retry_from_dlq(dlq_id: int) -> bool:
        """إعادة محاولة حدث من DLQ"""
        try:
            dlq_event = DeadLetterEvent.objects.get(id=dlq_id, resolved=False)
            # إعادة إنشاء الحدث في outbox
            new_event = OutboxEvent.objects.create(
                event_type=dlq_event.event_type,
                payload=dlq_event.payload,
                status='pending',
                correlation_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4())
            )
            dlq_event.resolved = True
            dlq_event.save()
            StructuredLogger.log('INFO', f"Event retried from DLQ", 
                                dlq_id=dlq_id, 
                                new_event_id=new_event.id)
            return True
        except DeadLetterEvent.DoesNotExist:
            logger.error(f"DLQ event {dlq_id} not found or already resolved")
            return False
        except Exception as e:
            logger.error(f"Failed to retry from DLQ: {e}")
            return False


# ============================================================
# 📦 Event Schemas (Pydantic Validation)
# ============================================================

class ContractCompletedPayload(BaseModel):
    """Schema لحدث إكمال العقد"""
    contract_id: int = Field(..., gt=0)
    client_id: int = Field(..., gt=0)
    freelancer_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": 123,
                "client_id": 456,
                "freelancer_id": 789,
                "title": "Website Development"
            }
        }


class SkillPostCreatedPayload(BaseModel):
    """Schema لحدث إنشاء منشور مهارة"""
    skill_id: int = Field(..., gt=0)
    post_id: int = Field(..., gt=0)


class UserRegisteredPayload(BaseModel):
    """Schema لحدث تسجيل مستخدم"""
    user_id: int = Field(..., gt=0)
    username: str = Field(..., min_length=3, max_length=150)


# ============================================================
# 🔄 Stale Event Recovery with DLQ
# ============================================================

@shared_task(queue='low_priority', bind=True)
def recover_stale_outbox_events(self, timeout_minutes: int = 30, max_retries: int = 3) -> Dict[str, int]:
    """
    ✅ استرداد الأحداث العالقة مع إرسال المتكررة الفشل إلى DLQ
    """
    threshold = timezone.now() - timedelta(minutes=timeout_minutes)
    
    stats = {'recovered': 0, 'stale_found': 0, 'sent_to_dlq': 0}
    
    with transaction.atomic():
        stale_events = OutboxEvent.objects.select_for_update().filter(
            Q(status='processing') | Q(status='pending'),
            processed_at__lt=threshold
        )
        
        stale_count = stale_events.count()
        stats['stale_found'] = stale_count
        
        for event in stale_events:
            # إذا تجاوز الحد الأقصى للمحاولات
            if event.retry_count >= max_retries:
                DeadLetterQueue.send_failed_event(
                    event, 
                    f"Exceeded max retries ({max_retries}) after being stale for {timeout_minutes} minutes",
                    event.retry_count
                )
                event.delete()  # حذف من outbox بعد الإرسال إلى DLQ
                stats['sent_to_dlq'] += 1
            else:
                # إعادة تعيين الحالة إلى pending
                event.status = 'pending'
                event.error_message = f"Recovered from stale state, retry {event.retry_count + 1}"
                event.retry_count = F('retry_count') + 1
                event.save(update_fields=['status', 'error_message', 'retry_count'])
                stats['recovered'] += 1
        
        if stats['recovered'] > 0 or stats['sent_to_dlq'] > 0:
            StructuredLogger.log('WARNING', f"Stale events processed", 
                                recovered=stats['recovered'],
                                sent_to_dlq=stats['sent_to_dlq'],
                                total_stale=stale_count)
    
    return stats


# ============================================================
# 🔄 Improved Outbox Processor with CASE/WHEN
# ============================================================

class OutboxProcessor:
    """معالج Outbox متكامل مع state machine وجميع التحسينات"""
    
    @staticmethod
    def validate_event_payload(event_type: str, payload: Dict) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """✅ التحقق من صحة payload الحدث"""
        if not PYDANTIC_AVAILABLE:
            return True, payload, None
        
        try:
            if event_type == 'contract.completed':
                validated = ContractCompletedPayload(**payload)
                return True, validated.model_dump(), None
            elif event_type == 'skill.post_created':
                validated = SkillPostCreatedPayload(**payload)
                return True, validated.model_dump(), None
            elif event_type == 'user.registered':
                validated = UserRegisteredPayload(**payload)
                return True, validated.model_dump(), None
            else:
                return True, payload, None
        except ValidationError as e:
            return False, None, str(e)
    
    @staticmethod
    def _fetch_pending_events(batch_size: int, retry_timeout_ms: int = 1000) -> List[OutboxEvent]:
        """جلب الأحداث pending مع قفل للصف وإعادة محاولة ذكية"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with transaction.atomic():
                    return list(OutboxEvent.objects.select_for_update(
                        skip_locked=False,  # انتظر بدل تخطي
                        nowait=False
                    ).filter(
                        status='pending'
                    )[:batch_size])
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(retry_timeout_ms / 1000)
                    continue
                raise e
        return []
    
    @staticmethod
    def _bulk_update_status(event_ids: List[int], status: str, **kwargs):
        """تحديث جماعي لحالة الأحداث"""
        if not event_ids:
            return
        
        update_fields = {'status': status, 'updated_at': timezone.now()}
        update_fields.update(kwargs)
        
        OutboxEvent.objects.filter(id__in=event_ids).update(**update_fields)
    
    @staticmethod
    def _process_single_event(event: OutboxEvent) -> Tuple[bool, Optional[str]]:
        """معالجة حدث فردي وإرجاع النتيجة"""
        start_time = time.time()
        
        try:
            # ✅ Schema validation
            is_valid, validated_payload, error = OutboxProcessor.validate_event_payload(
                event.event_type, event.payload
            )
            
            if not is_valid:
                MetricsCollector().record_failure()
                return False, f"Validation error: {error}"
            
            # تحديث payload بالنسخة المحققة
            if validated_payload:
                event.payload = validated_payload
                event.save(update_fields=['payload'])
            
            # معالجة الحدث
            if event.event_type == 'contract.completed':
                EventHandler.handle_contract_completed(
                    event.payload.get('contract_id'),
                    event.payload.get('client_id'),
                    event.payload.get('freelancer_id'),
                    event.correlation_id,
                    event.trace_id
                )
            elif event.event_type == 'skill.post_created':
                EventHandler.handle_skill_post_created(
                    event.payload.get('skill_id'),
                    event.correlation_id
                )
            elif event.event_type == 'user.registered':
                EventHandler.handle_user_registered(
                    event.payload.get('user_id'),
                    event.correlation_id
                )
            
            MetricsCollector().record_success((time.time() - start_time) * 1000)
            return True, None
            
        except Exception as e:
            MetricsCollector().record_failure()
            return False, str(e)
    
    @staticmethod
    def process_events(batch_size: int = 50, max_retries: int = 3) -> Dict[str, int]:
        """
        ✅ معالجة الأحداث مع state machine و bulk updates باستخدام CASE/WHEN
        """
        stats = {
            'claimed': 0, 
            'completed': 0, 
            'failed': 0, 
            'validation_errors': 0,
            'bulk_updated': 0,
            'sent_to_dlq': 0
        }
        
        with transaction.atomic():
            # 1. جلب الأحداث pending مع قفل
            events = OutboxProcessor._fetch_pending_events(batch_size)
            
            if not events:
                return stats
            
            # 2. Claiming state: تغيير الحالة إلى processing
            event_ids = [e.id for e in events]
            OutboxProcessor._bulk_update_status(
                event_ids, 
                'processing',
                processed_at=timezone.now()
            )
            stats['claimed'] = len(event_ids)
            
            # 3. معالجة الأحداث وتجميع النتائج
            completed_ids = []
            failed_events = []  # تخزين (event, error)
            
            for event in events:
                success, error = OutboxProcessor._process_single_event(event)
                
                if success:
                    completed_ids.append(event.id)
                else:
                    failed_events.append((event, error))
                    
                    if "Validation error" in error:
                        stats['validation_errors'] += 1
            
            # 4. تحديث جماعي للأحداث المكتملة
            if completed_ids:
                OutboxProcessor._bulk_update_status(
                    completed_ids,
                    'completed',
                    completed_at=timezone.now()
                )
                stats['completed'] = len(completed_ids)
                stats['bulk_updated'] += len(completed_ids)
            
            # 5. تحديث جماعي للأحداث الفاشلة باستخدام CASE/WHEN
            if failed_events:
                # إنشاء حالات لكل حدث فاشل
                cases = []
                dlq_candidates = []
                
                for event, error in failed_events:
                    # زيادة عداد المحاولات
                    new_retry_count = (event.retry_count or 0) + 1
                    
                    if new_retry_count >= max_retries:
                        dlq_candidates.append((event, error, new_retry_count))
                    else:
                        cases.append(
                            When(id=event.id, then=Value(error[:500]))
                        )
                
                # تحديث الأحداث التي لم تصل للحد الأقصى
                if cases:
                    failed_ids = [event.id for event, _ in failed_events 
                                 if (event.retry_count or 0) + 1 < max_retries]
                    
                    if failed_ids:
                        OutboxEvent.objects.filter(id__in=failed_ids).update(
                            status='failed',
                            error_message=Case(*cases, output_field=CharField()),
                            failed_at=timezone.now(),
                            retry_count=F('retry_count') + 1
                        )
                        stats['failed'] = len(failed_ids)
                
                # إرسال الأحداث التي تجاوزت المحاولات إلى DLQ
                for event, error, retry_count in dlq_candidates:
                    DeadLetterQueue.send_failed_event(event, error, retry_count)
                    event.delete()  # حذف من outbox
                    stats['sent_to_dlq'] += 1
                    stats['failed'] += 1
        
        # تسجيل المقاييس
        metrics = MetricsCollector().get_metrics()
        StructuredLogger.log('INFO', f"Outbox processing completed with metrics", 
                            **stats, **metrics)
        
        return stats


# ============================================================
# 🔄 Async Audit Log with Retry and Circuit Breaker
# ============================================================

@shared_task(queue='low_priority', bind=True, max_retries=5)
def async_audit_log(
    self,
    user_id: int,
    username: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Dict = None,
    correlation_id: str = None
):
    """✅ تسجيل audit log بشكل غير متزامن مع retry logic محسّن"""
    start_time = time.time()
    
    try:
        from .models import AuditLog
        from django.contrib.auth.models import User
        
        # استخدام cache لتقليل الـ DB queries
        cache_key = f"user_exists_{user_id}"
        if not cache.get(cache_key):
            user = User.objects.only('id').get(id=user_id)
            cache.set(cache_key, True, timeout=300)
        
        AuditLog.objects.create(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details or {},
            correlation_id=correlation_id or str(uuid.uuid4()),
            created_at=timezone.now()
        )
        
        latency_ms = (time.time() - start_time) * 1000
        StructuredLogger.log('DEBUG', f"Async audit log created", 
                            user_id=user_id, 
                            action=action, 
                            latency_ms=latency_ms)
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for audit log")
        return
        
    except Exception as e:
        logger.error(f"Failed to create async audit log (attempt {self.request.retries + 1}/{self.max_retries}): {e}")
        
        if self.request.retries < self.max_retries:
            # Exponential backoff with jitter
            base_delay = 60 * (2 ** self.request.retries)
            jitter = random.uniform(0, base_delay * 0.1)
            countdown = base_delay + jitter
            raise self.retry(exc=e, countdown=countdown)


# ============================================================
# 🔄 Improved Rate Limiter DB Fallback (محسّن)
# ============================================================

class ImprovedRateLimiterDBFallback:
    """✅ Rate limiter DB fallback محسّن مع cleanup وتحسين الأداء"""
    
    @staticmethod
    def cleanup_old_logs(days_to_keep: int = 7) -> int:
        """تنظيف السجلات القديمة"""
        cutoff = timezone.now() - timedelta(days=days_to_keep)
        result = SkillUpdateLog.objects.filter(created_at__lt=cutoff).delete()
        deleted_count = result[0] if result else 0
        
        if deleted_count:
            StructuredLogger.log('INFO', f"Cleaned up old rate limit logs", 
                                deleted_count=deleted_count)
        
        return deleted_count
    
    @staticmethod
    def check_and_increment(skill_id: int, max_requests: int = 1, window_hours: int = 1) -> bool:
        cutoff_time = timezone.now() - timedelta(hours=window_hours)
        
        try:
            with transaction.atomic():
                recent_logs = SkillUpdateLog.objects.select_for_update().filter(
                    skill_id=skill_id,
                    created_at__gte=cutoff_time
                ).count()
                
                if recent_logs >= max_requests:
                    StructuredLogger.log('WARNING', f"Rate limit hit (DB fallback)", 
                                        skill_id=skill_id,
                                        recent_count=recent_logs,
                                        limit=max_requests)
                    return False
                
                SkillUpdateLog.objects.create(
                    skill_id=skill_id,
                    hour_key=timezone.now().strftime('%Y%m%d%H')
                )
                return True
                
        except Exception as e:
            logger.error(f"DB fallback failed: {e}")
            return True


# ============================================================
# 🔄 Connection Pool for Redis with Timeout
# ============================================================

class RedisConnectionPool:
    """✅ إدارة اتصالات Redis مع connection pooling و timeout"""
    
    _instance = None
    _connection_pool = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def _get_pool(self):
        if self._connection_pool is None:
            with self._lock:
                if self._connection_pool is None:
                    import redis
                    
                    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/1')
                    
                    self._connection_pool = redis.ConnectionPool.from_url(
                        redis_url,
                        max_connections=20,
                        decode_responses=True,
                        socket_connect_timeout=3,
                        socket_timeout=3,
                        socket_keepalive=True,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
        
        return self._connection_pool
    
    @contextmanager
    def get_client(self, timeout_ms: int = 5000):
        """الحصول على عميل Redis مع timeout وضمان الإغلاق"""
        import redis
        
        client = None
        try:
            pool = self._get_pool()
            client = redis.Redis(connection_pool=pool)
            # تعيين timeout للعمليات
            client.connection_pool.connection_kwargs['socket_timeout'] = timeout_ms / 1000
            yield client
        except redis.TimeoutError:
            MetricsCollector().record_redis_failure()
            raise
        except Exception as e:
            MetricsCollector().record_redis_failure()
            raise
        finally:
            if client:
                client.close()


# ============================================================
# 🔄 Sliding Window Rate Limiter (نهائي)
# ============================================================

class ImprovedSlidingWindowRateLimiter:
    """✅ Rate limiter متكامل مع connection pooling و timeout"""
    
    def __init__(self, key_prefix: str, window_seconds: int = 3600, max_requests: int = 1):
        self.key_prefix = key_prefix
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._redis_pool = RedisConnectionPool()
        self._metrics = MetricsCollector()
    
    def _check_db_fallback(self, skill_id: int) -> bool:
        """التحقق من قاعدة البيانات عند فشل Redis"""
        if not isinstance(skill_id, int) or skill_id <= 0:
            StructuredLogger.log('WARNING', f"Invalid skill_id for DB fallback", 
                                skill_id=skill_id)
            return True
        
        cutoff_time = timezone.now() - timedelta(seconds=self.window_seconds)
        
        try:
            with transaction.atomic():
                recent_logs = SkillUpdateLog.objects.select_for_update().filter(
                    skill_id=skill_id,
                    created_at__gte=cutoff_time
                ).count()
                
                if recent_logs >= self.max_requests:
                    StructuredLogger.log('WARNING', f"Rate limit hit (DB fallback)", 
                                        skill_id=skill_id,
                                        recent_count=recent_logs,
                                        limit=self.max_requests,
                                        window_seconds=self.window_seconds)
                    return False
                
                SkillUpdateLog.objects.create(
                    skill_id=skill_id,
                    hour_key=timezone.now().strftime('%Y%m%d%H')
                )
                self._metrics.record_db_fallback()
                return True
                
        except Exception as e:
            logger.error(f"DB fallback failed: {e}")
            return True
    
    def _validate_identifier(self, identifier: str) -> int:
        """التحقق من صحة identifier"""
        if not identifier or not identifier.isdigit():
            raise ValueError(f"Identifier must be a positive integer, got '{identifier}'")
        
        skill_id = int(identifier)
        if skill_id <= 0:
            raise ValueError(f"Identifier must be positive, got {skill_id}")
        
        return skill_id
    
    def check_and_increment(self, identifier: str, timeout_ms: int = 3000) -> Tuple[bool, Dict]:
        """
        ✅ التحقق من معدل الطلبات مع timeout
        """
        start_time = time.time()
        
        try:
            skill_id = self._validate_identifier(identifier)
        except ValueError as e:
            StructuredLogger.log('ERROR', f"Invalid identifier", 
                                identifier=identifier, error=str(e))
            return True, {'mode': 'fail_open', 'error': str(e)}
        
        key = f"ratelimit:{self.key_prefix}:{identifier}"
        current_time = time.time() * 1000
        window_start = current_time - (self.window_seconds * 1000)
        
        # تحسين Lua script
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])
        
        -- حذف الطلبات القديمة
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
        
        -- الحصول على العدد الحالي
        local current_count = redis.call('ZCARD', key)
        
        -- التحقق من السماح
        if current_count < max_requests then
            -- إضافة طلب جديد مع timestamp فريد
            local timestamp = now .. ':' .. math.random(1, 999999) .. ':' .. math.random(1, 999999)
            redis.call('ZADD', key, now, timestamp)
            redis.call('EXPIRE', key, window_seconds)
            
            return {
                1, current_count + 1, 
                max_requests - (current_count + 1), 
                window_seconds
            }
        else
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local reset_in = window_seconds
            
            if #oldest > 0 then
                local oldest_time = tonumber(oldest[2])
                local elapsed = now - oldest_time
                reset_in = math.max(0, window_seconds - (elapsed / 1000))
            end
            
            return {0, current_count, 0, math.ceil(reset_in)}
        end
        """
        
        try:
            with self._redis_pool.get_client(timeout_ms) as redis_client:
                script = redis_client.register_script(lua_script)
                result = script(
                    keys=[key], 
                    args=[current_time, window_start, self.max_requests, self.window_seconds]
                )
                
                allowed = result[0] == 1
                latency_ms = (time.time() - start_time) * 1000
                
                stats = {
                    'limit': self.max_requests,
                    'remaining': int(result[2]),
                    'current': int(result[1]),
                    'reset': int(time.time() + result[3]),
                    'reset_in_seconds': int(result[3]),
                    'mode': 'redis',
                    'latency_ms': round(latency_ms, 2)
                }
                return allowed, stats
                
        except Exception as e:
            self._metrics.record_redis_failure()
            StructuredLogger.log('WARNING', f"Redis failed, using DB fallback", 
                                error=str(e), identifier=identifier)
            
            try:
                allowed = self._check_db_fallback(skill_id)
            except Exception as db_error:
                logger.error(f"DB fallback also failed: {db_error}")
                allowed = True
            
            stats = {
                'mode': 'db_fallback', 
                'limit': self.max_requests,
                'latency_ms': round((time.time() - start_time) * 1000, 2)
            }
            return allowed, stats


# ============================================================
# 🔄 Circuit Breaker with Metrics and Half-Open
# ============================================================

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerWithFallback:
    """✅ Circuit Breaker متكامل مع metrics وتحسين half-open"""
    
    def __init__(self, service_name: str, fallback_function: Callable = None, 
                 cached_stale_seconds: int = 60, failure_threshold: int = 5,
                 reset_timeout_seconds: int = 60, half_open_max_calls: int = 3):
        self.service_name = service_name
        self.fallback_function = fallback_function
        self.cached_stale_seconds = cached_stale_seconds
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        
        self._last_successful_response = None
        self._last_successful_time = None
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0
        self._lock = Lock()
        self._metrics = MetricsCollector()
    
    def _should_attempt_reset(self) -> bool:
        """التحقق من إعادة فتح الـ circuit"""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            if time.time() - self._last_failure_time > self.reset_timeout_seconds:
                with self._lock:
                    if self._state == CircuitState.OPEN:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        StructuredLogger.log('INFO', f"Circuit breaker half-open for {self.service_name}")
                        return True
        return False
    
    def execute(self, func: Callable, *args, **kwargs):
        """تنفيذ الدالة مع circuit breaker محسّن"""
        self._should_attempt_reset()
        
        with self._lock:
            current_state = self._state
        
        if current_state == CircuitState.OPEN:
            StructuredLogger.log('WARNING', f"Circuit breaker OPEN for {self.service_name}")
            return self._handle_open_state(*args, **kwargs)
        
        try:
            result = self._execute_with_protection(func, *args, **kwargs)
            
            # إذا كنا في half-open ونجحت، نغلق الـ circuit
            if current_state == CircuitState.HALF_OPEN:
                with self._lock:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    StructuredLogger.log('INFO', f"Circuit breaker closed for {self.service_name}")
            
            return result
            
        except Exception as e:
            return self._handle_failure(e, *args, **kwargs)
    
    def _execute_with_protection(self, func: Callable, *args, **kwargs):
        """تنفيذ الدالة مع الحماية"""
        if CIRCUIT_BREAKER_AVAILABLE and self.service_name in circuit_breakers:
            breaker = circuit_breakers[self.service_name]
            
            @breaker
            def protected_func():
                result = func(*args, **kwargs)
                self._last_successful_response = result
                self._last_successful_time = time.time()
                with self._lock:
                    self._failure_count = 0
                return result
            
            return protected_func()
        else:
            result = func(*args, **kwargs)
            self._last_successful_response = result
            self._last_successful_time = time.time()
            with self._lock:
                self._failure_count = 0
            return result
    
    def _handle_open_state(self, *args, **kwargs):
        """معالجة حالة circuit مفتوح"""
        if self._last_successful_response and self._last_successful_time:
            age = time.time() - self._last_successful_time
            if age < self.cached_stale_seconds:
                StructuredLogger.log('INFO', f"Using cached stale response", 
                                    age_seconds=age)
                return self._last_successful_response
        
        if self.fallback_function:
            StructuredLogger.log('INFO', f"Using fallback function")
            return self.fallback_function(*args, **kwargs)
        
        raise Exception(f"Circuit breaker open for {self.service_name}")
    
    def _handle_failure(self, exception: Exception, *args, **kwargs):
        """معالجة الفشل وتحديث حالة circuit"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    self._state = CircuitState.OPEN
                    self._metrics.record_circuit_trip()
                    StructuredLogger.log('WARNING', f"Circuit breaker reopened", 
                                        half_open_calls=self._half_open_calls)
            elif self._failure_count >= self.failure_threshold and self._state != CircuitState.OPEN:
                self._state = CircuitState.OPEN
                self._metrics.record_circuit_trip()
                StructuredLogger.log('WARNING', f"Circuit breaker OPENED", 
                                    failure_count=self._failure_count)
        
        StructuredLogger.log('WARNING', f"Circuit breaker error", 
                            error=str(exception), 
                            state=self._state.value)
        
        if self.fallback_function:
            return self.fallback_function(*args, **kwargs)
        
        raise exception


# ============================================================
# 🔄 Celery Tasks (محسّنة نهائياً)
# ============================================================

@shared_task(queue='medium_priority', bind=True, max_retries=3)
def process_outbox_events_v2(self, batch_size: int = 50):
    """✅ معالجة الأحداث مع جميع التحسينات"""
    try:
        stats = OutboxProcessor.process_events(batch_size)
        
        StructuredLogger.log('INFO', f"Outbox processing V9 completed", **stats)
        
        # تنظيف دوري (كل 1000 معالجة)
        if hasattr(process_outbox_events_v2, 'call_count'):
            process_outbox_events_v2.call_count += 1
        else:
            process_outbox_events_v2.call_count = 1
        
        if process_outbox_events_v2.call_count % 1000 == 0:
            scheduled_cleanup_rate_limits.delay()
        
        return stats
        
    except Exception as e:
        logger.error(f"Outbox processing failed: {e}")
        
        if self.request.retries < self.max_retries:
            jitter = random.uniform(0, 30)
            countdown = 60 * (2 ** self.request.retries) + jitter
            raise self.retry(exc=e, countdown=countdown)
        
        raise


@shared_task(queue='low_priority', bind=True)
def scheduled_recovery(self):
    """مهمة مجدولة لاسترداد الأحداث العالقة"""
    return recover_stale_outbox_events.delay()


@shared_task(queue='low_priority')
def scheduled_cleanup_rate_limits():
    """تنظيف دوري لسجلات rate limit"""
    return ImprovedRateLimiterDBFallback.cleanup_old_logs()


@shared_task(queue='low_priority')
def retry_dead_letter_events():
    """إعادة محاولة الأحداث في DLQ (كل ساعة)"""
    dlq_events = DeadLetterEvent.objects.filter(resolved=False, created_at__lt=timezone.now() - timedelta(hours=1))
    
    stats = {'total': 0, 'retried': 0, 'failed': 0}
    
    for dlq_event in dlq_events[:100]:
        stats['total'] += 1
        if DeadLetterQueue.retry_from_dlq(dlq_event.id):
            stats['retried'] += 1
        else:
            stats['failed'] += 1
    
    if stats['total'] > 0:
        StructuredLogger.log('INFO', f"DLQ retry completed", **stats)
    
    return stats


@shared_task(queue='low_priority')
def get_metrics_report():
    """تقرير المقاييس (مراقبة الصحة)"""
    metrics = MetricsCollector().get_metrics()
    StructuredLogger.log('INFO', f"System metrics report", **metrics)
    return metrics

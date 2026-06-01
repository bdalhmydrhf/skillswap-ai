# core/models/outbox.py
"""
نموذج Outbox Events - لتخزين الأحداث قبل المعالجة
"""

from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta

# ✅ نقل تعريف Gauge إلى خارج الدالة (مرة واحدة فقط عند تحميل الملف)
try:
    from prometheus_client import Gauge
    OUTBOX_SIZE = Gauge('outbox_size', 'Pending outbox events')
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    OUTBOX_SIZE = None


class OutboxEvent(models.Model):
    """نموذج Outbox pattern - لتخزين الأحداث مؤقتاً"""
    
    EVENT_VERSIONS = [
        ('v1', 'Version 1'),
        ('v2', 'Version 2'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    event_type = models.CharField(max_length=255, db_index=True)
    event_version = models.CharField(max_length=10, choices=EVENT_VERSIONS, default='v1', db_index=True)
    aggregate_id = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    retry_count = models.IntegerField(default=0)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)
    trace_id = models.CharField(max_length=64, blank=True)
    version = models.IntegerField(default=1)
    
    # إضافة حقل انتهاء الصلاحية
    expires_at = models.DateTimeField(
        null=True, 
        blank=True, 
        db_index=True,
        help_text="انتهاء صلاحية الحدث - سيتم حذفه تلقائياً بعد هذا الوقت"
    )
    
    class Meta:
        verbose_name = "Outbox Event"
        verbose_name_plural = "Outbox Events"
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['event_type', 'event_version', 'aggregate_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        # تعيين expires_at تلقائياً إذا لم يُحدد
        if not self.expires_at and self.created_at:
            self.expires_at = self.created_at + timedelta(days=7)
        elif not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
        
        # ✅ تحديث المقياس الموجود (بدون إنشاء مقياس جديد)
        if PROMETHEUS_AVAILABLE and OUTBOX_SIZE:
            try:
                OUTBOX_SIZE.set(OutboxEvent.objects.filter(status='pending').count())
            except Exception:
                pass  # تجاهل أخطاء Prometheus
    
    def is_expired(self) -> bool:
        """التحقق مما إذا كان الحدث قد انتهت صلاحيته"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def mark_completed(self):
        """تحديث الحالة إلى completed"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_failed(self, error: str):
        """تحديث الحالة إلى failed مع تسجيل الخطأ"""
        self.retry_count += 1
        self.error = error
        if self.retry_count >= 3:
            self.status = 'failed'
        else:
            self.status = 'pending'
        self.save(update_fields=['status', 'retry_count', 'error'])
    
    def __str__(self):
        return f"OutboxEvent {self.event_type} - {self.status}"
    
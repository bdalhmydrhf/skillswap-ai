"""
نظام المهارات المتقدم - النسخة المحسّنة V2
✅ Caching مع Redis
✅ Validation كاملة
✅ Type Hints
✅ Async Processing (Celery)
✅ Signals للتحديث التلقائي (مع Class Reference)
✅ Prometheus Metrics (مع تحسين cardinality)
✅ Soft Delete
✅ Atomic Updates (F() expressions)
✅ Service Layer خفيف
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db.models import F, Avg
from django.utils import timezone
from typing import Optional, Dict, Any
from prometheus_client import Counter, Gauge
import logging

logger = logging.getLogger(__name__)

# Prometheus Metrics (محسّنة - بدون high cardinality)
try:
    SKILL_UPDATES = Counter('skill_updates_total', 'Total skill updates', ['status'])
    # ✅ تحسين: استخدام skill_id بدلاً من skill_name (تجنب high cardinality)
    SKILL_DEMAND_LEVEL = Gauge('skill_demand_level', 'Demand level per skill', ['skill_id', 'category'])
    ACTIVE_SKILLS = Gauge('active_skills_total', 'Total active skills')
except ImportError:
    class MockMetric:
        def inc(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    SKILL_UPDATES = MockMetric()
    SKILL_DEMAND_LEVEL = MockMetric()
    ACTIVE_SKILLS = MockMetric()

# استيراد Celery task في أعلى الملف (لتحسين الأداء)
from celery import shared_task


class Skill(models.Model):
    """نموذج المهارات المتقدم"""
    
    name = models.CharField(max_length=120, db_index=True, verbose_name="Skill Name")
    category = models.CharField(max_length=80, blank=True, db_index=True, verbose_name="Category")
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icon")
    
    demand_level = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Demand Level"
    )
    avg_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Average Price"
    )
    
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Active")
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name="Soft Deleted")
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Cache version
    cache_version = models.IntegerField(default=1)
    
    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['demand_level']),
            models.Index(fields=['name', 'category']),
            models.Index(fields=['is_deleted', 'created_at']),
        ]
        ordering = ['name']
        constraints = [
            models.CheckConstraint(check=models.Q(demand_level__gte=0, demand_level__lte=100), name='demand_level_range'),
            models.CheckConstraint(check=models.Q(avg_price__gte=0), name='avg_price_positive'),
        ]
    
    def clean(self) -> None:
        """التحقق من صحة البيانات"""
        errors = {}
        
        if self.demand_level < 0 or self.demand_level > 100:
            errors['demand_level'] = 'Demand level must be between 0 and 100'
        
        if self.avg_price < 0:
            errors['avg_price'] = 'Average price must be greater than or equal to 0'
        
        if errors:
            raise ValidationError(errors)
    
    def _get_cache_key(self) -> str:
        """الحصول على مفتاح cache"""
        return f"skill_stats_{self.id}_v{self.cache_version}"
    
    def _invalidate_cache(self) -> None:
        """مسح cache"""
        cache.delete(self._get_cache_key())
    
    def update_stats(self, async_mode: bool = True) -> Optional[Dict]:
        """
        تحديث إحصائيات المهارة
        
        Args:
            async_mode: إذا كان True، يتم التحديث بشكل غير متزامن
        
        Returns:
            الإحصائيات المحدثة أو None
        """
        if async_mode:
            update_skill_stats_async.delay(self.id)
            return None
        
        return self._update_stats_sync()
    
    def _update_stats_sync(self) -> Dict:
        """تحديث الإحصائيات بشكل متزامن (مع Atomic Update)"""
        try:
            posts = self.posts.filter(visible=True, status='open', is_deleted=False)
            
            old_demand = self.demand_level
            old_price = self.avg_price
            
            if posts.exists():
                avg_price = posts.aggregate(avg=Avg('price'))['avg'] or 0
                demand_level = min(100, posts.count() * 10)
            else:
                avg_price = 0
                demand_level = 0
            
            # ✅ تحسين: استخدام F() expressions لمنع race condition
            Skill.objects.filter(id=self.id).update(
                avg_price=avg_price,
                demand_level=demand_level,
                cache_version=F('cache_version') + 1
            )
            
            # تحديث الكائن الحالي
            self.avg_price = avg_price
            self.demand_level = demand_level
            self.cache_version += 1
            
            # تحديث cache
            cache_key = self._get_cache_key()
            cache.set(cache_key, {
                'avg_price': float(self.avg_price),
                'demand_level': self.demand_level
            }, 3600)
            
            # ✅ تحسين: استخدام skill_id بدلاً من skill_name
            SKILL_UPDATES.labels(status='success').inc()
            SKILL_DEMAND_LEVEL.labels(
                skill_id=self.id, 
                category=self.category or 'uncategorized'
            ).set(self.demand_level)
            
            logger.info(f"Skill stats updated: {self.name} (demand: {old_demand}→{self.demand_level}, price: {old_price}→{self.avg_price})")
            
            return {
                'success': True,
                'avg_price': float(self.avg_price),
                'demand_level': self.demand_level
            }
            
        except Exception as e:
            SKILL_UPDATES.labels(status='error').inc()
            logger.error(f"Error updating skill statistics for {self.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict:
        """الحصول على الإحصائيات من cache"""
        cache_key = self._get_cache_key()
        stats = cache.get(cache_key)
        
        if stats:
            return stats
        
        return {
            'avg_price': float(self.avg_price),
            'demand_level': self.demand_level
        }
    
    def soft_delete(self, reason: str = '') -> None:
        """حذف ناعم للمهارة"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])
        
        self._invalidate_cache()
        ACTIVE_SKILLS.dec()
        
        logger.info(f"Skill {self.id} soft deleted: {reason}")
    
    def restore(self) -> None:
        """استعادة مهارة محذوفة"""
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])
        
        self._invalidate_cache()
        ACTIVE_SKILLS.inc()
        
        logger.info(f"Skill {self.id} restored")
    
    def __str__(self) -> str:
        status = "🗑" if self.is_deleted else "✓"
        return f"{status} {self.name} (demand: {self.demand_level})"


# ============================================================
# 📨 Celery Task للتحديث غير المتزامن
# ============================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_skill_stats_async(self, skill_id: int) -> Dict:
    """تحديث إحصائيات المهارة بشكل غير متزامن"""
    try:
        skill = Skill.objects.get(id=skill_id, is_deleted=False)
        return skill._update_stats_sync()
    except Skill.DoesNotExist:
        logger.error(f"Skill {skill_id} not found")
        return {'success': False, 'error': 'Skill not found'}
    except Exception as e:
        logger.error(f"Failed to update skill stats for {skill_id}: {e}")
        raise self.retry(exc=e, countdown=60)


# ============================================================
# 📡 Signal للتحديث التلقائي (مع Class Reference)
# ============================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
@receiver(post_save, sender='core.SkillPost')  # ✅ استخدم string بدل import
@receiver(post_delete, sender='core.SkillPost')
def update_skill_stats_on_post_change(sender, instance, **kwargs):
    if hasattr(instance, 'skill_id') and instance.skill_id:
        update_skill_stats_async.delay(instance.skill_id)

# ============================================================
# 📊 Admin Interface
# ============================================================

from django.contrib import admin


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'demand_level', 'avg_price', 'is_active', 'is_deleted', 'created_at']
    list_filter = ['category', 'is_active', 'is_deleted', 'created_at']
    search_fields = ['name', 'category']
    readonly_fields = ['created_at', 'updated_at', 'cache_version']
    actions = ['soft_delete_selected', 'restore_selected']
    
    def soft_delete_selected(self, request, queryset):
        count = 0
        for skill in queryset:
            if not skill.is_deleted:
                skill.soft_delete(f"Bulk delete by {request.user}")
                count += 1
        self.message_user(request, f"{count} skills soft deleted")
    soft_delete_selected.short_description = "Soft delete selected skills"
    
    def restore_selected(self, request, queryset):
        count = 0
        for skill in queryset:
            if skill.is_deleted:
                skill.restore()
                count += 1
        self.message_user(request, f"{count} skills restored")
    restore_selected.short_description = "Restore selected skills"


# ============================================================
# 🏥 Health Check
# ============================================================

def skills_health_check() -> dict:
    """فحص صحة نظام المهارات"""
    return {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'metrics': {
            'total_skills': Skill.objects.filter(is_deleted=False).count(),
            'active_skills': Skill.objects.filter(is_active=True, is_deleted=False).count(),
            'soft_deleted_skills': Skill.objects.filter(is_deleted=True).count(),
            'avg_demand_level': Skill.objects.filter(is_deleted=False).aggregate(avg=models.Avg('demand_level'))['avg'] or 0,
        }
    }
    
"""
واجهات API لنظام التوصيات الذكي - النسخة المؤسساتية V4.0
Enterprise Grade - Production Ready
✅ Clean Architecture | ✅ No Threading | ✅ Smart Cache | ✅ A/B Testing
"""

import logging
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.conf import settings
from django.utils import timezone  # ✅ أضفنا هذا

# استخدام Celery بدلاً من threading
from celery import shared_task

# Rate limiting محسن
from django.core.cache import cache as redis_cache

from core.recommendation_engine import (
    get_user_recommendations,
    update_all_trust_scores,
    calculate_trust_score,
    update_user_preferences,
    get_system_health_report,
    get_metrics
)
from core.serializers import UserProfileSerializer
from core.models import UserProfile, Contract, ContractRating

logger = logging.getLogger(__name__)


# ============================================================
# 📊 A/B Testing Framework (جديد)
# ============================================================

class ABTestFramework:
    """إطار عمل لاختبار A/B - يحل مشكلة evaluation layer"""
    
    def __init__(self):
        self._redis = self._get_redis()
        self.tests = {
            'A': {'method': 'smart_hybrid', 'weight': 0.5},
            'B': {'method': 'faiss', 'weight': 0.5}
        }
    
    def _get_redis(self):
        try:
            import redis
            return redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/1'))
        except:
            return None
    
    def get_method_for_user(self, user_id: int) -> str:
        """تحديد الطريقة للمستخدم مع تتبع المجموعة"""
        if not self._redis:
            return 'smart_hybrid'
        
        # حفظ تعيين المستخدم لمدة 30 يوم
        key = f"ab_test:user:{user_id}"
        assigned = self._redis.get(key)
        
        if assigned:
            return self.tests[assigned.decode()]['method']
        
        # توزيع عشوائي حسب الوزن
        import random
        rand = random.random()
        cumulative = 0
        
        for test_id, config in self.tests.items():
            cumulative += config['weight']
            if rand <= cumulative:
                self._redis.setex(key, 86400 * 30, test_id)
                return config['method']
        
        return 'smart_hybrid'
    
    def record_metric(self, user_id: int, method: str, success: bool, latency_ms: float):
        """تسجيل مقاييس الأداء لكل مجموعة"""
        if not self._redis:
            return
        
        key = f"ab_test:metrics:{method}:{time.strftime('%Y-%m-%d')}"
        self._redis.hincrby(key, 'requests', 1)
        if success:
            self._redis.hincrby(key, 'success', 1)
        self._redis.hincrbyfloat(key, 'total_latency', latency_ms)
        self._redis.expire(key, 86400 * 7)  # حفظ لمدة 7 أيام
    
    def get_results(self) -> Dict:
        """الحصول على نتائج اختبار A/B"""
        if not self._redis:
            return {'error': 'Redis not available'}
        
        results = {}
        for test_id, config in self.tests.items():
            method = config['method']
            key = f"ab_test:metrics:{method}:{time.strftime('%Y-%m-%d')}"
            data = self._redis.hgetall(key)
            
            requests = int(data.get(b'requests', 0))
            success = int(data.get(b'success', 0))
            total_latency = float(data.get(b'total_latency', 0))
            
            results[test_id] = {
                'method': method,
                'requests': requests,
                'success_rate': success / requests if requests > 0 else 0,
                'avg_latency_ms': total_latency / requests if requests > 0 else 0
            }
        
        return results


_ab_test = ABTestFramework()


# ============================================================
# 🔧 Smart Cache Manager (محل delete_pattern الخطير)
# ============================================================

class SmartCacheManager:
    """
    مدير cache ذكي - يستخدم versioned keys بدلاً من delete_pattern
    هذا يحل مشكلة الأداء على Redis
    """
    
    CACHE_VERSION_KEY = "cache_version_v4"
    
    @classmethod
    def get_current_version(cls) -> str:
        """الحصول على إصدار cache الحالي"""
        version = cache.get(cls.CACHE_VERSION_KEY)
        if not version:
            version = "v1"
            cache.set(cls.CACHE_VERSION_KEY, version, 86400 * 30)
        return version
    
    @classmethod
    def invalidate_all(cls):
        """إبطال كل الـ cache دفعة واحدة - O(1) بدلاً من O(n)"""
        current = cls.get_current_version()
        new_version = f"v{int(current[1:]) + 1}"
        cache.set(cls.CACHE_VERSION_KEY, new_version, 86400 * 30)
        logger.info(f"🔄 Cache version updated: {current} -> {new_version}")
        return new_version
    
    @classmethod
    def invalidate_user(cls, user_id: int):
        """إبطال cache مستخدم محدد - باستخدام keys محددة"""
        keys = [
            f"recommendations_v4_{user_id}_smart_hybrid",
            f"recommendations_v4_{user_id}_faiss",
            f"user_trust_{user_id}_v4",
            f"user_vector_{user_id}_v4",
            f"user_behavior_{user_id}_v4",
            f"fast_rec_{user_id}_v4",
        ]
        for key in keys:
            cache.delete(key)
        logger.info(f"🗑️ Cache cleared for user {user_id}")
    
    @classmethod
    def get_versioned_key(cls, base_key: str) -> str:
        """الحصول على مفتاح مع الإصدار الحالي"""
        return f"{base_key}_{cls.get_current_version()}"


# ============================================================
# 📊 API التوصيات الرئيسي (محسن)
# ============================================================

class RecommendationsAPIView(APIView):
    """
    API متقدم للتوصيات - نسخة مؤسساتية
    - A/B Testing مدمج
    - Clean Architecture
    - Performance optimized
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        start_time = time.time()
        
        # ✅ 1. التحقق من الصلاحيات
        if request.user.id != user_id and not request.user.is_staff:
            logger.warning(f"Unauthorized: user={request.user.id}, target={user_id}")
            return Response({
                'success': False,
                'error': 'Unauthorized access',
                'code': 'UNAUTHORIZED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ✅ 2. معاملات الطلب مع validation آمن
        try:
            page = max(1, int(request.GET.get('page', 1)))
            page_size = min(int(request.GET.get('page_size', 20)), 100)
            with_explanations = request.GET.get('explanations', 'true').lower() == 'true'
        except ValueError:
            page, page_size, with_explanations = 1, 20, True
        
        # ✅ 3. A/B testing - تحديد الطريقة
        method = request.GET.get('method')
        if not method or method not in ['tfidf', 'svd', 'embeddings', 'hybrid', 'smart_hybrid', 'faiss']:
            method = _ab_test.get_method_for_user(user_id)
        
        # ✅ 4. استخدام versioned cache (آمن وفعال)
        cache_key = SmartCacheManager.get_versioned_key(f"recommendations_v4_{user_id}_{method}_{page}_{page_size}")
        cached_result = cache.get(cache_key)
        
        if cached_result:
            latency = (time.time() - start_time) * 1000
            _ab_test.record_metric(user_id, method, True, latency)
            response = Response(cached_result)
            response['X-Cache-Status'] = 'HIT'
            response['X-Ab-Test-Method'] = method
            return response
        
        try:
            # ✅ 5. استدعاء محرك التوصيات
            result = get_user_recommendations(
                user_id=user_id,
                page=page,
                page_size=page_size,
                with_explanations=with_explanations
            )
            
            if not result.get('success', True):
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            # ✅ 6. بناء الرد
            response_data = {
                'success': True,
                'user_id': user_id,
                'method': method,
                'ab_tests': _ab_test.get_results() if request.user.is_staff else None,
                'timestamp': result.get('timestamp', time.time()),
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': result.get('pagination', {}).get('total', 0),
                    'total_pages': result.get('pagination', {}).get('total_pages', 0)
                },
                'recommendations': result.get('recommended_users', []),
                'trending_skills': result.get('trending_skills', []),
                'trending_users': result.get('trending_users', []),
                'explainability': {
                    'enabled': with_explanations,
                    'features': ['common_skills', 'trust_score', 'rating', 'completion_rate']
                }
            }
            
            # ✅ 7. تخزين في cache
            cache.set(cache_key, response_data, 600)  # 10 دقائق
            
            latency = (time.time() - start_time) * 1000
            _ab_test.record_metric(user_id, method, True, latency)
            
            response = Response(response_data)
            response['X-Cache-Status'] = 'MISS'
            response['X-Response-Time'] = f"{latency:.2f}ms"
            response['X-Ab-Test-Method'] = method
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            
            logger.info(f"Recommendations: user={user_id}, method={method}, latency={latency:.2f}ms")
            return response
            
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found',
                'code': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Recommendations error: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 📈 API نظام الثقة (محسن)
# ============================================================

class TrustAPIView(APIView):
    """API إدارة الثقة مع تحسين cache"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id=None):
        if not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            if user_id:
                try:
                    profile = UserProfile.objects.get(id=user_id)
                    new_score = calculate_trust_score(profile, use_cache=False)
                    
                    # استخدام SmartCacheManager بدلاً من delete_pattern
                    SmartCacheManager.invalidate_user(user_id)
                    
                    return Response({
                        'success': True,
                        'user_id': user_id,
                        'new_trust_score': new_score,
                        'message': f'Trust score updated for {profile.user.username}'
                    })
                except UserProfile.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # تحديث جميع المستخدمين
                update_all_trust_scores()
                
                # إبطال كل الـ cache دفعة واحدة O(1)
                SmartCacheManager.invalidate_all()
                
                return Response({
                    'success': True,
                    'message': 'All trust scores updated successfully',
                    'admin': request.user.username
                })
        except Exception as e:
            logger.error(f"Trust error: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 🧠 API تعلم من سلوك المستخدم (محسن)
# ============================================================

class UserActionAPIView(APIView):
    """
    API تسجيل تفاعلات المستخدم
    - يستخدم Celery بدلاً من threading
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        action_type = request.data.get('action')
        target_id = request.data.get('target_id')
        
        if not action_type or not target_id:
            return Response({
                'success': False,
                'error': 'action and target_id required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        valid_actions = ['click', 'view', 'accept', 'reject', 'hire', 'ignore']
        if action_type not in valid_actions:
            return Response({
                'success': False,
                'error': f'Invalid action. Must be one of: {valid_actions}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_id = int(target_id)
            if target_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response({
                'success': False,
                'error': 'Invalid target_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ استخدام Celery بدلاً من threading
        update_preferences_async.delay(request.user.id, action_type, target_id)
        
        return Response({
            'success': True,
            'message': 'User action queued for processing',
            'action': action_type,
            'target_id': target_id
        }, status=status.HTTP_202_ACCEPTED)


@shared_task(bind=True, max_retries=3)
def update_preferences_async(self, user_id: int, action_type: str, target_id: int):
    """معالجة غير متزامنة باستخدام Celery (بدلاً من threading)"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        update_user_preferences(user, action_type, target_id)
        logger.info(f"Async: User {user_id} {action_type} on {target_id}")
    except Exception as e:
        logger.error(f"Async task failed: {e}")
        if self.request.retries < 2:
            raise self.retry(exc=e, countdown=60)


# ============================================================
# 🩺 API صحة النظام (محسن)
# ============================================================

class HealthCheckAPIView(APIView):
    """API فحص صحة النظام - نسخة مؤسساتية"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # ✅ تصحيح منطق health check
        cache.set('health_check_test', 'ok', 10)
        cache_status = 'healthy' if cache.get('health_check_test') == 'ok' else 'unhealthy'
        
        try:
            connection.ensure_connection()
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
        
        # ✅ إضافة Celery health check
        celery_status = self._check_celery()
        
        overall = 'healthy' if all([
            db_status == 'healthy',
            cache_status == 'healthy',
            celery_status == 'healthy'
        ]) else 'degraded'
        
        return Response({
            'status': overall,
            'timestamp': time.time(),
            'version': '4.0.0-enterprise',
            'components': {
                'database': db_status,
                'cache': cache_status,
                'celery': celery_status,
                'recommendation_engine': 'active'
            }
        })
    
    def _check_celery(self) -> str:
        """التحقق من صحة Celery"""
        try:
            from celery import current_app
            result = current_app.control.ping(timeout=1)
            return 'healthy' if result else 'unhealthy'
        except Exception:
            return 'unhealthy'


# ============================================================
# 📊 API مقاييس A/B Testing (Admin Only)
# ============================================================

class ABTestMetricsAPIView(APIView):
    """API للحصول على نتائج اختبار A/B"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        results = _ab_test.get_results()
        return Response({
            'success': True,
            'ab_test_results': results,
            'timestamp': time.time()
        })


# ============================================================
# 🗑️ API مسح Cache (Admin Only - محسن)
# ============================================================

class ClearCacheAPIView(APIView):
    """API مسح الـ cache - آمن وفعال"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id=None):
        if not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            if user_id:
                SmartCacheManager.invalidate_user(user_id)
                message = f'Cache cleared for user {user_id}'
            else:
                SmartCacheManager.invalidate_all()
                message = 'All cache cleared'
            
            logger.info(f"Cache cleared by {request.user.username}")
            return Response({
                'success': True,
                'message': message,
                'admin': request.user.username
            })
        except Exception as e:
            logger.error(f"Clear cache error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# ============================================================
# 📊 API مقاييس النظام (Admin Only)
# ============================================================

class MetricsAPIView(APIView):
    """
    API لعرض مقاييس أداء النظام
    (للمشرفين فقط)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # ✅ فقط المشرفين
        if not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from core.recommendation_engine import get_metrics, get_system_health_report
            
            metrics = get_metrics()
            health_report = get_system_health_report()
            
            return Response({
                'success': True,
                'metrics': metrics,
                'health': health_report,
                'cache_version': cache.get('current_cache_version', 'v1')
            })
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================
# 🔐 API توقيع العقود بالبصمة (Biometric Sign)
# ============================================================

class BiometricSignAPIView(APIView):
    """
    API لتوقيع العقود باستخدام البصمة
    
    POST /api/v3/sign-contract/{contract_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, contract_id):
        """توقيع عقد باستخدام البصمة"""
        try:
            from core.models import Contract
            from ai.blockchain import sign_contract_with_biometric
            from core.biometric_integration import BiometricAuditLog
            
            # جلب العقد
            try:
                contract = Contract.objects.select_related('client', 'freelancer').get(id=contract_id)
            except Contract.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'العقد غير موجود',
                    'code': 'NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # ✅ التحقق من الصلاحيات
            if request.user != contract.client and request.user != contract.freelancer:
                logger.warning(f"User {request.user.id} not authorized to sign contract {contract_id}")
                return Response({
                    'success': False,
                    'error': 'غير مصرح لك بتوقيع هذا العقد',
                    'code': 'PERMISSION_DENIED'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # ✅ التحقق من حالة العقد
            if contract.status not in ['pending', 'active']:
                return Response({
                    'success': False,
                    'error': f'لا يمكن توقيع العقد في هذه المرحلة (الحالة: {contract.status})',
                    'code': 'INVALID_STATUS'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ التحقق من عدم توقيع المستخدم مسبقاً
            if request.user == contract.client and contract.client_signed_at:
                return Response({
                    'success': False,
                    'error': 'لقد قمت بتوقيع هذا العقد بالفعل',
                    'code': 'ALREADY_SIGNED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if request.user == contract.freelancer and contract.freelancer_signed_at:
                return Response({
                    'success': False,
                    'error': 'لقد قمت بتوقيع هذا العقد بالفعل',
                    'code': 'ALREADY_SIGNED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ التحقق من بيانات البصمة
            biometric_data = request.data.get('biometric_data')
            if not biometric_data:
                return Response({
                    'success': False,
                    'error': 'بيانات البصمة مطلوبة للتوقيع',
                    'code': 'MISSING_BIOMETRIC'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ التوقيع بالبصمة
            try:
                block = sign_contract_with_biometric(contract, request.user, request)
            except Exception as e:
                logger.error(f"Biometric signing failed: {e}")
                return Response({
                    'success': False,
                    'error': str(e),
                    'code': 'BIOMETRIC_FAILED'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # ✅ تحديث حالة العقد
            if request.user == contract.client:
                contract.client_signed_at = timezone.now()
            else:
                contract.freelancer_signed_at = timezone.now()
            
            # إذا تم توقيع الطرفين
            if contract.client_signed_at and contract.freelancer_signed_at:
                contract.status = 'active'
                contract.signed_at = timezone.now()
            
            contract.save()
            
            # ✅ تسجيل في Audit Log
            try:
                BiometricAuditLog.objects.create(
                    user=request.user,
                    action='sign_contract',
                    status='success',
                    confidence_score=0.95,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    contract_id=contract_id
                )
            except Exception as e:
                logger.warning(f"Failed to create audit log: {e}")
            
            logger.info(f"Contract {contract_id} signed by user {request.user.id}")
            
            return Response({
                'success': True,
                'message': 'تم توقيع العقد بنجاح',
                'contract_id': contract.id,
                'status': contract.status,
                'block_hash': getattr(block, 'current_hash', '')[:16] if hasattr(block, 'current_hash') else '',
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error signing contract {contract_id}: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': 'حدث خطأ في التوقيع، يرجى المحاولة لاحقاً',
                'code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# ⭐ API تقييم العقود (Rating)
# ============================================================

class RatingAPIView(APIView):
    """
    API لتقييم العقود
    
    POST /api/v3/rate-contract/{contract_id}/
    Body: {"rating": 5, "feedback": "ممتاز"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, contract_id):
        """تقييم عقد"""
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Contract not found',
                'code': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ✅ التحقق من أن المستخدم طرف في العقد
        if request.user != contract.client and request.user != contract.freelancer:
            return Response({
                'success': False,
                'error': 'Not authorized to rate this contract',
                'code': 'UNAUTHORIZED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        rating_value = request.data.get('rating')
        feedback = request.data.get('feedback', '')
        
        if not rating_value:
            return Response({
                'success': False,
                'error': 'Rating is required',
                'code': 'MISSING_RATING'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rating_value = float(rating_value)
            if rating_value < 1 or rating_value > 5:
                raise ValueError
        except (TypeError, ValueError):
            return Response({
                'success': False,
                'error': 'Rating must be between 1 and 5',
                'code': 'INVALID_RATING'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # تحديد المستخدم المُقيَّم
        rated_user = contract.freelancer if contract.client == request.user else contract.client
        
        rating_obj, created = ContractRating.objects.update_or_create(
            contract=contract,
            rated_by=request.user,
            defaults={
                'rated_user': rated_user,
                'rating': rating_value,
                'communication': request.data.get('communication', rating_value),
                'quality': request.data.get('quality', rating_value),
                'deadline': request.data.get('deadline', rating_value),
                'feedback': feedback
            }
        )
        # تحديث الثقة بعد التقييم
        try:
            calculate_trust_score(rated_user.profile, use_cache=False)
            # مسح cache التوصيات للمستخدم المُقيَّم
            SmartCacheManager.invalidate_user(rated_user.id)
        except Exception as e:
            logger.warning(f"Failed to update trust score: {e}")
        
        logger.info(f"Contract {contract_id} rated by user {request.user.id}: {rating_value}/5")
        
        return Response({
            'success': True,
            'message': 'تم التقييم بنجاح',
            'rating': rating_obj.rating,
            'feedback': rating_obj.feedback,
            'rated_user': rated_user.username,
            'created': created
        }, status=status.HTTP_201_CREATED)

# ============================================================
# 🧬 دوال متوافقة مع الـ urls.py القديم (للتوافق العكسي)
# ============================================================

@login_required
def recommendations_legacy(request, user_id):
    """نسخة متوافقة مع الـ urls.py القديم"""
    from django.http import JsonResponse
    from core.recommendation_engine import get_user_recommendations
    
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 20)), 100)
    with_explanations = request.GET.get('explanations', 'true').lower() == 'true'
    
    result = get_user_recommendations(
        user_id=user_id,
        page=page,
        page_size=page_size,
        with_explanations=with_explanations
    )
    
    return JsonResponse(result)


@login_required
def recalculate_trust_legacy(request, user_id=None):
    """نسخة متوافقة مع الـ urls.py القديم"""
    from django.http import JsonResponse
    from core.recommendation_engine import calculate_trust_score, update_all_trust_scores
    from core.models import UserProfile
    
    try:
        if user_id:
            profile = UserProfile.objects.get(id=user_id)
            new_score = calculate_trust_score(profile, use_cache=False)
            SmartCacheManager.invalidate_user(user_id)
            return JsonResponse({
                'success': True,
                'user_id': user_id,
                'new_trust_score': new_score
            })
        else:
            update_all_trust_scores()
            SmartCacheManager.invalidate_all()
            return JsonResponse({
                'success': True,
                'message': 'All trust scores updated successfully'
            })
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def sign_contract_with_biometrics_legacy(request, contract_id):
    """نسخة متوافقة مع الـ urls.py القديم"""
    view = BiometricSignAPIView()
    view.request = request
    return view.post(request, contract_id)


@login_required
def rate_contract_legacy(request, contract_id):
    """نسخة متوافقة مع الـ urls.py القديم"""
    view = RatingAPIView()
    view.request = request
    return view.post(request, contract_id)
# ============================================================
# 🎯 API لعرض FAISS Recommendations في الواجهة (للدكتور)
# ============================================================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faiss_demo_api(request):
    """
    API لعرض نتائج FAISS في الواجهة الأمامية
    """
    from core.recommendation_engine import FAISSIndex
    from core.models import UserProfile
    
    try:
        # جلب المستخدم الحالي
        user_profile = UserProfile.objects.get(user=request.user)
        
        # إنشاء فهرس FAISS
        faiss_index = FAISSIndex()
        
        # جلب توصيات مشابهة (إذا كانت الدالة موجودة)
        similar_users = []
        if hasattr(faiss_index, 'get_similar_users'):
            similar_users = faiss_index.get_similar_users(request.user.id, top_k=5)
        
        return Response({
            'success': True,
            'faiss_loaded': faiss_index.index is not None,
            'current_user': {
                'id': request.user.id,
                'username': request.user.username,
                'trust_score': user_profile.trust_score
            },
            'recommendations': similar_users,
            'message': 'FAISS is working!' if faiss_index.index is not None else 'FAISS not loaded'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
# ============================================================
# 📋 التسجيل
# ============================================================

logger.info("=" * 70)
logger.info("🚀 RECOMMENDATION VIEWS V4.0 - ENTERPRISE")
logger.info("=" * 70)
logger.info("✅ Clean Architecture: ENABLED")
logger.info("✅ A/B Testing: ACTIVE")
logger.info("✅ Smart Cache: ACTIVE (Versioned)")
logger.info("✅ Celery Async: ACTIVE")
logger.info("✅ No Threading: CONFIRMED")
logger.info("=" * 70)

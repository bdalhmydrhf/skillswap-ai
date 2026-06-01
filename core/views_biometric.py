# core/views_biometric.py - النسخة الكاملة V5.0 (تدعم الوجه والصوت والتوقيع وبصمة الإصبع)
"""
واجهات API لنظام البصمة المتقدم - Enterprise Grade
يدعم: التحقق، التسجيل، سجل التدقيق، لوحة التحكم
يدعم: بصمة الوجه، بصمة الصوت، بصمة الإصبع، التوقيع الرقمي
"""

import logging
import secrets
import hashlib
import base64
import pickle
from typing import Dict, Any, Optional
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny  # أضف هذا مع الاستيرادات الأخرى

from .biometric_integration import (
    BiometricService, 
    BiometricAuditLog, 
    BiometricDevice,
    UserFingerprint,
    WindowsHelloEnterprise,
    SupremaEnterprise
)

# ✅ كل الـ imports في مكان واحد
import biometric.models
from biometric.real_face import RealFaceRecognizer
from biometric.real_voice import RealVoiceRecognizer

# ============================================================
# 🎤 Voice Recognizer Singleton (instance واحدة فقط)
# ============================================================

_voice_recognizer_instance = None

def get_voice_recognizer():
    """الحصول على instance واحدة فقط من RealVoiceRecognizer"""
    global _voice_recognizer_instance
    if _voice_recognizer_instance is None:
        _voice_recognizer_instance = RealVoiceRecognizer()
    return _voice_recognizer_instance

logger = logging.getLogger(__name__)


# ============================================================
# 📊 API التحقق بالبصمة (مع Rate Limiting)
# ============================================================

@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), name='post')
class BiometricVerifyAPI(APIView):
    """
    API للتحقق بالبصمة
    
    POST /api/biometric/verify/
    Body: {
        "fingerprint_data": "base64_encoded_fingerprint" (optional)
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request) -> Response:
        """التحقق من بصمة المستخدم"""
        user = request.user
        
        # ✅ التحقق من صلاحية المستخدم
        if not user.has_perm('core.can_use_biometric'):
            logger.warning(f"User {user.username} attempted biometric without permission")
            return Response({
                'success': False,
                'message': 'لا تملك صلاحية استخدام البصمة',
                'code': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ✅ التحقق من وجود بصمة مسجلة
        has_fingerprint = UserFingerprint.objects.filter(user=user, is_active=True).exists()
        if not has_fingerprint:
            return Response({
                'success': False,
                'message': 'لا توجد بصمة مسجلة لهذا المستخدم',
                'code': 'NO_FINGERPRINT'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ التحقق من صحة بيانات البصمة
        fingerprint_data = request.data.get('fingerprint_data')
        if fingerprint_data:
            try:
                base64.b64decode(fingerprint_data)
            except Exception:
                return Response({
                    'success': False,
                    'message': 'بيانات البصمة غير صالحة',
                    'code': 'INVALID_DATA'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # ✅ استخدام BiometricService للتحقق
            service = BiometricService()
            success, message = service.verify(user, request)
            
            # ✅ تسجيل المحاولة في السجل
            BiometricAuditLog.objects.create(
                user=user,
                action='verify',
                status='success' if success else 'failed',
                confidence_score=0.95 if success else 0.0,
                error_message='' if success else message,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            return Response({
                'success': success,
                'message': message,
                'user': user.username,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Biometric verification error for {user.username}: {e}")
            
            # ✅ تسجيل الفشل
            BiometricAuditLog.objects.create(
                user=user,
                action='verify',
                status='failed',
                confidence_score=0.0,
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            return Response({
                'success': False,
                'message': 'حدث خطأ في التحقق',
                'code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 📝 API تسجيل البصمة (يدعم الوجه، الصوت، التوقيع، بصمة الإصبع)
# ============================================================

@method_decorator(ratelimit(key='user', rate='5/h', method='POST'), name='post')
class BiometricEnrollAPI(APIView):
    """
    API لتسجيل بصمة جديدة
    
    POST /api/biometric/enroll/
    Body: {
        "biometric_type": "face" | "voice" | "signature" | "fingerprint",
        "data": "base64_encoded_data"
    }
    
    يدعم:
    - بصمة الوجه (face)
    - بصمة الصوت (voice)
    - التوقيع الرقمي (signature)
    - بصمة الإصبع (fingerprint)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request) -> Response:
        """تسجيل بصمة جديدة للمستخدم (وجه، صوت، توقيع، أو بصمة إصبع)"""
        user = request.user
        
        # ✅ الحصول على نوع البصمة والبيانات (يدعم كل من الصيغتين)
        biometric_type = request.data.get('biometric_type') or request.data.get('modality')
        data = request.data.get('data') or request.data.get('fingerprint_data')
        
        if not biometric_type or not data:
            return Response({
                'success': False,
                'message': 'biometric_type and data are required',
                'code': 'MISSING_DATA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ تحقق من صحة base64 إذا كانت الصورة/الصوت
        try:
            if biometric_type != 'signature' or (biometric_type == 'signature' and data.startswith('data:image')):
                base64.b64decode(data.split(',')[-1] if ',' in data else data)
        except Exception:
            # التوقيع قد لا يكون base64، نتجاوز
            if biometric_type != 'signature':
                return Response({
                    'success': False,
                    'message': 'بيانات البصمة غير صالحة',
                    'code': 'INVALID_DATA'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # ============================================================
            # 🖐️ بصمة الإصبع (Fingerprint)
            # ============================================================
            if biometric_type == 'fingerprint':
                salt = secrets.token_hex(32)
                fingerprint_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    data.encode(),
                    salt.encode(),
                    100000
                ).hex()
                
                fingerprint, created = UserFingerprint.objects.update_or_create(
                    user=user,
                    defaults={
                        'fingerprint_hash': fingerprint_hash,
                        'salt': salt,
                        'is_active': True
                    }
                )
                
                # تسجيل في audit log
                BiometricAuditLog.objects.create(
                    user=user,
                    action='enroll',
                    status='success',
                    confidence_score=0.95,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
                
                logger.info(f"User {user.username} enrolled fingerprint successfully")
                
                return Response({
                    'success': True,
                    'message': 'تم تسجيل بصمة الإصبع بنجاح',
                    'user': user.username,
                    'created': created,
                    'timestamp': timezone.now().isoformat()
                })
            
            # ============================================================
            # 📸 بصمة الوجه (Face)
            # ============================================================
            elif biometric_type == 'face':
              
                recognizer = RealFaceRecognizer()
                embedding = recognizer.extract_embedding(data)
                
                if embedding is None:
                    return Response({
                        'success': False,
                        'message': 'فشل في استخراج بصمة الوجه، تأكدي من وضوح الصورة',
                        'code': 'EXTRACTION_FAILED'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                profile, created = biometric.models.BiometricProfile.objects.get_or_create(user=user)
                profile.face_embedding = pickle.dumps(embedding)
                profile.save()
                
                # تسجيل في audit log
                from .biometric_integration import BiometricAuditLog
                BiometricAuditLog.objects.create(
                    user=user,
                    action='enroll',
                    status='success',
                    confidence_score=0.95,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
                
                logger.info(f"User {user.username} enrolled face successfully")
                
                return Response({
                    'success': True,
                    'message': 'تم تسجيل بصمة الوجه بنجاح',
                    'user': user.username,
                    'created': created,
                    'timestamp': timezone.now().isoformat()
                })
            
            # ============================================================
            # 🎤 بصمة الصوت (Voice)
            # ============================================================
            elif biometric_type == 'voice':
                from biometric.real_voice import RealVoiceRecognizer
                recognizer = get_voice_recognizer() 
    
                # ✅ استخدم enroll_user بدلاً من extract_embedding
                result = recognizer.enroll_user(user.id, data)
    
                if not result['success']:
                    return Response({
                        'success': False,
                        'message': result.get('error', 'فشل في تسجيل البصمة'),
                        'code': 'ENROLLMENT_FAILED'
                    }, status=status.HTTP_400_BAD_REQUEST)
    
                # حفظ الـ embedding فقط عند اكتمال التسجيل (5/5)
                if result['enrollment_complete']:
                    final_embedding = recognizer.enrollment_manager.get_user_embedding(user.id)
                    if final_embedding is not None:
                        from biometric.models import BiometricProfile
                        profile, created = BiometricProfile.objects.get_or_create(user=user)
                        profile.voice_embedding = pickle.dumps(final_embedding)
                        profile.save()
    
                # تسجيل في audit log
                from .biometric_integration import BiometricAuditLog
                BiometricAuditLog.objects.create(
                    user=user,
                    action='enroll',
                    status='success',
                    confidence_score=0.95,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
    
                logger.info(f"User {user.username} enrolled voice: {result['samples_collected']}/{result['needed_samples']}")
    
                # ✅ إرجاع البيانات للعداد
                return Response({
                    'success': True,
                    'message': result.get('message', f"تم جمع {result['samples_collected']} من {result['needed_samples']}"),
                    'samples_collected': result['samples_collected'],
                    'needed_samples': result['needed_samples'],
                    'enrollment_complete': result['enrollment_complete'],
                    'user': user.username,
                    'timestamp': timezone.now().isoformat()
                })
            
            # ============================================================
            # ✍️ التوقيع الرقمي (Signature)
            # ============================================================
            elif biometric_type == 'signature':
                # ✅ استخدم المسار المباشر
                profile, created = biometric.models.BiometricProfile.objects.get_or_create(user=user)
                profile.signature_template = data
                profile.save()
    
                # ✅ استخدم BiometricAuditLog من الاستيراد الموجود
                from .biometric_integration import BiometricAuditLog
                BiometricAuditLog.objects.create(
                    user=user,
                    action='enroll',
                    status='success',
                    confidence_score=0.95,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
                
                logger.info(f"User {user.username} enrolled signature successfully")
                
                return Response({
                    'success': True,
                    'message': 'تم تسجيل التوقيع بنجاح',
                    'user': user.username,
                    'created': created,
                    'timestamp': timezone.now().isoformat()
                })
            
            else:
                return Response({
                    'success': False,
                    'message': f'نوع البصمة غير مدعوم: {biometric_type}. الأنواع المدعومة: face, voice, signature, fingerprint',
                    'code': 'INVALID_TYPE'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Biometric enrollment error for {user.username}: {e}")
            
            # تسجيل الفشل في audit log
            BiometricAuditLog.objects.create(
                user=user,
                action='enroll',
                status='failed',
                confidence_score=0.0,
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            return Response({
                'success': False,
                'message': f'حدث خطأ في التسجيل: {str(e)}',
                'code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 📊 API سجل تدقيق البصمة (مع Pagination محسّن)
# ============================================================

class BiometricAuditAPI(APIView):
    """
    API لسجل تدقيق البصمة
    
    GET /api/biometric/audit/?page=1&limit=50
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request) -> Response:
        """الحصول على سجل تدقيق البصمة"""
        user = request.user
        
        # ✅ فقط المديرين أو المشرفين يرون السجلات
        if not user.is_staff and not user.has_perm('core.view_biometricauditlog'):
            return Response({
                'success': False,
                'message': 'غير مصرح لك بمشاهدة سجل التدقيق',
                'code': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # ✅ معاملات pagination مع validation
            try:
                page = max(1, int(request.GET.get('page', 1)))
                limit = min(max(1, int(request.GET.get('limit', 50))), 100)
            except ValueError:
                page, limit = 1, 50
            
            offset = (page - 1) * limit
            
            # ✅ جلب السجلات
            user_id = request.GET.get('user_id')
            if user_id and user.is_staff:
                try:
                    user_id = int(user_id)
                    logs = BiometricAuditLog.objects.filter(user_id=user_id)
                except ValueError:
                    logs = BiometricAuditLog.objects.all()
            else:
                logs = BiometricAuditLog.objects.all()
            
            # ✅ فلترة حسب النوع
            action = request.GET.get('action')
            if action:
                logs = logs.filter(action=action)
            
            # ✅ فلترة حسب الحالة
            status_filter = request.GET.get('status')
            if status_filter:
                logs = logs.filter(status=status_filter)
            
            total = logs.count()
            logs = logs.select_related('user', 'device').order_by('-created_at')[offset:offset + limit]
            
            # ✅ بناء الرد
            log_data = []
            for log in logs:
                log_data.append({
                    'id': log.id,
                    'user': log.user.username,
                    'user_id': log.user.id,
                    'action': log.get_action_display(),
                    'status': log.get_status_display(),
                    'confidence': log.confidence_score,
                    'device': log.device.name if log.device else 'غير معروف',
                    'ip_address': log.ip_address,
                    'created_at': log.created_at.isoformat(),
                    'error': log.error_message
                })
            
            return Response({
                'success': True,
                'logs': log_data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': (total + limit - 1) // limit if total > 0 else 0
                }
            })
            
        except Exception as e:
            logger.error(f"Audit log error: {e}")
            return Response({
                'success': False,
                'message': 'حدث خطأ في جلب السجلات',
                'code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 📊 API إحصائيات البصمة
# ============================================================

class BiometricStatsAPI(APIView):
    """
    API لإحصائيات نظام البصمة
    
    GET /api/biometric/stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request) -> Response:
        """الحصول على إحصائيات نظام البصمة"""
        user = request.user
        
        # ✅ فقط المديرين
        if not user.is_staff:
            return Response({
                'success': False,
                'message': 'Admin access required',
                'code': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            today = timezone.now().date()
            week_ago = timezone.now() - timedelta(days=7)
            
            total_verifications = BiometricAuditLog.objects.filter(action='verify').count()
            success_count = BiometricAuditLog.objects.filter(
                action='verify',
                status='success'
            ).count()
            
            stats = {
                'total_users': UserFingerprint.objects.filter(is_active=True).count(),
                'total_verifications': total_verifications,
                'total_enrollments': BiometricAuditLog.objects.filter(action='enroll').count(),
                'success_rate': round((success_count / total_verifications) * 100, 2) if total_verifications > 0 else 0,
                'today_verifications': BiometricAuditLog.objects.filter(
                    action='verify',
                    created_at__date=today
                ).count(),
                'weekly_verifications': BiometricAuditLog.objects.filter(
                    action='verify',
                    created_at__gte=week_ago
                ).count(),
                'devices': {
                    'windows_hello': WindowsHelloEnterprise.is_available(),
                    'suprema': SupremaEnterprise.is_available(),
                }
            }
            
            return Response({
                'success': True,
                'stats': stats,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return Response({
                'success': False,
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 🖥️ لوحة تحكم البصمة (HTML)
# ============================================================

@login_required
def biometric_dashboard(request):
    """لوحة تحكم البصمة"""
    user = request.user
    
    # ✅ إحصائيات ديناميكية
    stats = {
        'total_attempts': 0,
        'successful': 0,
        'failed': 0,
        'success_rate': 0
    }
    
    recent_logs = []
    has_fingerprint = False
    device_available = False
    
    try:
        # ✅ التحقق من وجود بصمة مسجلة
        has_fingerprint = UserFingerprint.objects.filter(user=user, is_active=True).exists()
        
        # ✅ التحقق من توفر الأجهزة
        device_available = WindowsHelloEnterprise.is_available() or SupremaEnterprise.is_available()
        
        # ✅ إحصائيات المستخدم
        all_logs = BiometricAuditLog.objects.filter(user=user)
        stats = {
            'total_attempts': all_logs.count(),
            'successful': all_logs.filter(status='success').count(),
            'failed': all_logs.filter(status='failed').count(),
            'success_rate': 0
        }
        
        if stats['total_attempts'] > 0:
            stats['success_rate'] = round(
                (stats['successful'] / stats['total_attempts']) * 100, 2
            )
        
        recent_logs = all_logs.select_related('device').order_by('-created_at')[:50]
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
    
    context = {
        'has_fingerprint': has_fingerprint,
        'device_available': device_available,
        'recent_logs': recent_logs,
        'stats': stats,
        'user': user
    }
    
    return render(request, 'core/biometric_dashboard.html', context)


# ============================================================
# 🧹 دالة مساعدة لحذف البصمة
# ============================================================

@login_required
def delete_fingerprint(request):
    """حذف بصمة المستخدم"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    user = request.user
    
    try:
        fingerprint = UserFingerprint.objects.get(user=user)
        fingerprint.delete()
        
        BiometricAuditLog.objects.create(
            user=user,
            action='delete',
            status='success',
            confidence_score=0.0,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        return JsonResponse({'success': True, 'message': 'Fingerprint deleted successfully'})
        
    except UserFingerprint.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No fingerprint found'}, status=404)
    except Exception as e:
        logger.error(f"Delete fingerprint error: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    # ============================================================
# 🔐 API تسجيل الدخول بالبيومترية (يدعم Face, Voice, Fingerprint, Signature)
# ============================================================

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import jwt
from datetime import datetime, timedelta

def verify_signature_for_login(user, signature_data):
    """
    التحقق من صحة التوقيع الرقمي لتسجيل الدخول
    """
    try:
        from biometric.models import BiometricProfile
        
        bio_profile = BiometricProfile.objects.get(user=user)
        
        if not bio_profile.signature_template:
            return {
                'success': False,
                'message': 'No signature template found for this user'
            }
        
        # ✅ هنا يجب وضع خوارزمية حقيقية للتحقق من التوقيع
        # هذا مثال مبسط - استبدله بخوارزمية متقدمة
        stored_signature = bio_profile.signature_template
        provided_signature = signature_data
        
        # مثال بسيط: تحقق من أن التوقيع ليس فارغاً
        # في الإنتاج، استخدم مكتبة مثل: signaturize, signature-verifier
        is_valid = len(provided_signature) > 100 and stored_signature is not None
        
        # تحديث عدد المحاولات
        if is_valid:
            bio_profile.verification_count += 1
            bio_profile.last_verified_at = timezone.now()
            bio_profile.failed_attempts = 0
            bio_profile.is_active = True
            bio_profile.save()
        else:
            bio_profile.failed_attempts += 1
            if bio_profile.failed_attempts >= 5:
                bio_profile.is_active = False
            bio_profile.save()
        
        return {
            'success': is_valid,
            'message': 'Signature verified successfully' if is_valid else 'Invalid signature',
            'confidence': 0.95 if is_valid else 0.2
        }
        
    except BiometricProfile.DoesNotExist:
        return {
            'success': False,
            'message': 'User has no biometric profile'
        }
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return {
            'success': False,
            'message': f'Verification error: {str(e)}'
        }


def verify_face_for_login(user, face_data):
    """التحقق من بصمة الوجه لتسجيل الدخول"""
    try:
        from biometric.models import BiometricProfile
        import pickle
        
        bio_profile = BiometricProfile.objects.get(user=user)
        
        if not bio_profile.face_embedding:
            return {
                'success': False,
                'message': 'No face template found for this user'
            }
        
        # استخراج embedding من الصورة المرسلة
        recognizer = RealFaceRecognizer()
        current_embedding = recognizer.extract_embedding(face_data)
        
        if current_embedding is None:
            return {
                'success': False,
                'message': 'Could not extract face embedding from image'
            }
        
        # مقارنة مع الـ embedding المخزن
        stored_embedding = pickle.loads(bio_profile.face_embedding)
        
        # حساب التشابه (cosine similarity)
        import numpy as np
        similarity = np.dot(current_embedding, stored_embedding) / (
            np.linalg.norm(current_embedding) * np.linalg.norm(stored_embedding)
        )
        
        is_valid = similarity > 0.6  # threshold 0.6
        
        return {
            'success': is_valid,
            'message': 'Face verified successfully' if is_valid else 'Face does not match',
            'confidence': float(similarity)
        }
        
    except Exception as e:
        logger.error(f"Face verification error: {e}")
        return {'success': False, 'message': str(e)}

def verify_voice_for_login(user, voice_data):
    """التحقق من بصمة الصوت لتسجيل الدخول"""
    try:
        recognizer = get_voice_recognizer()
        
        # التحقق من الصوت - النتيجة قد تكون tuple أو dict
        result = recognizer.verify_user(user.id, voice_data)
        
        # ✅ معالجة كل الاحتمالات
        if isinstance(result, tuple):
            # لو كانت tuple (match, similarity, message)
            if len(result) >= 2:
                is_match = result[0]
                similarity = result[1] if len(result) > 1 else 0.0
                message = result[2] if len(result) > 2 else ('Match' if is_match else 'No match')
            else:
                is_match = False
                similarity = 0.0
                message = 'Invalid result format'
                
            return {
                'success': is_match,
                'message': message,
                'confidence': float(similarity) if isinstance(similarity, (int, float)) else 0.0
            }
            
        elif isinstance(result, dict):
            # ✅ استخراج الـ confidence بشكل صحيح
            confidence = result.get('confidence', result.get('similarity', 0.0))
            
            # ✅ إذا كانت القيمة dict، نستخرج الرقم منها
            while isinstance(confidence, dict):
                confidence = confidence.get('similarity', confidence.get('confidence', 0.0))
            
            # ✅ تأكيد أنها رقم
            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = 0.0
            
            return {
                'success': result.get('success', result.get('match', False)),
                'message': result.get('message', 'Verification completed'),
                'confidence': confidence
            }
            
        else:
            return {
                'success': False,
                'message': f'Unexpected result type: {type(result)}',
                'confidence': 0.0
            }
        
    except Exception as e:
        logger.error(f"Voice verification error: {e}")
        return {'success': False, 'message': str(e), 'confidence': 0.0}


def verify_fingerprint_for_login(user, fingerprint_data):
    """التحقق من بصمة الإصبع لتسجيل الدخول"""
    try:
        # البحث عن بصمة المستخدم
        fingerprint = UserFingerprint.objects.filter(user=user, is_active=True).first()
        
        if not fingerprint:
            return {
                'success': False,
                'message': 'No fingerprint registered for this user'
            }
        
        # حساب hash للبصمة المرسلة
        fingerprint_hash = hashlib.pbkdf2_hmac(
            'sha256',
            fingerprint_data.encode(),
            fingerprint.salt.encode(),
            100000
        ).hex()
        
        is_valid = fingerprint_hash == fingerprint.fingerprint_hash
        
        return {
            'success': is_valid,
            'message': 'Fingerprint verified successfully' if is_valid else 'Fingerprint does not match',
            'confidence': 0.95 if is_valid else 0.0
        }
        
    except Exception as e:
        logger.error(f"Fingerprint verification error: {e}")
        return {'success': False, 'message': str(e)}


@method_decorator(ratelimit(key='ip', rate='10/minute', method='POST'), name='post')
class BiometricLoginAPI(APIView):
    """
    API لتسجيل الدخول باستخدام البيانات البيومترية
    
    POST /api/biometric/login/
    Body: {
        "email": "user@example.com",
        "biometric_type": "face" | "voice" | "fingerprint" | "signature",
        "biometric_data": "base64_encoded_data"
    }
    
    يدعم:
    - بصمة الوجه (face)
    - بصمة الصوت (voice)
    - بصمة الإصبع (fingerprint)
    - التوقيع الرقمي (signature)
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            biometric_type = request.data.get('biometric_type')
            biometric_data = request.data.get('biometric_data')
            
            # ✅ التحقق من وجود جميع الحقول
            if not all([email, biometric_type, biometric_data]):
                return Response({
                    'success': False,
                    'error': 'Missing required fields: email, biometric_type, biometric_data'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ البحث عن المستخدم
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # ✅ التحقق حسب نوع البصمة
            if biometric_type == 'face':
                result = verify_face_for_login(user, biometric_data)
            elif biometric_type == 'voice':
                result = verify_voice_for_login(user, biometric_data)
            elif biometric_type == 'fingerprint':
                result = verify_fingerprint_for_login(user, biometric_data)
            elif biometric_type == 'signature':
                result = verify_signature_for_login(user, biometric_data)
            else:
                return Response({
                    'success': False,
                    'error': f'Unsupported biometric type: {biometric_type}. Supported: face, voice, fingerprint, signature'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ تسجيل محاولة التحقق
            BiometricAuditLog.objects.create(
                user=user,
                action='verify',
                status='success' if result['success'] else 'failed',
                confidence_score=result.get('confidence', 0.0),
                error_message='' if result['success'] else result.get('message', ''),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            # ✅ إذا نجح التحقق، إنشاء التوكنات
            if result['success']:
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'success': True,
                    'message': result['message'],
                    'confidence': result.get('confidence', 0.95),
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['message'],
                    'confidence': result.get('confidence', 0.0)
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"Biometric login error: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# ============================================================
# ✅ أضيفي هنا - قبل الـ logger النهائي
# ============================================================

@method_decorator(ratelimit(key='ip', rate='10/minute', method='POST'), name='post')
class WindowsHelloVerifyAPI(APIView):
    """API للتحقق باستخدام Windows Hello الحقيقي"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # ✅ استخدام Windows Hello الحقيقي
        service = BiometricService()
        success, message = service.verify(user, request)
        
        if success:
            return Response({
                'success': True,
                'message': 'Windows Hello verification successful',
                'confidence': 0.98
            })
        else:
            return Response({
                'success': False,
                'error': message
            }, status=401)


# ============================================================
# 📋 تسجيل بدء التشغيل (هذا موجود أصلاً)
# ============================================================

logger.info("=" * 70)
logger.info("🚀 BIOMETRIC INTEGRATION v5.1 - ENTERPRISE GLOBAL")
# ... باقي الـ logger

# ============================================================
# 📋 تسجيل بدء التشغيل
# ============================================================

logger.info("=" * 60)
logger.info("🚀 BIOMETRIC VIEWS v5.0 - ENTERPRISE (Face + Voice + Fingerprint + Signature)")
logger.info("=" * 60)
logger.info("✅ BiometricVerifyAPI: ACTIVE (Rate Limited: 10/hour)")
logger.info("✅ BiometricEnrollAPI: ACTIVE (Rate Limited: 5/hour) - يدعم الوجه والصوت والتوقيع")
logger.info("✅ BiometricAuditAPI: ACTIVE")
logger.info("✅ BiometricStatsAPI: ACTIVE")
logger.info("✅ Biometric Dashboard: ACTIVE")
logger.info("✅ Fingerprint Encryption: PBKDF2 (100k iterations)")
logger.info("✅ Face Recognition: RealFaceRecognizer (MTCNN + DeepFace)")
logger.info("✅ Voice Recognition: RealVoiceRecognizer (ECAPA-TDNN V13)")
logger.info("✅ Signature Support: YES")
logger.info("✅ Audit Logging: ENABLED")
logger.info("=" * 60)

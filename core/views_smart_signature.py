# core/views_smart_signature.py - النسخة المحسنة

"""
واجهات API للتوقيع الذكي على العقود - Enterprise Grade
يدعم: التوقيع بالبصمة، التحقق من الصحة، Rate Limiting متقدم، Audit Logging
"""

import hashlib
import json
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied  # ✅ أضف هذا السطر
from .models import Contract, BlockchainBlock
from .biometric_integration import BiometricAuditLog
from ai.blockchain import sign_contract_with_biometric, verify_contract_signature

logger = logging.getLogger(__name__)


# ============================================================
# 🔐 Rate Limiter متقدم
# ============================================================

class SmartSignatureRateLimiter:
    """Rate Limiter متقدم لتوقيع العقود"""
    
    MAX_ATTEMPTS_PER_HOUR = 5
    MAX_ATTEMPTS_PER_DAY = 20
    
    @staticmethod
    def can_sign(user_id: int, contract_id: int) -> tuple[bool, str]:
        """التحقق من إمكانية التوقيع"""
        hour_key = f"sign_attempts_{user_id}_{contract_id}_hour"
        day_key = f"sign_attempts_{user_id}_{contract_id}_day"
        
        hour_count = cache.get(hour_key, 0)
        day_count = cache.get(day_key, 0)
        
        if hour_count >= SmartSignatureRateLimiter.MAX_ATTEMPTS_PER_HOUR:
            return False, f"Too many attempts. Max {SmartSignatureRateLimiter.MAX_ATTEMPTS_PER_HOUR} per hour"
        
        if day_count >= SmartSignatureRateLimiter.MAX_ATTEMPTS_PER_DAY:
            return False, f"Too many attempts. Max {SmartSignatureRateLimiter.MAX_ATTEMPTS_PER_DAY} per day"
        
        return True, ""
    
    @staticmethod
    def record_attempt(user_id: int, contract_id: int):
        """تسجيل محاولة توقيع"""
        hour_key = f"sign_attempts_{user_id}_{contract_id}_hour"
        day_key = f"sign_attempts_{user_id}_{contract_id}_day"
        
        cache.set(hour_key, cache.get(hour_key, 0) + 1, 3600)
        cache.set(day_key, cache.get(day_key, 0) + 1, 86400)


# ============================================================
# 📝 API التوقيع الذكي
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_contract_signature(request, contract_id):
    """
    توقيع ذكي للعقود - متكامل مع ai/blockchain.py
    
    POST /api/smart-signature/{contract_id}/
    Body: {
        "biometric_data": "base64_encoded_fingerprint" (optional)
    }
    
    Returns:
        {
            "message": "✅ تم توقيع العقد بنجاح",
            "block_index": 123,
            "block_hash": "a1b2c3...",
            "verification_method": "biometric",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    # ✅ 1. التحقق من وجود العقد
    try:
        contract = Contract.objects.select_related('client', 'freelancer').get(id=contract_id)
    except Contract.DoesNotExist:
        logger.warning(f"Contract {contract_id} not found")
        return Response({
            "success": False,
            "error": "العقد غير موجود",
            "code": "NOT_FOUND"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # ✅ 2. التحقق من صلاحيات المستخدم
    if request.user != contract.client and request.user != contract.freelancer:
        logger.warning(f"User {request.user.id} not authorized to sign contract {contract_id}")
        return Response({
            "success": False,
            "error": "غير مصرح لك بتوقيع هذا العقد",
            "code": "PERMISSION_DENIED"
        }, status=status.HTTP_403_FORBIDDEN)
    
    # ✅ 3. التحقق من حالة العقد
    if contract.status not in ['pending', 'active']:
        logger.warning(f"Contract {contract_id} cannot be signed in status: {contract.status}")
        return Response({
            "success": False,
            "error": f"لا يمكن توقيع العقد في هذه المرحلة (الحالة: {contract.status})",
            "code": "INVALID_STATUS"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ✅ 4. التحقق من عدم توقيع المستخدم مسبقاً
    if request.user == contract.client and contract.client_signed_at:
        return Response({
            "success": False,
            "error": "لقد قمت بتوقيع هذا العقد بالفعل",
            "code": "ALREADY_SIGNED"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user == contract.freelancer and contract.freelancer_signed_at:
        return Response({
            "success": False,
            "error": "لقد قمت بتوقيع هذا العقد بالفعل",
            "code": "ALREADY_SIGNED"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ✅ 5. التحقق من بيانات البصمة
    biometric_data = request.data.get('biometric_data')
    if not biometric_data:
        return Response({
            "success": False,
            "error": "بيانات البصمة مطلوبة للتوقيع",
            "code": "MISSING_BIOMETRIC"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ✅ 6. Rate Limiting متقدم
    can_sign, rate_error = SmartSignatureRateLimiter.can_sign(request.user.id, contract_id)
    if not can_sign:
        logger.warning(f"Rate limit exceeded for user {request.user.id} on contract {contract_id}")
        BiometricAuditLog.objects.create(
            user=request.user,
            action='sign_contract_attempt',
            status='failed',
            confidence_score=0.0,
            error_message=rate_error,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return Response({
            "success": False,
            "error": rate_error,
            "code": "RATE_LIMIT_EXCEEDED"
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # ✅ 7. تسجيل المحاولة
    SmartSignatureRateLimiter.record_attempt(request.user.id, contract_id)
    
    try:
        # ✅ 8. استخدام النظام القوي من ai/blockchain.py
        block = sign_contract_with_biometric(contract, request.user, request)
        
        # ✅ 9. تسجيل النجاح في Audit Log
        BiometricAuditLog.objects.create(
            user=request.user,
            action='sign_contract',
            status='success',
            confidence_score=0.95,
            ip_address=ip_address,
            user_agent=user_agent,
            contract_id=contract_id
        )
        
        logger.info(f"Contract {contract_id} signed by user {request.user.id}")
        
        return Response({
            "success": True,
            "message": "✅ تم توقيع العقد بنجاح",
            "block_index": block.index,
            "block_hash": block.current_hash[:16],
            "verification_method": getattr(block, 'verification_method', 'biometric'),
            "timestamp": timezone.now().isoformat()
        }, status=status.HTTP_201_CREATED)
        
    except PermissionDenied as e:
        logger.warning(f"Permission denied for user {request.user.id} on contract {contract_id}: {e}")
        
        BiometricAuditLog.objects.create(
            user=request.user,
            action='sign_contract',
            status='failed',
            confidence_score=0.0,
            error_message=str(e),
            ip_address=ip_address,
            user_agent=user_agent,
            contract_id=contract_id
        )
        
        return Response({
            "success": False,
            "error": str(e),
            "code": "BIOMETRIC_FAILED"
        }, status=status.HTTP_403_FORBIDDEN)
        
    except Exception as e:
        logger.error(f"Smart signature failed for contract {contract_id}: {e}", exc_info=True)
        
        BiometricAuditLog.objects.create(
            user=request.user,
            action='sign_contract',
            status='failed',
            confidence_score=0.0,
            error_message=str(e),
            ip_address=ip_address,
            user_agent=user_agent,
            contract_id=contract_id
        )
        
        return Response({
            "success": False,
            "error": "حدث خطأ في التوقيع، يرجى المحاولة لاحقاً",
            "code": "INTERNAL_ERROR"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 🔍 API التحقق من صحة التوقيع
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def verify_biometrics(request, contract_id):
    """
    التحقق من صحة توقيع العقد
    
    GET /api/verify-signature/{contract_id}/
    
    Returns:
        {
            "verified": true,
            "message": "التوقيع صحيح",
            "signed_by_client": true,
            "signed_by_freelancer": true,
            "chain_valid": true,
            "client_signature": "0x1234...",
            "freelancer_signature": "0x5678..."
        }
    """
    ip_address = request.META.get('REMOTE_ADDR')
    
    # ✅ 1. التحقق من وجود العقد
    try:
        contract = Contract.objects.select_related('client', 'freelancer').get(id=contract_id)
    except Contract.DoesNotExist:
        logger.warning(f"Contract {contract_id} not found for verification")
        return Response({
            "success": False,
            "error": "العقد غير موجود",
            "code": "NOT_FOUND"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # ✅ 2. التحقق من الصلاحيات (فقط أطراف العقد والمشرفين)
    if not (request.user.is_staff or request.user == contract.client or request.user == contract.freelancer):
        logger.warning(f"User {request.user.id} not authorized to verify contract {contract_id}")
        return Response({
            "success": False,
            "error": "غير مصرح لك بالتحقق من هذا العقد",
            "code": "PERMISSION_DENIED"
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # ✅ 3. استخدام نظام التحقق من ai/blockchain.py
        result = verify_contract_signature(contract)
        
        # ✅ 4. تسجيل عملية التحقق في Audit Log
        BiometricAuditLog.objects.create(
            user=request.user,
            action='verify_signature',
            status='success' if result['is_valid'] else 'failed',
            confidence_score=1.0 if result['is_valid'] else 0.0,
            error_message='' if result['is_valid'] else 'Invalid signature',
            ip_address=ip_address,
            contract_id=contract_id
        )
        
        logger.info(f"Contract {contract_id} verification: {result['is_valid']}")
        
        return Response({
            "success": True,
            "verified": result['is_valid'],
            "message": result['message'],
            "signed_by_client": result.get('signed_by_client', False),
            "signed_by_freelancer": result.get('signed_by_freelancer', False),
            "chain_valid": result.get('chain_valid', True),
            "client_signature": result.get('client_signature'),
            "freelancer_signature": result.get('freelancer_signature'),
            "timestamp": timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Verification error for contract {contract_id}: {e}", exc_info=True)
        
        BiometricAuditLog.objects.create(
            user=request.user,
            action='verify_signature',
            status='failed',
            confidence_score=0.0,
            error_message=str(e),
            ip_address=ip_address,
            contract_id=contract_id
        )
        
        return Response({
            "success": False,
            "error": "حدث خطأ في التحقق",
            "code": "INTERNAL_ERROR"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 📋 تسجيل بدء التشغيل
# ============================================================

logger.info("=" * 60)
logger.info("🔐 SMART SIGNATURE VIEWS v2.0 LOADED")
logger.info("=" * 60)
logger.info("✅ Smart Contract Signature: ACTIVE (Rate Limited: 5/hour)")
logger.info("✅ Signature Verification: ACTIVE")
logger.info("✅ Audit Logging: ENABLED")
logger.info("✅ Blockchain Integration: ACTIVE")
logger.info("=" * 60)

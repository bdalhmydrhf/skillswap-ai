# core/views.py - النسخة النهائية الصحيحة 100%

"""
واجهات API الرئيسية لنظام SkillSwap-AI
يدعم: إدارة المستخدمين، المهارات، العقود، الدردشة، الملفات
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import pickle 
from .models import Skill, UserProfile, Contract, SkillPost, ChatRoom, ChatMessage, Media
from .serializers import (
    UserSerializer, SkillSerializer, UserProfileSerializer, ContractSerializer,
    SkillPostSerializer, ChatRoomSerializer, ChatMessageSerializer, MediaSerializer,
    ChatRoomCreateSerializer, ChatMessageCreateSerializer, ChatMessageUpdateSerializer 
)
from .utils import sign_contract, verify_signature
from .recommendation_engine import update_user_preferences_async

import logging
from django.conf import settings
from biometric.context_engine import ContextAwareEngine
from biometric.decision_engine import AdaptiveDecisionEngine
# أضيفي هذه الدالة في بداية الملف مع بقية الاستيرادات
from biometric.context_engine import get_smart_context_from_user_agent
# ✅ إنشاء نسخة واحدة من المحركين (لتوفير الذاكرة)
_context_engine = None
_decision_engine = None

def get_context_engine():
    global _context_engine
    if _context_engine is None:
        _context_engine = ContextAwareEngine()
    return _context_engine

def get_decision_engine():
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = AdaptiveDecisionEngine()
    return _decision_engine
logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.filter(is_deleted=False, is_active=True)
    serializer_class = SkillSerializer
    search_fields = ['name', 'category']
    filterset_fields = ['category', 'is_active']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.AllowAny()]


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.select_related('user').prefetch_related('skills')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]


@method_decorator(ratelimit(key='user', rate='50/h', method='POST'), name='create')
class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related('client', 'freelancer', 'skill')
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Contract.objects.filter(
                Q(client=user) | Q(freelancer=user)
            ).select_related('client', 'freelancer', 'skill')
        return Contract.objects.none()
    
    def perform_create(self, serializer):
        chatroom_id = self.request.data.get('chatroom_id')
    
        # ✅ حفظ العقد
        contract = serializer.save(client=self.request.user)
    
        # ✅ التأكد من وجود skill
        if not contract.skill:
            raise ValidationError({"skill_id": "Skill is required to create a contract"})
    
  
        if chatroom_id:
            try:
                chatroom = ChatRoom.objects.get(id=chatroom_id)
                contract.chatroom = chatroom
                contract.save(update_fields=['chatroom'])
                chatroom.contract = contract
                chatroom.save(update_fields=['contract'])
                logger.info(f"✅ Contract {contract.id} linked to ChatRoom {chatroom_id}")
            except ChatRoom.DoesNotExist:
                logger.warning(f"ChatRoom {chatroom_id} not found")
    
    
        try:
            text_to_sign = f"{contract.client.id}-{contract.freelancer.id}-{contract.id}-{contract.skill.id}"
            signature = sign_contract(text_to_sign, self.request.user)
            if signature:
                contract.contract_hash = signature
                contract.save(update_fields=['contract_hash'])
                logger.info(f"✅ Contract {contract.id} hash created")
        except Exception as e:
            logger.error(f"Failed to create contract hash: {e}")
        
        return contract
    
    def perform_update(self, serializer):
        contract = self.get_object()
        if contract.status == 'completed':
            raise PermissionDenied("لا يمكن تعديل عقد مكتمل")
        if contract.status == 'signed':
            raise PermissionDenied("لا يمكن تعديل عقد بعد التوقيع")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.status not in ['pending', 'draft']:
            raise PermissionDenied("لا يمكن حذف عقد بعد الموافقة عليه")
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    @method_decorator(ratelimit(key='user', rate='10/h', method='POST'))
    def verify(self, request, pk=None):
        contract = self.get_object()
        text_to_sign = f"{contract.client.id}-{contract.freelancer.id}-{contract.id}-{contract.skill.id}"
        
        client_valid = verify_signature(text_to_sign, contract.client_signature, contract.client) if contract.client_signature else False
        freelancer_valid = verify_signature(text_to_sign, contract.freelancer_signature, contract.freelancer) if contract.freelancer_signature else False
        
        return Response({
            'client_signature_valid': client_valid,
            'freelancer_signature_valid': freelancer_valid,
            'both_signed': client_valid and freelancer_valid
        })
    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """توقيع العقد بعد التحقق البيومتري"""
        from django.utils import timezone  # ✅ أضيفي هذا السطر هنا
        contract = self.get_object()
        user = request.user
        
        # ✅ التحقق من أن المستخدم طرف في العقد
        if user != contract.client and user != contract.freelancer:
            return Response({'error': 'You are not a party to this contract'}, status=403)
        
        # ✅ التحقق من عدم توقيع المستخدم مسبقاً
        if (user == contract.client and contract.client_signature) or \
           (user == contract.freelancer and contract.freelancer_signature):
            return Response({'error': 'You have already signed this contract'}, status=400)
        
        # ✅ التحقق من وجود تحقق بيومتري مسبق
        biometric_verified = request.data.get('biometric_verified', False)
        pin_verified = request.data.get('pin_verified', False)
        
        # ✅ التحقق من وجود توكن التحقق في الـ cache
        cache_key = f"biometric_verified_{user.id}_{contract.id}"
        cached_verification = cache.get(cache_key)
        
        if not biometric_verified and not pin_verified and not cached_verification:
            return Response({'error': 'Biometric or PIN verification required before signing'}, status=400)
        
        try:
            # ✅ تسجيل التوقيع
            if user == contract.client:
                contract.client_signature = f"Signed at {timezone.now()}"
            else:
                contract.freelancer_signature = f"Signed at {timezone.now()}"
            
            fully_signed = contract.client_signature and contract.freelancer_signature
            
            if fully_signed:
                contract.status = 'active'
                contract.signed_at = timezone.now()
            
            contract.save()
            cache.delete(cache_key)
            
            # ✅ تحديث Trust Score عند اكتمال التوقيع
            if fully_signed:
                try:
                    from .models import UserProfile
                    
                    client_profile = UserProfile.objects.get(user=contract.client)
                    freelancer_profile = UserProfile.objects.get(user=contract.freelancer)
                    
                    client_profile.contracts_count += 1
                    freelancer_profile.contracts_count += 1
                    
                    client_profile.completion_rate = min(client_profile.completion_rate + 10, 100)
                    freelancer_profile.completion_rate = min(freelancer_profile.completion_rate + 10, 100)
                    
                    client_profile.save()
                    freelancer_profile.save()
                    
                    client_profile.update_reputation()
                    freelancer_profile.update_reputation()
                    
                    logger.info(f"✅ Trust score updated for client {contract.client.id} and freelancer {contract.freelancer.id}")
                except Exception as e:
                    logger.error(f"❌ Failed to update trust score: {e}")
                
                # ✅ إنشاء بلوكشين بلوك     
                try:
                    import hashlib
                    import json
                    import os
                    from django.utils import timezone
                    from eth_account import Account
        
                    from core.models.blockchain import RealBlockchainService, BlockchainBlock
                    from ai.blockchain import ContractLedger, LedgerEntryType
        
                    logger.info(f"🚀 بدء تسجيل العقد {contract.id} على البلوكشين")
        
                    # 1️⃣ تسجيل في دفتر الأحداث
                    ledger = ContractLedger(contract)
                    ledger.add_entry(
                        entry_type=LedgerEntryType.AUDIT_LOG,
                        data={'action': 'blockchain_started', 'message': 'بدء تسجيل العقد'},
                        signed_by=user.id,
                        verification_method='pin' if pin_verified else 'biometric'
                    )
        
                    # 2️⃣ إنشاء هاش العقد
                    contract_hash = hashlib.sha256(
                        f"{contract.id}{contract.client.id}{contract.freelancer.id}{contract.created_at.isoformat()}{contract.total_amount}".encode()
        ).hexdigest()
        
                    contract.contract_hash = contract_hash
                    contract.blockchain_status = 'preparing'
                    contract.save(update_fields=['contract_hash', 'blockchain_status'])
        
                    # 3️⃣ عناوين المحافظ - إنشاء محافظ حقيقية
                    from eth_account import Account
                    from web3 import Web3
                    import secrets    
                    # محفظة العميل
                    client_keys = getattr(contract.client, 'keys', None)
                    if client_keys and client_keys.eth_wallet_address:
                        client_wallet = client_keys.eth_wallet_address
                    else:
                        # إنشاء محفظة جديدة
                        new_account = Account.create(secrets.token_hex(32))
                        client_wallet = new_account.address
                        if client_keys:
                            client_keys.eth_wallet_address = client_wallet
                            client_keys.save()
                        logger.info(f"Created wallet for client{contract.client.username}: {client_wallet}")
                    # محفظة الفريلانسر
                    freelancer_keys = getattr(contract.freelancer, 'keys', None)
                    if freelancer_keys and freelancer_keys.eth_wallet_address:
                        freelancer_wallet = freelancer_keys.eth_wallet_address
                    else:   
                        # إنشاء محفظة جديدة
                        new_account = Account.create(secrets.token_hex(32))
                        freelancer_wallet = new_account.address
                        if freelancer_keys:
                            freelancer_keys.eth_wallet_address = freelancer_wallet
                            freelancer_keys.save()
                        logger.info(f"Created wallet for freelancer{contract.freelancer.username}: {freelancer_wallet}")
                    
                    # ✅ الأسطر التالية تم نقلها من داخل else إلى هنا (خارج else)
                    # ✅ التأكد من وجود محفظة للعميل
                    if client_wallet == "0x0000000000000000000000000000000000000000" or not client_wallet:
                        # إنشاء محفظة جديدة للعميل
                        from eth_account import Account
                        import secrets
                        new_account = Account.create(secrets.token_hex(32))
                        client_wallet = new_account.address
                        # حفظ المحفظة في قاعدة البيانات
                        if hasattr(contract.client, 'keys') and contract.client.keys:
                            contract.client.keys.eth_wallet_address = client_wallet
                            contract.client.keys.save()
                        logger.info(f"🆕 Created new wallet for client {contract.client.username}: {client_wallet}")

                    # ✅ التأكد من وجود محفظة للفريلانسر (نفس الشي)
                    if freelancer_wallet == "0x0000000000000000000000000000000000000000" or not freelancer_wallet:
                        from eth_account import Account
                        import secrets
                        new_account = Account.create(secrets.token_hex(32))
                        freelancer_wallet = new_account.address
                        if hasattr(contract.freelancer, 'keys') and contract.freelancer.keys:
                            contract.freelancer.keys.eth_wallet_address = freelancer_wallet
                            contract.freelancer.keys.save()
                        logger.info(f"🆕 Created new wallet for freelancer {contract.freelancer.username}: {freelancer_wallet}")

                    # ✅ حل دائم: استخدم عنوان الفريلانسر للطرفين
                    if client_wallet == "0x0000000000000000000000000000000000000000" or not client_wallet:
                        client_wallet = freelancer_wallet
                        logger.info(f"🔄 Using freelancer wallet for client: {client_wallet}")
                    
                    # ✅ تحويل إلى Checksum
                    client_wallet = Web3.to_checksum_address(client_wallet)
                    freelancer_wallet = Web3.to_checksum_address(freelancer_wallet) 
                    
                    # تأكيد أن العناوين صالحة
                    if not client_wallet:
                        client_wallet = "0x0000000000000000000000000000000000000000"
                    if not freelancer_wallet:
                        freelancer_wallet = "0x0000000000000000000000000000000000000000"
                    # ✅ أضيفي هالأسطر الجديدة هنا 👇
                    if not contract_hash or contract_hash == '':
                        contract_hash = "0x" + "0" * 64
                        logger.warning(f"⚠️ Contract hash was empty, using zero hash")
                    # ✅ الكود الجديد (بياخذ العنوان من الإعدادات)
                    from django.conf import settings
                    contract_address = getattr(settings, 'SKILLSWAP_CONTRACT_ADDRESS', None)
                    
                    if not contract_address or contract_address == '0x0000000000000000000000000000000000000000':
                        logger.error("❌ SKILLSWAP_CONTRACT_ADDRESS not configured correctly")
                        raise Exception("عنوان العقد الذكي غير مهيأ بشكل صحيح")
                    logger.info(f"✅ Using contract address: {contract_address}")
                    # 4️⃣ الاتصال بالبلوكشين
                    blockchain = RealBlockchainService(network='sepolia')
        
        
                    if not blockchain.is_connected():
                        raise Exception("لا يمكن الاتصال بالبلوكشين")
        
                    logger.info("Connected to real blockchain!")
                    # ✅ استخراج عنوان المحفظة من المفتاح الخاص
                    from eth_account import Account
                    PRIVATE_KEY = getattr(settings, 'CONTRACT_OWNER_PRIVATE_KEY', '')
                    signer_address = Account.from_key(PRIVATE_KEY).address
                    logger.info(f"🔄 Using signer address: {signer_address}")
        
                    # 5️⃣ تحضير المعاملة
                    contract_data = {
                        'contract_id': contract.id,
                        'contract_hash': contract_hash,
                        'ipfs_cid': contract.ipfs_cid or "",
                        'client_wallet': signer_address,
                        'freelancer_wallet': signer_address,
                            'contract_address': getattr(contract, 'blockchain_contract_address', None) or "0x0000000000000000000000000000000000000000"
                    }
        
                    result = blockchain.prepare_contract_registration(contract_data)
        
                    if not result.get('success'):
                        raise Exception(result.get('error', 'فشل تحضير المعاملة'))
        
                    # ============================================================
                    # 🔥🔥🔥 الجزء المهم: توقيع وإرسال المعاملة 🔥🔥🔥
                    # ============================================================
        
                    # ⚠️ يجب وضع المفتاح الخاص في ملف .env
                    PRIVATE_KEY = getattr(settings, 'CONTRACT_OWNER_PRIVATE_KEY', '')
        
                    if not PRIVATE_KEY:
                        logger.error("❌ لا يوجد مفتاح خاص - لا يمكن إرسال المعاملة")
                        contract.blockchain_status = 'failed'
                        contract.last_blockchain_error = "Missing private key"
                        contract.save()
                    else:
                        # توقيع المعاملة
                        signed_tx = Account.sign_transaction(
                            result['unsigned_transaction'], 
                            PRIVATE_KEY
                        )
            
                        # إرسال المعاملة إلى البلوكشين
                        tx_result = blockchain.submit_signed_transaction(
                            signed_tx.raw_transaction.hex(),
                            contract.id
                        )
            
                        if tx_result.get('success'):
                            # ✅✅✅ تم الإرسال بنجاح ✅✅✅
                
                            # حفظ في جدول البلوكشين
                            block = BlockchainBlock.objects.create(
                                contract=contract,
                                index=0,
                                previous_hash='0'*64,
                                current_hash=contract_hash,
                                data={
                                    'contract_id': contract.id,
                                    'transaction_hash': tx_result.get('transaction_hash'),
                                    'contract_address': result.get('contract_address'),
                                },
                                is_confirmed=False,
                                transaction_hash=tx_result.get('transaction_hash'),
                                network='sepolia',
                                signed_by=user,
                                verification_method='pin' if pin_verified else 'biometric'
                            )
                
                            # تحديث العقد
                            contract.blockchain_tx_hash = tx_result.get('transaction_hash')
                            contract.blockchain_status = 'submitted'
                            contract.save(update_fields=['blockchain_tx_hash', 'blockchain_status'])
                
                            # تسجيل في دفتر الأحداث
                            ledger.add_entry(
                                entry_type=LedgerEntryType.CONTRACT_ACTIVATED,
                                data={
                                    'activated_at': timezone.now().isoformat(),
                                    'transaction_hash': tx_result.get('transaction_hash'),
                                    'contract_address': result.get('contract_address'),
                                    'contract_hash': contract_hash
                                },
                                signed_by=user.id,
                                verification_method='pin' if pin_verified else 'biometric'
                            )
                
                            logger.warning(f"🎉🎉🎉 تم إرسال العقد {contract.id} إلى البلوكشين!")
                            logger.info(f"   رابط المعاملة: https://sepolia.etherscan.io/tx/{tx_result['transaction_hash']}")
                
                        else:
                            raise Exception(tx_result.get('error', 'فشل إرسال المعاملة'))
         
                except Exception as e:
                    logger.error(f"❌ خطأ: {e}")
                    contract.blockchain_status = 'failed'
                    contract.last_blockchain_error = str(e)
                    contract.save()
        
                    try:
                        ledger = ContractLedger(contract)
                        ledger.add_entry(
                            entry_type=LedgerEntryType.AUDIT_LOG,
                            data={'action': 'error', 'error': str(e)},
                            signed_by=user.id
                        )
                    except:
                        pass
        except Exception as e:
            logger.error(f"❌ خطأ في التوقيع: {e}")
            return Response({'error': f'Failed to sign contract: {str(e)}'}, status=500)
        # ✅✅✅ أضيفي هذا السطر هنا (خارج الـ try) ✅✅✅
        return Response({
            'success': True,
            'fully_signed': fully_signed,
            'status': contract.status,
            'message': 'Contract signed successfully' if fully_signed else 'Your signature has been recorded. Waiting for the other party.'
        })
    # ✅✅✅ أضيفي دالة complete هنا (بعد دالة sign مباشرة) ✅✅✅
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        contract = self.get_object()
        
        if contract.status != 'active':
            return Response({'error': 'Only active contracts can be completed'}, status=400)
        
        contract.status = 'completed'
        contract.save()
        
        # ✅ تحديث Trust Score بعد إكمال العقد
        try:
            from .models import UserProfile
            client_profile = UserProfile.objects.get(user=contract.client)
            freelancer_profile = UserProfile.objects.get(user=contract.freelancer)
            
            # زيادة نسبة الإتمام
            client_profile.completion_rate = min(client_profile.completion_rate + 10, 100)
            freelancer_profile.completion_rate = min(freelancer_profile.completion_rate + 10, 100)
            
            client_profile.save()
            freelancer_profile.save()
            
            # إعادة حساب Trust Score
            client_profile.update_reputation()
            freelancer_profile.update_reputation()
            
            logger.info(f"✅ Trust score updated after completion for contract {contract.id}")
        except Exception as e:
            logger.error(f"❌ Failed to update trust score on completion: {e}")
        
        return Response({'success': True, 'status': 'completed'})
class SkillPostViewSet(viewsets.ModelViewSet):
    queryset = SkillPost.objects.filter(visible=True, is_deleted=False).select_related('creator', 'skill')
    serializer_class = SkillPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'requirements', 'creator__username', 'skill__name']
    ordering_fields = ['created_at', 'price', 'views_count']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    def perform_update(self, serializer):
        post = self.get_object()
        if post.creator != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("لا يمكنك تعديل منشور ليس ملكك")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        post = self.get_object()
        post.views_count += 1
        post.save(update_fields=['views_count'])
        return Response({'views_count': post.views_count})


class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [IsAuthenticated]
    
    MAX_FILE_SIZE = 200 * 1024 * 1024
    
    ALLOWED_TYPES = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/svg+xml',
        'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/mpeg',
        'video/ogg', 'video/x-matroska',
        'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/mp3',
        'audio/aac', 'audio/x-ms-wma',
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain', 'application/rtf',
        'text/x-python', 'text/javascript', 'text/html', 'text/css',
        'application/json', 'application/xml', 'text/xml',
        'application/zip', 'application/x-rar-compressed', 'application/x-tar',
        'application/gzip', 'application/x-7z-compressed',
        'text/csv',
    ]

    def get_queryset(self):
        return Media.objects.filter(uploaded_by=self.request.user)
    
    def perform_create(self, serializer):
        file = self.request.FILES.get('file')
        if not file:
            raise ValidationError("الملف مطلوب")
        
        if file.size > self.MAX_FILE_SIZE:
            raise ValidationError(f"الملف كبير جداً. الحد الأقصى {self.MAX_FILE_SIZE // (1024*1024)}MB")
        
        if file.content_type not in self.ALLOWED_TYPES:
            logger.warning(f"Unsupported file type: {file.content_type} for file: {file.name}")
            raise ValidationError(f"نوع الملف '{file.content_type}' غير مدعوم")
        
        serializer.save(uploaded_by=self.request.user)
        


class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all().prefetch_related('participants')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            from .serializers import ChatRoomCreateSerializer
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def get_queryset(self):
        return ChatRoom.objects.filter(
            participants=self.request.user,
            is_active=True
        ).select_related('post', 'contract').prefetch_related('participants', 'messages').order_by('-last_activity')

    def create(self, request, *args, **kwargs):
        from .serializers import ChatRoomCreateSerializer
        serializer = ChatRoomCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        output_serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        room = self.get_object()
        participants = request.data.get('participants', [])
        if self.request.user.id not in participants:
            raise PermissionDenied("لا يمكنك إزالة نفسك من الغرفة")
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        room = self.get_object()
        if request.user not in room.participants.all():
            return Response({'error': 'You are not a participant in this room'}, status=status.HTTP_403_FORBIDDEN)
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        messages = room.messages.select_related('sender').all()
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated_messages = messages[start:end]
        
        from .serializers import ChatMessageSerializer
        serializer = ChatMessageSerializer(paginated_messages, many=True, context={'request': request})
        
        for msg in paginated_messages:
            if msg.sender != request.user and msg.status == 'sent':
                msg.mark_as_delivered()
        
        return Response({
            'messages': serializer.data,
            'total': messages.count(),
            'page': page,
            'page_size': page_size,
            'has_next': end < messages.count()
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        room = self.get_object()
        messages = room.messages.filter(status__in=['sent', 'delivered']).exclude(sender=request.user)
        count = 0
        for msg in messages:
            msg.mark_as_read()
            count += 1
        return Response({'status': 'success', 'marked_count': count})
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        room = self.get_object()
        user_id = request.data.get('user_id')
        
        if request.user not in room.participants.all():
            return Response({'error': 'Only participants can add others'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(id=user_id)
            room.add_participant(user)
            return Response({'status': 'success', 'message': f'{user.username} added to chat'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def sign_contract_from_chat(self, request, pk=None):
        room = self.get_object()
        
        if not room.contract:
            return Response({'error': 'No contract associated with this chat'}, status=400)
        
        contract = room.contract
        user = request.user
        
        if user != contract.client and user != contract.freelancer:
            return Response({'error': 'You are not a party to this contract'}, status=403)
        
        biometric_verified = request.data.get('biometric_verified', False)
        
        if not biometric_verified:
            return Response({'error': 'Biometric verification required'}, status=400)
        
        signature = request.data.get('signature')
        if not signature:
            return Response({'error': 'Signature required'}, status=400)
        
        try:
            is_valid = contract.verify_signature(user, signature)
            
            if not is_valid:
                return Response({'error': 'Invalid signature'}, status=400)
            
            is_fully_signed = contract.client_signature and contract.freelancer_signature
            
            if is_fully_signed:
                room.notify_participants_optimized('contract_fully_signed', {
                    'contract_id': contract.id,
                    'signed_by': user.id,
                    'status': 'active'
                })
            else:
                room.notify_participants_optimized('contract_signed', {
                    'contract_id': contract.id,
                    'signed_by': user.id,
                    'status': 'partially_signed'
                })
            
            return Response({
                'success': True,
                'contract_id': contract.id,
                'status': contract.status,
                'fully_signed': is_fully_signed
            })
            
        except Exception as e:
            logger.error(f"Contract signing failed: {e}")
            return Response({'error': str(e)}, status=500)


class ChatMessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import ChatMessageSerializer, ChatMessageCreateSerializer, ChatMessageUpdateSerializer
        
        if self.action == 'create':
            return ChatMessageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ChatMessageUpdateSerializer
        return ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.filter(
            room__participants=self.request.user
        ).select_related('sender', 'room').order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        from .serializers import ChatMessageCreateSerializer
        serializer = ChatMessageCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        output_serializer = ChatMessageSerializer(message, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        if message.sender == request.user:
            return Response({'error': 'Cannot mark your own message as read'}, status=status.HTTP_400_BAD_REQUEST)
        message.mark_as_read()
        return Response({'status': 'success', 'message_id': message.id, 'status': message.status})


@receiver(post_save, sender=Contract)
def update_recommendations_on_contract(sender, instance, created, **kwargs):
    if created and instance.status == 'pending':
        update_user_preferences_async.delay(instance.client.id, 'create_contract', instance.freelancer.id)
        logger.info(f"Recommendations updated for contract {instance.id}")


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    import json
    print("=" * 60)
    print("📥 REGISTRATION REQUEST")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"Data: {request.data}")
    print("=" * 60)
    
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    pin = request.data.get('pin')
    
    if not username:
        return Response({'error': 'اسم المستخدم مطلوب'}, status=400)
    
    if not email:
        return Response({'error': 'البريد الإلكتروني مطلوب'}, status=400)
    
    if not password:
        return Response({'error': 'كلمة المرور مطلوبة'}, status=400)
    
    if pin and (len(pin) != 8 or not pin.isdigit()):
        return Response({'error': 'PIN must be 8 digits'}, status=400)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'اسم المستخدم موجود مسبقاً'}, status=400)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'البريد الإلكتروني موجود مسبقاً'}, status=400)
    
    try:
        user = User.objects.create_user(
            username=username.strip(),
            email=email.strip().lower(),
            password=password
        )
        
        profile = UserProfile.objects.get(user=user)
        if pin and len(pin) == 8:
            profile.pin_code = pin
            profile.save(update_fields=['pin_code'])
        
        return Response({
            'success': True,
            'message': 'تم التسجيل بنجاح',
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }, status=201)
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({'error': f'خطأ في التسجيل: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'trust_score': profile.trust_score,
        'contracts_count': profile.contracts_count,
        'completion_rate': profile.completion_rate,
        'avg_rating': profile.avg_rating,
        'city': profile.city,
        'country': profile.country,
        'bio': profile.bio,
        'profile_image': profile.profile_image.url if profile.profile_image else None,
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_current_user_profile(request):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    if 'first_name' in request.data:
        user.first_name = request.data['first_name']
    if 'last_name' in request.data:
        user.last_name = request.data['last_name']
    user.save()
    
    allowed_fields = ['bio', 'city', 'country', 'phone', 'headline']
    for field in allowed_fields:
        if field in request.data:
            setattr(profile, field, request.data[field])
    
    profile.save()
    # ✅ إعادة حساب Trust Score بعد تحديث البيانات
    profile.update_reputation()
    
    return Response({
        'success': True,
        'message': 'تم تحديث الملف الشخصي بنجاح'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_before_signing(request, contract_id):
    user = request.user
    biometric_type = request.data.get('biometric_type')
    biometric_data = request.data.get('biometric_data')
    
    if not biometric_type or not biometric_data:
        return Response({
            'success': False,
            'error': 'نوع البصمة والبيانات مطلوبة'
        }, status=400)
    
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'العقد غير موجود'
        }, status=404)
    
    if user != contract.client and user != contract.freelancer:
        return Response({
            'success': False,
            'error': 'غير مصرح لك بتوقيع هذا العقد'
        }, status=403)
    
    try:
        from biometric.models import BiometricProfile
        bio_profile = BiometricProfile.objects.get(user=user)
    except:
        return Response({
            'success': False,
            'error': 'لا توجد بصمة مسجلة'
        }, status=400)
    
    verified = False
    confidence = 0.0
    
    if biometric_type == 'face':
        from biometric.real_face import RealFaceRecognizer
        import pickle
        import numpy as np
    
        recognizer = RealFaceRecognizer()
    
        # التحقق من وجود بصمة مسجلة
        if bio_profile.face_embedding is None:
            return Response({
                'success': False,
                'error': 'لم يتم تسجيل بصمة وجه لهذا المستخدم'
            }, status=400)
    
        try:
            # ✅ تحويل البيانات المخزنة من bytes إلى numpy array
            stored_embedding = pickle.loads(bio_profile.face_embedding)
        
            # ✅ استخراج embedding من الصورة الجديدة
            new_embedding = recognizer.extract_embedding(biometric_data)
        
            if new_embedding is None:
                return Response({
                    'success': False,
                    'error': 'فشل في استخراج بصمة الوجه، تأكدي من وضوح الصورة والإضاءة'
                }, status=400)
        
            # ✅ حساب نسبة التشابه (Cosine Similarity) يدوياً
            # تطبيع الـ embeddings
            norm_stored = np.linalg.norm(stored_embedding)
            norm_new = np.linalg.norm(new_embedding)
        
            if norm_stored > 0 and norm_new > 0:
                similarity = np.dot(new_embedding, stored_embedding) / (norm_new * norm_stored)
            else:
                similarity = 0.0
        
            similarity = float(similarity)
            threshold = 0.6  # عتبة 60% للتطابق
            verified = similarity >= threshold
            confidence = similarity
        
            logger.info(f"Face verification: similarity={similarity:.4f}, threshold={threshold}, match={verified}")
        
        except Exception as e:
            logger.error(f"Face verification error: {e}")
            return Response({
                'success': False,
                'error': f'حدث خطأ في التحقق: {str(e)}'
            }, status=500)
    
    elif biometric_type == 'voice':
        from biometric.real_voice import RealVoiceRecognizer
        recognizer = RealVoiceRecognizer()
        is_match, confidence = recognizer.verify_user(user.id, biometric_data)
        verified = is_match
    
    elif biometric_type == 'fingerprint':
        from biometric.real_fingerprint import RealFingerprintRecognizer
        recognizer = RealFingerprintRecognizer()
        stored_template = bio_profile.fingerprint_template
        if stored_template:
            is_match, confidence = recognizer.verify_fingerprints(biometric_data, stored_template)
            verified = is_match
    
    if not verified:
        return Response({
            'success': False,
            'error': 'فشل التحقق البيومتري',
            'confidence': confidence
        }, status=401)
    
    cache_key = f"biometric_verified_{user.id}_{contract_id}"
    cache.set(cache_key, {
        'verified': True,
        'biometric_type': biometric_type,
        'confidence': confidence,
        'timestamp': timezone.now().isoformat()
    }, 300)
    
    return Response({
        'success': True,
        'message': 'تم التحقق البيومتري بنجاح، يمكنك توقيع العقد الآن',
        'verified': True,
        'confidence': confidence,
        'expires_in': 300
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_pin(request):
    user = request.user
    pin = request.data.get('pin')
    
    if not pin:
        return Response({'error': 'PIN is required'}, status=400)
    
    if len(pin) != 8 or not pin.isdigit():
        return Response({'error': 'PIN must be 8 digits'}, status=400)
    
    try:
        from datetime import timedelta
        profile = UserProfile.objects.get(user=user)
        
        if profile.pin_locked_until and timezone.now() < profile.pin_locked_until:
            return Response({
                'error': f'PIN locked until {profile.pin_locked_until}',
                'locked_until': profile.pin_locked_until
            }, status=429)
        
        if profile.pin_code == pin:
            profile.pin_attempts = 0
            profile.save(update_fields=['pin_attempts'])
            cache.set(f"pin_verified_{user.id}", True, 300)
            
            return Response({
                'success': True,
                'verified': True,
                'message': 'PIN verified successfully'
            })
        else:
            profile.pin_attempts += 1
            if profile.pin_attempts >= 5:
                profile.pin_locked_until = timezone.now() + timedelta(minutes=30)
            profile.save(update_fields=['pin_attempts', 'pin_locked_until'])
            
            remaining = 5 - profile.pin_attempts
            return Response({
                'error': f'Invalid PIN. {remaining} attempts remaining',
                'remaining_attempts': remaining,
                'locked': profile.pin_attempts >= 5
            }, status=401)
            
    except UserProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_image(request):
    user = request.user
    
    if 'profile_image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=400)
    
    file = request.FILES['profile_image']
    
    if file.size > 5 * 1024 * 1024:
        return Response({'error': 'Image too large (max 5MB)'}, status=400)
    
    try:
        profile = UserProfile.objects.get(user=user)
        profile.profile_image = file
        profile.save()
        
        return Response({
            'success': True,
            'url': profile.profile_image.url
        })
    except UserProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_cover_image(request):
    user = request.user
    
    if 'cover_image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=400)
    
    file = request.FILES['cover_image']
    
    if file.size > 10 * 1024 * 1024:
        return Response({'error': 'Image too large (max 10MB)'}, status=400)
    
    try:
        profile = UserProfile.objects.get(user=user)
        profile.cover_image = file
        profile.save()
        
        return Response({
            'success': True,
            'url': profile.cover_image.url
        })
    except UserProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_identity_verification(request):
    user = request.user
    
    if 'document_front' not in request.FILES:
        return Response({'error': 'Document image is required'}, status=400)
    
    if 'selfie_photo' not in request.FILES:
        return Response({'error': 'Selfie photo is required'}, status=400)
    
    verification_method = request.data.get('verification_method', 'national_id')
    
    try:
        from core.models.verification import IdentityVerification
        
        existing = IdentityVerification.objects.filter(
            user=user,
            verification_status__in=['pending', 'under_review']
        ).first()
        
        if existing:
            return Response({
                'error': 'You already have a pending verification request',
                'verification_id': existing.id,
                'status': existing.verification_status
            }, status=400)
        
        from core.models.verification import VerificationRateLimiter
        allowed, message, stats = VerificationRateLimiter.can_submit(user.id)
        
        if not allowed:
            return Response({'error': message, 'stats': stats}, status=429)
        
        verification_data = {
            'user': user,
            'verification_method': verification_method,
            'document_front': request.FILES['document_front'],
            'selfie_photo': request.FILES['selfie_photo'],
            'verification_status': 'pending'
        }
        
        if 'document_back' in request.FILES:
            verification_data['document_back'] = request.FILES['document_back']
        
        verification = IdentityVerification.objects.create(**verification_data)
        
        from core.models.verification import start_verification_process
        start_verification_process.delay(verification.id)
        
        from core.models.verification import VerificationAuditLog
        VerificationAuditLog.objects.create(
            verification=verification,
            action='submitted',
            performed_by=user,
            details={
                'verification_method': verification_method,
                'correlation_id': verification.correlation_id,
                'has_back_side': 'document_back' in request.FILES
            }
        )
        
        return Response({
            'success': True,
            'verification_id': verification.id,
            'status': 'pending',
            'message': 'Verification submitted successfully. You will be notified when completed.'
        }, status=201)
        
    except ImportError as e:
        logger.error(f"Verification module import error: {e}")
        return Response({'error': 'Verification system not fully configured'}, status=500)
    except Exception as e:
        logger.error(f"Verification submission failed: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_verification_status(request):
    user = request.user
    
    try:
        from core.models.verification import IdentityVerification
        
        verification = IdentityVerification.objects.filter(user=user).order_by('-submitted_at').first()
        
        if not verification:
            return Response({
                'has_verification': False,
                'message': 'No verification found'
            })
        
        return Response({
            'has_verification': True,
            'verification_id': verification.id,
            'status': verification.verification_status,
            'method': verification.verification_method,
            'submitted_at': verification.submitted_at,
            'verified_at': verification.verified_at,
            'face_match_score': verification.face_match_score,
            'overall_score': verification.overall_score,
            'verification_level': verification.verification_level,
            'rejection_reason': verification.rejection_reason
        })
        
    except ImportError:
        return Response({'error': 'Verification system not available'}, status=500)
    except Exception as e:
        logger.error(f"Failed to get verification status: {e}")
        return Response({'error': str(e)}, status=500)
    
    # ✅ Signal لتحديث الـ Dashboard تلقائياً
@receiver(post_save, sender=Contract)
def notify_dashboard_on_contract_change(sender, instance, created, **kwargs):
    """إرسال إشارة لتحديث Dashboard عند تغيير العقود"""
    from django.core.cache import cache
    # تخزين وقت آخر تحديث في cache عشان الـ Frontend يشوفه
    cache.set(f"contract_updated_{instance.id}", timezone.now().isoformat(), 3600)
    logger.info(f"📢 Contract {instance.id} updated, dashboard should refresh")
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_blockchain_status(request, contract_id):
    """الحصول على حالة العقد على البلوكشين"""
    try:
        contract = Contract.objects.get(id=contract_id)
        
        # التحقق من الصلاحية
        if request.user != contract.client and request.user != contract.freelancer:
            return Response({'error': 'Unauthorized'}, status=403)
        
        return Response({
            'contract_id': contract.id,
            'blockchain_tx_hash': contract.blockchain_tx_hash,
            'blockchain_status': contract.blockchain_status,
            'is_confirmed': contract.blockchain_status == 'confirmed',
            'network': getattr(contract, 'blockchain_network', 'sepolia'),
            'block_number': getattr(contract, 'blockchain_block_number', None),
            'contract_hash': contract.contract_hash,
        })
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
# ============================================================
# 🎯 Biometric Decision API (محسّن للتعلم الذاتي)
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_and_decide(request):
    """
    تحليل السياق واختيار الوسائل المناسبة
    يدعم التعلم الذاتي من سلوك المستخدم
    """
    context_engine = get_context_engine()
    decision_engine = get_decision_engine()
    
    # ============================================================
    # 1. استخراج السياق من الطلب (من Frontend أو إنشاء سياق ذكي)
    # ============================================================
    user_context = request.data.get('context', {})
    
    # إذا لم يرسل Frontend سياقاً كاملاً، قم بإنشاء سياق ذكي
    if not user_context or len(user_context) < 2:
        # استخراج معلومات من User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_info = get_smart_context_from_user_agent(user_agent)
        
        user_context = {
            'location': user_context.get('location', 'home'),
            'device_type': device_info['device_type'],
            'network_type': user_context.get('network_type', 'unknown'),
            'os_type': device_info['os_type'],
            'browser': device_info['browser'],
            'is_mobile': device_info['is_mobile'],
        }
    
    # إضافة معلومات الوقت الحالي (مهمة لتحليل السلوك)
    current_hour = timezone.now().hour
    user_context['hour'] = current_hour
    user_context['is_weekend'] = timezone.now().weekday() >= 5
    user_context['is_night'] = current_hour < 6 or current_hour > 22
    
    # ============================================================
    # 2. معالجة جودة البيانات
    # ============================================================
    quality_scores = request.data.get('quality_scores', {})
    
    # ============================================================
    # 3. معلومات الجهاز (قدرات الكاميرا، الميكروفون، الخ)
    # ============================================================
    device_info = request.data.get('device_info', {})
    
    # ============================================================
    # 4. تحليل السياق (مع user_id للتعلم الذاتي)
    # ============================================================
    context_result = context_engine.analyze_context(
        context=user_context,
        quality_scores=quality_scores,
        user_id=request.user.id,
        voice_confidence=quality_scores.get('voice', None),
    )
    
    # ============================================================
    # 5. اختيار وسائل التحقق المناسبة
    # ============================================================
    decision_result = decision_engine.choose_modalities(
        device_info=device_info,
        context={'risk_level': context_result.risk_level.value},
        quality_scores=quality_scores,
        user_confidence=context_result.trust_score,
    )
    
    # ============================================================
    # 6. تسجيل المحاولة للتعلم الذاتي (حتى لو فشلت)
    # ============================================================
    context_engine.record_attempt_result(
        request.user.id,
        {
            'trust_score': context_result.trust_score,
            'avg_quality': sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.5,
            'location': user_context.get('location', 'unknown'),
            'device_type': user_context.get('device_type', 'unknown'),
        },
        was_successful=(context_result.decision.value == 'allow')
    )
    
    # ============================================================
    # 7. إرجاع النتيجة للـ Frontend
    # ============================================================
    return Response({
        'success': True,
        'decision': context_result.decision.value,
        'risk_level': context_result.risk_level.value,
        'trust_score': round(context_result.trust_score, 3),
        'modalities': decision_result.selected_modalities,
        'needs_fusion': decision_result.needs_fusion,
        'explanation': context_result.recommendations[0] if context_result.recommendations else 'OK',
        'decision_explanation': decision_result.explanation,
        'confidence': round(decision_result.confidence, 3),
        'anomaly_score': round(context_result.anomaly_score, 3),
        'adaptive_threshold': round(context_result.adaptive_threshold, 3),
        'context': {
            'location': user_context.get('location'),
            'device_type': user_context.get('device_type'),
            'hour': current_hour,
            'is_night': user_context.get('is_night', False),
        }
    })
# ============================================================
# 🎯 API لتسجيل نتيجة المصادقة (للتعلم الذاتي)
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_auth_result(request):
    """
    تسجيل نتيجة محاولة المصادقة للتعلم الذاتي
    يُستدعى بعد كل محاولة مصادقة (نجحت أو فشلت)
    """
    context_engine = get_context_engine()
    
    was_successful = request.data.get('success', False)
    attempt_data = {
        'trust_score': request.data.get('trust_score', 0.5),
        'avg_quality': request.data.get('avg_quality', 0.5),
        'location': request.data.get('location', 'unknown'),
        'device_type': request.data.get('device_type', 'unknown'),
    }
    
    context_engine.record_attempt_result(
        user_id=request.user.id,
        attempt_data=attempt_data,
        was_successful=was_successful
    )
    
    logger.info(f"📊 Recorded auth result for user {request.user.id}: {'success' if was_successful else 'failed'}")
    
    return Response({'status': 'recorded', 'success': was_successful})
logger.info("=" * 60)
logger.info("🚀 MAIN VIEWS v2.0 LOADED")
logger.info("=" * 60)
logger.info("✅ UserViewSet: ACTIVE")
logger.info("✅ SkillViewSet: ACTIVE (Admin write)")
logger.info("✅ ContractViewSet: ACTIVE (Rate Limited)")
logger.info("✅ ChatRoomViewSet: ACTIVE")
logger.info("✅ Integration with Recommendations: ACTIVE")
logger.info("=" * 60)

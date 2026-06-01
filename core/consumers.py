# core/consumers.py - النسخة المتكاملة V3.1 (تم إصلاح الأخطاء)

"""
WebSocket Consumer للدردشة - متكامل مع نموذج ChatMessage
✅ متوافق مع routing.py (يدعم UUID و Room Name)
✅ يدعم المصادقة عبر JWT Token من URL
يدعم: تشفير الرسائل، Rate Limiting، Typing Indicator، Read Receipts
"""

import json
import logging
import time
import uuid as uuid_lib
from typing import Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from core.models import ChatRoom, ChatMessage

logger = logging.getLogger(__name__)


# ============================================================
# 🔐 Helper Functions
# ============================================================

async def get_user_from_token(token_string: str) -> Optional[User]:
    """
    استخراج المستخدم من JWT token
    """
    try:
        if not token_string:
            return None
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        return await database_sync_to_async(User.objects.get)(id=user_id)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None


# ============================================================
# 🔐 Rate Limiter للـ WebSocket
# ============================================================

class WebSocketRateLimiter:
    """Rate Limiter متقدم للـ WebSocket connections"""
    
    MAX_MESSAGES_PER_MINUTE = 100  # ✅ تم التعديل من 30 إلى 100
    MAX_CONNECTIONS_PER_HOUR = 50   # ✅ تم التعديل من 10 إلى 50
    
    @staticmethod
    def can_send_message(user_id: int) -> tuple[bool, int]:
        """التحقق من إمكانية إرسال رسالة"""
        minute_key = f"ws_msg_{user_id}_{time.time() // 60}"
        count = cache.get(minute_key, 0)
        
        if count >= WebSocketRateLimiter.MAX_MESSAGES_PER_MINUTE:
            return False, WebSocketRateLimiter.MAX_MESSAGES_PER_MINUTE - count
        
        cache.set(minute_key, count + 1, 60)
        return True, WebSocketRateLimiter.MAX_MESSAGES_PER_MINUTE - (count + 1)
    
    @staticmethod
    def can_connect(user_id: int) -> tuple[bool, int]:
        """التحقق من إمكانية الاتصال (لمنع DoS)"""
        hour_key = f"ws_connect_{user_id}_{time.time() // 3600}"
        count = cache.get(hour_key, 0)
        
        if count >= WebSocketRateLimiter.MAX_CONNECTIONS_PER_HOUR:
            return False, WebSocketRateLimiter.MAX_CONNECTIONS_PER_HOUR - count
        
        cache.set(hour_key, count + 1, 3600)
        return True, WebSocketRateLimiter.MAX_CONNECTIONS_PER_HOUR - (count + 1)


# ============================================================
# 🎮 Chat Consumer (المصادقة عبر Token)
# ============================================================

class ChatConsumer(AsyncWebsocketConsumer):
    """
    مستهلك WebSocket لإدارة الدردشة - متوافق مع routing.py V2.1
    
    يدعم:
        ✅ اتصال بـ UUID (room_uuid)
        ✅ اتصال بـ Room Name (room_name)
        ✅ اتصال مباشر بـ room_identifier (يدعم الاثنين)
        ✅ المصادقة عبر JWT Token من URL (?token=xxx)
        ✅ تشفير الرسائل
        ✅ Rate Limiting
        ✅ Typing Indicator
        ✅ Read Receipts
    """
    
    async def connect(self):
        """الاتصال بالغرفة - يدعم UUID و Room Name و JWT Token"""
        
        # ✅ الحصول على المعرف من الـ URL (يدعم 3 أنواع)
        self.room_identifier = (
            self.scope["url_route"]["kwargs"].get("room_uuid") or
            self.scope["url_route"]["kwargs"].get("room_name") or
            self.scope["url_route"]["kwargs"].get("room_identifier")
        )
        
        if not self.room_identifier:
            logger.error("No room identifier provided in URL")
            await self.close()
            return
        
        self.room_group_name = f"chat_{self.room_identifier}"
        
        # ✅ استخراج token من query string
        query_string = self.scope['query_string'].decode()
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        # ✅ المصادقة عبر token أولاً
        if token:
            self.user = await get_user_from_token(token)
            logger.info(f"User authenticated via token: {self.user.username if self.user else 'None'}")
        else:
            # ✅ إذا ما في token، جرب المصادقة العادية
            self.user = self.scope.get("user")
        
        # ✅ التحقق من صحة المستخدم
        if not self.user or self.user.is_anonymous:
            logger.warning(f"Unauthenticated connection attempt to room {self.room_identifier}")
            await self.close()
            return
        
        # ✅ Rate Limiting للاتصال (بدون إرسال رسالة قبل القبول)
        can_connect, remaining = WebSocketRateLimiter.can_connect(self.user.id)
        if not can_connect:
            logger.warning(f"Rate limit exceeded for user {self.user.id}")
            await self.close()  # ✅ أغلق مباشرة بدون إرسال رسالة
            return
        
        # ✅ التحقق من وجود الغرفة وصلاحية المستخدم
        room_valid, room = await self.is_valid_room(self.room_identifier, self.user.id)
        if not room_valid:
            logger.warning(f"Invalid room or user not authorized: {self.room_identifier}, user {self.user.id}")
            await self.close()
            return
        
        self.room = room
        
        # ✅ الانضمام إلى المجموعة
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # ✅ ✅ ✅ قبول الاتصال أولاً ✅ ✅ ✅
        await self.accept()
        
        # ✅ ✅ ✅ بعد القبول، أرسل رسائل التأكيد ✅ ✅ ✅
        await self.send(text_data=json.dumps({
            "type": "connected",
            "message": f"Connected to chat room",
            "room_identifier": self.room_identifier,
            "room_uuid": str(self.room.room_uuid),
            "room_name": self.room.name if hasattr(self.room, 'name') else None,
            "user": self.user.username,
            "room_id": self.room.id,
            "encryption_enabled": True
        }))
        
        # ✅ إشعار المستخدمين الآخرين بانضمام مستخدم جديد
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user": self.user.username,
                "user_id": self.user.id,
                "timestamp": timezone.now().isoformat()
            }
        )
        
        logger.info(f"User {self.user.username} connected to room {self.room_identifier}")
    
    async def disconnect(self, close_code):
        """مغادرة الغرفة"""
        if hasattr(self, 'user') and self.user and not self.user.is_anonymous:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_left",
                    "user": self.user.username,
                    "user_id": self.user.id,
                    "timestamp": timezone.now().isoformat()
                }
            )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {getattr(self, 'user', None)} disconnected")
    
    async def receive(self, text_data):
        """استقبال الرسالة من المستخدم"""
        try:
            data = json.loads(text_data)
            action = data.get("action", "message")
            
            if action == "message":
                await self.handle_message(data)
            elif action == "typing":
                await self.handle_typing(data)
            elif action == "read":
                await self.handle_read_receipt(data)
            elif action == "mark_read":
                await self.handle_mark_read(data)
            else:
                logger.warning(f"Unknown action: {action} from user {self.user.id}")
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "error": f"Unknown action: {action}"
                }))
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            await self.send(text_data=json.dumps({
                "type": "error",
                "error": "Invalid JSON format"
            }))
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            await self.send(text_data=json.dumps({
                "type": "error",
                "error": "Internal server error"
            }))
    
    async def handle_message(self, data):
        """معالجة رسالة نصية أو ملف"""
        message_text = data.get("message", "")
        message_type = data.get("message_type", "text")
        reply_to = data.get("reply_to", None)
        media_id = data.get("media_id", None)  
        
        # ✅ التأكد أن message_text ليس dict
        if isinstance(message_text, dict):
            message_text = message_text.get('text', '') or ''
        
        # ✅ ✅ ✅ السماح بنص فارغ إذا كان في ملف ✅ ✅ ✅
        if not message_text and not media_id:
            await self.send(text_data=json.dumps({
                "type": "error",
                "error": "Message cannot be empty"
            }))
            return
        
        # ✅ Rate Limiting للإرسال
        can_send, remaining = WebSocketRateLimiter.can_send_message(self.user.id)
        if not can_send:
            await self.send(text_data=json.dumps({
                "type": "error",
                "error": f"Rate limit exceeded. Max {WebSocketRateLimiter.MAX_MESSAGES_PER_MINUTE} messages per minute.",
                "remaining": remaining
            }))
            return
        
        # ✅ تخزين الرسالة في قاعدة البيانات (مع media_id)
        message = await self.save_message(
            room_identifier=self.room_identifier,
            user_id=self.user.id,
            text=message_text,
            message_type=message_type,
            reply_to=reply_to,
            media_id=media_id
        )
        
        # ✅ الحصول على النص المفكك
        decrypted_text = message.get_decrypted_text() if hasattr(message, 'get_decrypted_text') else message_text
        
        # ✅ الحصول على رابط الملف إذا وجد
        file_url = None
        file_name = None
        if message.media:
            file_url = message.media.get_file_url(use_cdn=True) if hasattr(message.media, 'get_file_url') else message.media.file.url
            file_name = message.media.file.name.split('/')[-1] if message.media.file else None
            
        # ✅ إرسال الرسالة لكل أعضاء الغرفة
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": decrypted_text,
                "sender": self.user.username,
                "sender_id": self.user.id,
                "message_id": message.id,
                "message_uuid": str(message.message_uuid),
                "created_at": message.created_at.isoformat(),
                "message_type": message_type,
                "reply_to": reply_to,
                "media_id": media_id,
                "file_url": file_url,
                "file_name": file_name,
                "encrypted": True
            }
        )
    
    async def handle_typing(self, data):
        """معالجة مؤشر الكتابة"""
        is_typing = data.get("is_typing", True)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user": self.user.username,
                "user_id": self.user.id,
                "is_typing": is_typing,
                "timestamp": timezone.now().isoformat()
            }
        )
    
    async def handle_read_receipt(self, data):
        """معالجة إشعار القراءة"""
        message_id = data.get("message_id")
        
        if message_id:
            await self.mark_message_as_read(message_id, self.user.id)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_receipt",
                    "message_id": message_id,
                    "user": self.user.username,
                    "user_id": self.user.id,
                    "timestamp": timezone.now().isoformat()
                }
            )
    
    async def handle_mark_read(self, data):
        """معالجة تحديد جميع الرسائل كمقروءة"""
        await self.mark_all_messages_as_read(self.room.id, self.user.id)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "all_read",
                "user": self.user.username,
                "user_id": self.user.id,
                "timestamp": timezone.now().isoformat()
            }
        )
    
    # ============================================================
    # Event Handlers (إرسال إلى العميل)
    # ============================================================
    
    async def chat_message(self, event):
        """إرسال الرسالة للعميل"""
        await self.send(text_data=json.dumps({
            "type": "message",
            "action": "message",
            "message": event.get("message", ""),
            "sender": event.get("sender", "Unknown"),
            "sender_id": event.get("sender_id"),
            "message_id": event.get("message_id"),
            "message_uuid": event.get("message_uuid"),
            "created_at": event.get("created_at"),
            "message_type": event.get("message_type", "text"),
            "reply_to": event.get("reply_to"),
            "media_id": event.get("media_id"),
            "file_url": event.get("file_url"),
            "file_name": event.get("file_name"),
            "encrypted": event.get("encrypted", False)
        }))
    
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "action": "typing",
            "user": event["user"],
            "user_id": event["user_id"],
            "is_typing": event["is_typing"],
            "timestamp": event["timestamp"]
        }))
    
    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            "type": "read",
            "action": "read",
            "message_id": event["message_id"],
            "user": event["user"],
            "user_id": event["user_id"],
            "timestamp": event["timestamp"]
        }))
    
    async def all_read(self, event):
        await self.send(text_data=json.dumps({
            "type": "all_read",
            "action": "all_read",
            "user": event["user"],
            "user_id": event["user_id"],
            "timestamp": event["timestamp"]
        }))
    
    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_joined",
            "user": event["user"],
            "user_id": event["user_id"],
            "timestamp": event["timestamp"]
        }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_left",
            "user": event["user"],
            "user_id": event["user_id"],
            "timestamp": event["timestamp"]
        }))
    
    # ============================================================
    # Database Operations (متوافقة مع UUID و Room ID)
    # ============================================================
    
    @database_sync_to_async
    def is_valid_room(self, room_identifier: str, user_id: int) -> tuple[bool, Optional[ChatRoom]]:
        """
        التحقق من صحة الغرفة - يدعم UUID و Room ID
        """
        try:
            # ✅ محاولة البحث بـ UUID أولاً
            try:
                uuid_obj = uuid_lib.UUID(room_identifier)
                room = ChatRoom.objects.get(room_uuid=uuid_obj, is_active=True)
            except (ValueError, ChatRoom.DoesNotExist):
                # ✅ إذا لم يكن UUID، حاول البحث بالـ ID
                try:
                    room_id = int(room_identifier)
                    room = ChatRoom.objects.get(id=room_id, is_active=True)
                except (ValueError, ChatRoom.DoesNotExist):
                    logger.warning(f"Room not found: {room_identifier}")
                    return False, None
            
            # ✅ التحقق من أن المستخدم مشارك في الغرفة
            is_participant = room.participants.filter(id=user_id).exists()
            return is_participant, room if is_participant else None
            
        except Exception as e:
            logger.error(f"Error validating room: {e}")
            return False, None

    @database_sync_to_async
    def save_message(self, room_identifier: str, user_id: int, text: str,
                     message_type: str, reply_to: int = None, media_id: int = None) -> ChatMessage:
        """
        حفظ الرسالة - يدعم UUID و Room ID و Media ID
        """
        # ✅ البحث عن الغرفة (يدعم UUID أو ID)
        try:
            try:
                uuid_obj = uuid_lib.UUID(room_identifier)
                room = ChatRoom.objects.get(room_uuid=uuid_obj)
            except ValueError:
                # إذا لم يكن UUID، جرب البحث بالـ ID
                room_id = int(room_identifier)
                room = ChatRoom.objects.get(id=room_id)
        except (ChatRoom.DoesNotExist, ValueError) as e:
            raise ValueError(f"Room not found: {room_identifier}")
        
        user = User.objects.get(id=user_id)
        
        # ✅ تشفير المحتوى (إذا كان نصاً)
        encrypted_content = None
        if text and message_type == 'text':
            encrypted_content = room.encrypt_message(text)
        
        # ✅ إنشاء الرسالة
        message = ChatMessage.objects.create(
            room=room,
            sender=user,
            encrypted_content=encrypted_content,
            text='' if encrypted_content else (text if text else '📎 File'),
            message_type=message_type,
            status='sent'
        )
        
        # ✅ ربط الملف إذا وجد
        if media_id:
            from core.models import Media
            try:
                media = Media.objects.get(id=media_id, uploaded_by=user)
                message.media = media
                message.save(update_fields=['media'])
                # ✅ إذا كان الملف موجود ولم يكن هناك نص، نوع الرسالة يكون file
                if not text and message_type == 'text':
                    if media.is_image:
                        message.message_type = 'image'
                    elif media.is_video:
                        message.message_type = 'video'
                    elif media.is_audio:
                        message.message_type = 'audio'
                    else:
                        message.message_type = 'file'
                    message.save(update_fields=['message_type'])
                logger.info(f"Message {message.id} linked to media {media_id}")
            except Media.DoesNotExist:
                logger.warning(f"Media {media_id} not found for user {user_id}")
                
        # ✅ تحديث إحصائيات الغرفة
        room.last_activity = timezone.now()
        if text:
            room.last_message_preview = text[:100]
        room.total_messages += 1
        room.save(update_fields=['last_activity', 'last_message_preview', 'total_messages'])
        
        # ✅ معالجة الرد على رسالة سابقة
        if reply_to:
            try:
                parent_message = ChatMessage.objects.get(id=reply_to)
                message.reply_to = parent_message
                message.save(update_fields=['reply_to'])
            except ChatMessage.DoesNotExist:
                pass
        
        return message
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id: int, user_id: int):
        """تحديد رسالة كمقروءة"""
        try:
            message = ChatMessage.objects.get(id=message_id)
            if message.sender.id != user_id:
                message.mark_as_read()
        except ChatMessage.DoesNotExist:
            pass
    
    @database_sync_to_async
    def mark_all_messages_as_read(self, room_id: int, user_id: int):
        """تحديد جميع رسائل الغرفة كمقروءة"""
        count = ChatMessage.objects.filter(
            room_id=room_id,
            status='sent'
        ).exclude(sender_id=user_id).update(status='read', read_at=timezone.now())
        
        logger.info(f"Marked {count} messages as read in room {room_id} for user {user_id}")
        return count
    
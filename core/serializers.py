# core/serializers.py - النسخة النهائية الكاملة مع كل تعديلات الدردشة وميزة الرد

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Skill, UserProfile, Contract, SkillPost, 
    ChatRoom, ChatMessage, Media, ContractRating
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'description', 'demand_level']


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['id', 'file', 'description', 'file_size', 'uploaded_at']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    pin_code = serializers.CharField(write_only=True, required=False, max_length=8, min_length=8)
    has_pin = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'profile_image', 'cover_image', 'bio', 'headline',
            'city', 'country', 'experience_years', 'skills',
            'contracts_count', 'completion_rate', 'avg_response_time',
            'avg_rating', 'trust_score', 'reputation_level',
             'pin_code', 'has_pin'  # ✅ أضيفي هذول
        ]


    def get_has_pin(self, obj):
        """التحقق من وجود PIN"""
        return bool(obj.pin_code)
    
class ContractSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    skill = SkillSerializer(read_only=True)
    
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='client'
    )
    freelancer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='freelancer'
    )
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), write_only=True, source='skill'
    )
    
    # ✅✅✅ أضيفي هذا الحقل ✅✅✅
    chatroom_id = serializers.PrimaryKeyRelatedField(
        queryset=ChatRoom.objects.all(), write_only=True, source='chatroom', required=False, allow_null=True
    )
    
    class Meta:
        model = Contract
        fields = [
            'id', 'title', 'client', 'freelancer', 'skill',
            'client_id', 'freelancer_id', 'skill_id', 'chatroom_id',
            'total_amount', 'currency', 'status', 'progress',
            'contract_hash', 'created_at', 'updated_at', 'signed_at',
            'deadline'
        ]


class SkillPostSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), write_only=True, source='skill'
    )

    class Meta:
        model = SkillPost
        fields = [
            'id', 'creator', 'title', 'skill', 'skill_id',
            'description', 'requirements', 'price', 'currency',
            'status', 'views_count', 'created_at', 'visible'
        ]


# ============================================================
# 📊 CHAT SERIALIZERS - النسخة الأسطورية الكاملة
# ============================================================

# ✅ ChatRoomSerializer - النسخة المطورة بالكامل (مع حل مشكلة name)
class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participants_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    
    # ✅✅✅ أضيفي هذا السطر ✅✅✅
    contract = ContractSerializer(read_only=True)  # جلب بيانات العقد المرتبط
    # ✅✅✅ أضف هذه الحقول الجديدة ✅✅✅
    skill_id = serializers.SerializerMethodField()
    post_skill_id = serializers.SerializerMethodField()
    post_title = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_uuid', 'name', 'participants', 'participants_count',
            'room_type', 'is_active', 'created_at', 'last_activity',
            'total_messages', 'last_message_at', 'last_message_preview',
            'unread_count', 'last_message',
            'contract', 'post',
            'skill_id', 'post_skill_id', 'post_title'  # ✅ أضفهم هنا
        ]
        read_only_fields = ['created_at', 'last_activity', 'room_uuid', 'total_messages', 'last_message_at']
    def get_skill_id(self, obj):
        """جلب skill_id من المنشور المرتبط بالغرفة"""
        if obj.post and obj.post.skill:
            return obj.post.skill.id
        return None
    
    def get_post_skill_id(self, obj):
        """نفس skill_id (للتوافق)"""
        if obj.post and obj.post.skill:
            return obj.post.skill.id
        return None
    
    def get_post_title(self, obj):
        """جلب عنوان المنشور"""
        if obj.post:
            return obj.post.title
        return None
    
    def get_name(self, obj):
        """جلب اسم الغرفة - حل مشكلة الحقل name"""
        if obj.post:
            return f"💬 {obj.post.title[:40]}"
        elif obj.contract:
            return f"📄 Contract #{obj.contract.id}"
        return f"Chat #{obj.id}"
    
    def get_participants_count(self, obj):
        return obj.participants.count()
    
    def get_last_message(self, obj):
        """آخر رسالة في الغرفة"""
        last_msg = obj.messages.select_related('sender').first()
        if last_msg:
            return {
                'id': last_msg.id,
                'text': last_msg.get_decrypted_text()[:100],
                'sender_id': last_msg.sender.id,
                'sender_name': last_msg.sender.username,
                'created_at': last_msg.created_at.isoformat(),
                'message_type': last_msg.message_type
            }
        return None
    
    def get_last_message_preview(self, obj):
        """معاينة آخر رسالة (للعرض في القائمة)"""
        last_msg = obj.messages.first()
        if last_msg:
            text = last_msg.get_decrypted_text()
            if len(text) > 50:
                text = text[:47] + '...'
            return text
        return ""
    
    def get_unread_count(self, obj):
        """عدد الرسائل غير المقروءة للمستخدم الحالي"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0


# ✅ ChatRoomCreateSerializer - لإنشاء غرف جديدة
class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """مخصص لإنشاء غرف محادثة جديدة"""
    post_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    contract_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    participant_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = ChatRoom
        fields = ['post_id', 'contract_id', 'participant_id', 'room_type']
    
    def validate(self, data):
        """التحقق من صحة البيانات"""
        if not data.get('post_id') and not data.get('contract_id'):
            raise serializers.ValidationError("Either post_id or contract_id is required")
        return data
    
    def validate_participant_id(self, value):
        """التحقق من وجود المستخدم"""
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Participant not found")
        return value
    
    def create(self, validated_data):
        post_id = validated_data.pop('post_id', None)
        contract_id = validated_data.pop('contract_id', None)
        participant_id = validated_data.pop('participant_id')
        room_type = validated_data.get('room_type', 'post_discussion')
        
        request = self.context.get('request')
        
        # البحث عن غرفة موجودة (لتجنب التكرار)
        existing_room = None
        
        if post_id:
            existing_room = ChatRoom.objects.filter(
                post_id=post_id,
                participants=request.user
            ).first()
        
        if existing_room:
            return existing_room
        
        # إنشاء غرفة جديدة
        room = ChatRoom.objects.create(
            post_id=post_id,
            contract_id=contract_id,
            room_type=room_type
        )
        
        # إضافة المشاركين
        room.participants.add(request.user)
        if participant_id != request.user.id:
            try:
                room.participants.add(participant_id)
            except User.DoesNotExist:
                pass
        
        return room


# ✅ ChatMessageSerializer - للقراءة فقط (عرض الرسائل)
class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    text = serializers.SerializerMethodField(read_only=True)
    reply_to_message = serializers.SerializerMethodField(read_only=True)
    is_mine = serializers.SerializerMethodField()
        
    # ✅✅✅ أضيفي هذول ✅✅✅
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField() 

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'room', 'sender', 'encrypted_content', 'text',
            'message_type', 'message_uuid', 'reply_to', 'reply_to_message',
            'status', 'created_at', 'read_at', 'delivered_at', 'is_mine',
            'file_url', 'file_name', 'file_size'  # ✅ أضيفي هذول
        ]
        read_only_fields = ['message_uuid', 'created_at', 'status']
    
    def get_text(self, obj):
        try:
            return obj.get_decrypted_text()
        except:
            return "[Encrypted]"
    
    def get_reply_to_message(self, obj):
        if obj.reply_to:
            return ChatMessageSerializer(obj.reply_to, context=self.context).data
        return None
    
    def get_is_mine(self, obj):
        """تحديد إذا كانت الرسالة من المستخدم الحالي"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender.id == request.user.id
        return False
   
      # ✅ عدلي هذه الدالة
    def get_file_url(self, obj):
        # ✅ أولاً: التحقق من media (نظام Media المتقدم)
        if obj.media:
            return obj.media.get_file_url(use_cdn=True)
        # ✅ ثانياً: التحقق من file العادي (للتوافق مع القديم)
        if obj.file:
            return obj.file.url
        return None
    # ✅ أضيفي هذه الدالة الجديدة
    def get_file_name(self, obj):
        if obj.media:
            return obj.media.file.name.split('/')[-1]
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None
     # ✅ أضيفي هذه الدالة الجديدة
    def get_file_size(self, obj):
        if obj.media:
            return obj.media.size_mb
        if obj.file and obj.file.size:
            return round(obj.file.size / (1024 * 1024), 2)
        return None
# ✅ ChatMessageCreateSerializer - لإنشاء رسائل جديدة (مع ميزة الرد)
class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """مخصص لإنشاء الرسائل الجديدة مع التحقق من الصلاحية وميزة الرد"""
    
    reply_to_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    media_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
   
    class Meta:
        model = ChatMessage
        fields = ['room', 'text', 'message_type', 'reply_to_id','media_id', 'file' ]
    
    def validate_room(self, value):
        """التحقق من أن المستخدم عضو في الغرفة"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user not in value.participants.all():
                raise serializers.ValidationError("You are not a participant in this room")
        return value
    def validate_text(self, value):
        """التحقق من أن النص غير فارغ - مع السماح بنص فارغ للملفات"""
    # ✅ السماح بنص فارغ إذا كان في media_id
        media_id = self.initial_data.get('media_id')
        if media_id and not value:
            return ""  # هذا مهم للملفات والفيديو
    
        if not value or not value.strip():
                raise serializers.ValidationError("Message text cannot be empty")
        if len(value) > 5000:
                raise serializers.ValidationError("Message too long (max 5000 characters)")
                return value.strip()
    
    
    def validate_reply_to_id(self, value):
        """التحقق من وجود الرسالة التي يرد عليها"""
        if value:
            if not ChatMessage.objects.filter(id=value).exists():
                raise serializers.ValidationError("Message to reply to not found")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        reply_to_id = validated_data.pop('reply_to_id', None)
        media_id = validated_data.pop('media_id', None)
        
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
            
         # ✅✅✅ ربط الملف من نظام Media ✅✅✅
        if media_id:
            from .models import Media
            try:
                media = Media.objects.get(id=media_id, uploaded_by=request.user)
                validated_data['media'] = media
                # تحديث نوع الرسالة حسب نوع الملف
                if media.is_image:
                    validated_data['message_type'] = 'image'
                elif media.is_video:
                    validated_data['message_type'] = 'video'
                elif media.is_audio:
                    validated_data['message_type'] = 'audio'
                else:
                    validated_data['message_type'] = 'file'
                validated_data['text'] = f"📎 {media.file.name.split('/')[-1]}"
            except Media.DoesNotExist:
                pass
        
        message = super().create(validated_data)
        
        if reply_to_id:
            try:
                reply_to = ChatMessage.objects.get(id=reply_to_id)
                message.reply_to = reply_to
                message.save(update_fields=['reply_to'])
            except ChatMessage.DoesNotExist:
                pass
        
        return message
        

# ✅ ChatMessageUpdateSerializer - لتحديث حالة الرسائل (read/delivered)
class ChatMessageUpdateSerializer(serializers.ModelSerializer):
    """تحديث حالة الرسائل (مقروءة، موصلة)"""
    
    class Meta:
        model = ChatMessage
        fields = ['status']
    
    def validate_status(self, value):
        if value not in ['delivered', 'read']:
            raise serializers.ValidationError("Status must be 'delivered' or 'read'")
        return value


# ✅ ChatRoomListSerializer - لقائمة الغرف المبسطة (للواجهة الرئيسية)
class ChatRoomListSerializer(serializers.ModelSerializer):
    """نسخة مبسطة لقائمة المحادثات"""
    name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    participants_avatars = serializers.SerializerMethodField()
    
    # ✅✅✅ أضيفي هذا السطر ✅✅✅
    contract = ContractSerializer(read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_uuid', 'room_type', 'last_message',
            'last_message_at', 'unread_count', 'participants_count',
            'participants_avatars', 'is_active', 'created_at',
            'contract','post'
        ]
    
    def get_name(self, obj):
        if obj.post:
            return obj.post.title[:50]
        elif obj.contract:
            return f"Contract #{obj.contract.id}"
        return "Chat"
    
    def get_last_message(self, obj):
        last_msg = obj.messages.first()
        if last_msg:
            text = last_msg.get_decrypted_text()
            sender = last_msg.sender.username
            if len(text) > 60:
                text = text[:57] + '...'
            return f"{sender}: {text}"
        return "No messages yet"
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0
    
    def get_participants_count(self, obj):
        return obj.participants.count()
    
    def get_participants_avatars(self, obj):
        """أفاتار المشاركين (للعرض في الواجهة)"""
        avatars = []
        for participant in obj.participants.all()[:3]:
            profile = getattr(participant, 'profile', None)
            if profile and profile.profile_image:
                avatars.append(profile.profile_image)
            else:
                avatars.append(None)
        return avatars


# ============================================================
# ⭐ CONTRACT RATING SERIALIZER
# ============================================================

class ContractRatingSerializer(serializers.ModelSerializer):
    rated_by = UserSerializer(read_only=True)
    rated_user = UserSerializer(read_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = ContractRating
        fields = ['id', 'contract', 'rated_by', 'rated_user', 'rating', 'feedback', 'created_at']


# ============================================================
# 🔄 RECOMMENDATION SERIALIZERS
# ============================================================

class UserRecommendationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    trust_score = serializers.FloatField()
    skills = serializers.ListField(child=serializers.CharField())
    reputation_level = serializers.CharField()
    profile_image = serializers.CharField(allow_null=True)
    city = serializers.CharField(allow_null=True)
    country = serializers.CharField(allow_null=True)
    completion_rate = serializers.FloatField()
    avg_rating = serializers.FloatField()
    explanation = serializers.DictField(required=False)


class MetricsSerializer(serializers.Serializer):
    request_count = serializers.IntegerField()
    error_rate = serializers.FloatField()
    avg_duration_ms = serializers.FloatField()
    cache_hit_rate = serializers.FloatField()
    
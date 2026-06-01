from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    UserKeys, Skill, UserProfile, SkillPost, Contract, 
    ChatRoom, ChatMessage, LegalNotification, IdentityVerification,
    ContractTemplate, BlockchainBlock, ContractAuditLog, ContractRating, Media
)

# ---------------------------
# User Keys Admin
# ---------------------------
@admin.register(UserKeys)
class UserKeysAdmin(admin.ModelAdmin):
    list_display = ('user', 'key_version', 'created_at', 'last_rotated', 'public_key_preview')
    readonly_fields = ('created_at', 'last_rotated', 'public_key_preview')
    search_fields = ('user__username', 'key_version')
    list_filter = ('key_version', 'created_at')

    def public_key_preview(self, obj):
        if obj.public_key:
            return format_html(f"<code style='font-size:10px;'>{obj.public_key[:50]}...</code>")
        return "-"
    public_key_preview.short_description = "Public Key"

# ---------------------------
# Skills Admin
# ---------------------------
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'demand_level', 'avg_price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'category', 'description')
    readonly_fields = ('avg_price', 'demand_level', 'created_at')
    actions = ['update_skills_stats']

    def update_skills_stats(self, request, queryset):
        for skill in queryset:
            skill.update_stats()
        self.message_user(request, f"Updated statistics for {queryset.count()} skills")
    update_skills_stats.short_description = "Update selected skills statistics"

# ---------------------------
# User Profiles Admin
# ---------------------------
class UserProfileSkillsInline(admin.TabularInline):
    model = UserProfile.skills.through
    extra = 1
    verbose_name = "Skill"
    verbose_name_plural = "Skills"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'city', 'country', 'trust_score_display', 
        'reputation_level_display', 'verification_level_display',
        'profile_image_tag', 'contracts_count', 'created_at'
    )
    list_filter = ('reputation_level', 'verification_level', 'created_at')
    search_fields = ('user__username', 'city', 'country', 'headline')
    readonly_fields = (
        'trust_score', 'reputation_level', 'contracts_count', 
        'completion_rate', 'avg_rating', 'total_earnings',
        'profile_image_tag', 'cover_image_tag', 'age_display',
        'created_at', 'updated_at'
    )
    inlines = [UserProfileSkillsInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'profile_image', 'profile_image_tag', 'cover_image', 'cover_image_tag')
        }),
        ('Personal Information', {
            'fields': ('bio', 'headline', 'phone', 'city', 'country', 'birth_date', 'age_display', 'gender')
        }),
        ('Professional Information', {
            'fields': ('experience_years', 'skills')
        }),
        ('Performance Statistics', {
            'fields': (
                'contracts_count', 'completion_rate', 'avg_response_time', 
                'avg_rating', 'total_earnings'
            )
        }),
        ('Reputation and Trust System', {
            'fields': ('trust_score', 'reputation_level', 'verification_level')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def trust_score_display(self, obj):
        score = obj.trust_score
        color = "green" if score >= 70 else "orange" if score >= 50 else "red"
        return format_html(f"<span style='color:{color}; font-weight:bold;'>{score}/100</span>")
    trust_score_display.short_description = "Trust Level"

    def reputation_level_display(self, obj):
        levels = {
            'newbie': ('Newbie', '🟢'),
            'rising': ('Rising', '🟡'),
            'pro': ('Professional', '🔵'),
            'expert': ('Expert', '🟣')
        }
        level, emoji = levels.get(obj.reputation_level, ('', ''))
        return format_html(f"{emoji} {level}")
    reputation_level_display.short_description = "Reputation Level"

    def verification_level_display(self, obj):
        levels = {
            1: ('Basic', '⚪'),
            2: ('Verified', '🔵'),
            3: ('Professional', '🟢')
        }
        level, emoji = levels.get(obj.verification_level, ('', ''))
        return format_html(f"{emoji} {level}")
    verification_level_display.short_description = "Verification Level"

    def profile_image_tag(self, obj):
        if obj.profile_image:
            return format_html(
                f"<img src='{obj.profile_image.url}' width='80' height='80' "
                f"style='border-radius:50%; border:3px solid #4CAF50; object-fit:cover;' />"
            )
        return "❌ No Image"
    profile_image_tag.short_description = "Profile Image"

    def cover_image_tag(self, obj):
        if obj.cover_image:
            return format_html(
                f"<img src='{obj.cover_image.url}' width='160' height='80' "
                f"style='border:2px solid #2196F3; object-fit:cover; border-radius:8px;' />"
            )
        return "❌ No Cover Image"
    cover_image_tag.short_description = "Cover Image"

    def age_display(self, obj):
        return obj.age or "Not specified"
    age_display.short_description = "Age"

# ---------------------------
# Skill Posts Admin
# ---------------------------
@admin.register(SkillPost)
class SkillPostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'creator', 'skill', 'price_with_currency', 'status_display', 
        'featured', 'urgent', 'days_remaining_display', 'created_at'
    )
    list_filter = ('status', 'featured', 'urgent', 'skill__category', 'created_at')
    search_fields = ('title', 'description', 'creator_username', 'skill_name')
    readonly_fields = ('views_count', 'offers_count', 'likes_count', 'created_at', 'updated_at', 'is_expired_display')
    list_editable = ('featured', 'urgent')
    fieldsets = (
        ('Basic Information', {
            'fields': ('creator', 'title', 'skill', 'description', 'requirements')
        }),
        ('Financial Details', {
            'fields': ('price', 'currency', 'is_negotiable')
        }),
        ('Location and Settings', {
            'fields': ('location', 'status', 'featured', 'urgent')
        }),
        ('Interaction Statistics', {
            'fields': ('views_count', 'offers_count', 'likes_count')
        }),
        ('Duration Management', {
            'fields': ('expiry_date', 'is_expired_display', 'visible')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def price_with_currency(self, obj):
        return f"{obj.price} {obj.currency}"
    price_with_currency.short_description = "Price"

    def status_display(self, obj):
        status_map = {
            'open': ('Open', '🟢'),
            'in_progress': ('In Progress', '🟡'),
            'completed': ('Completed', '🔵'),
            'closed': ('Closed', '🔴')
        }
        status, emoji = status_map.get(obj.status, ('', ''))
        return format_html(f"{emoji} {status}")
    status_display.short_description = "Status"

    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days > 7:
            color = "green"
        elif days > 3:
            color = "orange"
        else:
            color = "red"
        return format_html(f"<span style='color:{color}; font-weight:bold;'>{days} days</span>")
    days_remaining_display.short_description = "Days Remaining"

    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html("✅ <strong>Expired</strong>")
        return format_html("❌ <strong>Active</strong>")
    is_expired_display.short_description = "Expired"

# ---------------------------
# Contracts Admin
# ---------------------------
class ContractAuditLogInline(admin.TabularInline):
    model = ContractAuditLog
    extra = 0
    readonly_fields = ('action', 'performed_by', 'timestamp', 'details_preview')
    can_delete = False
    def details_preview(self, obj):
        if obj.details is None:
            return "No details"
        return format_html("<code>{}...</code>", str(obj.details)[:50])
    details_preview.short_description = "Details"

class BlockchainBlockInline(admin.TabularInline):
    model = BlockchainBlock
    extra = 0
    readonly_fields = ('index', 'previous_hash', 'current_hash', 'timestamp', 'is_confirmed')
    can_delete = False

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'client', 'freelancer', 'skill', 'total_amount_with_currency',
        'status_display', 'progress_display', 'is_active_display', 
        'days_until_deadline_display', 'created_at'
    )
    list_filter = ('status', 'payment_type', 'skill', 'created_at')
    search_fields = ('title', 'description', 'client__username', 'freelancer__username', 'skill_name')
    readonly_fields = (
        'contract_hash', 'timestamp_token', 'signed_at', 'completed_at',
        'created_at', 'updated_at', 'is_active_display', 'days_until_deadline_display',
        'client_signature_preview', 'freelancer_signature_preview'
    )
    inlines = [ContractAuditLogInline, BlockchainBlockInline]
    fieldsets = (
        ('Parties', {
            'fields': ('client', 'freelancer')
        }),
        ('Project Details', {
            'fields': ('title', 'description', 'skill')
        }),
        ('Financial Terms', {
            'fields': ('total_amount', 'currency', 'payment_type')
        }),
        ('Status Management', {
            'fields': ('status', 'progress')
        }),
        ('Dates', {
            'fields': ('deadline', 'days_until_deadline_display', 'signed_at', 'completed_at')
        }),
        ('Digital Signatures', {
            'fields': ('client_signature', 'client_signature_preview', 'freelancer_signature', 'freelancer_signature_preview')
        }),
        ('Security', {
            'fields': ('contract_hash', 'timestamp_token')
        }),
        ('Terms and Deliverables', {
            'fields': ('terms', 'deliverables')
        }),
        ('Automatic Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def total_amount_with_currency(self, obj):
        return f"{obj.total_amount} {obj.currency}"
    total_amount_with_currency.short_description = "Amount"

    def status_display(self, obj):
        status_map = {
            'draft': ('Draft', '📝'),
            'pending': ('Pending Signature', '⏳'),
            'active': ('Active', '🔄'),
            'completed': ('Completed', '✅'),
            'cancelled': ('Cancelled', '❌'),
            'disputed': ('Disputed', '⚠')
        }
        status, emoji = status_map.get(obj.status, ('', ''))
        return format_html(f"{emoji} {status}")
    status_display.short_description = "Status"

    def progress_display(self, obj):
        color = "green" if obj.progress >= 80 else "orange" if obj.progress >= 50 else "red"
        return format_html(
            f"<div style='background:#f0f0f0; border-radius:10px; height:20px; width:100px;'>"
            f"<div style='background:{color}; width:{obj.progress}%; height:100%; border-radius:10px; text-align:center; color:white; font-size:12px;'>"
            f"{obj.progress}%</div></div>"
        )
    progress_display.short_description = "Progress"

    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = "Active"

    def days_until_deadline_display(self, obj):
        days = obj.days_until_deadline
        if days > 10:
            color = "green"
        elif days > 3:
            color = "orange"
        else:
            color = "red"
        return format_html(f"<span style='color:{color}; font-weight:bold;'>{days} days</span>")
    days_until_deadline_display.short_description = "Days Until Deadline"

    def client_signature_preview(self, obj):
        if obj.client_signature:
            return format_html(f"<code style='font-size:10px; color:green;'>✓ {obj.client_signature[:30]}...</code>")
        return "❌ Not signed"
    client_signature_preview.short_description = "Client Signature"

    def freelancer_signature_preview(self, obj):
        if obj.freelancer_signature:
            return format_html(f"<code style='font-size:10px; color:blue;'>✓ {obj.freelancer_signature[:30]}...</code>")
        return "❌ Not signed"
    freelancer_signature_preview.short_description = "Freelancer Signature"

# ---------------------------
# Legal Notifications Admin
# ---------------------------
@admin.register(LegalNotification)
class LegalNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'contract', 'user', 'notification_type_display', 'priority_display', 'sent_at', 'is_read')
    list_filter = ('notification_type', 'priority_level', 'sent_at', 'is_mandatory')
    search_fields = ('title', 'message', 'contract_title', 'userusername')
    readonly_fields = ('sent_at', 'read_at', 'sent_via_preview')
    actions = ['send_selected_notifications']

    def notification_type_display(self, obj):
        type_map = {
            'contract_reminder': ('Contract Reminder', '⏰'),
            'deadline_warning': ('Deadline Warning', '⚠'),
            'payment_due': ('Payment Due', '💰'),
            'breach_notice': ('Contract Breach Notice', '🚨')
        }
        notification_type, emoji = type_map.get(obj.notification_type, ('', ''))
        return format_html(f"{emoji} {notification_type}")
    notification_type_display.short_description = "Notification Type"

    def priority_display(self, obj):
        priorities = {
            1: ('Low', '🟢'),
            2: ('Medium', '🟡'),
            3: ('High', '🔴')
        }
        priority, emoji = priorities.get(obj.priority_level, ('', ''))
        return format_html(f"{emoji} {priority}")
    priority_display.short_description = "Priority"

    def is_read(self, obj):
        return obj.read_at is not None
    is_read.boolean = True
    is_read.short_description = "Read"

    def sent_via_preview(self, obj):
        if obj.sent_via:
            return format_html(f"<code>{', '.join(obj.sent_via)}</code>")
        return "Not sent yet"
    sent_via_preview.short_description = "Delivery Methods"

    def send_selected_notifications(self, request, queryset):
        for notification in queryset:
            notification.send_notification()
        self.message_user(request, f"Sent {queryset.count()} notifications")
    send_selected_notifications.short_description = "Send selected notifications"

# ---------------------------
# Identity Verification Admin
# ---------------------------
@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_method_display', 'verification_status_display', 'verification_level_display', 'submitted_at')
    list_filter = ('verification_method', 'verification_status', 'verification_level', 'submitted_at')
    search_fields = ('user__username', 'verification_data')
    readonly_fields = ('submitted_at', 'verified_at', 'document_front_preview', 'verification_data_preview')
    actions = ['approve_selected_verifications']

    def verification_method_display(self, obj):
        methods = {
            'national_id': ('National ID', '🆔'),
            'passport': ('Passport', '📘'),
            'biometric': ('Biometric', '👁')
        }
        method, emoji = methods.get(obj.verification_method, ('', ''))
        return format_html(f"{emoji} {method}")
    verification_method_display.short_description = "Verification Method"

    def verification_status_display(self, obj):
        status_map = {
            'pending': ('Pending Review', '🟡'),
            'approved': ('Approved', '🟢'),
            'rejected': ('Rejected', '🔴')
        }
        status, emoji = status_map.get(obj.verification_status, ('', ''))
        return format_html(f"{emoji} {status}")
    verification_status_display.short_description = "Verification Status"

    def verification_level_display(self, obj):
        levels = {
            1: ('Basic', '⚪'),
            2: ('Verified', '🔵'),
            3: ('Professional', '🟢')
        }
        level, emoji = levels.get(obj.verification_level, ('', ''))
        return format_html(f"{emoji} {level}")
    verification_level_display.short_description = "Verification Level"

    def document_front_preview(self, obj):
        if obj.document_front:
            return format_html(f"<img src='{obj.document_front.url}' width='200' style='border:2px solid #ccc; border-radius:8px;' />")
        return "❌ No document"
    document_front_preview.short_description = "Document Image"

    def verification_data_preview(self, obj):
        return format_html(f"<pre style='background:#f5f5f5; padding:10px; border-radius:5px;'>{obj.verification_data}</pre>")
    verification_data_preview.short_description = "Verification Data"

    def approve_selected_verifications(self, request, queryset):
        for verification in queryset:
            verification.approve(request.user)
        self.message_user(request, f"Approved {queryset.count()} verification processes")
    approve_selected_verifications.short_description = "Approve selected verifications"

# ---------------------------
# Contract Templates Admin
# ---------------------------
@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_display', 'is_approved', 'is_public', 'version', 'usage_count', 'created_at')
    list_filter = ('category', 'is_approved', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'template_content')
    list_editable = ('is_approved', 'is_public')
    readonly_fields = ('usage_count', 'created_at', 'variables_preview')

    def category_display(self, obj):
        categories = {
            'freelance': ('Freelance', '💼'),
            'employment': ('Employment', '👔'),
            'service': ('Services', '🔧')
        }
        category, emoji = categories.get(obj.category, ('', ''))
        return format_html(f"{emoji} {category}")
    category_display.short_description = "Category"

    def variables_preview(self, obj):
        if obj.variables is None:
            return "No variables"
        return format_html("<pre style='background:#f5f5f5; padding:10px; border-radius:5px;'>{}</pre>", obj.variables)
    variables_preview.short_description = "Variables"

# ---------------------------
# Blockchain Blocks Admin
# ---------------------------
@admin.register(BlockchainBlock)
class BlockchainBlockAdmin(admin.ModelAdmin):
    list_display = ('contract', 'index', 'previous_hash_preview', 'current_hash_preview', 'timestamp', 'is_confirmed')
    list_filter = ('is_confirmed', 'timestamp', 'contract')
    search_fields = ('contract__title', 'previous_hash', 'current_hash')
    readonly_fields = ('previous_hash', 'current_hash', 'timestamp', 'nonce', 'is_confirmed', 'integrity_status')

    def previous_hash_preview(self, obj):
        return format_html(f"<code style='font-size:9px;'>{obj.previous_hash[:20]}...</code>")
    previous_hash_preview.short_description = "Previous Hash"

    def current_hash_preview(self, obj):
        return format_html(f"<code style='font-size:9px;'>{obj.current_hash[:20]}...</code>")
    current_hash_preview.short_description = "Current Hash"

    def integrity_status(self, obj):
        if obj.verify_integrity():
            return format_html("✅ <strong>Integrity OK</strong>")
        return format_html("❌ <strong>Integrity Failed</strong>")
    integrity_status.short_description = "Block Integrity"

# ---------------------------
# Contract Audit Logs Admin
# ---------------------------
@admin.register(ContractAuditLog)
class ContractAuditLogAdmin(admin.ModelAdmin):
    list_display = ('contract', 'action_display', 'performed_by', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('contract_title', 'performed_by_username', 'details', 'ip_address')
    readonly_fields = ('timestamp', 'details_preview')

    def action_display(self, obj):
        actions = {
            'created': ('Created', '🆕'),
            'signed': ('Signed', '✍'),
            'updated': ('Updated', '🔄'),
            'completed': ('Completed', '✅'),
            'cancelled': ('Cancelled', '❌'),
            'disputed': ('Disputed', '⚠')
        }
        action, emoji = actions.get(obj.action, ('', ''))
        return format_html(f"{emoji} {action}")
    action_display.short_description = "Action"

    def details_preview(self, obj):
        if obj.details is None:
            return "No details"
        return format_html("<pre style='background:#f5f5f5; padding:10px; border-radius:5px;'>{}</pre>", obj.details)
    details_preview.short_description = "Details"

# ---------------------------
# Contract Ratings Admin
# ---------------------------
@admin.register(ContractRating)
class ContractRatingAdmin(admin.ModelAdmin):
    list_display = ('contract', 'rated_by', 'rated_user', 'rating_display', 'would_recommend', 'created_at')
    list_filter = ('would_recommend', 'created_at')
    search_fields = ('contract_title', 'rated_byusername', 'rated_user_username', 'feedback')
    readonly_fields = ('rating', 'created_at', 'feedback_preview')

    def rating_display(self, obj):
        stars = "⭐" * int(obj.rating)
        return format_html(f"{stars} ({obj.rating:.1f}/5)")
    rating_display.short_description = "Rating"

    def feedback_preview(self, obj):
        if obj.feedback:
            return format_html(f"<div style='background:#f9f9f9; padding:10px; border-radius:5px; border-right:3px solid #4CAF50;'>{obj.feedback}</div>")
        return "No feedback"
    feedback_preview.short_description = "Feedback"

# ---------------------------
# Media Admin
# ---------------------------
@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_preview', 'uploaded_by', 'file_type', 'file_size_display', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('description', 'uploaded_by__username')
    readonly_fields = ('file_type', 'file_size', 'uploaded_at', 'file_preview_large')

    def file_preview(self, obj):
        if obj.file:
            ext = obj.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return format_html(f"<img src='{obj.file.url}' width='50' height='50' style='border-radius:5px; object-fit:cover;' />")
            elif ext in ['mp4', 'webm', 'avi']:
                return format_html("🎥 Video")
            elif ext in ['mp3', 'wav', 'ogg']:
                return format_html("🎵 Audio")
            else:
                return format_html("📄 File")
        return "❌ No file"
    file_preview.short_description = "Preview"

    def file_preview_large(self, obj):
        if obj.file:
            ext = obj.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return format_html(f"<img src='{obj.file.url}' width='300' style='border-radius:8px; border:2px solid #ddd;' />")
            elif ext in ['mp4', 'webm', 'avi']:
                return format_html(f"<video width='300' controls><source src='{obj.file.url}' type='video/{ext}'></video>")
            elif ext in ['mp3', 'wav', 'ogg']:
                return format_html(f"<audio controls><source src='{obj.file.url}' type='audio/{ext}'></audio>")
            else:
                return format_html(f"<a href='{obj.file.url}' target='_blank' class='button'>📥 Download File</a>")
        return "❌ No file"
    file_preview_large.short_description = "Large Preview"

    def file_size_display(self, obj):
        if obj.file_size:
            size_kb = obj.file_size / 1024
            if size_kb < 1024:
                return f"{size_kb:.1f} KB"
            else:
                return f"{size_kb/1024:.1f} MB"
        return "0 KB"
    file_size_display.short_description = "Size"

# ---------------------------
# Chat System Admin
# ---------------------------
class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'message_type', 'created_at', 'text_preview')
    can_delete = False

    def text_preview(self, obj):
        if obj.text:
            return format_html(f"<div style='max-width:200px; overflow:hidden; text-overflow:ellipsis;'>{obj.text[:50]}...</div>")
        return "📎 File attached"
    text_preview.short_description = "Message Text"

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_type_display', 'post', 'contract', 'participants_count', 'messages_count', 'last_activity', 'is_active')
    list_filter = ('room_type', 'is_active', 'created_at')
    search_fields = ('post_title', 'contract_title')
    readonly_fields = ('created_at', 'last_activity', 'participants_list')
    inlines = [ChatMessageInline]
    filter_horizontal = ('participants',)

    def room_type_display(self, obj):
        types = {
            'post_discussion': ('Post Discussion', '💬'),
            'contract_negotiation': ('Contract Negotiation', '🤝'),
            'project_collaboration': ('Project Collaboration', '👥')
        }
        room_type, emoji = types.get(obj.room_type, ('', ''))
        return format_html(f"{emoji} {room_type}")
    room_type_display.short_description = "Room Type"

    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = "Participants Count"

    def messages_count(self, obj):
        return obj.messages.count()
    messages_count.short_description = "Messages Count"

    def participants_list(self, obj):
        participants = obj.participants.all()
        if participants:
            return format_html("<br>".join([f"👤 {user.username}" for user in participants]))
        return "No participants"
    participants_list.short_description = "Participants List"

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'message_type_display', 'status_display', 'created_at', 'has_file')
    list_filter = ('message_type', 'status', 'created_at')
    search_fields = ('text', 'sender_username', 'room_id')
    readonly_fields = ('created_at', 'file_preview', 'text_display')

    def message_type_display(self, obj):
        types = {
            'text': ('Text', '📝'),
            'image': ('Image', '🖼'),
            'file': ('File', '📎'),
            'system': ('System', '⚙')
        }
        message_type, emoji = types.get(obj.message_type, ('', ''))
        return format_html(f"{emoji} {message_type}")
    message_type_display.short_description = "Message Type"

    def status_display(self, obj):
        status_map = {
            'sent': ('Sent', '🟡'),
            'delivered': ('Delivered', '🔵'),
            'read': ('Read', '🟢')
        }
        status, emoji = status_map.get(obj.status, ('', ''))
        return format_html(f"{emoji} {status}")
    status_display.short_description = "Status"

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = "Has File"

    def file_preview(self, obj):
        if obj.file:
            ext = obj.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return format_html(f"<img src='{obj.file.url}' width='200' style='border-radius:8px;' />")
            elif ext in ['mp4', 'webm', 'avi']:
                return format_html(f"<video width='300' controls><source src='{obj.file.url}' type='video/{ext}'></video>")
            else:
                return format_html(f"<a href='{obj.file.url}' target='_blank' class='button'>📥 {obj.file.name}</a>")
        return "❌ No file attached"
    file_preview.short_description = "File Preview"

    def text_display(self, obj):
        if obj.text:
            return format_html(f"<div style='background:#f9f9f9; padding:15px; border-radius:8px; border-right:3px solid #4CAF50; white-space:pre-wrap;'>{obj.text}</div>")
        return "📎 Message with attached file"
    text_display.short_description = "Message Text"

# ---------------------------
# Custom User Admin with Inlines
# ---------------------------
class UserKeysInline(admin.StackedInline):
    model = UserKeys
    can_delete = False
    verbose_name_plural = 'User Keys'
    readonly_fields = ('key_version', 'created_at', 'last_rotated', 'public_key_preview')
    
    def public_key_preview(self, obj):
        if obj.public_key:
            return format_html(f"<code style='font-size:9px;'>{obj.public_key[:30]}...</code>")
        return "❌ No keys"
    public_key_preview.short_description = "Public Key"

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    readonly_fields = ('trust_score_display', 'reputation_level_display', 'verification_level_display')
    
    def trust_score_display(self, obj):
        score = obj.trust_score
        color = "green" if score >= 70 else "orange" if score >= 50 else "red"
        return format_html(f"<span style='color:{color}; font-weight:bold;'>{score}/100</span>")
    trust_score_display.short_description = "Trust Level"
    
    def reputation_level_display(self, obj):
        levels = {
            'newbie': ('Newbie', '🟢'),
            'rising': ('Rising', '🟡'), 
            'pro': ('Professional', '🔵'),
            'expert': ('Expert', '🟣')
        }
        level, emoji = levels.get(obj.reputation_level, ('', ''))
        return format_html(f"{emoji} {level}")
    reputation_level_display.short_description = "Reputation Level"
    
    def verification_level_display(self, obj):
        levels = {
            1: ('Basic', '⚪'),
            2: ('Verified', '🔵'),
            3: ('Professional', '🟢')
        }
        level, emoji = levels.get(obj.verification_level, ('', ''))
        return format_html(f"{emoji} {level}")
    verification_level_display.short_description = "Verification Level"

class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, UserKeysInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_info')
    
    def profile_info(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile:
            return format_html(f"👤 {profile.city or 'Not specified'} | ⭐ {profile.trust_score:.1f}")
        return "❌ No profile"
    profile_info.short_description = "Profile Info"

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
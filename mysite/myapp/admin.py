from django.contrib import admin
from .models import User, Currency, Interaction, FreelanceTask, Vacancy, ChatRoom, Message, Notification, Project

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'role', 'university', 'email', 'date_joined']
    list_filter = ['role', 'university']
    search_fields = ['username', 'email', 'university']

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'rate', 'rate_date']
    list_filter = ['code', 'rate_date']
    search_fields = ['code', 'name']

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'object_id', 'interaction_type', 'created_at']
    list_filter = ['interaction_type', 'content_type', 'created_at']
    search_fields = ['user__username']

@admin.register(FreelanceTask)
class FreelanceTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'executor', 'cost', 'currency', 'deadline']
    list_filter = ['currency', 'deadline']
    search_fields = ['title', 'description']
    raw_id_fields = ['creator', 'executor']

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'hired_candidate', 'salary_from', 'currency', 'expiration', 'is_active', 'created_at']
    list_filter = ['currency', 'is_active', 'expiration', 'created_at']
    search_fields = ['title', 'description']
    raw_id_fields = ['employer', 'hired_candidate']

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'created_by', 'created_at', 'is_active']
    list_filter = ['room_type', 'is_active', 'created_at']
    search_fields = ['name']
    raw_id_fields = ['created_by']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'sender', 'content_preview', 'message_type', 'created_at', 'is_read']
    list_filter = ['message_type', 'is_read']
    search_fields = ['content']
    raw_id_fields = ['room', 'sender', 'reply_to']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Содержание'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message_text']
    raw_id_fields = ['user', 'room', 'message']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'contributors_count', 'id']
    list_filter = ['author']
    search_fields = ['title', 'description']
    raw_id_fields = ['author']
    
    def contributors_count(self, obj):
        return obj.contributors.count()
    contributors_count.short_description = 'Количество участников'

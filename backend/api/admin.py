"""
Django admin configuration for the AI Chatbot MVP.
"""

from django.contrib import admin
from .models import (
    User, ChatSession, ChatMessage,
    KnowledgeDocument, KnowledgeChunk,
    FAQ, NavigationGuide, AIConfig,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("username", "email")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "started_at")
    list_filter = ("started_at",)
    search_fields = ("title",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "created_at")
    list_filter = ("role", "created_at")


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_by", "chunk_count", "created_at")
    search_fields = ("title",)


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "chunk_index")
    list_filter = ("document",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("question", "answer")


@admin.register(NavigationGuide)
class NavigationGuideAdmin(admin.ModelAdmin):
    list_display = ("intent", "question", "created_at")
    search_fields = ("intent", "question")


@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ("provider_name", "model_name", "embedding_model", "is_active")

"""
DRF Serializers for all API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ChatSession, ChatMessage, KnowledgeDocument, KnowledgeChunk,
    FAQ, NavigationGuide, AIConfig,
)

User = get_user_model()


# ──────────────── Auth ────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("username", "email", "password", "role")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            role=validated_data.get("role", "user"),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "created_at")


# ──────────────── Chat ────────────────

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ("id", "title", "started_at")
        read_only_fields = ("id", "started_at")


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "session", "role", "message", "response_time", "created_at")
        read_only_fields = ("id", "created_at")


class ChatMessageCreateSerializer(serializers.Serializer):
    """Serializer for sending a message and getting a streaming response."""
    session_id = serializers.IntegerField(required=False, help_text="Leave empty to start a new session")
    message = serializers.CharField()


# ──────────────── Knowledge Base ────────────────

class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.username", read_only=True, default=None)

    class Meta:
        model = KnowledgeDocument
        fields = ("id", "title", "file", "uploaded_by", "uploaded_by_name", "chunk_count", "created_at")
        read_only_fields = ("id", "uploaded_by", "chunk_count", "created_at")


class KnowledgeChunkSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)

    class Meta:
        model = KnowledgeChunk
        fields = ("id", "document", "document_title", "content", "chunk_index", "metadata")


# ──────────────── FAQ ────────────────

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ("id", "question", "answer", "category", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


# ──────────────── Navigation Guide ────────────────

class NavigationGuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationGuide
        fields = ("id", "intent", "question", "answer", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


# ──────────────── AI Config ────────────────

class AIConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConfig
        fields = ("id", "provider_name", "api_base_url", "model_name", "api_key",
                  "temperature", "max_tokens", "embedding_model", "is_active", "updated_at")
        read_only_fields = ("id", "updated_at")
        extra_kwargs = {
            "api_key": {"write_only": True, "required": False},
        }

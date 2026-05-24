"""
Database models for AI Chatbot MVP.
All tables use PostgreSQL + pgvector for semantic search.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from pgvector.django import VectorField, HnswIndex


class User(AbstractUser):
    """Extended user model with role support (user / admin)."""
    ROLE_CHOICES = (
        ("user", "User"),
        ("admin", "Admin"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def is_admin(self):
        return self.role == "admin"


class ChatSession(models.Model):
    """A conversation session between a user and the chatbot."""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=255, default="New Chat")
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Session {self.id} - {self.user.username}"


class ChatMessage(models.Model):
    """Individual message in a chat session."""
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
    )
    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    message = models.TextField()
    response_time = models.FloatField(null=True, blank=True, help_text="Seconds taken to generate response")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.message[:80]}"


class KnowledgeDocument(models.Model):
    """Uploaded PDF document for the knowledge base."""
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="pdfs/")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    chunk_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class KnowledgeChunk(models.Model):
    """A chunk of text extracted from a PDF, with its vector embedding."""
    id = models.BigAutoField(primary_key=True)
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField()
    embedding = VectorField(dimensions=768, null=True, blank=True)
    chunk_index = models.IntegerField(help_text="Position of this chunk in the original document")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "knowledge_chunks"
        indexes = [
            # HNSW index for fast approximate nearest-neighbor search
            HnswIndex(
                name="knowledge_chunk_emb_idx",
                fields=["embedding"],
                opclasses=["vector_cosine_ops"],
                m=16,
                ef_construction=64
            ),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"


class FAQ(models.Model):
    """Frequently asked question with a direct answer."""
    id = models.BigAutoField(primary_key=True)
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True, default="General")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "faqs"
        ordering = ["category", "id"]

    def __str__(self):
        return f"FAQ: {self.question[:80]}"


class NavigationGuide(models.Model):
    """Navigation help entry mapping intents to app navigation steps."""
    id = models.BigAutoField(primary_key=True)
    intent = models.CharField(max_length=255, help_text="User intent keyword (e.g., create_project)")
    question = models.TextField(help_text="How the user might ask this")
    answer = models.TextField(help_text="Navigation steps to follow")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "navigation_guides"
        ordering = ["intent"]

    def __str__(self):
        return f"Nav: {self.intent}"


class AIConfig(models.Model):
    """AI provider configuration (single active row)."""
    id = models.BigAutoField(primary_key=True)
    provider_name = models.CharField(max_length=100, default="ollama")
    api_base_url = models.URLField(default="http://localhost:11434")
    model_name = models.CharField(max_length=100, default="llama3.2")
    api_key = models.CharField(max_length=500, blank=True, default="", help_text="Optional, not needed for Ollama")
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2048)
    embedding_model = models.CharField(max_length=100, default="nomic-embed-text")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_config"

    def __str__(self):
        return f"{self.provider_name} - {self.model_name}"

    @classmethod
    def get_active(cls):
        """Return the active configuration or create a default one."""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config = cls.objects.create()
        return config

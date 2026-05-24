"""
URL patterns for the API endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # ──────── Auth ────────
    path("auth/register/", views.RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="auth-token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/me/", views.MeView.as_view(), name="auth-me"),

    # ──────── Chat ────────
    path("chat/sessions/", views.ChatSessionListCreateView.as_view(), name="chat-sessions"),
    path("chat/sessions/<int:pk>/", views.ChatSessionDetailView.as_view(), name="chat-session-detail"),
    path("chat/sessions/<int:session_id>/messages/", views.ChatMessageListView.as_view(), name="chat-messages"),
    path("chat/query/", views.ChatQueryView.as_view(), name="chat-query"),

    # ──────── Admin — Knowledge Base ────────
    path("admin/documents/", views.KnowledgeDocumentListView.as_view(), name="admin-documents"),
    path("admin/documents/<int:pk>/", views.KnowledgeDocumentDetailView.as_view(), name="admin-document-detail"),

    # ──────── Admin — FAQs ────────
    path("admin/faqs/", views.FAQListCreateView.as_view(), name="admin-faqs"),
    path("admin/faqs/<int:pk>/", views.FAQDetailView.as_view(), name="admin-faq-detail"),

    # ──────── Admin — Navigation Guides ────────
    path("admin/navigation/", views.NavigationGuideListCreateView.as_view(), name="admin-navigation"),
    path("admin/navigation/<int:pk>/", views.NavigationGuideDetailView.as_view(), name="admin-nav-detail"),

    # ──────── Admin — Chat Logs ────────
    path("admin/chat-logs/", views.ChatLogListView.as_view(), name="admin-chat-logs"),

    # ──────── Admin — AI Config ────────
    path("admin/ai-config/", views.AIConfigView.as_view(), name="admin-ai-config"),
]

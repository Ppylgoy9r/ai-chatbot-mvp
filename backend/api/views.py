"""
API Views — All endpoints for the AI Chatbot MVP.
"""

import json
import logging

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import StreamingHttpResponse
from django.contrib.auth import get_user_model

from .models import (
    ChatSession, ChatMessage, KnowledgeDocument,
    FAQ, NavigationGuide, AIConfig,
)
from .serializers import (
    RegisterSerializer, UserSerializer,
    ChatSessionSerializer, ChatMessageSerializer, ChatMessageCreateSerializer,
    KnowledgeDocumentSerializer,
    FAQSerializer, NavigationGuideSerializer, AIConfigSerializer,
)
from .rag import PDFProcessor, QueryPipeline
from .permissions import IsAdmin

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
#  Auth Endpoints
# ============================================================

class RegisterView(APIView):
    """Register a new user account."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user).data,
            "message": "Registration successful. Please log in.",
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """Get current user profile."""

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ============================================================
#  Chat Endpoints
# ============================================================

class ChatSessionListCreateView(generics.ListCreateAPIView):
    """List user's chat sessions or create a new one."""
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ChatSession.objects.filter(user=self.request.user)
        # Guest users manage session IDs in local storage, so listing is not needed
        return ChatSession.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)


class ChatSessionDetailView(generics.RetrieveDestroyAPIView):
    """Get or delete a specific chat session."""
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ChatSession.objects.filter(user=self.request.user)
        return ChatSession.objects.filter(user__isnull=True)


class ChatMessageListView(generics.ListAPIView):
    """List all messages in a chat session."""
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        session_id = self.kwargs["session_id"]
        if self.request.user.is_authenticated:
            return ChatMessage.objects.filter(
                session_id=session_id,
                session__user=self.request.user,
            )
        return ChatMessage.objects.filter(
            session_id=session_id,
            session__user__isnull=True,
        )


class ChatQueryView(APIView):
    """
    Send a message and receive a streaming AI response (SSE).
    POST /api/chat/query/
    Body: { "session_id": 1, "message": "What is CQRS?" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data["message"]
        session_id = serializer.validated_data.get("session_id")

        # Get or create session
        if session_id:
            if request.user.is_authenticated:
                session = ChatSession.objects.filter(
                    id=session_id, user=request.user
                ).first()
            else:
                session = ChatSession.objects.filter(
                    id=session_id, user__isnull=True
                ).first()
            if not session:
                return Response(
                    {"error": "Session not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Auto-generate title from first message
            title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            if request.user.is_authenticated:
                session = ChatSession.objects.create(
                    user=request.user, title=title
                )
            else:
                session = ChatSession.objects.create(
                    user=None, title=title
                )

        # Save user message
        ChatMessage.objects.create(
            session=session, role="user", message=user_message
        )

        # Build chat history from previous messages
        previous = ChatMessage.objects.filter(session=session).order_by("created_at")
        chat_history = [
            {"role": msg.role, "content": msg.message}
            for msg in previous
        ]

        # Stream response
        pipeline = QueryPipeline()

        def event_stream():
            full_response = []
            response_time = None

            try:
                for chunk in pipeline.query_stream(user_message, chat_history, session_id=session.id):
                    yield chunk
                    # Parse tokens for saving
                    try:
                        if chunk.startswith("data: "):
                            data = json.loads(chunk[6:].strip())
                            if "token" in data:
                                full_response.append(data["token"])
                            if data.get("done"):
                                response_time = data.get("response_time")
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                # Send error as SSE event so frontend can display it
                error_msg = f"Error generating response: {str(e)}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                full_response.append(error_msg)

            # Save assistant message (even partial responses on error)
            assistant_text = "".join(full_response)
            if assistant_text.strip():
                ChatMessage.objects.create(
                    session=session,
                    role="assistant",
                    message=assistant_text,
                    response_time=response_time,
                )

        response = StreamingHttpResponse(
            event_stream(), content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response



# ============================================================
#  Admin — Knowledge Base (PDF) Endpoints
# ============================================================

class KnowledgeDocumentListView(APIView):
    """List all uploaded PDFs or upload a new one."""
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        docs = KnowledgeDocument.objects.all()
        serializer = KnowledgeDocumentSerializer(docs, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Upload a PDF and process it (extract, chunk, embed, store)."""
        file = request.FILES.get("file")
        title = request.data.get("title", file.name if file else "Untitled")

        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.lower().endswith(".pdf"):
            return Response({"error": "Only PDF files are supported"}, status=status.HTTP_400_BAD_REQUEST)

        # Save file to disk
        doc = KnowledgeDocument.objects.create(
            title=title,
            file=file,
            uploaded_by=request.user,
            chunk_count=0,
        )

        # Process PDF in the background (for MVP, synchronous)
        try:
            processor = PDFProcessor()
            processor.process_pdf(doc.file.path, title, request.user)
            # Delete the placeholder and refresh
            doc.delete()
            doc = KnowledgeDocument.objects.filter(title=title).first()
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            doc.delete()
            return Response(
                {"error": f"PDF processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            KnowledgeDocumentSerializer(doc).data,
            status=status.HTTP_201_CREATED,
        )


class KnowledgeDocumentDetailView(APIView):
    """Get or delete a specific PDF document and its chunks."""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        doc = generics.get_object_or_404(KnowledgeDocument, pk=pk)
        serializer = KnowledgeDocumentSerializer(doc)
        return Response(serializer.data)

    def delete(self, request, pk):
        doc = generics.get_object_or_404(KnowledgeDocument, pk=pk)
        doc.file.delete(save=False)  # Delete file from disk
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
#  Admin — FAQ Endpoints
# ============================================================

class FAQListCreateView(generics.ListCreateAPIView):
    """List all FAQs or create a new one."""
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [permissions.AllowAny()]


class FAQDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a FAQ."""
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [IsAdmin]


# ============================================================
#  Admin — Navigation Guide Endpoints
# ============================================================

class NavigationGuideListCreateView(generics.ListCreateAPIView):
    """List all navigation guides or create a new one."""
    queryset = NavigationGuide.objects.all()
    serializer_class = NavigationGuideSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [permissions.AllowAny()]


class NavigationGuideDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a navigation guide."""
    queryset = NavigationGuide.objects.all()
    serializer_class = NavigationGuideSerializer
    permission_classes = [IsAdmin]


# ============================================================
#  Admin — Chat Logs
# ============================================================

class ChatLogListView(APIView):
    """View all chat sessions and messages (admin only)."""
    permission_classes = [IsAdmin]

    def get(self, request):
        sessions = ChatSession.objects.select_related("user").all()
        data = []
        for session in sessions:
            messages = ChatMessage.objects.filter(session=session).order_by("created_at")
            data.append({
                "session": ChatSessionSerializer(session).data,
                "user": session.user.username,
                "messages": ChatMessageSerializer(messages, many=True).data,
            })
        return Response(data)


# ============================================================
#  Admin — AI Config
# ============================================================

class AIConfigView(APIView):
    """Get or update AI provider configuration (admin only)."""
    permission_classes = [IsAdmin]

    def get(self, request):
        config = AIConfig.get_active()
        serializer = AIConfigSerializer(config)
        return Response(serializer.data)

    def put(self, request):
        config = AIConfig.get_active()
        serializer = AIConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

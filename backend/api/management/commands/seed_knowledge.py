"""
Management command to seed sample FAQs and navigation guides.
Usage: python manage.py seed_knowledge
"""

from django.core.management.base import BaseCommand
from api.models import FAQ, NavigationGuide


class Command(BaseCommand):
    help = "Seed the database with sample FAQs and navigation guides"

    def handle(self, *args, **options):
        # ─── FAQs ───
        faqs = [
            {
                "question": "How do I reset my password?",
                "answer": "Go to Settings > Security > Reset Password. Enter your email and follow the verification link sent to your inbox.",
                "category": "Account",
            },
            {
                "question": "What is CQRS?",
                "answer": "CQRS stands for Command Query Responsibility Segregation. It separates read and write operations into different models, improving scalability and performance in complex domains.",
                "category": "System Design",
            },
            {
                "question": "What is event sourcing?",
                "answer": "Event sourcing is a pattern where state changes are stored as a sequence of immutable events rather than overwriting the current state. The current state is derived by replaying these events.",
                "category": "System Design",
            },
            {
                "question": "How does the chatbot work?",
                "answer": "The chatbot uses RAG (Retrieval-Augmented Generation). It first searches FAQs and navigation guides for direct answers, then falls back to semantic search on uploaded PDF documents. The most relevant context is sent to an AI model to generate a response.",
                "category": "General",
            },
            {
                "question": "Is my data secure?",
                "answer": "Yes. All AI processing happens on-premises using Ollama. No data is sent to external APIs. PDF documents and chat history are stored in your local PostgreSQL database.",
                "category": "Security",
            },
        ]

        for faq_data in faqs:
            obj, created = FAQ.objects.get_or_create(
                question=faq_data["question"],
                defaults=faq_data,
            )
            if created:
                self.stdout.write(f"  Created FAQ: {faq_data['question'][:60]}")

        # ─── Navigation Guides ───
        guides = [
            {
                "intent": "create_project",
                "question": "How do I create a new project?",
                "answer": "Go to Dashboard > Projects > click 'New Project' button > fill in project details > click 'Create'.",
            },
            {
                "intent": "upload_pdf",
                "question": "How do I upload a PDF document?",
                "answer": "Go to Admin Dashboard > Knowledge Base > click 'Upload PDF' > select your file > add a title > click 'Upload & Process'.",
            },
            {
                "intent": "view_chat_logs",
                "question": "Where can I see chat logs?",
                "answer": "Go to Admin Dashboard > Chat Logs tab. You will see all conversations with timestamps.",
            },
            {
                "intent": "configure_ai",
                "question": "How do I change the AI model?",
                "answer": "Go to Admin Dashboard > AI Config tab. Update the model name, temperature, or other settings. Make sure the model is available in your Ollama instance.",
            },
            {
                "intent": "manage_faqs",
                "question": "How do I add or edit FAQs?",
                "answer": "Go to Admin Dashboard > FAQs tab. Click 'Add FAQ' to create new, or click the edit icon next to an existing FAQ to modify it.",
            },
        ]

        for guide_data in guides:
            obj, created = NavigationGuide.objects.get_or_create(
                intent=guide_data["intent"],
                defaults=guide_data,
            )
            if created:
                self.stdout.write(f"  Created Nav Guide: {guide_data['intent']}")

        self.stdout.write(self.style.SUCCESS("Knowledge seeding complete!"))

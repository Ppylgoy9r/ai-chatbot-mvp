"""
Management command to ingest a PDF into the knowledge base.
Usage: python manage.py ingest_pdf <path_to_pdf> [--title "Custom Title"]
"""

import os
from django.core.management.base import BaseCommand, CommandError
from api.rag import PDFProcessor


class Command(BaseCommand):
    help = "Ingest a PDF file into the knowledge base (extract, chunk, embed, store)"

    def add_arguments(self, parser):
        parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
        parser.add_argument(
            "--title", type=str, default=None,
            help="Title for the document (defaults to filename)",
        )

    def handle(self, *args, **options):
        pdf_path = options["pdf_path"]

        if not os.path.isfile(pdf_path):
            raise CommandError(f"File not found: {pdf_path}")

        if not pdf_path.lower().endswith(".pdf"):
            raise CommandError("Only PDF files are supported")

        title = options["title"] or os.path.basename(pdf_path)

        self.stdout.write(f"Processing: {pdf_path}")
        self.stdout.write(f"Title: {title}")

        processor = PDFProcessor()
        try:
            doc = processor.process_pdf(pdf_path, title)
            self.stdout.write(self.style.SUCCESS(
                f"Successfully ingested '{title}' with {doc.chunk_count} chunks"
            ))
        except Exception as e:
            raise CommandError(f"Processing failed: {e}")

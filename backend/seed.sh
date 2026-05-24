#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  Seed Script — Initialize the database with sample data
#  and ingest the System Design PDF.
#
#  Usage:  ./seed.sh
#  Run this AFTER migrations and with Ollama running.
# ═══════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════"
echo "  AI Chatbot MVP — Database Seeding"
echo "═══════════════════════════════════════════"

cd "$(dirname "$0")"

# 1. Create admin user
echo ""
echo "📌 Creating admin user..."
python manage.py create_admin --username admin --password admin123 --email admin@example.com 2>/dev/null || echo "   Admin user already exists, skipping."

# 2. Create a regular test user
echo "📌 Creating test user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='user').exists():
    User.objects.create_user(username='user', password='user123', email='user@test.com', role='user')
    print('   Test user created: user / user123')
else:
    print('   Test user already exists, skipping.')
"

# 3. Seed FAQs and navigation guides
echo "📌 Seeding FAQs and navigation guides..."
python manage.py seed_knowledge

# 4. Ingest the seed PDF
SEED_PDF="seed_data/System_Design_Zero_to_Hero.pdf"
if [ -f "$SEED_PDF" ]; then
    echo "📌 Ingesting System Design PDF (this may take a few minutes)..."
    python manage.py ingest_pdf "$SEED_PDF" --title "System Design - Zero to Hero"
else
    echo "⚠️  Seed PDF not found at $SEED_PDF"
    echo "   You can manually ingest PDFs later using:"
    echo "   python manage.py ingest_pdf <path_to_pdf> --title \"Document Title\""
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ Seeding complete!"
echo ""
echo "  Login credentials:"
echo "    Admin:  admin / admin123"
echo "    User:   user  / user123"
echo "═══════════════════════════════════════════"

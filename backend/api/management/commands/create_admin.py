"""
Management command to create a superuser / admin account.
Usage: python manage.py create_admin --username admin --password admin123 --email admin@example.com
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create an admin user for the chatbot system"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, required=True)
        parser.add_argument("--password", type=str, required=True)
        parser.add_argument("--email", type=str, default="admin@example.com")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]

        if User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists")

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role="admin",
        )
        self.stdout.write(self.style.SUCCESS(
            f"Admin user '{username}' created successfully"
        ))

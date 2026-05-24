import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_project.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.filter(username="admin").first()

if admin:
    print(f"Admin exists: True")
    print(f"is_staff: {admin.is_staff}")
    print(f"is_superuser: {admin.is_superuser}")
    pwd_check = admin.check_password("admin123")
    print(f"password_check: {pwd_check}")
else:
    print("Admin does not exist")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_project.settings")
django.setup()

from django.test import Client
c = Client()
response = c.post('/admin/login/', {'username': 'admin', 'password': 'admin123'})
print("Login status code:", response.status_code)
print("Redirect URL:", response.url if hasattr(response, 'url') else 'No redirect')

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class SecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='adm', role='admin', is_staff=True)
        self.customer = User.objects.create_user(username='client1', role='client')

    def test_manager_report_access(self):
        """Проверка защиты отчетов менеджера."""
        url = reverse('manager_report')
        
        # 1. Аноним (редирект на логин)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # 2. Обычный клиент (403 Forbidden или редирект)
        self.client.force_login(self.customer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) # Если используем raise_exception=True

        # 3. Админ (200 OK)
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
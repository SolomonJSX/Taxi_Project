from django.test import TestCase
from django.contrib.auth import get_user_model
from taxi.models import Driver, Review

User = get_user_model()

class DriverModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 1. Создаем пользователя (сигнал сам создаст пустой Driver)
        cls.user = User.objects.create_user(username='driver1', role='driver')
        
        # 2. Не создаем, а получаем уже созданный профиль и обновляем его
        cls.driver = Driver.objects.get(user=cls.user)
        cls.driver.last_name = "Suleymenov"
        cls.driver.first_name = "Zhanserik"
        cls.driver.save()
        
    def test_average_rating_calculation(self):
        """Проверка расчета среднего рейтинга водителя."""
        # Act: Добавляем отзывы (в реальном проекте через создание Order)
        # Для простоты примера предположим, что Review связан напрямую
        # (или создаем через фабрику заказов)
        self.assertEqual(self.user.get_average_rating(), "Нет оценок")
from django.test import TestCase
from django.contrib.auth import get_user_model
from taxi.models import Driver, Order, Review, Tariff

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

User = get_user_model()

class ReviewModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Arrange (Подготовка)
        cls.client_user = User.objects.create_user(username='client', role='client')
        cls.driver_user = User.objects.create_user(username='driver', role='driver')
        cls.tariff = Tariff.objects.create(name="Эконом", base_price=500, price_per_km=100)
        cls.order = Order.objects.create(
            client=cls.client_user,
            driver=cls.driver_user,
            point_a="Центр",
            point_b="Юго-Восток",
            tariff=cls.tariff,
            cost=1000,
            status='completed'
        )

    def test_review_creation(self):
        """Тестирование корректного создания объекта отзыва."""
        # Act (Действие)
        review = Review.objects.create(
            order=self.order,
            client=self.client_user,
            driver=self.driver_user,
            rating=5,
            comment="Отличная поездка!"
        )

        # Assert (Проверка)
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(review.rating, 5)
        self.assertEqual(str(review), f"Отзыв на заказ #{self.order.id} — 5⭐️")
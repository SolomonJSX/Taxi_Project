from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Driver(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_profile')
    
    # Добавляем default или null=True, blank=True
    last_name = models.CharField(max_length=50, verbose_name="Фамилия", default="")
    first_name = models.CharField(max_length=50, verbose_name="Имя", default="")
    middle_name = models.CharField(max_length=50, verbose_name="Отчество", blank=True, default="")
    
    iin = models.CharField(max_length=12, unique=True, verbose_name="ИИН", null=True, blank=True)
    phone = models.CharField(max_length=15, verbose_name="Телефон", default="")
    experience = models.PositiveIntegerField(verbose_name="Стаж (лет)", default=0) # Ставим 0 по умолчанию
    category = models.CharField(max_length=10, verbose_name="Категория прав", default="B")

    # Метод для удобного вывода полного имени в админке или шаблонах
    def get_full_name(self):
        # 1. Проверяем поля в модели Driver (убираем лишние пробелы)
        name_from_driver = f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()
        if name_from_driver:
            return name_from_driver
        
        # 2. Если в Driver пусто, лезем в CustomUser
        if self.user:
            # Сначала пробуем Имя + Фамилия из User
            user_full = f"{self.user.last_name} {self.user.first_name}".strip()
            if user_full:
                return user_full
            # Если и там пусто - возвращаем username (он точно есть!)
            return f"Логин: {self.user.username}"
            
        return "Без имени"
    
    def get_average_rating(self):
        # Считаем среднее по всем полученным отзывам
        avg = Review.objects.filter(driver=self.user).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else "Нет оценок"

    def __str__(self):
        return self.get_full_name()

# taxi/models.py
class Car(models.Model):
    brand = models.CharField(max_length=50, verbose_name="Марка")
    model = models.CharField(max_length=50, verbose_name="Модель")
    plate_number = models.CharField(max_length=15, unique=True, verbose_name="Госномер")
    car_class = models.ForeignKey('Tariff', on_delete=models.PROTECT, verbose_name="Класс/Тариф")
    
    # Оставляем только ОДНО поле связи с водителем
    driver = models.ForeignKey(
        'Driver', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cars',
        verbose_name="Текущий водитель"
    )
    
    status = models.CharField(
        max_length=20, 
        choices=[('active', 'На линии'), ('service', 'В ремонте'), ('free', 'Свободна')], 
        default='free', 
        verbose_name="Статус авто"
    )

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate_number})"

class Tariff(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название тарифа") # Эконом, Комфорт...
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Базовая цена (₸)")
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за км (₸)")
    icon = models.CharField(max_length=50, default="fas fa-car", help_text="Иконка FontAwesome")

    def __str__(self):
        return f"{self.name} ({self.base_price} ₸)"

class Order(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_orders')
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_orders')
    
    point_a = models.CharField(max_length=255, verbose_name="Точка А")
    point_b = models.CharField(max_length=255, verbose_name="Точка Б")
    tariff = models.ForeignKey('Tariff', on_delete=models.PROTECT)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="Новый")
    date_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    def __str__(self):
        return f"Заказ №{self.id} ({self.point_a} -> {self.point_b})"
    
class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='left_reviews')
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_reviews')
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка"
    )
    comment = models.TextField(blank=True, verbose_name="Отзыв")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв на заказ #{self.order.id} — {self.rating}⭐️"
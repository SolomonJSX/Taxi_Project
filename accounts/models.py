from django.contrib.auth.models import AbstractUser
from django.db import models  # Исправленный импорт
from taxi.models import Driver
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Avg

class CustomUser(AbstractUser):
    """Расширенная модель пользователя для Таксопарка."""
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('driver', 'Водитель'),
        ('client', 'Клиент'),
    ]
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='client', 
        verbose_name='Роль'
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name='Телефон'
    )
    balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Баланс (₸)"
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        # Кастомные разрешения для Лабораторной №4
        permissions = [
            ('can_edit_tariffs', 'Может редактировать тарифы'),
            ('can_view_driver_stats', 'Может просматривать статистику'),
        ]

    def __str__(self):
        return f"{self.username} | {self.get_role_display()} | {self.balance} ₸"
    
    def get_average_rating(self):
        # Импортируем внутри метода, чтобы избежать кругового импорта
        from taxi.models import Review
        avg = Review.objects.filter(driver=self).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else "Нет оценок"
    
@receiver(post_save, sender=CustomUser)
def create_driver_profile(sender, instance, created, **kwargs):
    # Если создан НОВЫЙ пользователь и его роль - водитель
    if created and instance.role == 'driver':
        Driver.objects.get_or_create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_driver_profile(sender, instance, **kwargs):
    if instance.role == 'driver':
        # Проверяем наличие профиля перед сохранением
        if hasattr(instance, 'driver_profile'):
            instance.driver_profile.save()
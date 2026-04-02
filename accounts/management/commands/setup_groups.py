from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
# ... остальной код из методички ...

class Command(BaseCommand):  # Название должно быть в точности такое
    help = 'Создание групп пользователей'

    def handle(self, *args, **options):
        # Твоя логика здесь
        self.stdout.write(self.style.SUCCESS('Группы созданы!'))
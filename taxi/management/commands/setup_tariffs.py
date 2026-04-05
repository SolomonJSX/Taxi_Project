# taxi/management/commands/setup_tariffs.py
from django.core.management.base import BaseCommand
from taxi.models import Tariff

class Command(BaseCommand):
    help = 'Создает стандартные тарифы для таксопарка'

    def handle(self, *args, **options):
        tariffs = [
            {
                'name': 'Эконом',
                'base_price': 500.00,
                'price_per_km': 100.00,
                'icon': 'fas fa-car'
            },
            {
                'name': 'Комфорт',
                'base_price': 800.00,
                'price_per_km': 150.00,
                'icon': 'fas fa-couch'
            },
            {
                'name': 'Бизнес',
                'base_price': 1500.00,
                'price_per_km': 300.00,
                'icon': 'fas fa-briefcase'
            },
        ]

        for t_data in tariffs:
            obj, created = Tariff.objects.get_or_create(
                name=t_data['name'],
                defaults=t_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Тариф "{t_data["name"]}" создан'))
            else:
                self.stdout.write(self.style.WARNING(f'Тариф "{t_data["name"]}" уже существует'))
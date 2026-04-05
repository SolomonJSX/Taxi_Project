from decimal import Decimal
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from .forms import DriverForm, OrderForm, ReviewForm
from .models import Driver, Review
from django.db.models.functions import Greatest
from django.contrib.postgres.search import TrigramSimilarity
from .models import Car, Order
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

# Create your views here.
@login_required
def index(request):
    user = request.user
    
    # 1. Логика для Менеджера
    if user.role == 'admin' or user.is_staff:
        total_revenue = Order.objects.filter(status='completed').aggregate(Sum('cost'))['cost__sum'] or 0
        
        context = {
            'total_drivers': Driver.objects.count(),
            'active_orders_count': Order.objects.filter(status='in_progress').count(),
            'new_orders_count': Order.objects.filter(status='new').count(),
            'total_cars': Car.objects.count(),
            'free_cars': Car.objects.filter(status='free').count(),
            'total_revenue': total_revenue,
            'recent_orders': Order.objects.all().order_by('-date_time')[:5], # Последние 5 событий
        }
        return render(request, 'taxi/roles/manager_dash.html', context)
    
    # 2. Логика для Водителя
    elif user.role == 'driver':
        # Вместо истории, на главной водителю лучше видеть статистику
        context = {
            'my_orders_count': Order.objects.filter(driver=user, status='completed').count(),
            'current_balance': user.balance,
        }
        return render(request, 'taxi/roles/driver_dash.html', context)
    
    # 3. Логика для Клиента (ПРОКАЧАННАЯ)
    else:
        context = {
            # Ищем заказ, который еще не завершен (новый или в процессе)
            'active_order': Order.objects.filter(client=user).exclude(status='completed').first(),
            # Последние 3 поездки
            'recent_trips': Order.objects.filter(client=user, status='completed').order_by('-date_time')[:3],
        }
        return render(request, 'taxi/roles/client_dash.html', context)
    
@login_required
@permission_required('taxi.add_driver', raise_exception=True)
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save() # Сохраняем водителя в базу данных
            return redirect('driver_list') # Перенаправляем на список водителей
    else:
        form = DriverForm()

    return render(request, 'taxi/add_driver.html', {'form': form})

@login_required
def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, 'taxi/driver_list.html', {'drivers': drivers})

@login_required
def create_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.client = request.user
            
            # Получаем базовые данные из формы
            selected_tariff = form.cleaned_data['tariff']
            # Допустим, расстояние мы пока берем фиксированное (например, 5 км) 
            # или добавим поле 'distance' в форму
            dist = Decimal('5.0') 
            
            # Базовая формула:
            # $$Cost = BasePrice + (PricePerKm \times Distance)$$
            base_cost = selected_tariff.base_price + (selected_tariff.price_per_km * dist)
            
            # Применяем наш умный множитель
            multiplier = get_surge_multiplier()
            order.cost = base_cost * multiplier
            
            order.status = 'new'
            order.save()
            
            messages.success(request, f'Заказ создан! Итоговая цена: {order.cost} ₸ (с учетом тарифа)')

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "drivers", # Имя группы, которую мы создали в Consumer
                {
                    "type": "new_order_notification",
                    "order": {
                        "id": order.id,
                        "point_a": order.point_a,
                        "point_b": order.point_b,
                        "cost": str(order.cost),
                        "tariff": order.tariff.name,
                    }
                }
            )
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm()
    
    return render(request, 'taxi/create_order.html', {'form': form})

def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Защита: только клиент этого заказа или админ/водитель могут его видеть
    if request.user != order.client and request.user.role != 'admin' and request.user != order.driver:
        raise PermissionDenied

    return render(request, 'taxi/order_detail.html', {'order': order})

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.role == 'admin')

# READ (List)
@login_required
@user_passes_test(is_admin)
def driver_list(request):
    drivers = Driver.objects.all().select_related('user') # Подгружаем юзеров сразу
    print(f"Найдено водителей: {drivers.count()}") # Посмотри в консоль терминала!
    return render(request, 'taxi/driver_list.html', {'drivers': drivers})

# UPDATE
def driver_update(request, pk):
    # В URL мы передаем ID пользователя (CustomUser)
    user = get_object_or_404(CustomUser, pk=pk)
    
    # При создании профиля Driver сразу копируем имя и фамилию из User в defaults
    driver, created = Driver.objects.get_or_create(
        user=user,
        defaults={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'experience': 0,
            'category': 'B'
        }
    )
    
    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            return redirect('driver_list')
    else:
        form = DriverForm(instance=driver)
    
    return render(request, 'taxi/add_driver.html', {'form': form, 'edit': True})

# DELETE
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        driver.delete()
        return redirect('driver_list')
    return render(request, 'taxi/driver_confirm_delete.html', {'driver': driver})

def driver_search(request):
    query = request.GET.get('q')
    results = []

    if query:
        # Интеллектуальный поиск по 4 полям сразу
        results = Driver.objects.annotate(
            similarity=Greatest(
                TrigramSimilarity('last_name', query),
                TrigramSimilarity('first_name', query),
                TrigramSimilarity('middle_name', query),
                TrigramSimilarity('iin', query),
            )
        ).filter(similarity__gt=0.1).order_by('-similarity')

    return render(request, 'taxi/driver_list.html', {
        'drivers': results,
        'query': query,
        'search_mode': True
    })

@user_passes_test(is_admin)
def car_list(request):
    cars = Car.objects.all().select_related('car_class', 'driver') # select_related ускорит загрузку
    return render(request, 'taxi/car_list.html', {'cars': cars})

def is_driver(user):
    return user.is_authenticated and user.role == 'driver'

@login_required
def driver_dashboard(request):
    # 1. Берем профиль водителя
    driver_profile = getattr(request.user, 'driver_profile', None)
    
    # 2. Ищем машину, где в поле driver указан наш текущий профиль
    assigned_car = Car.objects.filter(driver=driver_profile).first()
    
    # 3. Достаем доступные заказы (теперь только того тарифа, который у машины!)
    if assigned_car:
        # Важно: сравниваем тариф заказа с тарифом (классом) машины
        available_orders = Order.objects.filter(
            status='new', 
            tariff=assigned_car.car_class
        ).order_by('-date_time')
    else:
        available_orders = []

    # Достаем последние 5 отзывов именно для этого водителя
    reviews = Review.objects.filter(driver=request.user).order_by('-created_at')[:5]
    
    # Считаем средний рейтинг (если метод уже в модели, можно просто передать его)
    avg_rating = request.user.get_average_rating() if hasattr(request.user, 'get_average_rating') else 0

    context = {
        'assigned_car': assigned_car,
        'available_orders': Order.objects.filter(status='new').order_by('-date_time'), # или фильтр по тарифу
        'current_order': Order.objects.filter(driver=request.user, status='in_progress').first(),
        'reviews': reviews,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'taxi/roles/driver_dash.html', context)

@login_required
@user_passes_test(is_driver)
def accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='new')
    
    # Проверяем, нет ли у водителя уже активного заказа
    active_exists = Order.objects.filter(driver=request.user, status='in_progress').exists()
    if active_exists:
        messages.error(request, 'Сначала завершите текущий заказ!')
        return redirect('driver_dashboard')

    # Закрепляем заказ за водителем
    order.driver = request.user
    order.status = 'in_progress'
    order.save()
    
    messages.success(request, f'Вы приняли заказ #{order.id}. Удачной поездки!')
    return redirect('driver_dashboard')

@login_required
@user_passes_test(is_driver)
def complete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, driver=request.user, status='in_progress')
    order.status = 'completed'
    order.save()
    messages.success(request, f'Поездка #{order.id} успешно завершена!')
    return redirect('driver_dashboard')

@login_required
def order_history(request):
    user = request.user
    # Получаем даты из GET-запроса
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Начальный кверисет: только завершенные заказы пользователя
    if user.role == 'driver':
        orders = Order.objects.filter(driver=user, status='completed')
    else:
        orders = Order.objects.filter(client=user, status='completed')

    # Применяем фильтры по датам, если они указаны
    if date_from:
        orders = orders.filter(date_time__date__gte=parse_date(date_from))
    if date_to:
        orders = orders.filter(date_time__date__lte=parse_date(date_to))

    orders = orders.order_by('-date_time')

    # Для водителя считаем общую выручку за период
    total_earned = orders.aggregate(Sum('cost'))['cost__sum'] if user.role == 'driver' else None

    return render(request, 'taxi/order_history.html', {
        'orders': orders,
        'date_from': date_from,
        'date_to': date_to,
        'total_earned': total_earned
    })

@login_required
@user_passes_test(is_driver)
def complete_order(request, order_id):
    # Находим заказ, который выполняет именно этот водитель
    order = get_object_or_404(Order, id=order_id, driver=request.user, status='in_progress')
    
    with transaction.atomic():
        # 1. Меняем статус заказа
        order.status = 'completed'
        order.save()
        
        # 2. Начисляем деньги на баланс водителя
        driver = request.user
        driver.balance += order.cost
        driver.save()
        
    messages.success(request, f'Заказ #{order.id} завершен. На ваш баланс зачислено {order.cost} ₸')
    return redirect('driver_dashboard')

def get_surge_multiplier():
    """Функция для определения коэффициента цены."""
    multiplier = Decimal('1.0')
    now = timezone.now() # Учитывает время сервера

    # 1. НОЧНОЙ ТАРИФ (с 23:00 до 06:00)
    # Сейчас 23:56, так что это условие сработает!
    if now.hour >= 23 or now.hour < 6:
        multiplier += Decimal('0.5') # +50% к стоимости
        surge_reason = "Ночной тариф"
    
    # 2. ЧАС ПИК (например, если в системе более 3 новых заказов)
    active_orders = Order.objects.filter(status='new').count()
    if active_orders > 3:
        multiplier += Decimal('0.3') # Еще +30% за высокий спрос
        surge_reason = "Высокий спрос"
    
    return multiplier

@login_required
def cancel_order(request, pk):
    # Ищем заказ. Если его нет или он не принадлежит юзеру — 404
    order = get_object_or_404(Order, pk=pk, client=request.user)
    
    if order.status == 'new':
        order.status = 'cancelled' # Или order.delete(), если хочешь удалять совсем
        order.save()
        messages.success(request, "Заказ успешно отменен")
    else:
        messages.error(request, "Нельзя отменить заказ, который уже принят водителем")
        
    return redirect('index')

@login_required
@user_passes_test(is_admin)
def manager_report(request):
    # 1. Считаем заказы по дням за последнюю неделю
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = (
        Order.objects.filter(date_time__date__gte=week_ago)
        .annotate(date=TruncDate('date_time'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Готовим данные для JavaScript (списки меток и значений)
    chart_labels = [s['date'].strftime("%d.%m") for s in stats]
    chart_data = [s['count'] for s in stats]

    # 2. Общие показатели для карточек
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('cost'))['cost__sum'] or 0
    total_commission = total_revenue * Decimal('0.10') # Допустим, комиссия парка 10%

    context = {
        'labels': chart_labels,
        'data': chart_data,
        'total_revenue': total_revenue,
        'total_commission': total_commission,
        'active_drivers': CustomUser.objects.filter(role='driver', is_active=True).count()
    }
    
    return render(request, 'taxi/roles/manager_report.html', context)

@login_required
def add_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user, status='completed')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.client = request.user
            review.driver = order.driver
            review.save()
            messages.success(request, "Спасибо за ваш отзыв!")
            return redirect('order_detail', pk=order.id)
    return redirect('order_detail', pk=order.id)
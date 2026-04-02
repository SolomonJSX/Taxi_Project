from django.contrib import admin
from django.urls import path
from accounts import views as acc_views
from django.conf.urls.static import static
from taxi import views
from taxi.views import index
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('drivers/', views.driver_list, name='driver_list'),
    path('order/new/', views.create_order, name='create_order'),
    path('driver/add/', views.add_driver, name='add_driver'),

    # ДОБАВЬ ЭТИ ДВЕ СТРОКИ:
    path('driver/edit/<int:pk>/', views.driver_update, name='driver_update'),
    path('driver/delete/<int:pk>/', views.driver_delete, name='driver_delete'),

    path('cars/', views.car_list, name='car_list'),
    path('drivers/search/', views.driver_search, name='driver_search'),

    path('register/', acc_views.register_view, name='register'),
    path('login/', acc_views.login_view, name='login'),
    path('logout/', acc_views.logout_view, name='logout'),
    path('profile/', acc_views.profile_view, name='profile'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/accept/<int:order_id>/', views.accept_order, name='accept_order'),
    path('order/complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('history/', views.order_history, name='order_history'),
    path('manager/report/', views.manager_report, name='manager_report'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/cancel/<int:pk>/', views.cancel_order, name='cancel_order'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

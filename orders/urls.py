from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.orders, name='orders'),
    path('orders/<str:pk>/detail', views.order_detail, name='order_detail'),
    path('orders/order_new', views.order_new, name='order_new'),
    path('orders/<str:pk>/profile', views.profile, name='profile'),
    path('orders/<str:pk>/edit', views.order_edit, name='order_edit'),
    path('orders/<str:pk>/delete', views.order_delete, name='order_delete'),
    path('orders/info', views.info, name='info'),
]
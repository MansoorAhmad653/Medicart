from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/track/', views.track_order, name='track_order'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
]

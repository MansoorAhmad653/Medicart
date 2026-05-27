from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('upload/', views.upload_prescription, name='upload'),
]

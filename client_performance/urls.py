from django.urls import path
from . import views

urlpatterns = [
    path('', views.performance_view, name='performance_view'),
]

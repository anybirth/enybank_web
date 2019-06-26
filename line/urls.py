from django.urls import path
from . import views

app_name = 'line'
urlpatterns = [
    path('webhook/', views.callback, name='callback'),
]

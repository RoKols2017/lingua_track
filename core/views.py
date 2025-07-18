"""
Views приложения core.
Главная страница (index).
"""
from django.shortcuts import render

# Create your views here.


def index(request):
    """
    Рендерит главную страницу приложения.
    """
    return render(request, 'index.html')

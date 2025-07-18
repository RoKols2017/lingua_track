"""
Views приложения users: регистрация, вход, выход, профиль, генерация magic-ссылки для Telegram.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views import View
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import User
import secrets
from django.urls import reverse
from django.http import HttpResponseRedirect
import base64
try:
    import qrcode
    from io import BytesIO
except ImportError:
    qrcode = None
from cards.models import Card, Schedule
from django.db import models

# Create your views here.

class RegisterView(View):
    """
    Регистрация нового пользователя.
    GET — форма, POST — обработка и создание пользователя.
    """
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'users/register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        return render(request, 'users/register.html', {'form': form})

class LoginView(View):
    """
    Вход пользователя.
    GET — форма, POST — обработка и аутентификация.
    """
    def get(self, request):
        form = CustomAuthenticationForm()
        return render(request, 'users/login.html', {'form': form})

    def post(self, request):
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
        return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """
    Выход пользователя (logout).
    """
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    """
    Профиль пользователя (только для авторизованных).
    Показывает статус привязки Telegram, magic-ссылку, токен, QR-код и инструкцию.
    """
    user = request.user
    telegram_link = None
    telegram_qr = None
    telegram_token = None
    status = None
    if user.telegram_id:
        status = 'ok'
    elif user.telegram_link_token:
        telegram_token = user.telegram_link_token
        telegram_link = f'https://t.me/LinguaTrackbot?start={telegram_token}'
        if qrcode:
            qr = qrcode.make(telegram_link)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            telegram_qr = base64.b64encode(buffer.getvalue()).decode('utf-8')
        status = 'pending'
    else:
        status = 'none'
    return render(request, 'users/profile.html', {
        'user': user,
        'telegram_link': telegram_link,
        'telegram_qr': telegram_qr,
        'telegram_token': telegram_token,
        'status': status,
    })

def generate_telegram_link(request):
    """
    Генерация magic-ссылки и QR-кода для привязки Telegram.
    POST — генерирует токен, magic-ссылку и QR, возвращает в профиль.
    """
    if request.method == 'POST':
        user = request.user
        # Генерируем уникальный токен
        token = secrets.token_urlsafe(32)
        user.telegram_link_token = token
        user.save()
        # Формируем magic-ссылку (замените YOUR_BOT_USERNAME на реальное имя бота)
        telegram_link = f'https://t.me/LinguaTrackbot?start={token}'
        telegram_qr = None
        if qrcode:
            qr = qrcode.make(telegram_link)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            telegram_qr = base64.b64encode(buffer.getvalue()).decode('utf-8')
        # Передаём ссылку и QR в профиль
        return render(request, 'users/profile.html', {
            'user': user,
            'telegram_link': telegram_link,
            'telegram_qr': telegram_qr,
        })
    return HttpResponseRedirect(reverse('profile'))

@login_required
def user_progress_view(request):
    """
    Страница прогресса пользователя: всего карточек, выучено, ошибок, повторений, процент выученных.
    """
    user = request.user
    total = Card.objects.filter(user=user).count()
    learned = Schedule.objects.filter(card__user=user, interval__gte=21).count()
    errors = Schedule.objects.filter(card__user=user, last_result=False).count()
    repetitions = Schedule.objects.filter(card__user=user).aggregate(total_reps=models.Sum('repetition'))['total_reps'] or 0
    percentage = (learned / total) * 100 if total > 0 else 0
    context = {
        'total': total,
        'learned': learned,
        'errors': errors,
        'repetitions': repetitions,
        'percentage': percentage,
    }
    return render(request, 'users/progress.html', context)

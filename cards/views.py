"""
Views приложения cards: CRUD для карточек пользователя.
Только для авторизованных пользователей, только свои карточки.
Фильтрация по уровню сложности.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Card, Schedule
from .forms import CardForm, CardImportForm
import csv
from io import TextIOWrapper
from django.contrib import messages
from .sm2 import update_schedule
from datetime import date
from django.http import HttpResponseRedirect, FileResponse, JsonResponse, Http404, HttpResponse
from django.urls import reverse
from .speechkit import synthesize_speech, SpeechKitError, SpeechKitConfigError, SpeechKitAPIError, SpeechKitNetworkError
import logging
from random import sample, shuffle
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class CardListView(ListView):
    """
    Список карточек пользователя с фильтрацией по уровню сложности.
    Шаблон: cards/card_list.html
    """
    model = Card
    template_name = 'cards/card_list.html'
    context_object_name = 'cards'

    def get_queryset(self):
        """Фильтрует карточки по пользователю и уровню сложности (GET-параметр level)."""
        qs = Card.objects.filter(user=self.request.user).select_related('schedule').order_by('-created_at')
        level = self.request.GET.get('level')
        if level in dict(Card.LEVEL_CHOICES):
            qs = qs.filter(level=level)
        return qs

@method_decorator(login_required, name='dispatch')
class CardCreateView(CreateView):
    """
    Создание новой карточки для пользователя.
    Шаблон: cards/card_form.html
    """
    model = Card
    form_class = CardForm
    template_name = 'cards/card_form.html'
    success_url = reverse_lazy('card_list')

    def form_valid(self, form):
        """Привязывает карточку к текущему пользователю."""
        form.instance.user = self.request.user
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CardUpdateView(UpdateView):
    """
    Редактирование карточки пользователя.
    Шаблон: cards/card_form.html
    """
    model = Card
    form_class = CardForm
    template_name = 'cards/card_form.html'
    success_url = reverse_lazy('card_list')

    def get_queryset(self):
        """Ограничивает редактирование только своими карточками."""
        return Card.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        """Сохраняет карточку и обновляет дату повторения если указана."""
        response = super().form_valid(form)
        
        # Обновляем дату повторения если указана
        next_review = form.cleaned_data.get('next_review')
        if next_review:
            try:
                schedule = self.object.schedule
                schedule.next_review = next_review
                schedule.save()
                messages.success(self.request, f'Дата повторения обновлена на {next_review.strftime("%d.%m.%Y")}')
            except Exception as e:
                logger.error(f"Ошибка обновления даты повторения для карточки {self.object.id}: {e}")
                messages.warning(self.request, 'Не удалось обновить дату повторения')
        
        return response

@method_decorator(login_required, name='dispatch')
class CardDeleteView(DeleteView):
    """
    Удаление карточки пользователя.
    Шаблон: cards/card_confirm_delete.html
    """
    model = Card
    template_name = 'cards/card_confirm_delete.html'
    success_url = reverse_lazy('card_list')

    def get_queryset(self):
        """Ограничивает удаление только своими карточками."""
        return Card.objects.filter(user=self.request.user)

@login_required
def review_mode(request):
    """
    Страница выбора режима повторения: слово→перевод или перевод→слово.
    """
    if request.method == 'POST':
        mode = request.POST.get('mode', 'word2trans')
        request.session['review_mode'] = mode
        return redirect('card_review')
    return render(request, 'cards/review_mode.html')

@login_required
def review_card(request):
    """
    Режим повторения: слово→перевод или перевод→слово (выбор через review_mode).
    """
    mode = request.session.get('review_mode', 'word2trans')
    schedule = Schedule.objects.filter(card__user=request.user, next_review__lte=date.today()).order_by('next_review').select_related('card').first()
    if not schedule:
        return render(request, 'cards/review_done.html')
    card = schedule.card
    if request.method == 'POST':
        try:
            quality = int(request.POST.get('quality'))
            assert 0 <= quality <= 5
        except (TypeError, ValueError, AssertionError):
            messages.error(request, 'Оценка должна быть от 0 до 5')
            return HttpResponseRedirect(reverse('card_review'))
        update_schedule(schedule, quality)
        return HttpResponseRedirect(reverse('card_review'))
    # Определяем, что показывать: слово или перевод
    show_word = (mode == 'word2trans')
    return render(request, 'cards/review.html', {'card': card, 'schedule': schedule, 'show_word': show_word, 'mode': mode})

@login_required
def import_cards(request):
    """
    Импорт карточек из CSV-файла для текущего пользователя.
    Проверяет дубли по слову и переводу.
    """
    if request.method == 'POST':
        form = CardImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            try:
                decoded = TextIOWrapper(file, encoding='utf-8')
                reader = csv.DictReader(decoded)
                count, errors, duplicates = 0, [], 0
                for i, row in enumerate(reader, 1):
                    word = row.get('word', '').strip()
                    translation = row.get('translation', '').strip()
                    if not word or not translation:
                        errors.append(f'Строка {i}: word и translation обязательны')
                        continue
                    level = row.get('level', 'beginner').strip() or 'beginner'
                    if level not in dict(Card.LEVEL_CHOICES):
                        errors.append(f'Строка {i}: некорректный level')
                        continue
                    
                    # Проверка на дубли по слову и переводу
                    if Card.objects.filter(user=request.user, word=word, translation=translation).exists():
                        duplicates += 1
                        errors.append(f'Строка {i}: дубликат "{word} — {translation}"')
                        continue
                    
                    Card.objects.create(
                        user=request.user,
                        word=word,
                        translation=translation,
                        example=row.get('example', '').strip(),
                        comment=row.get('comment', '').strip(),
                        level=level,
                    )
                    count += 1
                
                if count:
                    messages.success(request, f'Импортировано карточек: {count}')
                if duplicates:
                    messages.warning(request, f'Пропущено дубликатов: {duplicates}')
                if errors:
                    messages.error(request, 'Ошибки импорта:\n' + '\n'.join(errors))
                return HttpResponseRedirect(reverse('card_list'))
            except Exception as e:
                messages.error(request, f'Ошибка чтения файла: {e}')
    else:
        form = CardImportForm()
    return render(request, 'cards/import.html', {'form': form})

@login_required
def export_cards(request):
    """
    Экспорт всех карточек пользователя в CSV.
    """
    cards = Card.objects.filter(user=request.user).order_by('word')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=cards_export.csv'
    writer = csv.writer(response)
    writer.writerow(['word', 'translation', 'example', 'comment', 'level'])
    for card in cards:
        writer.writerow([
            card.word,
            card.translation,
            card.example,
            card.comment,
            card.level
        ])
    return response

@login_required
def tts_card(request, pk):
    """
    Возвращает озвучку слова (или примера) карточки через Yandex SpeechKit (с кешем).
    Только для своих карточек. GET-параметры: field=word|example|translation, lang, voice.
    """
    card = get_object_or_404(Card, pk=pk, user=request.user)
    field = request.GET.get('field', 'word')
    text = getattr(card, field, None)
    if not text:
        return JsonResponse({'error': 'Нет текста для озвучки'}, status=400)
    lang = request.GET.get('lang', 'en-US')
    voice = request.GET.get('voice', 'alena')
    
    try:
        audio_path = synthesize_speech(text, language=lang, voice=voice)
        return FileResponse(open(audio_path, 'rb'), content_type='audio/ogg')
    except SpeechKitConfigError as e:
        logger.error(f"Ошибка конфигурации SpeechKit для карточки {pk}: {e}")
        return JsonResponse({
            'error': 'Озвучка не настроена. Обратитесь к администратору.',
            'details': str(e)
        }, status=503)
    except SpeechKitAPIError as e:
        logger.error(f"Ошибка API SpeechKit для карточки {pk}: {e}")
        return JsonResponse({
            'error': 'Ошибка сервиса озвучки. Попробуйте позже.',
            'details': f"Код ошибки: {e.status_code}"
        }, status=503)
    except SpeechKitNetworkError as e:
        logger.error(f"Ошибка сети SpeechKit для карточки {pk}: {e}")
        return JsonResponse({
            'error': 'Ошибка соединения с сервисом озвучки. Проверьте интернет.',
            'details': str(e)
        }, status=503)
    except SpeechKitError as e:
        logger.error(f"Общая ошибка SpeechKit для карточки {pk}: {e}")
        return JsonResponse({
            'error': 'Ошибка озвучки. Попробуйте позже.',
            'details': str(e)
        }, status=500)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при озвучке карточки {pk}: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера.',
            'details': str(e)
        }, status=500)

@login_required
def test_multiple_choice_view(request):
    """
    Тестирование с множественным выбором: очередь карточек на сегодня, 4 варианта, обратная связь, статистика.
    """
    # Получаем все карточки на сегодня
    schedules = list(Schedule.objects.filter(card__user=request.user, next_review__lte=date.today()).select_related('card').order_by('next_review'))
    if not schedules:
        return render(request, 'cards/test_done.html')
    # Индекс текущей карточки (через GET или POST)
    idx = int(request.GET.get('idx', 0))
    if idx >= len(schedules):
        return render(request, 'cards/test_done.html')
    schedule = schedules[idx]
    card = schedule.card
    feedback = None
    correct = None
    if request.method == 'POST':
        answer = request.POST.get('answer')
        is_correct = (answer.strip().lower() == card.translation.strip().lower())
        quality = 5 if is_correct else 2
        update_schedule(schedule, quality)
        feedback = '✅ Верно!' if is_correct else f'❌ Неверно! Правильный ответ: {card.translation}'
        correct = is_correct
        idx += 1
        if idx >= len(schedules):
            return render(request, 'cards/test_done.html')
        # Переходим к следующей карточке
        schedule = schedules[idx]
        card = schedule.card
    # Генерируем варианты ответа
    all_translations = list(Card.objects.filter(user=request.user).exclude(id=card.id).values_list('translation', flat=True))
    if len(all_translations) >= 3:
        wrong_choices = sample(all_translations, 3)
    else:
        wrong_choices = all_translations + ['—'] * (3 - len(all_translations))
    options = wrong_choices + [card.translation]
    shuffle(options)
    context = {
        'card': card,
        'schedule': schedule,
        'options': options,
        'idx': idx,
        'total': len(schedules),
        'feedback': feedback,
        'correct': correct,
    }
    return render(request, 'cards/test.html', context)

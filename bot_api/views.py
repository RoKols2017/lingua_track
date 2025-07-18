from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from users.models import User
from cards.models import Card, Schedule
from cards.speechkit import synthesize_speech, SpeechKitError, SpeechKitConfigError, SpeechKitAPIError, SpeechKitNetworkError
from datetime import date
import json
from django.db import models
import logging
from random import sample
from .models import BotLog

logger = logging.getLogger(__name__)

# Create your views here.

def log_bot_event(event_type, telegram_id=None, user=None, request_text='', response_text='', success=None, raw_data=None):
    try:
        BotLog.objects.create(
            event_type=event_type,
            telegram_id=telegram_id,
            user=user,
            request_text=request_text,
            response_text=response_text,
            success=success,
            raw_data=raw_data
        )
    except Exception as e:
        logger.error(f"Ошибка записи лога BotLog: {e}")

@csrf_exempt
def telegram_bind(request):
    if request.method != 'POST':
        log_bot_event('command', request_text='telegram_bind (not POST)', response_text='POST required', success=False)
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        token = data.get('token')
        telegram_id = data.get('telegram_id')
        if not token or not telegram_id:
            log_bot_event('command', telegram_id=telegram_id, request_text=str(data), response_text='token and telegram_id required', success=False)
            return JsonResponse({'error': 'token and telegram_id required'}, status=400)
        user = User.objects.filter(telegram_link_token=token).first()
        if not user:
            log_bot_event('command', telegram_id=telegram_id, request_text=str(data), response_text='invalid token', success=False)
            return JsonResponse({'error': 'invalid token'}, status=404)
        user.telegram_id = telegram_id
        user.telegram_link_token = None
        user.save()
        log_bot_event('command', telegram_id=telegram_id, user=user, request_text=str(data), response_text='ok', success=True)
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        log_bot_event('error', request_text='telegram_bind', response_text=str(e), success=False)
        return JsonResponse({'error': str(e)}, status=500)

def get_user_by_telegram_id(request):
    telegram_id = request.GET.get('telegram_id') or request.POST.get('telegram_id')
    if not telegram_id:
        return None, JsonResponse({'error': 'telegram_id required'}, status=400)
    user = User.objects.filter(telegram_id=telegram_id).first()
    if not user:
        return None, JsonResponse({'error': 'user not found'}, status=404)
    return user, None

def cards_list(request):
    user, error = get_user_by_telegram_id(request)
    if error:
        log_bot_event('command', request_text='cards_list', response_text=str(error.content), success=False)
        return error
    cards = Card.objects.filter(user=user)
    data = [
        {
            'id': c.id,
            'word': c.word,
            'translation': c.translation,
            'example': c.example,
            'comment': c.comment,
            'level': c.level,
        } for c in cards
    ]
    log_bot_event('command', telegram_id=user.telegram_id, user=user, request_text='cards_list', response_text=str(data), success=True)
    return JsonResponse({'cards': data})

def cards_today(request):
    user, error = get_user_by_telegram_id(request)
    if error:
        log_bot_event('command', request_text='cards_today', response_text=str(error.content), success=False)
        return error
    today = date.today()
    schedules = Schedule.objects.filter(card__user=user, next_review__lte=today).select_related('card')
    data = [
        {
            'id': s.card.id,
            'word': s.card.word,
            'translation': s.card.translation,
            'example': s.card.example,
            'comment': s.card.comment,
            'level': s.card.level,
            'next_review': s.next_review,
            'interval': s.interval,
            'repetition': s.repetition,
        } for s in schedules
    ]
    log_bot_event('command', telegram_id=user.telegram_id, user=user, request_text='cards_today', response_text=str(data), success=True)
    return JsonResponse({'cards': data})

def user_progress(request):
    user, error = get_user_by_telegram_id(request)
    if error:
        log_bot_event('command', request_text='user_progress', response_text=str(error.content), success=False)
        return error
    total = Card.objects.filter(user=user).count()
    learned = Schedule.objects.filter(card__user=user, interval__gte=21).count()  # условно "выучено"
    errors = Schedule.objects.filter(card__user=user, last_result=False).count()
    repetitions = Schedule.objects.filter(card__user=user).aggregate(total_reps=models.Sum('repetition'))['total_reps'] or 0
    resp = {
        'total': total,
        'learned': learned,
        'errors': errors,
        'repetitions': repetitions,
    }
    log_bot_event('command', telegram_id=user.telegram_id, user=user, request_text='user_progress', response_text=str(resp), success=True)
    return JsonResponse(resp)

def tts(request):
    telegram_id = request.GET.get('telegram_id')
    word = request.GET.get('word')
    if not telegram_id or not word:
        log_bot_event('command', telegram_id=telegram_id, request_text=f'tts: {word}', response_text='telegram_id and word required', success=False)
        return JsonResponse({'error': 'telegram_id and word required'}, status=400)
    user = User.objects.filter(telegram_id=telegram_id).first()
    if not user:
        log_bot_event('command', telegram_id=telegram_id, request_text=f'tts: {word}', response_text='user not found', success=False)
        return JsonResponse({'error': 'user not found'}, status=404)
    card = Card.objects.filter(user=user, word=word).first()
    if not card:
        log_bot_event('command', telegram_id=telegram_id, user=user, request_text=f'tts: {word}', response_text='word not found for user', success=False)
        return JsonResponse({'error': 'word not found for user'}, status=404)
    
    try:
        audio_path = synthesize_speech(word)  # если потребуется язык, можно добавить language=...
        with open(audio_path, 'rb') as f:
            log_bot_event('command', telegram_id=telegram_id, user=user, request_text=f'tts: {word}', response_text='audio ok', success=True)
            return HttpResponse(f.read(), content_type='audio/ogg')
    except SpeechKitConfigError as e:
        logger.error(f"Ошибка конфигурации SpeechKit для пользователя {telegram_id}, слово '{word}': {e}")
        log_bot_event('error', telegram_id=telegram_id, user=user, request_text=f'tts: {word}', response_text=str(e), success=False)
        return JsonResponse({
            'error': 'Озвучка не настроена на сервере.',
            'details': str(e)
        }, status=503)
    except SpeechKitAPIError as e:
        logger.error(f"Ошибка API SpeechKit для пользователя {telegram_id}, слово '{word}': {e}")
        log_bot_event('error', telegram_id=telegram_id, user=user, request_text=f'tts: {word}', response_text=f"Код ошибки: {e.status_code}", success=False)
        return JsonResponse({
            'error': 'Ошибка сервиса озвучки. Попробуйте позже.',
            'details': f"Код ошибки: {e.status_code}"
        }, status=503)
    except SpeechKitNetworkError as e:
        logger.error(f"Ошибка сети SpeechKit для пользователя {telegram_id}, слово '{word}': {e}")
        log_bot_event('error', telegram_id=telegram_id, user=user, request_text=f'tts: {word}', response_text=str(e), success=False)
        return JsonResponse({
            'error': 'Ошибка соединения с сервисом озвучки.',
            'details': str(e)
        }, status=503)
    except SpeechKitError as e:
        logger.error(f"Общая ошибка SpeechKit для пользователя {telegram_id}, слово '{word}': {e}")
        log_bot_event('error', telegram_id=telegram_id, user=user, request_text=f'tts: {word}', response_text=str(e), success=False)
        return JsonResponse({
            'error': 'Ошибка озвучки. Попробуйте позже.',
            'details': str(e)
        }, status=500)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при озвучке для пользователя {telegram_id}, слово '{word}': {e}")
        log_bot_event('error', telegram_id=telegram_id, user=user, request_text=f'tts: {word}', response_text=str(e), success=False)
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера.',
            'details': str(e)
        }, status=500)

@csrf_exempt
def test(request):
    if request.method != 'POST':
        log_bot_event('command', request_text='test (not POST)', response_text='POST required', success=False)
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        telegram_id = data.get('telegram_id')
        card_id = data.get('card_id')
        answer = data.get('answer')
        if not telegram_id or not card_id or answer is None:
            log_bot_event('command', telegram_id=telegram_id, request_text=str(data), response_text='telegram_id, card_id, answer required', success=False)
            return JsonResponse({'error': 'telegram_id, card_id, answer required'}, status=400)
        user = User.objects.filter(telegram_id=telegram_id).first()
        if not user:
            log_bot_event('command', telegram_id=telegram_id, request_text=str(data), response_text='user not found', success=False)
            return JsonResponse({'error': 'user not found'}, status=404)
        card = Card.objects.filter(user=user, id=card_id).first()
        if not card:
            log_bot_event('command', telegram_id=telegram_id, user=user, request_text=str(data), response_text='card not found', success=False)
            return JsonResponse({'error': 'card not found'}, status=404)
        schedule = Schedule.objects.filter(card=card).first()
        if not schedule:
            log_bot_event('command', telegram_id=telegram_id, user=user, request_text=str(data), response_text='schedule not found', success=False)
            return JsonResponse({'error': 'schedule not found'}, status=404)
        quality = 5 if answer else 2
        from cards.sm2 import update_schedule
        update_schedule(schedule, quality)
        msg = '✅ Отлично! Карточка перенесена на следующий повтор.' if answer else '❌ Ошибка. Карточка будет показана раньше.'
        resp = {
            'result': 'ok',
            'correct': answer,
            'next_review': str(schedule.next_review),
            'interval': schedule.interval,
            'msg': msg
        }
        log_bot_event('command', telegram_id=telegram_id, user=user, request_text=str(data), response_text=str(resp), success=True)
        return JsonResponse(resp)
    except Exception as e:
        log_bot_event('error', request_text='test', response_text=str(e), success=False)
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def test_multiple_choice(request):
    """
    API для теста с множественным выбором (multiple choice).
    GET: возвращает карточку на сегодня и 4 варианта (1 правильный, 3 неправильных).
    POST: принимает telegram_id, card_id, выбранный вариант, сохраняет результат.
    """
    if request.method == 'GET':
        user, error = get_user_by_telegram_id(request)
        if error:
            log_bot_event('command', request_text='test_multiple_choice (GET)', response_text=str(error.content), success=False)
            return error
        today = date.today()
        schedule = Schedule.objects.filter(card__user=user, next_review__lte=today).select_related('card').order_by('next_review').first()
        if not schedule:
            log_bot_event('command', telegram_id=user.telegram_id, user=user, request_text='test_multiple_choice (GET)', response_text='no_cards_today', success=False)
            return JsonResponse({'error': 'no_cards_today'}, status=404)
        card = schedule.card
        all_translations = list(Card.objects.filter(user=user).exclude(id=card.id).values_list('translation', flat=True))
        if len(all_translations) >= 3:
            wrong_choices = sample(all_translations, 3)
        else:
            wrong_choices = all_translations + ['—'] * (3 - len(all_translations))
        options = wrong_choices + [card.translation]
        from random import shuffle
        shuffle(options)
        resp = {
            'card': {
                'id': card.id,
                'word': card.word,
                'example': card.example,
                'comment': card.comment,
                'level': card.level,
            },
            'options': options
        }
        log_bot_event('command', telegram_id=user.telegram_id, user=user, request_text='test_multiple_choice (GET)', response_text=str(resp), success=True)
        return JsonResponse(resp)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            telegram_id = data.get('telegram_id')
            card_id = data.get('card_id')
            answer = data.get('answer')  # строка (выбранный перевод)
            if not telegram_id or not card_id or answer is None:
                log_bot_event('command', telegram_id=telegram_id, request_text=str(data), response_text='telegram_id, card_id, answer required', success=False)
                return JsonResponse({'error': 'telegram_id, card_id, answer required'}, status=400)
            user = User.objects.filter(telegram_id=telegram_id).first()
            if not user:
                log_bot_event('command', telegram_id=telegram_id, request_text=str(data), response_text='user not found', success=False)
                return JsonResponse({'error': 'user not found'}, status=404)
            card = Card.objects.filter(user=user, id=card_id).first()
            if not card:
                log_bot_event('command', telegram_id=telegram_id, user=user, request_text=str(data), response_text='card not found', success=False)
                return JsonResponse({'error': 'card not found'}, status=404)
            schedule = Schedule.objects.filter(card=card).first()
            if not schedule:
                log_bot_event('command', telegram_id=telegram_id, user=user, request_text=str(data), response_text='schedule not found', success=False)
                return JsonResponse({'error': 'schedule not found'}, status=404)
            is_correct = (answer.strip().lower() == card.translation.strip().lower())
            quality = 5 if is_correct else 2
            from cards.sm2 import update_schedule
            update_schedule(schedule, quality)
            msg = '✅ Верно!' if is_correct else f'❌ Неверно! Правильный ответ: {card.translation}'
            resp = {
                'result': 'ok',
                'correct': is_correct,
                'msg': msg,
                'next_review': str(schedule.next_review),
                'interval': schedule.interval
            }
            log_bot_event('command', telegram_id=telegram_id, user=user, request_text=str(data), response_text=str(resp), success=True)
            return JsonResponse(resp)
        except Exception as e:
            log_bot_event('error', request_text='test_multiple_choice (POST)', response_text=str(e), success=False)
            return JsonResponse({'error': str(e)}, status=500)

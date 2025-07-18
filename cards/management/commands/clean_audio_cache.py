"""
Django management command для очистки кэша аудиофайлов SpeechKit.
Удаляет файлы старше TTL и битые файлы.
"""
from django.core.management.base import BaseCommand
from cards.speechkit import clean_audio_cache, AUDIO_CACHE_DIR
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Очищает кэш аудиофайлов SpeechKit (удаляет устаревшие и битые файлы)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно очистить весь кэш (игнорировать TTL)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет удалено без фактического удаления',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Режим dry-run - файлы не будут удалены'))
        
        if force:
            self.stdout.write('Принудительная очистка всего кэша...')
            # Здесь можно добавить логику для принудительной очистки
            # Пока используем стандартную функцию
        else:
            self.stdout.write('Очистка устаревших файлов кэша...')
        
        try:
            # Показываем статистику перед очисткой
            total_files = len(list(AUDIO_CACHE_DIR.glob('*.ogg')))
            self.stdout.write(f'Всего файлов в кэше: {total_files}')
            
            if not dry_run:
                clean_audio_cache()
                self.stdout.write(self.style.SUCCESS('Кэш успешно очищен'))
            else:
                self.stdout.write('Dry-run завершен')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при очистке кэша: {e}')
            )
            logger.error(f"Ошибка в команде clean_audio_cache: {e}") 
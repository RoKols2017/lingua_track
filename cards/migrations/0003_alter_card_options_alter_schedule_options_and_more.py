# Generated by Django 5.2.4 on 2025-07-18 11:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0002_schedule'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='card',
            options={'ordering': ['-created_at'], 'verbose_name': 'Карточка', 'verbose_name_plural': 'Карточки'},
        ),
        migrations.AlterModelOptions(
            name='schedule',
            options={'ordering': ['next_review'], 'verbose_name': 'Расписание повторения', 'verbose_name_plural': 'Расписания повторений'},
        ),
        migrations.AlterField(
            model_name='card',
            name='comment',
            field=models.TextField(blank=True, help_text='Дополнительные заметки или пояснения', verbose_name='Комментарий'),
        ),
        migrations.AlterField(
            model_name='card',
            name='example',
            field=models.TextField(blank=True, help_text='Пример предложения с этим словом', verbose_name='Пример использования'),
        ),
        migrations.AlterField(
            model_name='card',
            name='level',
            field=models.CharField(choices=[('beginner', 'Начальный'), ('intermediate', 'Средний'), ('advanced', 'Продвинутый')], default='beginner', help_text='Уровень сложности слова', max_length=16, verbose_name='Уровень'),
        ),
        migrations.AlterField(
            model_name='card',
            name='translation',
            field=models.CharField(help_text='Перевод слова на родной язык', max_length=128, verbose_name='Перевод'),
        ),
        migrations.AlterField(
            model_name='card',
            name='word',
            field=models.CharField(help_text='Слово на иностранном языке', max_length=128, verbose_name='Слово'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='ef',
            field=models.FloatField(default=2.5, help_text='Коэффициент эффективности от 1.3 до 2.5', verbose_name='Эффективность (SM-2)'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='interval',
            field=models.PositiveIntegerField(default=1, help_text='Количество дней до следующего повторения', verbose_name='Интервал (дней)'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='last_result',
            field=models.BooleanField(blank=True, help_text='True - знал, False - не знал, None - не тестировался', null=True, verbose_name='Последний результат (успех)'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='repetition',
            field=models.PositiveIntegerField(default=0, help_text='Счетчик успешных повторений подряд', verbose_name='Номер повторения'),
        ),
        migrations.AddIndex(
            model_name='card',
            index=models.Index(fields=['user', 'level'], name='cards_card_user_id_efb68e_idx'),
        ),
        migrations.AddIndex(
            model_name='card',
            index=models.Index(fields=['created_at'], name='cards_card_created_591b38_idx'),
        ),
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['next_review'], name='cards_sched_next_re_ee8e4b_idx'),
        ),
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['card', 'next_review'], name='cards_sched_card_id_1537f4_idx'),
        ),
    ]

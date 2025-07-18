# 🚀 Деплой LinguaTrack на сервер

Этот каталог содержит все необходимые файлы для деплоя LinguaTrack на сервер Ubuntu с доменом `tarmo.opencove.ru`.

## 📋 Требования к серверу

### Минимальные требования:
- **ОС:** Ubuntu 20.04 LTS или новее
- **RAM:** 2 GB
- **CPU:** 1 ядро
- **Диск:** 10 GB свободного места
- **Сеть:** Доступ к интернету

### Рекомендуемые требования:
- **ОС:** Ubuntu 22.04 LTS
- **RAM:** 4 GB
- **CPU:** 2 ядра
- **Диск:** 20 GB SSD
- **Сеть:** Статический IP

## 🛠 Подготовка сервера

### 1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка Docker и Docker Compose
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка для применения изменений
sudo reboot
```

### 3. Настройка файрвола
```bash
# Установка UFW
sudo apt install ufw -y

# Настройка правил
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 📁 Подготовка файлов

### 1. Клонирование проекта
```bash
git clone https://github.com/RoKols2017/lingua_track.git
cd lingua_track/deploy
```

### 2. Настройка переменных окружения
```bash
# Копирование шаблона
cp env.production.example .env

# Редактирование .env файла
nano .env
```

**Замените в .env файле:**
- `SECRET_KEY` — сгенерируйте новый ключ
- `POSTGRES_PASSWORD` — сложный пароль для PostgreSQL
- `REDIS_PASSWORD` — сложный пароль для Redis
- `YANDEX_SPEECHKIT_API_KEY` — ваш API ключ Yandex
- `YANDEX_SPEECHKIT_FOLDER_ID` — ID папки в Yandex Cloud
- `TELEGRAM_BOT_TOKEN` — токен вашего Telegram-бота

### 3. Получение SSL сертификатов

#### Вариант A: Let's Encrypt (бесплатно)
```bash
# Установка Certbot
sudo apt install certbot -y

# Получение сертификата
sudo certbot certonly --standalone -d tarmo.opencove.ru

# Копирование сертификатов
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/tarmo.opencove.ru/fullchain.pem ssl/tarmo.opencove.ru.crt
sudo cp /etc/letsencrypt/live/tarmo.opencove.ru/privkey.pem ssl/tarmo.opencove.ru.key
sudo chown -R $USER:$USER ssl/
```

#### Вариант B: Собственные сертификаты
Поместите ваши SSL сертификаты в директорию `ssl/`:
- `ssl/tarmo.opencove.ru.crt` — сертификат
- `ssl/tarmo.opencove.ru.key` — приватный ключ

## 🚀 Запуск приложения

### 1. Первый запуск
```bash
# Сделать скрипт исполняемым
chmod +x deploy.sh

# Запуск приложения
./deploy.sh start
```

### 2. Проверка статуса
```bash
./deploy.sh status
```

### 3. Просмотр логов
```bash
./deploy.sh logs
```

## 📊 Мониторинг и управление

### Основные команды:
```bash
# Запуск
./deploy.sh start

# Остановка
./deploy.sh stop

# Перезапуск
./deploy.sh restart

# Просмотр логов
./deploy.sh logs

# Статус сервисов
./deploy.sh status

# Обновление приложения
./deploy.sh update

# Резервное копирование
./deploy.sh backup

# Восстановление
./deploy.sh restore backups/20231201_120000

# Полная очистка (ОСТОРОЖНО!)
./deploy.sh cleanup
```

### Просмотр логов отдельных сервисов:
```bash
# Логи Django
docker-compose logs web

# Логи бота
docker-compose logs bot

# Логи PostgreSQL
docker-compose logs postgres

# Логи Redis
docker-compose logs redis
```

## 🔧 Настройка автоматического обновления SSL

### Создание скрипта обновления:
```bash
sudo nano /etc/cron.d/ssl-renew
```

**Содержимое файла:**
```
0 12 * * * root certbot renew --quiet && cp /etc/letsencrypt/live/tarmo.opencove.ru/fullchain.pem /path/to/lingua_track/deploy/ssl/tarmo.opencove.ru.crt && cp /etc/letsencrypt/live/tarmo.opencove.ru/privkey.pem /path/to/lingua_track/deploy/ssl/tarmo.opencove.ru.key && chown -R user:user /path/to/lingua_track/deploy/ssl/ && cd /path/to/lingua_track/deploy && docker-compose restart nginx
```

## 📈 Мониторинг производительности

### Проверка использования ресурсов:
```bash
# Статистика контейнеров
docker stats

# Использование диска
df -h

# Использование памяти
free -h

# Нагрузка на CPU
htop
```

### Логи Nginx:
```bash
# Доступ к логам
docker-compose exec nginx tail -f /var/log/nginx/access.log
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

## 🔒 Безопасность

### Рекомендации:
1. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Меняйте пароли базы данных:**
   ```bash
   # Остановите приложение
   ./deploy.sh stop
   
   # Измените пароли в .env
   nano .env
   
   # Запустите заново
   ./deploy.sh start
   ```

3. **Настройте регулярные резервные копии:**
   ```bash
   # Добавьте в crontab
   crontab -e
   
   # Добавьте строку для ежедневного бэкапа
   0 2 * * * cd /path/to/lingua_track/deploy && ./deploy.sh backup
   ```

4. **Мониторинг безопасности:**
   ```bash
   # Проверка открытых портов
   sudo netstat -tlnp
   
   # Проверка логов безопасности
   sudo journalctl -f
   ```

## 🆘 Устранение неполадок

### Проблема: Контейнеры не запускаются
```bash
# Проверка логов
./deploy.sh logs

# Проверка статуса
./deploy.sh status

# Перезапуск
./deploy.sh restart
```

### Проблема: База данных недоступна
```bash
# Проверка PostgreSQL
docker-compose exec postgres pg_isready -U linguatrack_user

# Проверка логов PostgreSQL
docker-compose logs postgres
```

### Проблема: SSL сертификат не работает
```bash
# Проверка сертификатов
openssl x509 -in ssl/tarmo.opencove.ru.crt -text -noout

# Перезапуск Nginx
docker-compose restart nginx
```

### Проблема: Telegram-бот не отвечает
```bash
# Проверка логов бота
docker-compose logs bot

# Проверка HTTP endpoint
curl http://localhost:8080/health/
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи:** `./deploy.sh logs`
2. **Проверьте статус:** `./deploy.sh status`
3. **Перезапустите:** `./deploy.sh restart`
4. **Создайте резервную копию:** `./deploy.sh backup`

## 🎯 Результат

После успешного деплоя:

- 🌐 **Сайт:** https://tarmo.opencove.ru
- 🔧 **Админка:** https://tarmo.opencove.ru/admin/
- 📊 **Health check:** https://tarmo.opencove.ru/health/
- 🤖 **Telegram-бот:** работает с вашим токеном

**Удачи с деплоем! 🚀** 
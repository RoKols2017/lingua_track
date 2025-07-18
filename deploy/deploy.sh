#!/bin/bash

# Скрипт деплоя LinguaTrack на сервер
# Использование: ./deploy.sh [start|stop|restart|logs|status]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Docker и Docker Compose
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Установите Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен. Установите Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    log_success "Docker и Docker Compose найдены"
}

# Проверка наличия .env файла
check_env_file() {
    if [ ! -f .env ]; then
        log_warning "Файл .env не найден"
        if [ -f env.production.example ]; then
            log_info "Копирую env.production.example в .env"
            cp env.production.example .env
            log_warning "Отредактируйте .env файл и замените заглушки на реальные значения!"
            log_warning "Затем запустите скрипт снова."
            exit 1
        else
            log_error "Файл env.production.example не найден"
            exit 1
        fi
    fi
    
    log_success "Файл .env найден"
}

# Создание SSL сертификатов (если нужно)
setup_ssl() {
    if [ ! -d ssl ]; then
        log_info "Создание директории для SSL сертификатов..."
        mkdir -p ssl
        
        log_warning "SSL сертификаты не найдены в директории ssl/"
        log_info "Поместите ваши SSL сертификаты в директорию ssl/:"
        log_info "  - ssl/tarmo.opencove.ru.crt (сертификат)"
        log_info "  - ssl/tarmo.opencove.ru.key (приватный ключ)"
        log_warning "Или используйте Let's Encrypt для получения бесплатных сертификатов"
    fi
}

# Функция запуска
start() {
    log_info "Запуск LinguaTrack..."
    
    check_dependencies
    check_env_file
    setup_ssl
    
    log_info "Сборка и запуск контейнеров..."
    docker-compose up -d --build
    
    log_info "Ожидание готовности сервисов..."
    sleep 30
    
    log_info "Проверка статуса сервисов..."
    docker-compose ps
    
    log_success "LinguaTrack запущен!"
    log_info "Сайт доступен по адресу: https://tarmo.opencove.ru"
    log_info "Админка: https://tarmo.opencove.ru/admin/"
    log_info "Health check: https://tarmo.opencove.ru/health/"
}

# Функция остановки
stop() {
    log_info "Остановка LinguaTrack..."
    docker-compose down
    log_success "LinguaTrack остановлен"
}

# Функция перезапуска
restart() {
    log_info "Перезапуск LinguaTrack..."
    stop
    sleep 5
    start
}

# Функция просмотра логов
logs() {
    log_info "Просмотр логов..."
    docker-compose logs -f
}

# Функция статуса
status() {
    log_info "Статус сервисов..."
    docker-compose ps
    
    log_info "Использование ресурсов..."
    docker stats --no-stream
}

# Функция очистки
cleanup() {
    log_warning "Очистка всех данных (включая базу данных)!"
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Остановка и удаление контейнеров..."
        docker-compose down -v
        log_info "Удаление образов..."
        docker-compose down --rmi all
        log_success "Очистка завершена"
    else
        log_info "Очистка отменена"
    fi
}

# Функция обновления
update() {
    log_info "Обновление LinguaTrack..."
    
    log_info "Остановка сервисов..."
    docker-compose down
    
    log_info "Получение обновлений..."
    git pull origin main
    
    log_info "Пересборка и запуск..."
    docker-compose up -d --build
    
    log_success "Обновление завершено!"
}

# Функция резервного копирования
backup() {
    log_info "Создание резервной копии..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    log_info "Резервное копирование базы данных..."
    docker-compose exec -T postgres pg_dump -U linguatrack_user linguatrack > "$BACKUP_DIR/database.sql"
    
    log_info "Резервное копирование медиа файлов..."
    docker-compose exec -T web tar czf - /app/media > "$BACKUP_DIR/media.tar.gz"
    
    log_success "Резервная копия создана в $BACKUP_DIR"
}

# Функция восстановления
restore() {
    if [ -z "$1" ]; then
        log_error "Укажите путь к резервной копии"
        exit 1
    fi
    
    BACKUP_DIR="$1"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Директория $BACKUP_DIR не найдена"
        exit 1
    fi
    
    log_warning "Восстановление из резервной копии $BACKUP_DIR"
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Остановка сервисов..."
        docker-compose down
        
        log_info "Восстановление базы данных..."
        docker-compose up -d postgres
        sleep 10
        docker-compose exec -T postgres psql -U linguatrack_user -d linguatrack < "$BACKUP_DIR/database.sql"
        
        log_info "Восстановление медиа файлов..."
        docker-compose up -d web
        docker-compose exec -T web tar xzf - < "$BACKUP_DIR/media.tar.gz"
        
        log_info "Запуск всех сервисов..."
        docker-compose up -d
        
        log_success "Восстановление завершено!"
    else
        log_info "Восстановление отменено"
    fi
}

# Функция помощи
show_help() {
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  start     - Запуск LinguaTrack"
    echo "  stop      - Остановка LinguaTrack"
    echo "  restart   - Перезапуск LinguaTrack"
    echo "  logs      - Просмотр логов"
    echo "  status    - Статус сервисов"
    echo "  update    - Обновление приложения"
    echo "  backup    - Создание резервной копии"
    echo "  restore   - Восстановление из резервной копии"
    echo "  cleanup   - Полная очистка (удаление всех данных)"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start"
    echo "  $0 logs"
    echo "  $0 backup"
    echo "  $0 restore backups/20231201_120000"
}

# Основная логика
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    update)
        update
        ;;
    backup)
        backup
        ;;
    restore)
        restore "$2"
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac 
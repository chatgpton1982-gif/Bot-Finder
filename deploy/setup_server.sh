#!/bin/bash
# Setup script for tg_bot_finder deployment
# Запускать от root: sudo bash deploy/setup_server.sh
set -e

PROJECT_DIR="/opt/tg_bot_finder"
SECRETS_DIR="/etc/tg_bot_finder"
SECRETS_FILE="$SECRETS_DIR/secrets.env"
SERVICE_NAME="tg_bot_finder"

echo "=== Настройка сервера для tg_bot_finder ==="

# 1. Создание системного пользователя
echo "--- Создание пользователя tg_bot ---"
useradd -r -s /bin/false tg_bot 2>/dev/null || echo "Пользователь tg_bot уже существует"

# 2. Создание директории для секретов
echo "--- Создание директории секретов ---"
mkdir -p "$SECRETS_DIR"
chmod 750 "$SECRETS_DIR"
chown root:tg_bot "$SECRETS_DIR"

# 3. Создание файла секретов (если не существует)
if [ ! -f "$SECRETS_FILE" ]; then
    echo "--- Создание файла секретов ---"
    cat > "$SECRETS_FILE" << 'EOF'
# Критичные данные — личный аккаунт Telegram
# Получить: https://my.telegram.org/apps
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+79001234567
EOF
    chown root:tg_bot "$SECRETS_FILE"
    chmod 640 "$SECRETS_FILE"
    echo "ВНИМАНИЕ: Заполните $SECRETS_FILE реальными данными!"
else
    echo "Файл секретов уже существует: $SECRETS_FILE"
fi

# 4. Создание директории проекта
echo "--- Создание директории проекта ---"
mkdir -p "$PROJECT_DIR/data"

# 5. Создание .env (если не существует)
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "--- Создание .env из шаблона ---"
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    else
        echo "ВНИМАНИЕ: Скопируйте .env.example в $PROJECT_DIR/.env и заполните"
    fi
fi

# 6. Настройка прав на .env
if [ -f "$PROJECT_DIR/.env" ]; then
    chown tg_bot:tg_bot "$PROJECT_DIR/.env"
    chmod 640 "$PROJECT_DIR/.env"
fi

# 7. Создание systemd-сервиса
echo "--- Создание systemd-сервиса ---"
cat > /etc/systemd/system/${SERVICE_NAME}.service << 'EOF'
[Unit]
Description=Telegram Bot Finder
After=network.target

[Service]
Type=simple
User=tg_bot
Group=tg_bot
WorkingDirectory=/opt/tg_bot_finder

# Критичные секреты (API_ID, API_HASH, PHONE_NUMBER)
EnvironmentFile=/etc/tg_bot_finder/secrets.env

# Обычные настройки (BOT_TOKEN, AI-ключи и т.д.)
EnvironmentFile=/opt/tg_bot_finder/.env

ExecStart=/opt/tg_bot_finder/venv/bin/python -m bot.main
Restart=always
RestartSec=10

# Безопасность
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# 8. Настройка прав на директорию проекта
echo "--- Настройка прав доступа ---"
chown -R tg_bot:tg_bot "$PROJECT_DIR/data"
chmod 755 "$PROJECT_DIR"

# 9. Перезагрузка systemd
echo "--- Перезагрузка systemd ---"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
echo "=== Настройка завершена ==="
echo ""
echo "Следующие шаги:"
echo "1. Заполните секреты:   nano $SECRETS_FILE"
echo "2. Заполните .env:      nano $PROJECT_DIR/.env"
echo "3. Удалите API_ID, API_HASH, PHONE_NUMBER из .env (они уже в secrets.env)"
echo "4. Перенесите session-файл Telethon в $PROJECT_DIR/data/"
echo "5. Настройте права:     chown -R tg_bot:tg_bot $PROJECT_DIR/data"
echo "6. Запустите бота:      systemctl start $SERVICE_NAME"
echo "7. Проверьте статус:    systemctl status $SERVICE_NAME"
echo "8. Смотрите логи:       journalctl -u $SERVICE_NAME -f"
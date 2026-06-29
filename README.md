# Bot Finder — Telegram Bot для поиска и суммаризации сообщений

Бот работает через **личный аккаунт Telegram** (Telethon) для чтения любых каналов, где вы состоите. Управление — через inline-кнопки в Telegram.

## Возможности

- 🔍 **Поиск сообщений** по ключевым словам за определённую дату в любом канале
- 📊 **Сводка за день** — краткая выжимка о чём была переписка (через AI)
- 🤖 **Переключаемые AI-провайдеры**: OpenAI, Google Gemini, Anthropic Claude, DeepSeek, OpenRouter, Ollama, Кастомный (OpenAI-совместимый)
- 📅 **Inline-календарь** для удобного выбора даты
- ⚙️ **Настройка провайдера** прямо из меню бота

## Бесплатные AI-провайдеры

Бот поддерживает несколько способов работы с LLM **абсолютно бесплатно**:

### 🧠 Google Gemini (Free Tier) — рекомендуется

Google предоставляет бесплатный доступ к Gemini API:
- **Лимит:** до 1 500 запросов в день
- **Качество:** отличное (Gemini 2.0 Flash)
- **Что нужно сделать:**
  1. Перейти на https://aistudio.google.com/apikey
  2. Нажать «Get API key» → «Create API key»
  3. Скопировать ключ в `.env`: `GEMINI_API_KEY=ваш_ключ`
  4. Установить `DEFAULT_AI_PROVIDER=gemini`

### 🌐 OpenRouter (бесплатные модели)

OpenRouter — агрегатор LLM с бесплатными моделями:
- **Бесплатные модели:** `meta-llama/llama-3.2-3b-instruct:free`, `mistralai/mistral-7b-instruct:free` и другие
- **Лимит:** зависит от модели (обычно щедрый)
- **Что нужно сделать:**
  1. Зарегистрироваться на https://openrouter.ai/keys
  2. Создать API-ключ
  3. Скопировать ключ в `.env`: `OPENROUTER_API_KEY=sk-or-...`
  4. Установить `DEFAULT_AI_PROVIDER=openrouter`

### ⚙️ Кастомный OpenAI-совместимый провайдер

Подходит для любых API, совместимых с форматом OpenAI (например, **Xiaomi MiMo**, vLLM, TGI, Together AI, Fireworks AI и другие).

- **Стоимость:** зависит от провайдера (часто есть бесплатные модели)
- **Гибкость:** вы указываете `base_url`, `api_key` и название модели
- **Что нужно сделать:**
  1. Получить API-ключ и `base_url` у вашего провайдера
  2. В `.env` указать:
     ```ini
     CUSTOM_API_BASE=https://api.ваш-провайдер.com/v1
     CUSTOM_API_KEY=sk-ваш_ключ
     CUSTOM_MODEL=название-модели
     ```
  3. Установить `DEFAULT_AI_PROVIDER=custom`

**Пример для Xiaomi MiMo:**
```ini
CUSTOM_API_BASE=https://api.xiaomimimo.com/v1
CUSTOM_API_KEY=sk-ваш_ключ
CUSTOM_MODEL=mimo-v2-flash
```

Доступные модели MiMo: `mimo-v2-flash`, `mimo-v2-omni`, `mimo-v2-pro`, `mimo-v2-tts`, `mimo-v2.5`, `mimo-v2.5-asr`, `mimo-v2.5-pro`, `mimo-v2.5-tts`, `mimo-v2.5-tts-voiceclone`, `mimo-v2.5-tts-voicedesign`.

### 🖥️ Ollama (локально, полностью бесплатно)

Запуск LLM на вашем собственном сервере:
- **Стоимость:** $0 (абсолютно бесплатно)
- **Требования:** от 1 ГБ RAM (для `llama3.2:1b`) до 8 ГБ (для `llama3`)
- **Что нужно сделать:**
  1. Установить Ollama: https://ollama.com/download
  2. Скачать лёгкую модель: `ollama pull llama3.2:1b`
  3. Запустить сервер: `ollama serve`
  4. В `.env` установить `DEFAULT_AI_PROVIDER=ollama` и `OLLAMA_MODEL=llama3.2:1b`

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone <repo-url>
cd tg_bot_finder
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить `.env`

Скопируйте [`.env.example`](.env.example) в `.env` и заполните:

```bash
copy .env.example .env
```

#### Получение `BOT_TOKEN`:
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте полученный токен в `BOT_TOKEN`

#### Получение `API_ID` и `API_HASH` для Telethon:
1. Перейдите на https://my.telegram.org/apps
2. Войдите под своим аккаунтом Telegram
3. Создайте приложение, скопируйте `api_id` и `api_hash`
4. Укажите их в `.env` вместе с номером телефона (`PHONE_NUMBER`)

#### Настройка AI-провайдера:
- **Бесплатно:** Gemini (Free Tier), OpenRouter (free-модели), Ollama (локально) или Кастомный (OpenAI-совместимый)
- **Платно:** OpenAI, Anthropic Claude, DeepSeek

### 4. Запустить бота

```bash
python -m bot.main
```

При первом запуске Telethon запросит код подтверждения (придёт в Telegram).

## Использование

| Команда/Кнопка | Описание |
|---|---|
| `/start` | Главное меню |
| 🔍 **Поиск сообщений** | Выбрать канал → дату → ввести ключевые слова |
| 📊 **Сводка за день** | Выбрать канал → дату → получить AI-сводку |
| ⚙️ **Настройки** | Выбрать AI-провайдера |

## Структура проекта

```
tg_bot_finder/
├── bot/
│   ├── main.py              # Точка входа
│   ├── config.py            # Конфигурация
│   ├── handlers/            # Обработчики команд
│   │   ├── start.py
│   │   ├── search.py
│   │   ├── summary.py
│   │   └── settings.py
│   ├── keyboards/           # Inline-клавиатуры
│   │   ├── main.py
│   │   ├── channels.py
│   │   ├── calendar.py
│   │   └── settings.py
│   ├── services/            # Бизнес-логика
│   │   ├── telegram_client.py  # Telethon
│   │   └── llm_service.py      # LiteLLM
│   └── storage/             # SQLite
│       ├── database.py
│       └── models.py
├── scripts/                 # Вспомогательные скрипты
│   └── encrypt_env.py       # Шифрование .env
├── data/                    # Сессии Telethon + БД
├── .env                     # Настройки (не в git)
├── .env.encrypted           # Зашифрованный .env (локально)
├── requirements.txt
└── README.md
```

## 🔒 Безопасность

### Защита чувствительных данных

Проект работает с критичными данными: токен бота, API-ключи AI-провайдеров,
а также **данные личного аккаунта Telegram** (`API_ID`, `API_HASH`, `PHONE_NUMBER`).
Их компрометация даёт злоумышленнику полный доступ к вашему аккаунту.

### Локальная разработка (WSL / Windows)

Для защиты `.env` файла на локальной машине используется **шифрование с мастер-паролем**.

#### Установка зависимостей

```bash
pip install -r requirements.txt
```

#### Использование скрипта шифрования

```bash
# Зашифровать .env → .env.encrypted (исходный .env удаляется)
python scripts/encrypt_env.py encrypt

# Расшифровать .env.encrypted → .env
python scripts/encrypt_env.py decrypt

# С мастер-паролем из переменной окружения (для автоматизации)
ENV_MASTER_PASSWORD=secret python scripts/encrypt_env.py encrypt
ENV_MASTER_PASSWORD=secret python scripts/encrypt_env.py decrypt
```

**Рекомендуемый workflow:**

```bash
# 1. Расшифровать .env
python scripts/encrypt_env.py decrypt

# 2. Запустить бота
python -m bot.main

# 3. После работы — зашифровать обратно
python scripts/encrypt_env.py encrypt
```

### Деплой на VPS (Linux)

Для серверного развёртывания рекомендуется использовать **переменные окружения ОС**
через `systemd` — это исключает хранение ключей в файлах проекта.

#### 1. Создать пользователя для бота

```bash
sudo useradd -r -s /bin/false tg_bot
```

#### 2. Создать директорию для секретов

```bash
sudo mkdir -p /etc/tg_bot_finder
sudo chmod 750 /etc/tg_bot_finder
```

#### 3. Создать файл с критичными секретами

```bash
sudo nano /etc/tg_bot_finder/secrets.env
```

```ini
# Только самые критичные данные — личный аккаунт Telegram
API_ID=1234567
API_HASH=abc123def456
PHONE_NUMBER=+79001234567
```

#### 4. Выставить правильные права доступа

```bash
sudo chown root:tg_bot /etc/tg_bot_finder/secrets.env
sudo chmod 640 /etc/tg_bot_finder/secrets.env
# 640 = root读写, tg_bot只读, остальные — ничего
```

#### 5. Создать systemd-сервис

```bash
sudo nano /etc/systemd/system/tg_bot_finder.service
```

```ini
[Unit]
Description=Telegram Bot Finder
After=network.target

[Service]
Type=simple
User=tg_bot
Group=tg_bot
WorkingDirectory=/opt/tg_bot_finder

# Критичные секреты — из защищённого файла
EnvironmentFile=/etc/tg_bot_finder/secrets.env

# Обычные настройки — из .env в рабочей директории
ExecStart=/usr/bin/python3 -m bot.main
Restart=always
RestartSec=10

# Безопасность
ProtectHome=true
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

#### 6. Развернуть проект

```bash
sudo mkdir -p /opt/tg_bot_finder
sudo chown tg_bot:tg_bot /opt/tg_bot_finder
git clone <repo> /opt/tg_bot_finder
```

#### 7. Создать `.env` только с некритичными данными

```bash
sudo -u tg_bot nano /opt/tg_bot_finder/.env
```

```ini
# Только то, что не критично
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
DEFAULT_AI_PROVIDER=gemini
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# API_ID, API_HASH, PHONE_NUMBER — НЕ ПИШЕМ! Они в /etc/tg_bot_finder/secrets.env
```

#### 8. Перенести session-файл Telethon ⚠️ ВАЖНО

Telethon авторизуется **один раз** и сохраняет сессию в файл `data/telegram_session.session`.
При первом запуске бота Telethon запросит **код подтверждения** из Telegram — это можно сделать
только в **интерактивном терминале**. В systemd-сервисе интерактивного ввода нет, поэтому
**сначала авторизуйтесь локально**, затем скопируйте session-файл на сервер.

**Способ 1: Перенос с локальной машины**

```bash
# 1. Локально запустите бота один раз для авторизации
python -m bot.main
# Telethon попросит ввести код → введите → сессия сохранена в data/telegram_session.session

# 2. Скопируйте session-файл на сервер
scp -P 10022 data/telegram_session.session root@your-server:/opt/tg_bot_finder/data/

# 3. На сервере выставьте права
sudo chown tg_bot:tg_bot /opt/tg_bot_finder/data/telegram_session.session
sudo chmod 600 /opt/tg_bot_finder/data/telegram_session.session
```

**Способ 2: Авторизация на сервере через tmux**

```bash
# 1. Подключитесь к серверу по SSH
ssh -p 10022 root@your-server

# 2. Запустите tmux
tmux new -s auth

# 3. Авторизуйтесь от имени tg_bot
sudo -u tg_bot /opt/tg_bot_finder/venv/bin/python -m bot.main
# Telethon попросит ввести код → введите → после запуска polling нажмите Ctrl+C

# 4. Отключитесь от tmux: Ctrl+B, затем D

# 5. Проверьте, что session создан
ls -la /opt/tg_bot_finder/data/telegram_session.session
# Должно быть: tg_bot tg_bot ~77-82KB
```

> **Почему нельзя просто запустить systemd?**
> Если session-файл отсутствует или недействителен, `client.start()` вызывает `input()`
> для ввода кода подтверждения. В systemd нет stdin → получаем `EOFError` и бот падает.
> Поэтому авторизация должна быть выполнена заранее в интерактивном терминале.

#### 9. Запустить сервис

```bash
sudo systemctl daemon-reload
sudo systemctl enable tg_bot_finder
sudo systemctl start tg_bot_finder
sudo systemctl status tg_bot_finder

# Проверить логи
journalctl -u tg_bot_finder -f
```

### Как это работает

Код в [`bot/config.py`](bot/config.py) использует `os.getenv()`, который читает переменные
в следующем порядке приоритета:

1. **Переменные окружения ОС** (из `EnvironmentFile` в systemd) — высший приоритет
2. **Переменные из `.env` файла** (через `load_dotenv()`) — низший приоритет

Таким образом, `API_ID`, `API_HASH` и `PHONE_NUMBER` берутся из защищённого
`/etc/tg_bot_finder/secrets.env`, а остальные настройки — из обычного `.env`.

**Менять код не требуется** — `os.getenv()` уже поддерживает эту логику.

### Структура файлов после настройки безопасности

```
tg_bot_finder/
├── .env                      # Некритичные настройки (в .gitignore)
├── .env.encrypted            # Зашифрованный .env (локально)
├── .gitignore
├── scripts/
│   └── encrypt_env.py        # Скрипт шифрования .env
├── bot/
│   ├── config.py             # Читает: ОС → .env
│   └── ...
└── data/
    └── telegram_session*     # Сессия Telethon (в .gitignore)
```

### Дополнительные меры

- **`.env` уже в `.gitignore`** — не попадёт в репозиторий
- **`data/telegram_session*` в `.gitignore`** — сессия Telethon не попадёт в git
- **Логи не содержат ключи** — проверено, в коде нет логирования секретов
- **Рекомендуется `chmod 600 .env`** на сервере — только владелец читает файл

## Управление сервисом tg_bot_finder на VPS

Все команды выполняются на сервере через SSH:

```bash
ssh -i C:\Users\sysadmin.ssh\id_ed25519 -p 10022 root@45.198.0.230
```

### Статус сервиса

```bash
# Проверить, работает ли бот
systemctl status tg_bot_finder

# Короткий ответ: active / inactive / failed
systemctl is-active tg_bot_finder
```

### Запуск / Остановка / Перезапуск

```bash
# Запустить бота
systemctl start tg_bot_finder

# Остановить бота
systemctl stop tg_bot_finder

# Перезапустить (stop + start)
systemctl restart tg_bot_finder

# Перезагрузить конфигурацию (без остановки, если код не менялся)
systemctl reload tg_bot_finder
```

### Автозапуск при загрузке сервера

```bash
# Включить автозапуск (сейчас уже включено)
systemctl enable tg_bot_finder

# Отключить автозапуск
systemctl disable tg_bot_finder

# Проверить статус автозапуска
systemctl is-enabled tg_bot_finder
```

### Просмотр логов

```bash
# Последние 50 строк логов
journalctl -u tg_bot_finder -n 50 --no-pager

# Логи в реальном времени (как tail -f)
journalctl -u tg_bot_finder -f

# Логи за сегодня
journalctl -u tg_bot_finder --since today --no-pager

# Логи за последний час
journalctl -u tg_bot_finder --since "1 hour ago" --no-pager

# Только ошибки
journalctl -u tg_bot_finder -p err --no-pager

# Логи конкретного запуска (после последнего перезапуска)
journalctl -u tg_bot_finder -n 100 --no-pager -o verbose
```

### Редактирование конфигурации

```bash
# Обычные настройки (AI-провайдер, токены API)
nano /opt/tg_bot_finder/.env

# Критичные секреты (API_ID, API_HASH, номер телефона)
nano /etc/tg_bot_finder/secrets.env

# После изменения — перезапустить сервис
systemctl restart tg_bot_finder
```

### Обновление кода проекта

```bash
# Перейти в директорию проекта
cd /opt/tg_bot_finder

# Обновить код из git
sudo -u tg_bot git pull

# Обновить зависимости (если requirements.txt изменился)
sudo -u tg_bot /opt/tg_bot_finder/venv/bin/pip install -r requirements.txt

# Перезапустить сервис
systemctl restart tg_bot_finder
```

### Быстрая диагностика (одной командой из Windows)

```bash
ssh -i C:\Users\sysadmin.ssh\id_ed25519 -p 10022 root@45.198.0.230 "systemctl status tg_bot_finder --no-pager && echo '---LOGS---' && journalctl -u tg_bot_finder -n 10 --no-pager"
```

### Проверка безопасности

```bash
# Права на секреты
ls -la /etc/tg_bot_finder/secrets.env   # Должно быть: root:tg_bot 640
ls -la /opt/tg_bot_finder/.env           # Должно быть: tg_bot:tg_bot 640
ls -la /opt/tg_bot_finder/data/telegram_session.session  # tg_bot:tg_bot 600

# Проверить, что сервис работает от tg_bot, а не root
ps aux | grep bot.main
```

## Docker (альтернативный деплой)

Проект также можно запустить в Docker-контейнере.

### Сборка образа

```bash
docker build -t tg_bot_finder .
```

### Запуск

```bash
# С передачей переменных окружения
docker run -d \
  --name tg_bot_finder \
  --restart unless-stopped \
  -v $(pwd)/data:/opt/tg_bot_finder/data \
  -v $(pwd)/.env:/opt/tg_bot_finder/.env:ro \
  -e API_ID=1234567 \
  -e API_HASH=abc123def456 \
  -e PHONE_NUMBER=+79001234567 \
  tg_bot_finder
```

Или с файлом переменных:

```bash
docker run -d \
  --name tg_bot_finder \
  --restart unless-stopped \
  -v $(pwd)/data:/opt/tg_bot_finder/data \
  --env-file /etc/tg_bot_finder/secrets.env \
  --env-file .env \
  tg_bot_finder
```

### Важно для Telethon

Перед первым запуском в Docker необходимо авторизовать Telethon:

```bash
# Запустите интерактивно для ввода кода подтверждения
docker run -it --rm \
  -v $(pwd)/data:/opt/tg_bot_finder/data \
  --env-file /etc/tg_bot_finder/secrets.env \
  --env-file .env \
  tg_bot_finder

# Введите код из Telegram → сессия сохранится в data/telegram_session.session
# После этого можно запускать в фоновом режиме (-d)
```

## Требования

- Python 3.10+
- Telegram аккаунт
- API ключ хотя бы одного AI-провайдера (или локальный Ollama)
- Для Docker: Docker Engine 20.10+

#!/usr/bin/env python3
"""
Скрипт для шифрования/дешифрования .env файла.

Использование:
    # Зашифровать .env → .env.encrypted
    python scripts/encrypt_env.py encrypt

    # Расшифровать .env.encrypted → .env
    python scripts/encrypt_env.py decrypt

    # С мастер-паролем из переменной окружения (для автоматизации)
    ENV_MASTER_PASSWORD=secret python scripts/encrypt_env.py encrypt
    ENV_MASTER_PASSWORD=secret python scripts/encrypt_env.py decrypt

Внимание: после расшифровки не забывайте удалять .env или
использовать автозапуск с мастер-паролем из переменной ОС.

Для смены пароля используйте две команды:
    ENV_MASTER_PASSWORD=старый_пароль python scripts/encrypt_env.py decrypt
    ENV_MASTER_PASSWORD=новый_пароль  python scripts/encrypt_env.py encrypt
"""

import base64
import getpass
import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Константы
SALT_SIZE = 16  # байт
ENCODED_SALT_SIZE = 24  # base64-представление salt (16 байт → 24 символа)
ITERATIONS = 600_000  # итераций PBKDF2 (рекомендация OWASP 2024)


def _derive_key(password: str, salt: bytes) -> bytes:
    """Создаёт ключ Fernet из пароля и соли через PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt() -> None:
    """Шифрует .env в .env.encrypted."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден в текущей директории.")
        print("   Создайте .env из .env.example: copy .env.example .env")
        sys.exit(1)

    # Пароль: сначала из переменной ОС, потом запрос ввода
    password = os.environ.get("ENV_MASTER_PASSWORD")
    if not password:
        password = getpass.getpass("🔐 Мастер-пароль для шифрования: ")
        confirm = getpass.getpass("🔐 Повторите пароль: ")
        if password != confirm:
            print("❌ Пароли не совпадают.")
            sys.exit(1)

    # Генерируем соль
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)

    # Читаем и шифруем .env
    data = env_path.read_bytes()
    encrypted = Fernet(key).encrypt(data)

    # Сохраняем: [base64_salt][encrypted_data]
    encoded_salt = base64.urlsafe_b64encode(salt)
    enc_path = Path(".env.encrypted")
    enc_path.write_bytes(encoded_salt + encrypted)

    # Удаляем исходный .env
    env_path.unlink()

    print(f"✅ .env зашифрован → {enc_path}")
    print(f"   Исходный .env удалён.")
    print(f"   Для расшифровки: python scripts/encrypt_env.py decrypt")


def decrypt() -> None:
    """Расшифровывает .env.encrypted в .env."""
    enc_path = Path(".env.encrypted")
    if not enc_path.exists():
        print("❌ Файл .env.encrypted не найден.")
        print("   Сначала зашифруйте: python scripts/encrypt_env.py encrypt")
        sys.exit(1)

    # Пароль: сначала из переменной ОС, потом запрос ввода
    password = os.environ.get("ENV_MASTER_PASSWORD")
    if not password:
        password = getpass.getpass("🔐 Мастер-пароль для расшифровки: ")

    # Читаем файл
    data = enc_path.read_bytes()

    # Извлекаем salt (первые ENCODED_SALT_SIZE байт — base64)
    encoded_salt = data[:ENCODED_SALT_SIZE]
    encrypted_data = data[ENCODED_SALT_SIZE:]

    try:
        salt = base64.urlsafe_b64decode(encoded_salt)
    except Exception:
        print("❌ Файл .env.encrypted повреждён (неверный формат salt).")
        sys.exit(1)

    key = _derive_key(password, salt)

    try:
        decrypted = Fernet(key).decrypt(encrypted_data)
    except Exception:
        print("❌ Неверный мастер-пароль или файл повреждён.")
        sys.exit(1)

    # Записываем .env
    env_path = Path(".env")
    env_path.write_bytes(decrypted)

    print(f"✅ .env расшифрован → {env_path}")
    print(f"   Запускайте бота: python -m bot.main")
    print(f"   ⚠️  После работы зашифруйте обратно: python scripts/encrypt_env.py encrypt")


def main() -> None:
    """Точка входа."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "encrypt":
        encrypt()
    elif command == "decrypt":
        decrypt()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("   Используйте: encrypt или decrypt")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Веб-Форум на Flask

Веб-форум с аутентификацией пользователей, системой публикаций и комментариев, написанный на Flask.

## Возможности

- 👤 Система пользователей
  - Регистрация и авторизация
  - Профили пользователей
  - Роли (пользователь/администратор)

- 📝 Публикации
  - Создание постов
  - Редактирование своих постов
  - Удаление своих постов
  - Комментарии к постам

- 👑 Панель администратора
  - Управление пользователями
  - Управление публикациями
  - Статистика форума

- 🎨 Интерфейс
  - Адаптивный дизайн
  - Bootstrap 5
  - Поддержка русского языка

## Технологии

- Python 3.11
- Flask 2.3.3
- Flask-SQLAlchemy 3.0.5
- Flask-Login 0.6.2
- SQLite
- Bootstrap 5.1.3
- Bootstrap Icons

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/stmnbxll/forum.base.git
cd forum.base
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите приложение:
```bash
python app.py
```

5. Откройте браузер и перейдите по адресу `http://localhost:5000`

## Структура проекта

```
forum.base/
├── app.py              # Основной файл приложения
├── requirements.txt    # Зависимости проекта
├── forum.db           # База данных SQLite
└── templates/         # HTML шаблоны
    ├── admin.html     # Панель администратора
    ├── base.html      # Базовый шаблон
    ├── home.html      # Главная страница
    ├── login.html     # Страница входа
    ├── register.html  # Страница регистрации
    ├── post.html      # Просмотр поста
    └── create_post.html # Создание поста
```

## Администратор по умолчанию

- Логин: admin
- Email: admin@example.com
- Пароль: 123456

*Рекомендуется сменить данные в файле app.py*

## Лицензия

MIT License
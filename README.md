# FitTrack

Мобільний застосунок для фітнес-клубу на Python + Kivy. Підтримує чотири ролі (клієнт, тренер, адмін/директор, технік) з відповідними інтерфейсами: розклад занять, абонементи з заявками на покупку, відео-тренування з коментарями, СКУД-картка з QR-кодом, журнал обладнання.

## Вимоги

- Python 3.10+ (тестовано на 3.11)
- Windows / macOS / Linux для запуску на десктопі
- Android SDK + Buildozer для збірки APK (опціонально)

## Запуск

1. Створіть та активуйте віртуальне середовище:

   ```
   python -m venv .venv
   .venv\Scripts\activate            (Windows)
   source .venv/bin/activate         (macOS / Linux)
   ```

2. Встановіть залежності:

   ```
   pip install -r requirements.txt
   ```

3. Запустіть застосунок:

   ```
   python main.py
   ```

При першому запуску в `data/fittrack.db` створюється SQLite-схема й сід-дані (демо-користувачі, тарифи, заняття).

## Стартовий акаунт

Сід створює лише одного користувача — адміна. Всіх інших (тренерів, клієнтів, директорів, техніків) адмін додає та призначає ролі через вкладку `КОРИСТУВАЧІ`.

| Роль  | Email         | Пароль   |
|-------|---------------|----------|
| Адмін | admin@gym.ua  | admin123 |

## Збірка Android APK

```
pip install buildozer
buildozer android debug
```

Налаштування — у `buildozer.spec`.

## Структура проєкту

```
FitTrack/
    main.py                          точка входу, налаштування вікна, фільтр логів
    requirements.txt                 залежності pip
    buildozer.spec                   конфігурація Android-збірки
    README.md
    .gitignore
    app/
        __init__.py
        auth.py                      хешування паролів, Session, authenticate
        navigation.py                ScreenManager з go/fade_to/go_home
        theme.py                     кольори, шрифти, токени дизайну
        database/
            __init__.py
            db.py                    SQLite connection, init + міграції
            schema.sql               схема таблиць
            seed.py                  демо-дані для першого запуску
            repos.py                 шар репозиторіїв (User, Subscription, Schedule, Equipment, Video, Comment, Analytics)
            thumbnails.py            витяг першого кадру відео в JPG
        screens/
            __init__.py              реєстр екранів
            _layout.py               TopBar + рольовий BottomNav + screen_shell
            splash.py                заставка, автоперехід
            login.py                 екран авторизації
            home_client.py           головна клієнта (hero-карта абонементу, записи)
            home_trainer.py          головна тренера (статистика, заняття, аплоад відео)
            home_admin.py            адмін-панель (KPI, платежі, обладнання, керування)
            schedule.py              розклад занять, бронювання / видалення
            subscriptions.py         тарифи, покупка через заявку, керування абонементами
            subscription_requests.py заявки на абонемент - підтвердження / відхилення
            users.py                 список користувачів, зміна ролі, видалення
            equipment.py             інвентар, заявки на ремонт, позначення справним
            video_feed.py            стрічка відео, пошук, фільтр за категорією
            video_detail.py          плеєр, прогрес-бар, лайк, коментарі
            profile.py               профіль, QR-картка СКУД, вихід
        widgets/
            __init__.py
            animated_bg.py           анімований неоновий фон
            glass_card.py            glass-morphism картка
            neon_button.py           NeonButton / GhostButton / DangerButton
            status_chip.py           бейдж статусу (active / frozen / fault)
            pulse_ring.py            кільце прогресу для днів абонементу
            icon_button.py           CheckIcon / CrossIcon / MinusIcon
    assets/
        fonts/                       DejaVuSans для кирилиці
        icons/                       іконки
        illustrations/               ілюстрації
    data/
        fittrack.db                  створюється на першому запуску, ігнорується git
        videos/                      завантажені тренером відео, ігноруються git
        thumbnails/                  згенеровані прев'ю кадрів, ігноруються git
    docs/
        screenshots/                 скріншоти екранів
```

## Технічні деталі

- БД — SQLite (one-file `data/fittrack.db`), нормалізована схема в 3НФ із зовнішніми ключами. Міграції в `db._run_migrations` додають таблиці, які з'явились після першого релізу (`subscription_requests`).
- Аутентифікація — bcrypt, з fallback на sha256 (якщо bcrypt недоступний). Сесія — синглтон у `auth.Session`.
- Відео — `kivy.uix.video.Video` через ffpyplayer, з `eos="loop"` для повторного відтворення, тихий хвіст для файлів з битими DTS. Прогрес-бар — read-only.
- QR СКУД — генерується з `users.card_id_skud` через бібліотеку `qrcode`, рендериться в PNG потім у текстуру Kivy.
- Заявки на покупку — клієнт натискає `ПРИДБАТИ` потім підтвердження потім запис у `subscription_requests`. Адмін у вкладці `ЗАЯВКИ` підтверджує потім `SubscriptionRepo.sell` створює одночасно `subscriptions` і `payments`, що автоматично відображається в KPI та стрічці платежів.
- Видалення відео — `VideoRepo.delete` каскадно прибирає файл `.mp4` і thumbnail `.jpg` з диска плюс рядок з БД (лайки і коментарі — каскад FK).

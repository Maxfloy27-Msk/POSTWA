# POSTWA — Telegram-бот [@AutoWA27_bot](https://t.me/AutoWA27_bot)

Бот реализует поток из схемы:

```
/start → "Что вы хотите написать сегодня?" → текст пользователя
       → SMM WINNI2 (генерация постов)
       → готовые посты ⇒ параллельно:
            • отправить пользователю в чат
            • отправить в Auto_post_WA
       → Завершено
```

## Запуск

1. Бот: [@AutoWA27_bot](https://t.me/AutoWA27_bot). Токен выдаётся у [@BotFather](https://t.me/BotFather) (`/token`).
2. Скопируйте `.env.example` в `.env` и заполните переменные:
   - `BOT_TOKEN` — токен Telegram-бота
   - `SMM_WINNI2_URL` — URL вебхука, который принимает `{user_id, text}` и возвращает список постов
   - `AUTO_POST_WA_URL` — URL вебхука Auto_post_WA, принимает `{user_id, posts}`
3. Установите зависимости и запустите:

```bash
pip install -r requirements.txt
python bot.py
```

## Контракты вебхуков

### SMM WINNI2 (входящий запрос)
```json
POST /smm-winni2
{ "user_id": 123456, "text": "Тема поста от пользователя" }
```

Ответ принимается в любом из форматов:
- `["пост 1", "пост 2"]`
- `{"posts": ["пост 1", "пост 2"]}`
- `{"result": "один пост"}`
- `"один пост"`

### Auto_post_WA (исходящий запрос)
```json
POST /auto-post-wa
{ "user_id": 123456, "posts": ["пост 1", "пост 2"] }
```

## Структура

- `bot.py` — обработчики Telegram, FSM, точка входа
- `services.py` — интеграции с SMM WINNI2 и Auto_post_WA, параллельная доставка
- `config.py` — загрузка переменных окружения

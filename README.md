# HATTORI AI Assistant — backend

HATTORI — backend AI-ассистента для барбершопа. Сейчас это технический прототип: реализованы базовая модель данных, жизненный цикл записей, Event-журнал и изолированный HTTP-клиент Altegio. Реальные API-вызовы Altegio не проверялись из-за отсутствия credentials.

## Текущий статус проекта

### Реализовано

- FastAPI backend с endpoint `GET /health`, возвращающим `{"status": "ok"}`.
- PostgreSQL, SQLAlchemy, Alembic, Docker и Docker Compose.
- Конфигурация через environment variables.
- Модель `Customer`: нормализация номера телефона, включая казахстанские номера с начальной `8`, и уникальность нормализованного номера.
- Модель `Booking`, связанная с клиентом, со статусами: `SELECTED`, `BOOKED`, `CONFIRMED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`.
- `BookingStateTransition` для истории переходов состояния с датой и инициатором.
- `BookingService` с разрешёнными переходами:
  - `SELECTED → BOOKED`;
  - `BOOKED → CONFIRMED | CANCELLED | NO_SHOW | COMPLETED`;
  - `CONFIRMED → CANCELLED | NO_SHOW | COMPLETED`.
- Запрет остальных переходов и идемпотентность повторного перехода в текущее состояние.
- Увеличение `Customer.visit_count` только при первом переходе в `COMPLETED`.
- Перенос: старая запись становится `CANCELLED`, новая создаётся в `BOOKED` и связана с исходной.
- Event-журнал для аудита и разбора инцидентов; `BookingService` автоматически создаёт Event в той же транзакции.
- Базовый `AltegioClient` с методами получения услуг, мастеров, свободных слотов, создания и отмены записи.
- Mock HTTP-тесты для AltegioClient и unit-тесты текущей бизнес-логики.

### Пока не реализовано

- Реальное подключение к Altegio.
- GreenAPI.
- WhatsApp.
- OpenAI.
- AI-диалог.
- База знаний.
- Scheduler.
- Напоминания.
- Обратная связь.
- Бонусы.
- Жалобы и эскалации.
- Стоп-слова.
- Лист ожидания.
- Возврат клиентов.
- Instagram.
- Сайт RU/KZ.
- Аналитические отчёты.

## Требования

- Python 3.12+
- Docker и Docker Compose — для контейнерного запуска

## Запуск через Docker Compose

1. Создайте файл локального окружения:

   ```bash
   cp .env.example .env
   ```

   В Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Укажите в `.env` непубличное значение `POSTGRES_PASSWORD`.

3. Запустите API и PostgreSQL:

   ```bash
   docker compose up --build
   ```

4. Проверьте API:

   ```bash
   curl http://localhost:8000/health
   ```

   Ожидаемый ответ:

   ```json
   {"status": "ok"}
   ```

5. Примените миграции:

   ```bash
   docker compose exec api alembic upgrade head
   ```

## Локальный запуск через Python

1. Создайте виртуальное окружение и установите проект с зависимостями для разработки:

   ```bash
   python -m venv .venv
   .venv/bin/pip install -e ".[dev]"
   ```

   В Windows PowerShell:

   ```powershell
   .\.venv\Scripts\python -m pip install -e ".[dev]"
   ```

2. Запустите PostgreSQL:

   ```bash
   docker compose up -d db
   ```

3. Скопируйте `.env.example` в `.env`, задайте `POSTGRES_PASSWORD` и укажите локальный `DATABASE_URL` по примеру в файле окружения.

4. Примените миграции:

   ```bash
   alembic upgrade head
   ```

5. Запустите API:

   ```bash
   uvicorn app.main:app --reload
   ```

## Миграции Alembic

Alembic использует `DATABASE_URL` из environment variables.

Применить существующие миграции:

```bash
alembic upgrade head
```

После изменения ORM-моделей создать и применить новую миграцию:

```bash
alembic revision --autogenerate -m "описание изменения"
alembic upgrade head
```

## Тесты

Запуск полного набора тестов:

```bash
pytest
```

В Windows PowerShell при использовании локального окружения:

```powershell
.\.venv\Scripts\python -m pytest
```

## Что потребуется для продолжения

### Altegio

Интеграция подготовлена и покрыта mock-тестами, но реальные API-вызовы не проверялись. Для подключения понадобятся:

- Partner Token;
- User Token, если он необходим выбранной версии API;
- Location ID / Branch ID;
- подтверждение версии Altegio API;
- реальные endpoint paths для услуг, мастеров, слотов, создания и отмены записи;
- права доступа для выбранного способа авторизации.

Значения клиента вынесены в environment variables. В `.env.example` есть только placeholders; реальные credentials в репозиторий не добавляются.

### GreenAPI

- Instance ID;
- API token;
- рабочий номер WhatsApp;
- рабочая группа для эскалаций.

### OpenAI

- API key;
- база знаний HATTORI;
- прайс;
- описание услуг;
- характеристики мастеров;
- правила акций и скидок.


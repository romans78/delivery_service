# Delivery Service API
Этот проект предоставляет API для управления посылками, включая регистрацию, отслеживание и расчет стоимости доставки. Сервис построен на FastAPI с использованием асинхронных операций и включает интеграцию с MySQL и Redis.
Ссылка на описание тестового задания - https://docs.google.com/document/d/1WoL-ysivtlwzbRFwqUfETMSmFOUw9Wpnf0P1ewIW89E/edit?tab=t.0
## Особенности
* Регистрация новых посылок

* Получение списка типов посылок

* Фильтрация посылок по типу и статусу расчета стоимости

* Расчет стоимости доставки в фоновом режиме

* Обновление курса USD в реальном времени

* Документация API через Swagger UI

* Поддержка пагинации результатов

## Технологический стек
* Python 3.11

* FastAPI - веб-фреймворк

* SQLAlchemy 2.0 - ORM

* MySQL - база данных

* Redis - кэширование

* Alembic - управление миграциями базы данных

* Docker - контейнеризация

* Pytest - тестирование

## Запуск проекта
### Требования
* Docker

* Docker Compose

## Инструкция по запуску
1. Клонируйте репозиторий:
   * git clone https://github.com/romans78/delivery_service.git
   * cd delivery-service
2. Запустите сервисы:
    * docker-compose up app --build
3. Swagger будет доступен по адресу: http://localhost:8888/api/v1/docs

### Основные эндпоинты
* POST /api/v1/package - Регистрация новой посылки

* GET /api/v1/package_types - Получение списка типов посылок

* GET /api/v1/packages - Получение списка посылок с фильтрацией

* GET /api/v1/package/{package_id} - Получение информации о посылке по id

* POST /api/v1/tasks/refresh_usd_rate - Обновление курса USD по запросу

* POST /api/v1/tasks/calculate_delivery_cost - Расчет стоимости доставки по запросу

## Запуск тестов
Для запуска тестов выполните:
* docker-compose up tests --build

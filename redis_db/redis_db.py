import requests
import redis
from datetime import datetime, timedelta
import json



def get_usd_rub_rate():
    # Подключение к Redis (настройте параметры подключения при необходимости)
    r = redis.Redis(host='localhost', port=6379, db=0)

    # Формируем ключ для сегодняшней даты (например: 'usd_rate:2025-06-02')
    today_key = f"usd_rate:{datetime.now().strftime('%Y-%m-%d')}"

    # Пытаемся получить кешированное значение
    cached_rate = r.get(today_key)
    if cached_rate:
        return float(cached_rate.decode('utf-8'))

    try:
        # Запрос к API ЦБ РФ
        response = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()

        # Извлекаем курс USD
        usd_rate = data['Valute']['USD']['Value']

        # Кешируем курс до конца текущих суток (по МСК)
        expire_seconds = calculate_seconds_until_midnight()
        r.set(today_key, usd_rate, ex=expire_seconds)

        return usd_rate
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        # Обработка ошибок (можно добавить fallback-логику)
        raise ValueError(f"Ошибка при получении курса: {str(e)}")


def calculate_seconds_until_midnight():
    """Вычисляет количество секунд до конца суток по московскому времени."""
    tz_moscow = timedelta(hours=3)  # UTC+3 для Москвы
    now_utc = datetime.utcnow()
    now_moscow = now_utc + tz_moscow

    # Следующая полночь по МСК
    next_midnight = (now_moscow + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int((next_midnight - now_moscow).total_seconds())


# Пример использования
if __name__ == "__main__":
    try:
        rate = get_usd_rub_rate()
        print(f"Курс USD/RUB: {rate}")
    except Exception as e:
        print(str(e))
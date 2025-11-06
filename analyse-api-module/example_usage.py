"""
Пример использования API.
"""
import requests
import json

# Базовый URL API
BASE_URL = "http://localhost:8000"

# Тестовые данные
test_reviews = [
    "Отличный товар! Качество на высоте, очень доволен покупкой. Рекомендую всем.",
    "Хороший продукт за свою цену. Работает как надо, никаких нареканий.",
    "Не очень понравилось. Качество среднее, ожидал большего за такую цену.",
    "Прекрасное качество! Покупкой очень доволен, все работает отлично.",
    "Товар нормальный, но есть небольшие недочеты. В целом можно брать."
]


def example_usage():
    """Пример использования API."""
    
    # 1. Получаем токен
    print("1. Получение токена...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"Ошибка входа: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"Токен получен: {token[:20]}...")
    
    # 2. Проверяем информацию о пользователе
    print("\n2. Проверка информации о пользователе...")
    headers = {"Authorization": f"Bearer {token}"}
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Пользователь: {me_response.json()}")
    
    # 3. Анализируем отзывы
    print("\n3. Анализ отзывов...")
    analysis_response = requests.post(
        f"{BASE_URL}/analyze/reviews",
        headers=headers,
        json={
            "reviews": test_reviews,
            "product_id": "test-product-123"
        }
    )
    
    if analysis_response.status_code == 200:
        result = analysis_response.json()
        print("\nРезультат анализа:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Ошибка анализа: {analysis_response.text}")


if __name__ == "__main__":
    example_usage()


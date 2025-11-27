#!/usr/bin/env python3
"""
Скрипт для скачивания ML моделей из Hugging Face
"""

from huggingface_hub import snapshot_download
from pathlib import Path
import os

def download_models():
    """Скачивание моделей для анализа отзывов"""
    
    # Создание папок
    models_dir = Path("models")
    sentiment_dir = models_dir / "sentiment"
    summarizer_dir = models_dir / "summarizer"
    
    sentiment_dir.mkdir(parents=True, exist_ok=True)
    summarizer_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Скачивание ML моделей для Market Analytics")
    print("=" * 60)
    
    # Модель для тональности
    print("\n1. Скачивание модели тональности...")
    print("   Модель: blanchefort/rubert-base-cased-sentiment")
    print("   Размер: ~500 MB")
    try:
        snapshot_download(
            repo_id="blanchefort/rubert-base-cased-sentiment",
            local_dir=str(sentiment_dir),
            local_dir_use_symlinks=False
        )
        print("   ✓ Модель тональности успешно скачана!")
    except Exception as e:
        print(f"   ✗ Ошибка при скачивании модели тональности: {e}")
        return False
    
    # Модель для суммаризации
    print("\n2. Скачивание модели суммаризации...")
    print("   Модель: IlyaGusev/rut5_base_sum_gazeta")
    print("   Размер: ~500 MB")
    
    # Пробуем несколько вариантов
    summarizer_models = [
        "IlyaGusev/rut5_base_sum_gazeta",
        "IlyaGusev/rut5_base_sum_gazeta_v2",
        "cointegrated/rut5-base",
    ]
    
    success = False
    for model_name in summarizer_models:
        try:
            print(f"   Попытка: {model_name}")
            snapshot_download(
                repo_id=model_name,
                local_dir=str(summarizer_dir),
                local_dir_use_symlinks=False
            )
            print(f"   ✓ Модель суммаризации успешно скачана: {model_name}")
            success = True
            break
        except Exception as e:
            if model_name != summarizer_models[-1]:
                print(f"   Не удалось, пробую альтернативу...")
                continue
            print(f"   ✗ Ошибка при скачивании модели суммаризации: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("Все модели успешно скачаны!")
    print("=" * 60)
    print(f"\nМодели находятся в папке: {models_dir.absolute()}")
    print("\nТеперь можно запустить приложение:")
    print("  docker-compose up --build")
    
    return True

if __name__ == "__main__":
    try:
        download_models()
    except KeyboardInterrupt:
        print("\n\nСкачивание прервано пользователем")
    except Exception as e:
        print(f"\n\nКритическая ошибка: {e}")


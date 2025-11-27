#!/usr/bin/env python3
"""
Скрипт для скачивания РЕКОМЕНДУЕМЫХ ML моделей для Market Analytics

Рекомендации основаны на балансе качества, скорости и размера для русского языка.
"""

from huggingface_hub import snapshot_download
from pathlib import Path
import os

def download_recommended_models():
    """Скачивание рекомендуемых моделей - оптимальный баланс качества и скорости"""
    
    # Создание папок
    models_dir = Path("models")
    sentiment_dir = models_dir / "sentiment"
    summarizer_dir = models_dir / "summarizer"
    
    sentiment_dir.mkdir(parents=True, exist_ok=True)
    summarizer_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Скачивание РЕКОМЕНДУЕМЫХ ML моделей для Market Analytics")
    print("=" * 70)
    print("\n📊 Выбраны модели с оптимальным балансом:")
    print("   ✓ Качество анализа")
    print("   ✓ Скорость работы")
    print("   ✓ Размер моделей")
    print("   ✓ Поддержка русского языка")
    print()
    
    # ============================================
    # МОДЕЛЬ ТОНАЛЬНОСТИ - РЕКОМЕНДУЕМАЯ
    # ============================================
    print("=" * 70)
    print("1️⃣  МОДЕЛЬ ДЛЯ ТОНАЛЬНОСТИ")
    print("=" * 70)
    print()
    print("📦 Модель: blanchefort/rubert-base-cased-sentiment")
    print("   ⭐ Рейтинг: 5/5 (лучшая для русского языка)")
    print("   📏 Размер: ~500 MB")
    print("   ⚡ Скорость: Быстрая")
    print("   🎯 Классы: 3 (negative, neutral, positive)")
    print("   🇷🇺 Язык: Русский (специализированная)")
    print()
    print("   ✅ Преимущества:")
    print("      • Специально обучена для определения тональности")
    print("      • Отличное качество на русских текстах")
    print("      • Стабильные результаты")
    print("      • Активно используется в продакшене")
    print()
    
    try:
        snapshot_download(
            repo_id="blanchefort/rubert-base-cased-sentiment",
            local_dir=str(sentiment_dir),
            local_dir_use_symlinks=False
        )
        print("   ✅ Модель тональности успешно скачана!")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # ============================================
    # МОДЕЛЬ СУММАРИЗАЦИИ - РЕКОМЕНДУЕМАЯ
    # ============================================
    print()
    print("=" * 70)
    print("2️⃣  МОДЕЛЬ ДЛЯ СУММАРИЗАЦИИ")
    print("=" * 70)
    print()
    print("📦 Модель: IlyaGusev/rut5_base_sum_gazeta")
    print("   ⭐ Рейтинг: 5/5 (лучшая для русского языка)")
    print("   📏 Размер: ~500 MB")
    print("   ⚡ Скорость: Средняя (но качество отличное)")
    print("   🎯 Тип: T5-based (seq2seq)")
    print("   🇷🇺 Язык: Русский (специализированная)")
    print()
    print("   ✅ Преимущества:")
    print("      • Специально обучена для суммаризации")
    print("      • Отличное качество на русских текстах")
    print("      • Хорошо работает с длинными текстами")
    print("      • Проверенная и доступная модель")
    print()
    
    # Пробуем несколько вариантов моделей
    summarizer_models = [
        "IlyaGusev/rut5_base_sum_gazeta",  # Основная рекомендация
        "IlyaGusev/rut5_base_sum_gazeta_v2",  # Альтернатива
        "cointegrated/rut5-base",  # Более общая модель
    ]
    
    success = False
    for model_name in summarizer_models:
        try:
            print(f"   Попытка скачать: {model_name}")
            snapshot_download(
                repo_id=model_name,
                local_dir=str(summarizer_dir),
                local_dir_use_symlinks=False
            )
            print(f"   ✅ Модель суммаризации успешно скачана: {model_name}")
            success = True
            break
        except Exception as e:
            print(f"   ⚠️  Не удалось: {e}")
            if model_name != summarizer_models[-1]:
                print(f"   Пробую альтернативу...")
            continue
    
    if not success:
        print(f"   ❌ Не удалось скачать ни одну модель суммаризации")
        print(f"   💡 Попробуйте скачать вручную или используйте другую модель")
        return False
    
    # ============================================
    # ИТОГИ
    # ============================================
    print()
    print("=" * 70)
    print("✅ ВСЕ МОДЕЛИ УСПЕШНО СКАЧАНЫ!")
    print("=" * 70)
    print()
    print(f"📁 Модели находятся в: {models_dir.absolute()}")
    print()
    print("🚀 Теперь можно запустить приложение:")
    print("   docker-compose up --build")
    print()
    print("💡 Общий размер скачанных моделей: ~1 GB")
    print("⏱️  Время загрузки зависит от скорости интернета")
    print()
    
    return True


def download_lightweight_models():
    """Альтернатива: легкие модели (быстрее, но чуть хуже качество)"""
    
    models_dir = Path("models")
    sentiment_dir = models_dir / "sentiment"
    summarizer_dir = models_dir / "summarizer"
    
    sentiment_dir.mkdir(parents=True, exist_ok=True)
    summarizer_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Скачивание ЛЕГКИХ моделей (быстрее, меньше размер)")
    print("=" * 70)
    print()
    
    # Легкая модель тональности
    print("1. Тональность: cointegrated/rubert-tiny2 (~60 MB)")
    try:
        snapshot_download(
            repo_id="cointegrated/rubert-tiny2",
            local_dir=str(sentiment_dir),
            local_dir_use_symlinks=False
        )
        print("   ✅ Скачано")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Легкая модель суммаризации
    print("2. Суммаризация: IlyaGusev/rut5_base_sum_gazeta (~500 MB)")
    summarizer_models = [
        "IlyaGusev/rut5_base_sum_gazeta",
        "IlyaGusev/rut5_base_sum_gazeta_v2",
        "cointegrated/rut5-base",
    ]
    
    success = False
    for model_name in summarizer_models:
        try:
            snapshot_download(
                repo_id=model_name,
                local_dir=str(summarizer_dir),
                local_dir_use_symlinks=False
            )
            print(f"   ✅ Скачано: {model_name}")
            success = True
            break
        except Exception as e:
            if model_name != summarizer_models[-1]:
                continue
            print(f"   ❌ Ошибка: {e}")
            return False
    
    print("\n✅ Легкие модели скачаны!")
    return True


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("🎯 ВЫБОР МОДЕЛЕЙ")
    print("=" * 70)
    print()
    print("1. РЕКОМЕНДУЕМЫЕ (лучшее качество) - ~1 GB")
    print("2. ЛЕГКИЕ (быстрее, меньше размер) - ~560 MB")
    print()
    
    choice = input("Выберите вариант (1 или 2, Enter = 1): ").strip()
    
    if choice == "2":
        success = download_lightweight_models()
    else:
        success = download_recommended_models()
    
    if not success:
        print("\n❌ Произошла ошибка при скачивании моделей")
        sys.exit(1)


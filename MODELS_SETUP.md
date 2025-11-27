# Установка ML Моделей

Перед запуском приложения необходимо скачать и разместить обученные ML модели.

## Структура папок

Создайте следующую структуру в папке `models/`:

```
models/
├── sentiment/          # Модель для определения тональности
│   ├── config.json
│   ├── pytorch_model.bin (или model.safetensors)
│   ├── tokenizer_config.json
│   ├── vocab.json
│   └── merges.txt (если используется BPE)
└── summarizer/         # Модель для суммаризации
    ├── config.json
    ├── pytorch_model.bin (или model.safetensors)
    ├── tokenizer_config.json
    └── ...
```

## Рекомендуемые модели

### Для тональности (sentiment)

**Вариант 1: rubert-tiny2 (рекомендуется)**
- Легкая и быстрая модель
- Хорошее качество для русского языка
- Размер: ~60 MB

```bash
# Установка Hugging Face CLI
pip install huggingface_hub

# Скачивание модели
huggingface-cli download cointegrated/rubert-tiny2 --local-dir models/sentiment
```

**Вариант 2: blanchefort/rubert-base-cased-sentiment**
- Специализированная модель для тональности
- Больше размер, но лучше качество
- Размер: ~500 MB

```bash
huggingface-cli download blanchefort/rubert-base-cased-sentiment --local-dir models/sentiment
```

### Для суммаризации (summarizer)

**Вариант 1: rut5-base-summarizer (рекомендуется)**
- Специализированная модель для суммаризации
- Хорошее качество для русского языка
- Размер: ~500 MB

```bash
huggingface-cli download cointegrated/rut5-base-summarizer --local-dir models/summarizer
```

**Вариант 2: rubert-tiny2 (универсальная)**
- Можно использовать одну модель для обеих задач
- Меньше размер, но качество суммаризации ниже

```bash
huggingface-cli download cointegrated/rubert-tiny2 --local-dir models/summarizer
```

## Альтернативный способ (Python скрипт)

Создайте файл `download_models.py` в корне проекта:

```python
from huggingface_hub import snapshot_download

# Скачивание модели тональности
print("Скачивание модели тональности...")
snapshot_download(
    repo_id="cointegrated/rubert-tiny2",
    local_dir="models/sentiment",
    local_dir_use_symlinks=False
)

# Скачивание модели суммаризации
print("Скачивание модели суммаризации...")
snapshot_download(
    repo_id="cointegrated/rut5-base-summarizer",
    local_dir="models/summarizer",
    local_dir_use_symlinks=False
)

print("Модели успешно скачаны!")
```

Запустите:
```bash
pip install huggingface_hub
python download_models.py
```

## Проверка установки

После скачивания моделей проверьте, что файлы на месте:

```bash
ls -la models/sentiment/
ls -la models/summarizer/
```

## Важные замечания

1. **Размер моделей**: Модели могут занимать от 100 MB до 2 GB каждая. Убедитесь, что у вас достаточно места на диске.

2. **Права доступа**: Убедитесь, что Docker контейнер имеет доступ к папке `models/` (она монтируется через volume в docker-compose.yml).

3. **Версии**: Модели будут автоматически загружены при старте сервиса `analyzer-service`. Если локальные модели не найдены, будут использованы модели по умолчанию из Hugging Face (но это медленнее).

4. **Дообучение**: Если вы хотите дообучить модели, разместите дообученные версии в соответствующих папках. Структура файлов должна остаться такой же.

## Использование своих моделей

Если у вас есть свои обученные модели:

1. Сохраните их в формате Hugging Face (используя `model.save_pretrained()` и `tokenizer.save_pretrained()`)
2. Разместите в соответствующих папках `models/sentiment/` или `models/summarizer/`
3. Убедитесь, что структура файлов соответствует ожидаемой (config.json, pytorch_model.bin, tokenizer файлы)

## Troubleshooting

**Проблема**: Модели не загружаются
- Проверьте пути в `docker-compose.yml` (volume `./models:/app/models`)
- Убедитесь, что файлы моделей действительно находятся в папке `models/`
- Проверьте логи контейнера `analyzer-service`: `docker-compose logs analyzer-service`

**Проблема**: Ошибка памяти при загрузке моделей
- Используйте более легкие модели (rubert-tiny2 вместо rubert-base)
- Увеличьте память для Docker контейнера
- Используйте модели в формате `safetensors` вместо `pytorch_model.bin`


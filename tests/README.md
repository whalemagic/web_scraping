# Тесты для Web Scraping Service

## Структура тестов

```
tests/
├── fixtures/              # Сохраненные HTML страницы для тестирования
│   ├── page_10016.html
│   ├── page_15234.html
│   ├── page_1452.html
│   └── download_summary.json
├── output/                # Результаты тестирования
│   ├── current_scraper_result_*.json
│   ├── current_scraper_summary.json
│   ├── parsed_page_*.json
│   └── parsing_summary.json
├── download_test_pages.py      # Скрипт для загрузки тестовых страниц
├── test_current_scraper_simple.py  # Тест текущего скрипта парсинга
└── test_scraper_parsing.py     # Unit-тесты для парсинга сохраненных страниц
```

## Запуск тестов

### 1. Загрузка тестовых HTML страниц

```bash
python tests/download_test_pages.py
```

Загружает HTML страницы локально в `tests/fixtures/`:
- page_10016.html (Baffling Blocks)
- page_15234.html (Blank Prediction)
- page_1452.html

### 2. Тестирование текущего скрипта парсинга

```bash
python tests/test_current_scraper_simple.py
```

Запускает текущий скрипт парсинга на реальных страницах и сохраняет результаты в `tests/output/`.

### 3. Unit-тесты парсинга

```bash
python tests/test_scraper_parsing.py
```

Запускает unit-тесты на сохраненных HTML файлах.

## Результаты тестирования

### Текущий скрипт парсинга

**Дата:** 17 января 2025

**Результаты:**
- ✅ Всего страниц: 3
- ✅ Успешно: 3
- ❌ Ошибок: 0

**Детали:**
1. **page_10016** (Baffling Blocks)
   - Название: "Baffling Blocks (Gimmick and Online Instructions) by Eric Leclerc"
   - Цена: $18.75
   - Автор: Eric Leclerc
   - ✅ Успешно распарсено

2. **page_15234** (Blank Prediction)
   - Название: "Blank Prediction by Rey de Picas (Instant Download)"
   - Цена: $10.98
   - Автор: Rey de Picas
   - ✅ Успешно распарсено

3. **page_1452** (Discontinued Product)
   - Название: "Discontinued Product"
   - Цена: $169.95
   - Автор: None
   - ⚠️ Частично распарсено (нет автора и описания)

### Unit-тесты парсинга

**Результаты:**
- ✅ Всего тестов: 3
- ✅ Успешно: 3
- ❌ Ошибок: 0

Все тесты прошли успешно!

## Файлы результатов

- `tests/output/current_scraper_summary.json` - Сводка тестирования текущего скрипта
- `tests/output/parsing_summary.json` - Сводка unit-тестов
- `tests/output/current_scraper_result_*.json` - Детальные результаты для каждой страницы
- `tests/output/parsed_page_*.json` - Результаты парсинга из unit-тестов

## Следующие шаги

1. ✅ HTML страницы сохранены локально
2. ✅ Текущий скрипт протестирован на реальных страницах
3. ✅ Unit-тесты созданы и работают
4. ⏭️ Рефакторинг скрипта для улучшения архитектуры
5. ⏭️ Добавление больше тестов (edge cases, ошибки)

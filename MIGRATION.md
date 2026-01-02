# Миграция БД: Добавление колонок fees_24h и fee_rate

## Проблема
После добавления полей `fees_24h` и `fee_rate` в модель Pool, в существующей БД нет этих колонок.

## Решение

### Вариант 1: Добавить колонки через SQL (рекомендуется)
```bash
# Добавить fees_24h
sqlite3 data/bot.db "ALTER TABLE pools ADD COLUMN fees_24h REAL DEFAULT 0.0;"

# Добавить fee_rate
sqlite3 data/bot.db "ALTER TABLE pools ADD COLUMN fee_rate INTEGER DEFAULT 0;"
```

Или используйте файл `add_fees_column.sql`:
```bash
sqlite3 data/bot.db < add_fees_column.sql
sqlite3 data/bot.db "ALTER TABLE pools ADD COLUMN fee_rate INTEGER DEFAULT 0;"
```

### Вариант 2: Пересоздать БД (если данные не важны)
```bash
rm data/bot.db
# Затем запустите бота - БД создастся автоматически с новой структурой
```

## После миграции
Запустите бота и обновите пулы командой `/pools` - данные будут сохранены с новыми полями fees_24h и fee_rate.


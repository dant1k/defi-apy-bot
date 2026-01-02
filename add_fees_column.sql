-- SQL скрипт для добавления колонки fees_24h в таблицу pools
-- Запустите: sqlite3 data/bot.db < add_fees_column.sql

-- Проверяем, существует ли колонка (для SQLite)
-- Если колонка уже есть, скрипт вернет ошибку, но это нормально

ALTER TABLE pools ADD COLUMN fees_24h REAL DEFAULT 0.0;


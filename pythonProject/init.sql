-- Создание базы данных
CREATE DATABASE IF NOT EXISTS aml;

-- Использование созданной базы данных
USE aml;

-- Создание таблицы
CREATE TABLE IF NOT EXISTS `user_transactions` (
  `user_id` bigint NOT NULL,
  `remaining_transactions` int DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

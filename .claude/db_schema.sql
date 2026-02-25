-- MySQL dump 10.13  Distrib 8.0.44, for macos15 (arm64)
--
-- Host: 127.0.0.1    Database: trading_ai
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `account_balances`
--

DROP TABLE IF EXISTS `account_balances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_balances` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_id` bigint NOT NULL,
  `asset` varchar(32) NOT NULL,
  `free` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `locked` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `ts` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_balances_account_asset_ts` (`account_id`,`asset`,`ts`),
  KEY `idx_balances_account_ts` (`account_id`,`ts`),
  CONSTRAINT `fk_balances_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_balances_amounts` CHECK (((`free` >= 0) and (`locked` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `account_balances`
--

LOCK TABLES `account_balances` WRITE;
/*!40000 ALTER TABLE `account_balances` DISABLE KEYS */;
/*!40000 ALTER TABLE `account_balances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `exchange_id` bigint DEFAULT NULL,
  `name` varchar(120) NOT NULL,
  `mode` varchar(8) NOT NULL,
  `base_currency` varchar(16) NOT NULL DEFAULT 'USD',
  `status` varchar(16) NOT NULL DEFAULT 'active',
  `credentials_ref` varchar(255) DEFAULT NULL,
  `meta` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_accounts_user` (`user_id`),
  KEY `idx_accounts_mode` (`mode`),
  KEY `idx_accounts_exchange` (`exchange_id`),
  CONSTRAINT `fk_accounts_exchange` FOREIGN KEY (`exchange_id`) REFERENCES `exchanges` (`id`),
  CONSTRAINT `fk_accounts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `chk_accounts_meta_json` CHECK (json_valid(`meta`)),
  CONSTRAINT `chk_accounts_mode` CHECK ((`mode` in (_utf8mb4'paper',_utf8mb4'live'))),
  CONSTRAINT `chk_accounts_status` CHECK ((`status` in (_utf8mb4'active',_utf8mb4'suspended')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alert_events`
--

DROP TABLE IF EXISTS `alert_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `alert_rule_id` bigint DEFAULT NULL,
  `user_id` bigint DEFAULT NULL,
  `bot_id` bigint DEFAULT NULL,
  `ts` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `severity` varchar(16) NOT NULL DEFAULT 'info',
  `title` varchar(255) NOT NULL,
  `message` text,
  `payload` json NOT NULL,
  `delivery_status` varchar(16) NOT NULL DEFAULT 'pending',
  PRIMARY KEY (`id`),
  KEY `idx_alert_events_ts` (`ts`),
  KEY `idx_alert_events_user_ts` (`user_id`,`ts`),
  KEY `idx_alert_events_bot_ts` (`bot_id`,`ts`),
  KEY `fk_alert_events_rule` (`alert_rule_id`),
  KEY `idx_alert_events_delivery_ts` (`delivery_status`,`ts`),
  CONSTRAINT `fk_alert_events_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `fk_alert_events_rule` FOREIGN KEY (`alert_rule_id`) REFERENCES `alert_rules` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_alert_events_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `chk_alert_events_delivery` CHECK ((`delivery_status` in (_utf8mb4'pending',_utf8mb4'sent',_utf8mb4'failed'))),
  CONSTRAINT `chk_alert_events_payload_json` CHECK (json_valid(`payload`)),
  CONSTRAINT `chk_alert_events_severity` CHECK ((`severity` in (_utf8mb4'info',_utf8mb4'warning',_utf8mb4'critical')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alert_events`
--

LOCK TABLES `alert_events` WRITE;
/*!40000 ALTER TABLE `alert_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `alert_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alert_rules`
--

DROP TABLE IF EXISTS `alert_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_rules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint DEFAULT NULL,
  `bot_id` bigint DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `rule_type` varchar(16) NOT NULL,
  `rule_spec` json NOT NULL,
  `channels` json NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_alert_rules_user` (`user_id`),
  KEY `idx_alert_rules_bot` (`bot_id`),
  CONSTRAINT `fk_alert_rules_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `fk_alert_rules_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `chk_alert_rules_channels_json` CHECK (json_valid(`channels`)),
  CONSTRAINT `chk_alert_rules_rule_spec_json` CHECK (json_valid(`rule_spec`)),
  CONSTRAINT `chk_alert_rules_type` CHECK ((`rule_type` in (_utf8mb4'pnl',_utf8mb4'drawdown',_utf8mb4'signal',_utf8mb4'error',_utf8mb4'price')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alert_rules`
--

LOCK TABLES `alert_rules` WRITE;
/*!40000 ALTER TABLE `alert_rules` DISABLE KEYS */;
/*!40000 ALTER TABLE `alert_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint DEFAULT NULL,
  `bot_id` bigint DEFAULT NULL,
  `event_type` varchar(32) NOT NULL,
  `ts` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `ip` varchar(64) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `data` json NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_audit_logs_ts` (`ts`),
  KEY `idx_audit_logs_user_ts` (`user_id`,`ts`),
  KEY `idx_audit_logs_bot_ts` (`bot_id`,`ts`),
  CONSTRAINT `fk_audit_logs_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `fk_audit_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `chk_audit_logs_data_json` CHECK (json_valid(`data`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bots`
--

DROP TABLE IF EXISTS `bots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bots` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `strategy_id` bigint NOT NULL,
  `symbol_id` bigint NOT NULL,
  `timeframe_id` smallint NOT NULL,
  `mode` varchar(8) NOT NULL,
  `status` varchar(16) NOT NULL DEFAULT 'stopped',
  `risk_params` json NOT NULL,
  `started_at` timestamp(6) NULL DEFAULT NULL,
  `stopped_at` timestamp(6) NULL DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `account_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_bots_status` (`status`),
  KEY `idx_bots_strategy` (`strategy_id`),
  KEY `idx_bots_symbol` (`symbol_id`),
  KEY `fk_bots_timeframe` (`timeframe_id`),
  KEY `idx_bots_account` (`account_id`),
  CONSTRAINT `fk_bots_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`),
  CONSTRAINT `fk_bots_strategy` FOREIGN KEY (`strategy_id`) REFERENCES `strategies` (`id`),
  CONSTRAINT `fk_bots_symbol` FOREIGN KEY (`symbol_id`) REFERENCES `symbols` (`id`),
  CONSTRAINT `fk_bots_timeframe` FOREIGN KEY (`timeframe_id`) REFERENCES `timeframes` (`id`),
  CONSTRAINT `chk_bots_mode` CHECK ((`mode` in (_utf8mb4'paper',_utf8mb4'live'))),
  CONSTRAINT `chk_bots_risk_params_json` CHECK (json_valid(`risk_params`)),
  CONSTRAINT `chk_bots_status` CHECK ((`status` in (_utf8mb4'running',_utf8mb4'stopped',_utf8mb4'paused',_utf8mb4'error')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bots`
--

LOCK TABLES `bots` WRITE;
/*!40000 ALTER TABLE `bots` DISABLE KEYS */;
/*!40000 ALTER TABLE `bots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `candle_features`
--

DROP TABLE IF EXISTS `candle_features`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `candle_features` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `symbol_id` bigint NOT NULL,
  `timeframe_id` smallint NOT NULL,
  `ts` timestamp(6) NOT NULL,
  `feature_set_id` bigint NOT NULL,
  `features` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_candle_features` (`symbol_id`,`timeframe_id`,`ts`,`feature_set_id`),
  KEY `idx_candle_features_lookup` (`symbol_id`,`timeframe_id`,`ts`,`feature_set_id`),
  KEY `fk_candle_features_timeframe` (`timeframe_id`),
  KEY `fk_candle_features_set` (`feature_set_id`),
  CONSTRAINT `fk_candle_features_set` FOREIGN KEY (`feature_set_id`) REFERENCES `feature_sets` (`id`),
  CONSTRAINT `fk_candle_features_symbol` FOREIGN KEY (`symbol_id`) REFERENCES `symbols` (`id`),
  CONSTRAINT `fk_candle_features_timeframe` FOREIGN KEY (`timeframe_id`) REFERENCES `timeframes` (`id`),
  CONSTRAINT `chk_candle_features_json` CHECK (json_valid(`features`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `candle_features`
--

LOCK TABLES `candle_features` WRITE;
/*!40000 ALTER TABLE `candle_features` DISABLE KEYS */;
/*!40000 ALTER TABLE `candle_features` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `candles`
--

DROP TABLE IF EXISTS `candles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `candles` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `symbol_id` bigint NOT NULL,
  `timeframe_id` smallint NOT NULL,
  `ts` timestamp(6) NOT NULL,
  `open` decimal(30,12) NOT NULL,
  `high` decimal(30,12) NOT NULL,
  `low` decimal(30,12) NOT NULL,
  `close` decimal(30,12) NOT NULL,
  `volume` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_candles_symbol_tf_ts` (`symbol_id`,`timeframe_id`,`ts`),
  KEY `idx_candles_symbol_tf_ts` (`symbol_id`,`timeframe_id`,`ts`),
  KEY `fk_candles_timeframe` (`timeframe_id`),
  CONSTRAINT `fk_candles_symbol` FOREIGN KEY (`symbol_id`) REFERENCES `symbols` (`id`),
  CONSTRAINT `fk_candles_timeframe` FOREIGN KEY (`timeframe_id`) REFERENCES `timeframes` (`id`),
  CONSTRAINT `chk_candles_high_low` CHECK ((`high` >= `low`)),
  CONSTRAINT `chk_candles_prices` CHECK (((`open` >= 0) and (`high` >= 0) and (`low` >= 0) and (`close` >= 0) and (`volume` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `candles`
--

LOCK TABLES `candles` WRITE;
/*!40000 ALTER TABLE `candles` DISABLE KEYS */;
/*!40000 ALTER TABLE `candles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `datasets`
--

DROP TABLE IF EXISTS `datasets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `datasets` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text,
  `symbol_id` bigint DEFAULT NULL,
  `timeframe_id` smallint DEFAULT NULL,
  `start_ts` timestamp(6) NULL DEFAULT NULL,
  `end_ts` timestamp(6) NULL DEFAULT NULL,
  `dataset_hash` varchar(128) DEFAULT NULL,
  `query_spec` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_datasets_symbol_tf` (`symbol_id`,`timeframe_id`),
  KEY `fk_datasets_timeframe` (`timeframe_id`),
  CONSTRAINT `fk_datasets_symbol` FOREIGN KEY (`symbol_id`) REFERENCES `symbols` (`id`),
  CONSTRAINT `fk_datasets_timeframe` FOREIGN KEY (`timeframe_id`) REFERENCES `timeframes` (`id`),
  CONSTRAINT `chk_datasets_query_spec_json` CHECK (json_valid(`query_spec`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `datasets`
--

LOCK TABLES `datasets` WRITE;
/*!40000 ALTER TABLE `datasets` DISABLE KEYS */;
/*!40000 ALTER TABLE `datasets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exchanges`
--

DROP TABLE IF EXISTS `exchanges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exchanges` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `type` varchar(32) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_exchanges_name` (`name`),
  CONSTRAINT `chk_exchanges_type` CHECK ((`type` in (_utf8mb4'crypto_exchange',_utf8mb4'broker',_utf8mb4'data_vendor')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchanges`
--

LOCK TABLES `exchanges` WRITE;
/*!40000 ALTER TABLE `exchanges` DISABLE KEYS */;
/*!40000 ALTER TABLE `exchanges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feature_sets`
--

DROP TABLE IF EXISTS `feature_sets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feature_sets` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `version` varchar(32) NOT NULL DEFAULT '1.0.0',
  `description` text,
  `spec` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_feature_sets_name_version` (`name`,`version`),
  CONSTRAINT `chk_feature_sets_spec_json` CHECK (json_valid(`spec`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feature_sets`
--

LOCK TABLES `feature_sets` WRITE;
/*!40000 ALTER TABLE `feature_sets` DISABLE KEYS */;
/*!40000 ALTER TABLE `feature_sets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fills`
--

DROP TABLE IF EXISTS `fills`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fills` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_id` bigint NOT NULL,
  `exchange_trade_id` varchar(128) DEFAULT NULL,
  `ts` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `qty` decimal(30,12) NOT NULL,
  `price` decimal(30,12) NOT NULL,
  `fee` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `fee_asset` varchar(32) DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_fills_order_ts` (`order_id`,`ts`),
  KEY `idx_fills_exchange_trade_id` (`exchange_trade_id`),
  CONSTRAINT `fk_fills_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_fills_qty_price` CHECK (((`qty` > 0) and (`price` >= 0) and (`fee` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fills`
--

LOCK TABLES `fills` WRITE;
/*!40000 ALTER TABLE `fills` DISABLE KEYS */;
/*!40000 ALTER TABLE `fills` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `model_runs`
--

DROP TABLE IF EXISTS `model_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `model_runs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `model_id` bigint NOT NULL,
  `dataset_id` bigint DEFAULT NULL,
  `started_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `finished_at` timestamp(6) NULL DEFAULT NULL,
  `status` varchar(16) NOT NULL DEFAULT 'running',
  `metrics` json NOT NULL,
  `params` json NOT NULL,
  `logs_uri` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_model_runs_model` (`model_id`,`started_at`),
  KEY `idx_model_runs_dataset` (`dataset_id`),
  CONSTRAINT `fk_model_runs_dataset` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`),
  CONSTRAINT `fk_model_runs_model` FOREIGN KEY (`model_id`) REFERENCES `models` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_model_runs_metrics_json` CHECK (json_valid(`metrics`)),
  CONSTRAINT `chk_model_runs_params_json` CHECK (json_valid(`params`)),
  CONSTRAINT `chk_model_runs_status` CHECK ((`status` in (_utf8mb4'running',_utf8mb4'success',_utf8mb4'failed')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `model_runs`
--

LOCK TABLES `model_runs` WRITE;
/*!40000 ALTER TABLE `model_runs` DISABLE KEYS */;
/*!40000 ALTER TABLE `model_runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `models`
--

DROP TABLE IF EXISTS `models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `models` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `version` varchar(32) NOT NULL,
  `model_type` varchar(32) NOT NULL,
  `feature_set_id` bigint DEFAULT NULL,
  `artifact_uri` varchar(512) DEFAULT NULL,
  `status` varchar(16) NOT NULL DEFAULT 'active',
  `meta` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_models_name_version` (`name`,`version`),
  KEY `idx_models_status` (`status`),
  KEY `idx_models_feature_set` (`feature_set_id`),
  CONSTRAINT `fk_models_feature_set` FOREIGN KEY (`feature_set_id`) REFERENCES `feature_sets` (`id`),
  CONSTRAINT `chk_models_meta_json` CHECK (json_valid(`meta`)),
  CONSTRAINT `chk_models_model_type` CHECK ((`model_type` in (_utf8mb4'xgboost',_utf8mb4'lightgbm',_utf8mb4'sklearn',_utf8mb4'nn'))),
  CONSTRAINT `chk_models_status` CHECK ((`status` in (_utf8mb4'active',_utf8mb4'deprecated',_utf8mb4'archived')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `models`
--

LOCK TABLES `models` WRITE;
/*!40000 ALTER TABLE `models` DISABLE KEYS */;
/*!40000 ALTER TABLE `models` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bot_id` bigint NOT NULL,
  `signal_id` bigint DEFAULT NULL,
  `exchange_order_id` varchar(128) DEFAULT NULL,
  `ts` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `side` varchar(8) NOT NULL,
  `type` varchar(16) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'new',
  `qty` decimal(30,12) NOT NULL,
  `price` decimal(30,12) DEFAULT NULL,
  `stop_price` decimal(30,12) DEFAULT NULL,
  `time_in_force` varchar(8) DEFAULT NULL,
  `meta` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_orders_bot_ts` (`bot_id`,`ts`),
  KEY `idx_orders_status` (`status`),
  KEY `idx_orders_signal` (`signal_id`),
  KEY `idx_orders_exchange_order_id` (`exchange_order_id`),
  CONSTRAINT `fk_orders_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `fk_orders_signal` FOREIGN KEY (`signal_id`) REFERENCES `signals` (`id`),
  CONSTRAINT `chk_orders_meta_json` CHECK (json_valid(`meta`)),
  CONSTRAINT `chk_orders_price_logic` CHECK ((((`type` = _utf8mb4'market') and (`price` is null) and (`stop_price` is null)) or ((`type` = _utf8mb4'limit') and (`price` is not null) and (`stop_price` is null)) or ((`type` in (_utf8mb4'stop',_utf8mb4'stop_limit')) and (`stop_price` is not null)))),
  CONSTRAINT `chk_orders_qty` CHECK ((`qty` > 0)),
  CONSTRAINT `chk_orders_side` CHECK ((`side` in (_utf8mb4'buy',_utf8mb4'sell'))),
  CONSTRAINT `chk_orders_status` CHECK ((`status` in (_utf8mb4'new',_utf8mb4'sent',_utf8mb4'partially_filled',_utf8mb4'filled',_utf8mb4'canceled',_utf8mb4'rejected'))),
  CONSTRAINT `chk_orders_type` CHECK ((`type` in (_utf8mb4'market',_utf8mb4'limit',_utf8mb4'stop',_utf8mb4'stop_limit')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `portfolio_snapshots`
--

DROP TABLE IF EXISTS `portfolio_snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `portfolio_snapshots` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bot_id` bigint NOT NULL,
  `ts` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `equity` decimal(30,12) NOT NULL,
  `cash` decimal(30,12) NOT NULL,
  `unrealized_pnl` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `realized_pnl` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `meta` json NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_snapshots_bot_ts` (`bot_id`,`ts`),
  CONSTRAINT `fk_snapshots_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `chk_snapshots_meta_json` CHECK (json_valid(`meta`)),
  CONSTRAINT `chk_snapshots_money` CHECK (((`equity` >= 0) and (`cash` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `portfolio_snapshots`
--

LOCK TABLES `portfolio_snapshots` WRITE;
/*!40000 ALTER TABLE `portfolio_snapshots` DISABLE KEYS */;
/*!40000 ALTER TABLE `portfolio_snapshots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `positions`
--

DROP TABLE IF EXISTS `positions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `positions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bot_id` bigint NOT NULL,
  `symbol_id` bigint NOT NULL,
  `qty` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `avg_price` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `realized_pnl` decimal(30,12) NOT NULL DEFAULT '0.000000000000',
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_positions_bot_symbol` (`bot_id`,`symbol_id`),
  KEY `idx_positions_bot` (`bot_id`),
  KEY `fk_positions_symbol` (`symbol_id`),
  CONSTRAINT `fk_positions_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `fk_positions_symbol` FOREIGN KEY (`symbol_id`) REFERENCES `symbols` (`id`),
  CONSTRAINT `chk_positions_prices` CHECK ((`avg_price` >= 0)),
  CONSTRAINT `chk_positions_qty` CHECK ((`qty` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `positions`
--

LOCK TABLES `positions` WRITE;
/*!40000 ALTER TABLE `positions` DISABLE KEYS */;
/*!40000 ALTER TABLE `positions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `predictions`
--

DROP TABLE IF EXISTS `predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `predictions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bot_id` bigint NOT NULL,
  `model_id` bigint DEFAULT NULL,
  `symbol_id` bigint NOT NULL,
  `timeframe_id` smallint NOT NULL,
  `ts` timestamp(6) NOT NULL,
  `score` decimal(12,8) DEFAULT NULL,
  `raw_output` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_predictions` (`bot_id`,`model_id`,`symbol_id`,`timeframe_id`,`ts`),
  KEY `idx_predictions_bot_ts` (`bot_id`,`ts`),
  KEY `fk_predictions_model` (`model_id`),
  KEY `fk_predictions_timeframe` (`timeframe_id`),
  KEY `idx_predictions_symbol_tf_ts` (`symbol_id`,`timeframe_id`,`ts`),
  CONSTRAINT `fk_predictions_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_predictions_model` FOREIGN KEY (`model_id`) REFERENCES `models` (`id`),
  CONSTRAINT `fk_predictions_symbol` FOREIGN KEY (`symbol_id`) REFERENCES `symbols` (`id`),
  CONSTRAINT `fk_predictions_timeframe` FOREIGN KEY (`timeframe_id`) REFERENCES `timeframes` (`id`),
  CONSTRAINT `chk_predictions_raw_output_json` CHECK (json_valid(`raw_output`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `predictions`
--

LOCK TABLES `predictions` WRITE;
/*!40000 ALTER TABLE `predictions` DISABLE KEYS */;
/*!40000 ALTER TABLE `predictions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(32) NOT NULL,
  `name` varchar(120) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roles_code` (`code`),
  CONSTRAINT `chk_roles_code` CHECK ((`code` <> _utf8mb4''))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'user','Usuario',1,'2026-01-22 14:03:45.347999'),(2,'admin','Administrador',1,'2026-01-22 14:03:45.347999');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `signals`
--

DROP TABLE IF EXISTS `signals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `signals` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bot_id` bigint NOT NULL,
  `ts` timestamp(6) NOT NULL,
  `action` varchar(8) NOT NULL,
  `confidence` decimal(6,5) DEFAULT NULL,
  `model_version` varchar(64) DEFAULT NULL,
  `features_hash` varchar(128) DEFAULT NULL,
  `reasons` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_signals_bot_ts` (`bot_id`,`ts`),
  CONSTRAINT `fk_signals_bot` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `chk_signals_action` CHECK ((`action` in (_utf8mb4'buy',_utf8mb4'sell',_utf8mb4'hold'))),
  CONSTRAINT `chk_signals_confidence` CHECK (((`confidence` is null) or ((`confidence` >= 0) and (`confidence` <= 1)))),
  CONSTRAINT `chk_signals_reasons_json` CHECK (json_valid(`reasons`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `signals`
--

LOCK TABLES `signals` WRITE;
/*!40000 ALTER TABLE `signals` DISABLE KEYS */;
/*!40000 ALTER TABLE `signals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `strategies`
--

DROP TABLE IF EXISTS `strategies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `strategies` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `version` varchar(32) NOT NULL DEFAULT '1.0.0',
  `description` text,
  `parameters` json NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_strategies_name_version` (`name`,`version`),
  CONSTRAINT `chk_strategies_parameters_json` CHECK (json_valid(`parameters`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `strategies`
--

LOCK TABLES `strategies` WRITE;
/*!40000 ALTER TABLE `strategies` DISABLE KEYS */;
/*!40000 ALTER TABLE `strategies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `symbols`
--

DROP TABLE IF EXISTS `symbols`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `symbols` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `exchange_id` bigint NOT NULL,
  `symbol` varchar(64) NOT NULL,
  `base_asset` varchar(32) DEFAULT NULL,
  `quote_asset` varchar(32) DEFAULT NULL,
  `asset_class` varchar(16) NOT NULL,
  `tick_size` decimal(30,12) DEFAULT NULL,
  `lot_size` decimal(30,12) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_symbols_exchange_symbol` (`exchange_id`,`symbol`),
  KEY `idx_symbols_exchange` (`exchange_id`),
  KEY `idx_symbols_asset_class` (`asset_class`),
  CONSTRAINT `fk_symbols_exchange` FOREIGN KEY (`exchange_id`) REFERENCES `exchanges` (`id`),
  CONSTRAINT `chk_symbols_asset_class` CHECK ((`asset_class` in (_utf8mb4'crypto',_utf8mb4'metal',_utf8mb4'etf',_utf8mb4'stock',_utf8mb4'forex')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `symbols`
--

LOCK TABLES `symbols` WRITE;
/*!40000 ALTER TABLE `symbols` DISABLE KEYS */;
/*!40000 ALTER TABLE `symbols` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_events`
--

DROP TABLE IF EXISTS `system_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `component` varchar(32) NOT NULL,
  `event_type` varchar(32) NOT NULL,
  `ts` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `level` varchar(16) NOT NULL DEFAULT 'info',
  `message` text,
  `payload` json NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_system_events_ts` (`ts`),
  KEY `idx_system_events_component_ts` (`component`,`ts`),
  CONSTRAINT `chk_system_events_component` CHECK ((`component` in (_utf8mb4'market_data',_utf8mb4'execution',_utf8mb4'scheduler',_utf8mb4'api'))),
  CONSTRAINT `chk_system_events_level` CHECK ((`level` in (_utf8mb4'info',_utf8mb4'warning',_utf8mb4'error'))),
  CONSTRAINT `chk_system_events_payload_json` CHECK (json_valid(`payload`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_events`
--

LOCK TABLES `system_events` WRITE;
/*!40000 ALTER TABLE `system_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `system_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `timeframes`
--

DROP TABLE IF EXISTS `timeframes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `timeframes` (
  `id` smallint NOT NULL AUTO_INCREMENT,
  `code` varchar(8) NOT NULL,
  `seconds` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_timeframes_code` (`code`),
  CONSTRAINT `chk_timeframes_seconds` CHECK ((`seconds` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `timeframes`
--

LOCK TABLES `timeframes` WRITE;
/*!40000 ALTER TABLE `timeframes` DISABLE KEYS */;
/*!40000 ALTER TABLE `timeframes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role_id` bigint NOT NULL,
  `status` varchar(16) NOT NULL DEFAULT 'active',
  `failed_attempts` int NOT NULL DEFAULT '0',
  `login_locked_until` timestamp(6) NULL DEFAULT NULL,
  `last_login_at` timestamp(6) NULL DEFAULT NULL,
  `token_current_jti` varchar(64) DEFAULT NULL,
  `otp_code` varchar(255) DEFAULT NULL,
  `otp_created_at` timestamp(6) NULL DEFAULT NULL,
  `otp_expires_at` timestamp(6) NULL DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  KEY `idx_users_status` (`status`),
  KEY `idx_users_token_jti` (`token_current_jti`),
  KEY `idx_users_otp_expires` (`otp_expires_at`),
  KEY `idx_users_role_id` (`role_id`),
  KEY `idx_users_login_locked_until` (`login_locked_until`),
  CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`),
  CONSTRAINT `chk_users_failed_attempts` CHECK ((`failed_attempts` >= 0)),
  CONSTRAINT `chk_users_otp_dates` CHECK (((`otp_created_at` is null) or (`otp_expires_at` is null) or (`otp_expires_at` >= `otp_created_at`))),
  CONSTRAINT `chk_users_status` CHECK ((`status` in (_utf8mb4'active',_utf8mb4'blocked',_utf8mb4'disabled')))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (3,'andrescruznovoa@gmail.com','Andrés Cruz','$2b$12$DdLxc0vpeF22XjIV5axc3eJTULc45RTI96FfTTFnHv.FX5E/VBCEO',1,'active',0,NULL,'2026-02-05 14:11:29.892997',NULL,NULL,NULL,NULL,'2026-01-22 18:23:07.625248','2026-02-05 14:15:15.333701');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-24  6:53:32

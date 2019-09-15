DROP TABLE IF EXISTS `crawl_products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4;
CREATE TABLE `crawl_products` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `category_id` varchar(150) NOT NULL,
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `short_description` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `swatch_colors` longtext DEFAULT NULL,
  `specifications` longtext DEFAULT NULL,
  `old_price` decimal(10,2) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `images` longtext NOT NULL,
  `link` longtext NOT NULL,
  `brand` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shop` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `domain` varchar(256) NOT NULL,
  `rating_count` varchar(10) NOT NULL,
  `in_stock` tinyint(1) NOT NULL DEFAULT '1',
  `status` tinyint(1) NOT NULL DEFAULT '1',
  `free_shipping` tinyint(1) NOT NULL DEFAULT '0',
  `created_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_update` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
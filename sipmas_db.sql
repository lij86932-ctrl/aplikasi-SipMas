-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: May 19, 2026 at 01:22 AM
-- Server version: 8.0.30
-- PHP Version: 8.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `sipmas_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `category`
--

CREATE TABLE `category` (
  `id_category` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `nama_category` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `category`
--

INSERT INTO `category` (`id_category`, `created_at`, `nama_category`) VALUES
(1, '2026-05-17 15:44:10', 1);

-- --------------------------------------------------------

--
-- Table structure for table `complaint`
--

CREATE TABLE `complaint` (
  `id_complaint` int NOT NULL,
  `id_user` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `id_category` int NOT NULL,
  `lokasi` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `deskripsi` text NOT NULL,
  `status` enum('pending','selesai') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `attachment` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `anonim` enum('1','0') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `complaint`
--

INSERT INTO `complaint` (`id_complaint`, `id_user`, `title`, `id_category`, `lokasi`, `deskripsi`, `status`, `created_at`, `updated_at`, `attachment`, `anonim`) VALUES
(1, 6, 'ayam', 1, 'bento', 'enak', 'pending', '2026-05-17 15:46:35', '2026-05-17 15:46:35', 'image\\uploads\\1_1779032795.png', '0'),
(2, 6, 'waduh', 1, '31', 'lupa', 'pending', '2026-05-17 15:52:09', '2026-05-17 15:52:09', 'image\\uploads\\2_1779033129.png', '0'),
(5, 6, 'gunung meletus', 1, 'kec. suka ayam', 'ada lavanya', 'pending', '2026-05-17 17:35:39', '2026-05-17 17:35:39', '', '0'),
(6, 6, 'jalan rusak', 1, 'gatau deh', 'aspal hancur', 'pending', '2026-05-17 17:36:54', '2026-05-17 17:36:54', '', '0');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id_user` int NOT NULL,
  `nama` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `nik` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `no_hp` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `role` enum('masyarakat','petugas') DEFAULT 'masyarakat'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id_user`, `nama`, `nik`, `password`, `no_hp`, `role`) VALUES
(1, 'Zulhijjah', '2345678', 'scrypt:32768:8:1$B5FfbZ4cTSa9mbCp$973901899721cc919fa6ce487e3959a0c3b4f719395f640964aabc7d3caef43bb1ad4704e9517463cdd4be94e7ae3a36b9717ff05f74b376ca9b79471a54ae82', '082163932632', 'masyarakat'),
(6, 'anna', '1234567887', '$2b$12$QVENm0ENNFguah577OvUj./LQN49NfUbEmyT73BxHNUGFNR3mkQme', '08877655444', 'masyarakat'),
(7, 'ayam', '22223333', '$2b$12$8wn4kqu9EWJPjDGsNRmAZuVcpIeXWr4IC0Ch7p0zf5Cq9E9yfDLkK', '08877655444', 'masyarakat'),
(8, 'another', '', '$2b$12$KR5WA4p3czz4UUiiUeMJzOzlef.tyvzBiculCcU0B/Mp6spPRyyR6', '', 'petugas');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`id_category`);

--
-- Indexes for table `complaint`
--
ALTER TABLE `complaint`
  ADD PRIMARY KEY (`id_complaint`),
  ADD KEY `id_category` (`id_category`),
  ADD KEY `id_user` (`id_user`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id_user`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `category`
--
ALTER TABLE `category`
  MODIFY `id_category` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `complaint`
--
ALTER TABLE `complaint`
  MODIFY `id_complaint` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id_user` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `complaint`
--
ALTER TABLE `complaint`
  ADD CONSTRAINT `complaint_ibfk_1` FOREIGN KEY (`id_category`) REFERENCES `category` (`id_category`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `complaint_ibfk_2` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE RESTRICT ON UPDATE RESTRICT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

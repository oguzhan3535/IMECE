CREATE DATABASE IF NOT EXISTS ImeceDB;
USE ImeceDB;

-- Kullanıcılar Tablosu (Tüm roller buraya kaydolacak)
CREATE TABLE Kullanici (
    KullaniciID INT AUTO_INCREMENT PRIMARY KEY,
    AdSoyad VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    SifreHash VARCHAR(255) NOT NULL,
    Rol ENUM('Bagisci', 'IhtiyacSahibi', 'Esnaf', 'Admin') NOT NULL,
    Durum VARCHAR(20) DEFAULT 'Aktif',
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Esnaf Detay Tablosu
CREATE TABLE Esnaf (
    EsnafID INT PRIMARY KEY,
    EsnafAdi VARCHAR(100) NOT NULL,
    IBAN VARCHAR(50) NOT NULL,
    Durum VARCHAR(20) DEFAULT 'Aktif',
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (EsnafID) REFERENCES Kullanici(KullaniciID)
);

-- Ürün Paketleri (Bağışlanacak ürünler: Mont, Kalem vb.)
CREATE TABLE UrunPaketi (
    PaketID INT AUTO_INCREMENT PRIMARY KEY,
    PaketAdi VARCHAR(100) NOT NULL,
    Fiyat DECIMAL(10,2) NOT NULL,
    Adet INT NOT NULL,
    Aktif TINYINT(1) DEFAULT 1
);

-- Bağış Hareketleri
CREATE TABLE Bagis (
    BagisID INT AUTO_INCREMENT PRIMARY KEY,
    KullaniciID INT NOT NULL,
    PaketID INT NOT NULL,
    Tutar DECIMAL(10,2) NOT NULL,
    BagisTarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    Durum VARCHAR(20) DEFAULT 'Basarili',
    FOREIGN KEY (KullaniciID) REFERENCES Kullanici(KullaniciID),
    FOREIGN KEY (PaketID) REFERENCES UrunPaketi(PaketID)
);

-- Kupon Sistemi (Sistemin Kalbi)
CREATE TABLE Kupon (
    KuponID INT AUTO_INCREMENT PRIMARY KEY,
    KuponKodu VARCHAR(20) NOT NULL UNIQUE,
    KullaniciID INT NOT NULL, 
    BagisID INT NOT NULL,
    PaketID INT NOT NULL,
    EsnafID INT, 
    Durum ENUM('Issued', 'Used', 'Expired') DEFAULT 'Issued',
    IssuedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt DATETIME,
    UsedAt DATETIME,
    FOREIGN KEY (KullaniciID) REFERENCES Kullanici(KullaniciID),
    FOREIGN KEY (BagisID) REFERENCES Bagis(BagisID),
    FOREIGN KEY (PaketID) REFERENCES UrunPaketi(PaketID),
    FOREIGN KEY (EsnafID) REFERENCES Esnaf(EsnafID)
);



-- Talep Tablosu
USE ImeceDB;

CREATE TABLE IF NOT EXISTS Talep (
    TalepID INT AUTO_INCREMENT PRIMARY KEY,
    KullaniciID INT NOT NULL,
    Kategori VARCHAR(50) NOT NULL,
    Konum VARCHAR(100) NOT NULL,
    Detay TEXT NOT NULL,
    Durum VARCHAR(20) DEFAULT 'Beklemede',
    OlusturmaTarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (KullaniciID) REFERENCES Kullanickullanicikullaniciesnafi(KullaniciID)
);



-- Kara kutu log tablosu
CREATE TABLE IF NOT EXISTS SistemLog (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    KullaniciID INT,
    Islem VARCHAR(255) NOT NULL,
    Tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (KullaniciID) REFERENCES Kullanici(KullaniciID)
);


-- ihtiyaç sahibi talep adet seçme
ALTER TABLE Talep ADD COLUMN Adet INT DEFAULT 1;


ALTER TABLE Kupon MODIFY COLUMN Durum VARCHAR(50) DEFAULT 'Active';



-- 1. Kullanıcıların (özellikle esnafın) hangi şehirde olduğunu bilmek için:
ALTER TABLE Kullanici ADD COLUMN Sehir VARCHAR(50) DEFAULT 'Belirtilmedi';

-- 2. İhtiyaç sahibinin hangi esnaftan teslimat almak istediğini kaydetmek için:
ALTER TABLE Talep ADD COLUMN TeslimatEsnafID INT NULL;


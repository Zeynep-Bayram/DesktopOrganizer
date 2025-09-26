#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dosya Yönetim Modülü - Dosyaları taşıma, kopyalama ve organizasyon işlemleri
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from config import Config # config.py dosyasından Config sınıfını içe aktar

class FileManager:
    """Dosya yönetimi sınıfı"""

    def __init__(self):
        """
        FileManager sınıfının yapıcı metodu.
        Config ayarlarını ve logger objesini başlatır.
        """
        self.config = Config()
        self.logger = logging.getLogger(__name__)

    def move_file(self, source_path: Path, category: str) -> bool:
        """
        Belirtilen dosyayı (source_path) hedef kategoriye taşır.

        """
        import traceback
        self.logger.warning(f"MOVE_FILE ÇAĞRILDI: {source_path.name} -> {category}")
        self.logger.warning(f"CALL STACK:\n{''.join(traceback.format_stack())}")
        
        try:
            # Hedef dizini belirle
            target_dir = self.config.CATEGORIES.get(category)
            if not target_dir:
                self.logger.error(f"Bilinmeyen kategori: {category} için hedef dizin bulunamadı.")
                return False
            
            # Hedef dizini Path objesine dönüştür (eğer config'den string olarak gelirse)
            target_dir_path = Path(target_dir)

            # Hedef dizini oluştur (varsa hata vermez)
            target_dir_path.mkdir(parents=True, exist_ok=True)
            
            # Dosya adını al
            file_name = source_path.name
            
            # Hedef yolu oluştur
            target_path = target_dir_path / file_name
            
            # Dosya çakışması kontrolü ve çözüm stratejisi uygulama
            resolved_target_path = self._handle_file_conflict(target_path)
            
            if resolved_target_path is None: # Strateji 'skip' ise
                self.logger.info(f"Dosya atlandı (çakışma): {source_path}")
                return True # Atlandıysa da işlem başarılı sayılabilir, çünkü istenen bu
            
            # Dosyayı taşı
            shutil.move(str(source_path), str(resolved_target_path)) # shutil string path bekler

            self.logger.info(f"Dosya taşındı: '{source_path.name}' -> '{resolved_target_path}'")
            return True

        except FileNotFoundError:
            self.logger.error(f"Taşınacak dosya bulunamadı: {source_path}")
            return False
        except Exception as e:
            self.logger.error(f"Dosya taşıma hatası '{source_path.name}' -> '{target_dir}': {e}", exc_info=True)
            return False

    def copy_file(self, source_path: Path, category: str) -> bool:
        """
        Belirtilen dosyayı (source_path) hedef kategoriye kopyalar.

        Args:
            source_path (Path): Kopyalanacak dosyanın tam yolu.
            category (str): Dosyanın ait olduğu kategori adı.

        Returns:
            bool: Dosya kopyalama işlemi başarılıysa True, aksi takdirde False.
        """
        try:
            # Hedef dizini belirle
            target_dir = self.config.CATEGORIES.get(category)
            if not target_dir:
                self.logger.error(f"Bilinmeyen kategori: {category} için hedef dizin bulunamadı.")
                return False
            
            # Hedef dizini Path objesine dönüştür
            target_dir_path = Path(target_dir)

            # Hedef dizini oluştur
            target_dir_path.mkdir(parents=True, exist_ok=True)
            
            # Dosya adını al
            file_name = source_path.name
            
            # Hedef yolu oluştur
            target_path = target_dir_path / file_name
            
            # Dosya çakışması kontrolü
            resolved_target_path = self._handle_file_conflict(target_path)
            
            if resolved_target_path is None: # Strateji 'skip' ise
                self.logger.info(f"Dosya atlandı (çakışma): {source_path}")
                return True
            
            # Dosyayı kopyala (meta verilerle birlikte)
            shutil.copy2(str(source_path), str(resolved_target_path))

            self.logger.info(f"Dosya kopyalandı: '{source_path.name}' -> '{resolved_target_path}'")
            return True

        except FileNotFoundError:
            self.logger.error(f"Kopyalanacak dosya bulunamadı: {source_path}")
            return False
        except Exception as e:
            self.logger.error(f"Dosya kopyalama hatası '{source_path.name}' -> '{target_dir}': {e}", exc_info=True)
            return False

    def _handle_file_conflict(self, target_path: Path) -> Path | None:
        """
        Hedef dizinde aynı isimde bir dosya varsa, yapılandırılmış çakışma çözüm stratejisini uygular.
        
        Args:
            target_path (Path): Dosyanın olması beklenen hedef yol.

        Returns:
            Path | None: Çözümlenmiş yeni hedef yol (Path objesi) veya
                         eğer dosya atlanacaksa None.
        """
        if not target_path.exists(): # Hedef yolda dosya yoksa, çakışma yok
            return target_path
        
        self.logger.warning(f"Hedefte '{target_path.name}' adında zaten bir dosya var. Çakışma çözümleniyor...")

        file_stem = target_path.stem    # Dosya adının uzantısız kısmı
        file_suffix = target_path.suffix  # Dosya uzantısı
        file_dir = target_path.parent   # Dosyanın dizini
        
        strategy = self.config.CONFLICT_RESOLUTION # config'den stratejiyi al

        if strategy == 'rename':
            # Yeni bir isim bul (örn: dosya_1.txt, dosya_2.txt)
            counter = 1
            while True:
                new_name = f"{file_stem}_{counter}{file_suffix}"
                new_path = file_dir / new_name # Path objesi ile yol birleştirme
                
                if not new_path.exists():
                    self.logger.info(f"Dosya çakışması 'yeniden adlandır' stratejisiyle çözüldü: '{new_path.name}'")
                    return new_path
                
                counter += 1
                
                # Sonsuz döngüden korunma (aşırı deneme durumunda zaman damgasına geç)
                if counter > 1000:
                    self.logger.warning(
                        f"1000'den fazla yeniden adlandırma denemesi başarısız oldu. '{target_path.name}' için zaman damgası eklenecek."
                    )
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_name = f"{file_stem}_{timestamp}{file_suffix}"
                    return file_dir / new_name

        elif strategy == 'overwrite':
            # Mevcut dosyanın üzerine yaz
            self.logger.warning(f"Dosya çakışması 'üzerine yaz' stratejisiyle çözüldü: '{target_path.name}' üzerine yazılacak.")
            return target_path

        elif strategy == 'skip':
            # Dosyayı atla (hiçbir işlem yapma)
            self.logger.info(f"Dosya çakışması 'atla' stratejisiyle çözüldü: '{target_path.name}' atlandı.")
            return None # None döndürerek taşıma/kopyalama işleminin yapılmamasını sağlarız

        else:
            # Geçersiz strateji durumunda varsayılan olarak zaman damgası ekle
            self.logger.error(
                f"Geçersiz çakışma çözme stratejisi '{strategy}' belirtildi. Varsayılan olarak zaman damgası eklenecek."
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{file_stem}_{timestamp}{file_suffix}"
            return file_dir / new_name

    def create_category_folders(self) -> bool:
        """
        Config dosyasında tanımlanan tüm kategori klasörlerini oluşturur.

        Returns:
            bool: Tüm klasörler başarıyla oluşturulduysa True, aksi takdirde False.
        """
        self.logger.info("Kategori klasörleri oluşturuluyor...")
        try:
            for category, folder_path in self.config.CATEGORIES.items():
                category_path = Path(folder_path) # Yolu Path objesine dönüştür
                category_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Kategori klasörü oluşturuldu/zaten var: '{category}' -> '{category_path}'")
            
            self.logger.info("Tüm kategori klasörleri kontrol edildi ve oluşturuldu.")
            return True
            
        except Exception as e:
            self.logger.error(f"Kategori klasörü oluşturma hatası: {e}", exc_info=True)
            return False

    def get_file_size(self, file_path: Path) -> str:
        """
        Belirtilen dosyanın boyutunu okunabilir (Bytes, KB, MB, GB) formatta döndürür.

        Args:
            file_path (Path): Boyutu alınacak dosyanın tam yolu.

        Returns:
            str: Okunabilir dosya boyutu (örn: "12.34 MB") veya "Bilinmiyor" hata durumunda.
        """
        try:
            size_bytes = os.path.getsize(str(file_path)) # os.path.getsize string yol bekler
            
            if size_bytes < 1024:
                return f"{size_bytes} Bytes"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        except FileNotFoundError:
            self.logger.warning(f"Dosya boyutu alınamadı, dosya bulunamadı: '{file_path.name}'")
            return "Bilinmiyor"
        except Exception as e:
            self.logger.error(f"Dosya boyutu alma hatası ({file_path.name}): {e}", exc_info=True)
            return "Bilinmiyor"


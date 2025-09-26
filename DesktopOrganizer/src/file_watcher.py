#!/usr/bin/env python3
"""
Dosya İzleme Modülü - Masaüstündeki dosya değişikliklerini takip eder
"""

import os
import time
import logging
from pathlib import Path  # Path sınıfını içe aktarıyoruz
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import Config

class FileEventHandler(FileSystemEventHandler):
    """Dosya olaylarını yöneten sınıf"""
    
    def __init__(self, callback, delete_callback=None):
        self.callback = callback
        self.delete_callback = delete_callback
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # İşlem görmemesi gereken dosya uzantıları veya isim parçacıkları
        
        self.ignored_extensions = {'.tmp', '.temp', '.log', '.crdownload', '.part', '.download'}
        self.ignored_names = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
        self.ignored_prefixes = {'~$'} # Excel/Word geçici dosyaları için
        
        # Geçici dosya kontrolü için zaman damgası
        self.recent_files = {}
        
        # Yeni oluşturulan dosyalar için beklenecek geçici isimler
        self.temp_file_patterns = {
            # Türkçe Windows
            'yeni belge', 'yeni metin belgesi', 'yeni klasör', 'yeni bitmap görüntüsü',
            'yeni microsoft word belgesi', 'yeni microsoft excel çalışma sayfası',
            'yeni winrar arşivi', 'yeni winrar zip arşivi',
            # İngilizce Windows  
            'new document', 'new text document', 'new folder', 'new bitmap image',
            'new microsoft word document', 'new microsoft excel worksheet',
            'new winrar archive', 'new winrar zip archive',
            # Office dosyaları
            'document', 'document1', 'document2', 'document3',
            'workbook', 'workbook1', 'workbook2', 'workbook3', 
            'presentation', 'presentation1', 'presentation2', 'presentation3',
            # Genel geçici isimler
            'untitled', 'untitled1', 'untitled2', 'untitled3',
            'noname', 'temp', 'temporary'
        }
        
        # Yeni oluşturulan dosyaları takip et (rename beklemek için)
        self.pending_new_files = {}  # {file_path: creation_time} 
        
    def should_ignore_file(self, file_path: Path) -> bool: 
        """
        Dosyanın işlenmemesi gerekip gerekmediğini kontrol et.
        """
        file_name = file_path.name 
        
        # Gizli dosyalar (Linux/macOS'ta nokta ile başlayanlar)
        if file_name.startswith('.'):
            self.logger.debug(f"Ignore: Gizli dosya '{file_name}'")
            return True
            
        # Önceden tanımlanmış özel isimler veya uzantılar
        if file_name in self.ignored_names:
            self.logger.debug(f"Ignore: Tanımlı özel dosya '{file_name}'")
            return True
            
        if file_path.suffix.lower() in self.ignored_extensions:
            self.logger.debug(f"Ignore: Geçici uzantılı dosya '{file_name}'")
            return True

        if any(file_name.startswith(p) for p in self.ignored_prefixes):
            self.logger.debug(f"Ignore: Ön ekli geçici dosya '{file_name}'")
            return True

        # Organizasyon klasörlerindeki dosyaları ignore et
        # Bu, masaüstünde oluşturduğumuz "Organize" klasörünün içindeki dosyaların
        # tekrar tekrar işlenmesini engeller.
        for category_path_str in self.config.CATEGORIES.values():
            # category_path_str string olduğu için Path objesine çevirip kontrol ediyoruz
            category_path = Path(category_path_str) 
            if file_path.is_relative_to(category_path): # file_path, category_path'in altındaysa
                self.logger.debug(f"Ignore: Organizasyon klasöründeki dosya '{file_path}'")
                return True
            
        return False
    
    def is_temp_filename(self, file_path: Path) -> bool:
        """
        Dosya adının geçici/yeni oluşturulmuş dosya adı olup olmadığını kontrol et.
        """
        file_stem = file_path.stem.lower()  # Uzantısız dosya adı, küçük harf
        
        # Tam eşleşme kontrol et
        if file_stem in self.temp_file_patterns:
            self.logger.debug(f"Geçici dosya adı tespit edildi: {file_path.name}")
            return True
        
        # Kısmi eşleşme kontrol et (başlangıç)
        for pattern in self.temp_file_patterns:
            if file_stem.startswith(pattern):
                self.logger.debug(f"Geçici dosya adı deseni tespit edildi: {file_path.name} (desen: {pattern})")
                return True
        
        return False
    
    def is_file_stable(self, file_path: Path) -> bool: # file_path'i Path objesi olarak bekliyoruz
        """
        Dosyanın kararlı olup olmadığını kontrol et (kopyalama/yazma tamamlandı mı?).
        Belirli bir süre boyunca boyutunun değişmediğini kontrol eder.
        """
        try:
            initial_size = -1
            for _ in range(self.config.FILE_STABILITY_CHECKS):
                current_size = file_path.stat().st_size # Path objesi ile boyut alma
                if initial_size == -1:
                    initial_size = current_size
                elif current_size != initial_size:
                    self.logger.debug(f"Dosya boyutu değişti, henüz kararlı değil: {file_path.name}")
                    initial_size = current_size # Boyut değiştiyse yeni boyutu alıp tekrar bekle
                time.sleep(self.config.FILE_STABILITY_CHECK_INTERVAL)
            
            # Son boyutlar eşitse kararlıdır.
            if file_path.stat().st_size == initial_size:
                 self.logger.debug(f"Dosya kararlı olarak algılandı: {file_path.name}")
                 return True
            return False # Son bir kontrol
        except FileNotFoundError:
            self.logger.warning(f"Kararlılık kontrolü sırasında dosya bulunamadı: {file_path.name}")
            return False
        except Exception as e:
            self.logger.error(f"Dosya kararlılık kontrolü hatası ({file_path.name}): {e}", exc_info=True)
            return False
    
    def on_created(self, event):
        """Yeni dosya veya dizin oluşturulduğunda çalışır"""
        if event.is_directory:
            return # Dizinleri ignore et
            
        file_path = Path(event.src_path) # watchdog'dan gelen string'i Path objesine dönüştür
        
        # Dosyanın anlık varlığını ve ignore durumunu kontrol et
        if not file_path.exists():
            self.logger.debug(f"Oluşturulan dosya mevcut değil (geçici olabilir): {file_path.name}")
            return
        
        if self.should_ignore_file(file_path):
            return
        
        # Geçici dosya adı kontrolü
        if self.is_temp_filename(file_path):
            self.logger.info(f"Geçici dosya adı tespit edildi, rename bekleniyor: {file_path.name}")
            # Geçici dosyayı pending listesine ekle
            import time
            self.pending_new_files[str(file_path)] = time.time()
            return
        
        self.logger.info(f"Yeni dosya tespit edildi: {file_path.name}")
        
        # Dosyanın tamamen yazılmasını bekle
        if self.is_file_stable(file_path):
            self.logger.info(f"Dosya kararlı, işleme başlanıyor: {file_path.name}")
            self.callback(file_path) # Callback'e Path objesini gönder
        else:
            self.logger.warning(f"Dosya henüz kararlı değil, işlenmiyor: {file_path.name}")
    
    # on_modified olayını ekleyelim, çünkü bazı programlar dosyaları 'oluşturmak' yerine 'değiştirir'.
    def on_modified(self, event):
        """Mevcut dosya değiştirildiğinde çalışır."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        
        if not file_path.exists():
            self.logger.debug(f"Değiştirilen dosya mevcut değil (silinmiş olabilir): {file_path.name}")
            return

        if self.should_ignore_file(file_path):
            return
        
        # Eğer dosya yeni oluşturulmuş ve zaten on_created tarafından işlenmişse tekrar işlemeyi önle
        # Bu basit bir önleme yöntemidir, daha gelişmiş çözümler için dosya hashing veya durum takibi gerekebilir.
        # Örneğin, dosyanın son işlem zamanını kaydedip belirli bir süre içinde tekrar işlememeyi düşünebiliriz.
        # Ancak is_file_stable zaten bir gecikme ve kontrol sağladığı için şimdilik yeterli olabilir.

        self.logger.info(f"Mevcut dosya değiştirildi: {file_path.name}")
        if self.is_file_stable(file_path):
            self.callback(file_path)

    def on_moved(self, event):
        """Dosya taşındığında veya yeniden adlandırıldığında çalışır"""
        if event.is_directory:
            return # Dizinleri ignore et
            
        dest_path = Path(event.dest_path) # watchdog'dan gelen string'i Path objesine dönüştür
        src_path = Path(event.src_path) # Kaynak yolu da Path objesine dönüştür
        
        # DEBUG: Her move eventini logla
        self.logger.info(f"MOVE EVENT: {src_path.name} -> {dest_path}")
        
        # Pending new files listesinde bu dosya var mı? (rename işlemi olabilir)
        src_key = str(src_path)
        if src_key in self.pending_new_files:
            self.logger.info(f"Pending dosya yeniden adlandırıldı: {src_path.name} -> {dest_path.name}")
            # Pending listesinden çıkar
            del self.pending_new_files[src_key]
            
            # Yeni ad hala geçici mi kontrol et
            if self.is_temp_filename(dest_path):
                self.logger.info(f"Yeni ad hala geçici: {dest_path.name}")
                # Yeni adla pending listesine tekrar ekle
                import time
                self.pending_new_files[str(dest_path)] = time.time()
                return
            else:
                # Artık gerçek bir isim, işle
                self.logger.info(f"Dosya gerçek isim aldı, işleniyor: {dest_path.name}")
                if dest_path.exists() and self.is_file_stable(dest_path):
                    self.callback(dest_path)
                return
        
        # Hedef yolu ignore et
        if self.should_ignore_file(dest_path):
            self.logger.debug(f"Taşınan dosya hedefi ignore listesinde: {dest_path.name}")
            return
            
        # Eğer dosya, izlenen dizine (masaüstüne) yeni taşındıysa veya orada yeniden adlandırıldıysa işle.
        if dest_path.parent == Path(self.config.WATCH_DIRECTORY): # Hedef dizin izlenen dizin mi?
            # Sadece yeniden adlandırma ise (aynı dizin içinde) tekrar işleme
            # Ancak organize klasörlerinden masaüstüne taşınma ise işle
            
            # Kaynak organize klasöründen mi geliyor?
            src_from_organize = False
            for category_path_str in self.config.CATEGORIES.values():
                category_path = Path(category_path_str)
                if src_path.is_relative_to(category_path):
                    src_from_organize = True
                    break
            
            if src_from_organize:
                # Organize klasöründen masaüstüne geri taşındı, işle
                self.logger.info(f"Dosya organize klasöründen masaüstüne taşındı: '{src_path.name}' -> '{dest_path.name}'")
                if self.is_file_stable(dest_path):
                    self.callback(dest_path)
            else:
                # Masaüstünde yeniden adlandırılma - bu durumda işleme (zaten organize edildiyse tekrar edilecek)
                self.logger.debug(f"Dosya masaüstünde yeniden adlandırıldı (tekrar işlenmeyecek): '{src_path.name}' -> '{dest_path.name}'")
        else:
            self.logger.debug(f"Dosya izlenen dizin dışına taşındı: {src_path.name} -> {dest_path.name}")

    # on_deleted'ı da ekleyelim, sadece loglama amaçlı olabilir.
    def on_deleted(self, event):
        """Dosya veya dizin silindiğinde çalışır."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # DEBUG: Her delete eventini logla
        self.logger.warning(f"DELETE EVENT: {file_path.name} silindi!")
        
        # Pending listesinden çıkar (silinmişse)
        file_key = str(file_path)
        if file_key in self.pending_new_files:
            self.logger.info(f"Pending dosya silindi: {file_path.name}")
            del self.pending_new_files[file_key]
        
        # Organize klasörlerine taşınan dosyaları ignore et
        for category_path_str in self.config.CATEGORIES.values():
            category_path = Path(category_path_str)
            if file_path.name in [f.name for f in category_path.glob("*") if f.is_file()]:
                self.logger.debug(f"Dosya organize edildi (silindi sayılmıyor): {file_path.name}")
                return
                
        self.logger.warning(f"Dosya gerçekten silindi: {file_path.name}")
        
        # Delete callback'i çağır (main.py'deki temizlik için)
        if self.delete_callback:
            self.delete_callback(file_path)
    
    def cleanup_pending_files(self):
        """
        Timeout olan pending dosyaları işle (1 dakikadan eski olanlar)
        Kullanıcı varsayılan ismi değiştirmemiş olabilir, bu durumda işle
        """
        import time
        current_time = time.time()
        timeout = self.config.PENDING_FILE_TIMEOUT
        
        expired_files = []
        for file_path_str, creation_time in self.pending_new_files.items():
            if current_time - creation_time > timeout:
                expired_files.append(file_path_str)
        
        for file_path_str in expired_files:
            file_path = Path(file_path_str)
            self.logger.info(f"Pending dosya timeout, işleniyor: {file_path.name}")
            
            # Pending listesinden çıkar
            del self.pending_new_files[file_path_str]
            
            # Dosya hala var mı ve işlenebilir mi kontrol et
            if file_path.exists() and not self.should_ignore_file(file_path):
                self.logger.info(f"Timeout olan dosya işleniyor: {file_path.name}")
                
                # Dosyanın kararlı olup olmadığını kontrol et
                if self.is_file_stable(file_path):
                    self.callback(file_path)
                else:
                    self.logger.warning(f"Timeout olan dosya kararlı değil: {file_path.name}")
            else:
                self.logger.debug(f"Timeout olan dosya bulunamadı veya ignore listesinde: {file_path.name}")


class DesktopWatcher:
    """Masaüstünü izleyen ana sınıf"""
    
    def __init__(self, callback, delete_callback=None):
        self.callback = callback
        self.delete_callback = delete_callback
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Observer ve event handler'ı oluştur
        self.observer = Observer()
        self.event_handler = FileEventHandler(callback, delete_callback)
        
        # İzleme dizinini kontrol et
        # WATCH_DIRECTORY Path objesi olabilir, os.path.exists string bekler
        watch_dir_path = Path(self.config.WATCH_DIRECTORY) 
        if not watch_dir_path.exists():
            raise FileNotFoundError(f"İzleme dizini bulunamadı: {watch_dir_path}")
        
        if not watch_dir_path.is_dir():
             raise NotADirectoryError(f"İzleme dizini bir klasör değil: {watch_dir_path}")

    def start(self):
        """İzlemeyi başlatır."""
        try:
            watch_dir_path = Path(self.config.WATCH_DIRECTORY) # Path objesi olarak al
            self.observer.schedule(
                self.event_handler,
                str(watch_dir_path), # watchdog.Observer.schedule string yol bekler
                recursive=False # Sadece ana masaüstü dizinini izle, alt dizinleri değil
            )
            
            self.observer.start()
            self.logger.info(f"Dosya izleme başlatıldı: {watch_dir_path}")
            
            # Mevcut dosyaları işleme
            self._process_existing_files()
            self.logger.info("Mevcut dosyalar işlendi")
            
            # Periyodik temizlik için timer başlat
            self._start_cleanup_timer()
            
        except Exception as e:
            self.logger.error(f"İzleme başlatma hatası: {e}", exc_info=True)
            raise # Hatayı yukarı fırlat ki main.py yakalayabilsin
    
    def stop(self):
        """İzlemeyi durdurur."""
        try:
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
                self.logger.info("Dosya izleme durduruldu")
        except Exception as e:
            self.logger.error(f"İzleme durdurma hatası: {e}", exc_info=True)
    
    def _process_existing_files(self):
        """Masaüstündeki mevcut (daha önceden var olan) dosyaları işler."""
        self.logger.info("Mevcut dosyalar kontrol ediliyor...")
        try:
            # WATCH_DIRECTORY'yi Path objesi olarak alıp kullanıyoruz
            for file_path in Path(self.config.WATCH_DIRECTORY).iterdir():
                if file_path.is_file(): # Sadece dosyaları işle, klasörleri değil
                    
                    # Ignore kontrolü (Path objesi gönderiyoruz)
                    if not self.event_handler.should_ignore_file(file_path):
                        self.logger.info(f"Mevcut dosya işleniyor: {file_path.name}")
                        
                        # Dosya hala var mı tekrar kontrol et
                        if file_path.exists():
                            self.callback(file_path) # Callback'e Path objesini gönder
                        else:
                            self.logger.debug(f"Mevcut dosya kayboldu: {file_path.name}")
                    else:
                        self.logger.debug(f"Mevcut dosya atlandı (ignore): {file_path.name}")
                elif file_path.is_dir():
                    self.logger.debug(f"Mevcut dizin atlandı: {file_path.name}")
        except Exception as e:
            self.logger.error(f"Mevcut dosya işleme hatası: {e}", exc_info=True)
    
    def is_running(self):
        """İzlemenin aktif olup olmadığını kontrol eder."""
        return self.observer.is_alive()
    
    def _start_cleanup_timer(self):
        """Periyodik temizlik timer'ını başlat"""
        import threading
        
        def cleanup_job():
            while self.observer.is_alive():
                try:
                    self.event_handler.cleanup_pending_files()
                    threading.Event().wait(self.config.CLEANUP_INTERVAL)
                except Exception as e:
                    self.logger.error(f"Temizlik hatası: {e}")
        
        self.cleanup_thread = threading.Thread(target=cleanup_job, daemon=True)
        self.cleanup_thread.start()
        self.logger.info("Periyodik temizlik thread'i başlatıldı")
    
    def stop(self):
        """İzlemeyi durdurur."""
        try:
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
                self.logger.info("Dosya izleme durduruldu")
        except Exception as e:
            self.logger.error(f"İzleme durdurma hatası: {e}", exc_info=True)
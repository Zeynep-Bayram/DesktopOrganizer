#!/usr/bin/env python3
"""
Akıllı Masaüstü Dosya Organizatörü - Ana Uygulama
"""

import os
import sys
import time
import logging
from pathlib import Path
from colorama import init, Fore, Style

# Proje modüllerini import et
from file_watcher import DesktopWatcher
from file_classifier import FileClassifier
from file_manager import FileManager
from config import Config
from utils import setup_logging, create_directories
from content_extractors import ContentExtractor
from ai_renamer import SmartFileRenamer
from gui_manager import show_file_confirmation, show_startup_preferences, UserPreferences

# Colorama'yı başlat
init()

class DesktopOrganizer:
    def __init__(self):
        self.config = Config()
        self.logger = setup_logging()
        self.file_classifier = FileClassifier()
        self.file_manager = FileManager()
        self.content_extractor = ContentExtractor()
        self.ai_renamer = SmartFileRenamer()
        self.user_preferences = UserPreferences()
        self.watcher = DesktopWatcher(self.on_file_event, self.on_file_deleted)
        
        # İşlenmekte olan dosyaları takip et (çoklu event önlemi)
        self.processing_files = set()
        
        # Masaüstünde kalması istenen dosyaları takip et (tekrar işlenmemesi için)
        self.processed_desktop_files = set()  # {file_path_string}
        
        # Gerekli dizinleri oluştur
        create_directories(self.config.CATEGORIES)
        
        # AI durumunu kontrol et ve bildir
        ai_status = self.ai_renamer.get_ai_status()
        if ai_status['available']:
            self.logger.info("AI renamer hazır")
        else:
            self.logger.warning("AI renamer kullanılamıyor - GEMINI_API_KEY gerekli")
        
        # Başlangıçta hatırlanan tercihleri kontrol et
        self._check_startup_preferences()
    
    def _check_startup_preferences(self):
        """Başlangıçta hatırlanan tercihleri kontrol et ve kullanıcıya sor"""
        try:
            preference_count = self.user_preferences.get_remembered_preferences_count()
            
            if preference_count > 0:
                print(f"{Fore.CYAN}🧠 {preference_count} hatırlanan tercih bulundu...{Style.RESET_ALL}")
                
                # GUI modunda hatırlanan tercihleri göster
                if self.config.GUI_ENABLED and self.config.SHOW_STARTUP_PREFERENCES:
                    try:
                        preferences_summary = self.user_preferences.get_remembered_preferences_summary()
                        result = show_startup_preferences(preferences_summary)
                        
                        if result == 'clear':
                            self.user_preferences.clear_remembered_preferences()
                            print(f"{Fore.GREEN}🗑️ Hatırlanan tercihler temizlendi{Style.RESET_ALL}")
                            self.logger.info("Kullanıcı hatırlanan tercihleri temizledi")
                        elif result == 'keep':
                            print(f"{Fore.GREEN}✅ Hatırlanan tercihler korundu{Style.RESET_ALL}")
                            self.logger.info("Kullanıcı hatırlanan tercihleri korudu")
                        elif result == 'settings':
                            print(f"{Fore.BLUE}⚙️ Ayarlar penceresi açıldı{Style.RESET_ALL}")
                            
                    except Exception as e:
                        print(f"{Fore.RED}❌ Tercih dialogu hatası: {e}{Style.RESET_ALL}")
                        self.logger.error(f"Startup preferences dialog hatası: {e}")
                        
                else:
                    # Console modunda basit bilgilendirme
                    print(f"{Fore.BLUE}ℹ️ {preference_count} dosya türü için hatırlanan tercihler kullanılacak{Style.RESET_ALL}")
                    
        except Exception as e:
            self.logger.error(f"Startup preferences kontrolü hatası: {e}")
            print(f"{Fore.RED}❌ Tercih kontrolü hatası: {e}{Style.RESET_ALL}")
    
    def on_file_deleted(self, file_path):
        """Dosya silindiğinde çalışacak callback fonksiyonu"""
        file_key = str(file_path.resolve())
        
        # İşlenmiş dosyalar listesinden çıkar
        if file_key in self.processed_desktop_files:
            self.processed_desktop_files.remove(file_key)
            self.logger.debug(f"Silinen dosya işlenmiş listesinden çıkarıldı: {file_path.name}")
        
        # İşlenmekte olan dosyalar listesinden çıkar
        if file_key in self.processing_files:
            self.processing_files.remove(file_key)
        
    def on_file_event(self, file_path):
        """Dosya olayı geldiğinde çalışacak callback fonksiyonu"""
        # Çoklu event önlemi - eğer dosya zaten işleniyorsa atla
        file_key = str(file_path.resolve())
        if file_key in self.processing_files:
            self.logger.debug(f"Dosya zaten işleniyor, atlandı: {file_path.name}")
            return
        
        # Masaüstünde kalması istenen dosyaları kontrol et
        if file_key in self.processed_desktop_files:
            self.logger.debug(f"Dosya daha önce işlendi ve masaüstünde kalması istendi, atlandı: {file_path.name}")
            return
        
        # Dosyayı işleme listesine ekle
        self.processing_files.add(file_key)
        
        try:
            # Dosyanın hala var olup olmadığını kontrol et
            if not file_path.exists():
                self.logger.debug(f"Dosya bulunamadı (muhtemelen taşındı): {file_path}")
                return
            
            # İkinci kontrol
            if not file_path.exists():
                self.logger.debug(f"Dosya callback sırasında bulunamadı: {file_path}")
                return
                
            # İçerik çıkarma kontrolü
            if self.content_extractor.is_supported(file_path):
                print(f"{Fore.CYAN}İçerik çıkarılıyor: {os.path.basename(file_path)}{Style.RESET_ALL}")
                
                # Dosyadan içerik çıkar
                extraction_result = self.content_extractor.extract_content(file_path)
                
                if extraction_result['success']:
                    content = extraction_result['content']
                    print(f"{Fore.GREEN}İçerik çıkarıldı ({len(content)} karakter){Style.RESET_ALL}")
                    print(f"{Fore.BLUE}İlk 200 karakter: {content[:200]}...{Style.RESET_ALL}")
                    
                    # İçerik çıkarma sonrası dosya handle'larının bırakılması için kısa bekleme
                    import time
                    time.sleep(0.2)
                    
                    # ÖNEMLİ: Dosya hala var mı HEMEN kontrol et!
                    if not file_path.exists():
                        print(f"{Fore.RED}DOSYA İÇERİK ÇIKARMADAN SONRA KAYBOLDU!{Style.RESET_ALL}")
                        self.logger.error(f"Dosya içerik çıkarma sonrası kayboldu: {file_path}")
                        
                        # Dosyanın nereye gittiğini bul
                        print(f"{Fore.YELLOW}Dosya aranıyor...{Style.RESET_ALL}")
                        for category_path_str in self.config.CATEGORIES.values():
                            category_path = Path(category_path_str)
                            if category_path.exists():
                                for existing_file in category_path.glob("*"):
                                    if existing_file.name == file_path.name:
                                        print(f"{Fore.BLUE}DOSYA BULUNDU: {existing_file}{Style.RESET_ALL}")
                                        self.logger.info(f"Dosya farklı yerde bulundu: {existing_file}")
                                        return
                        
                        # Desktop'ta farklı isimle mi var?
                        for existing_file in file_path.parent.glob("*"):
                            if existing_file.suffix == file_path.suffix and existing_file != file_path:
                                print(f"{Fore.CYAN}BENZER DOSYA: {existing_file.name}{Style.RESET_ALL}")
                        
                        return
                    
                    # AI ile dosya adı önerisi al (sadece önerisi)
                    ai_suggested_name = None
                    if self.config.AI_RENAME_ENABLED and self.ai_renamer.get_ai_status()['available']:
                        print(f"{Fore.MAGENTA}AI ile dosya adı önerisi alınıyor...{Style.RESET_ALL}")
                        
                        ai_result = self.ai_renamer.get_ai_name_suggestion(file_path, content)
                        if ai_result['success']:
                            ai_suggested_name = ai_result['suggested_name']
                            print(f"{Fore.GREEN}AI önerisi hazır: {ai_suggested_name}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.YELLOW}AI önerisi alınamadı: {ai_result.get('error', 'Bilinmeyen hata')}{Style.RESET_ALL}")
                    
                    self.logger.info(f"İçerik çıkarıldı: {file_path.name} - {len(content)} karakter")
                    
                else:
                    print(f"{Fore.YELLOW}İçerik çıkarılamadı: {extraction_result['error']}{Style.RESET_ALL}")
                    self.logger.warning(f"İçerik çıkarma hatası: {file_path.name} - {extraction_result['error']}")
            
            # Son kontrol: Dosya hala var mı?
            if not file_path.exists():
                self.logger.debug(f"Dosya bulunamadı: {file_path}")
                return
            
            # Dosya organizasyonu kararı
            self._process_file_organization(
                file_path, 
                content if 'content' in locals() else None,
                ai_suggested_name if 'ai_suggested_name' in locals() else None
            )
                
        finally:
            # İşlem bittiğinde dosyayı processing listesinden çıkar
            if file_key in self.processing_files:
                self.processing_files.remove(file_key)
    
    def _process_file_organization(self, file_path, content=None, ai_suggested_name=None):
        """Dosya organizasyonu kararını ver ve uygula"""
        try:
            # Dosya uzantısını kontrol et - kullanıcı bu uzantıyı devre dışı bırakmış mı?
            file_extension = file_path.suffix.lower()
            if not self.user_preferences.is_extension_enabled(file_extension):
                print(f"{Fore.YELLOW}⏭️ {file_path.name} - Bu uzantı devre dışı{Style.RESET_ALL}")
                self.logger.info(f"Uzantı devre dışı: {file_path.name}")
                return
            
            # Dosya türünü belirle
            suggested_category = self.file_classifier.classify_file(file_path)
            
            if not suggested_category:
                print(f"{Fore.YELLOW}❓ {file_path.name} - Kategori belirlenemedi{Style.RESET_ALL}")
                self.logger.info(f"Sınıflandırılamadı: {file_path.name}")
                return
            
            # Kategori devre dışı mı?
            if not self.user_preferences.is_category_enabled(suggested_category):
                print(f"{Fore.YELLOW}⏭️ {file_path.name} - {suggested_category} kategorisi devre dışı{Style.RESET_ALL}")
                self.logger.info(f"Kategori devre dışı: {file_path.name} -> {suggested_category}")
                return
            
            # Kullanıcı modunu kontrol et
            user_mode = self.user_preferences.get_mode()
            
            # Hatırlanan seçimi kontrol et
            remembered_choice = self.user_preferences.get_remembered_choice(file_extension)
            
            if user_mode == 'log_only':
                # Sadece logla, taşıma
                print(f"{Fore.BLUE}📝 {file_path.name} -> {suggested_category} (Sadece loglama modu){Style.RESET_ALL}")
                self.logger.info(f"LOG ONLY: {file_path.name} -> {suggested_category}")
                return
            
            elif user_mode == 'auto' or remembered_choice:
                # Otomatik mod veya hatırlanan seçim
                if remembered_choice:
                    action = remembered_choice['action']
                    category = remembered_choice['category']
                    print(f"{Fore.CYAN}🔄 {file_path.name} - Hatırlanan seçim kullanılıyor{Style.RESET_ALL}")
                else:
                    action = 'move'
                    category = suggested_category
                    print(f"{Fore.CYAN}🤖 {file_path.name} - Otomatik işleniyor{Style.RESET_ALL}")
                
                self._execute_file_action(file_path, action, category)
            
            elif user_mode == 'ask':
                # Kullanıcıya sor
                if remembered_choice:
                    # Hatırlanan seçim varsa onu kullan
                    action = remembered_choice['action']
                    category = remembered_choice['category']
                    print(f"{Fore.CYAN}💭 {file_path.name} - Hatırlanan seçim: {action} -> {category}{Style.RESET_ALL}")
                    self._execute_file_action(file_path, action, category)
                else:
                    # Kullanıcıya sor modu - tek dialog ile AI önerisi de dahil
                    print(f"{Fore.MAGENTA}❓ {file_path.name} - Kullanıcı onayı bekleniyor...{Style.RESET_ALL}")
                    
                    # AI önerisi varsa onu da dahil et
                    final_ai_name = None
                    if (ai_suggested_name and 
                        self.config.AI_RENAME_ASK_USER and 
                        ai_suggested_name != file_path.name):
                        final_ai_name = ai_suggested_name
                        print(f"{Fore.CYAN}🤖 AI önerisi: {ai_suggested_name}{Style.RESET_ALL}")
                    
                    try:
                        result = show_file_confirmation(file_path, suggested_category, final_ai_name)
                        
                        if result and result['action'] != 'skip':
                            # AI rename işlemi
                            final_file_path = file_path
                            original_file_key = str(file_path.resolve())  # Orijinal path'i sakla
                            
                            if result.get('use_ai_name', False) and final_ai_name:
                                # AI ismiyle yeniden adlandır
                                suggested_path = file_path.parent / final_ai_name
                                
                                # Çakışma kontrolü
                                counter = 1
                                while suggested_path.exists() and suggested_path != file_path:
                                    name_parts = Path(final_ai_name).stem, Path(final_ai_name).suffix
                                    suggested_path = file_path.parent / f"{name_parts[0]}_{counter}{name_parts[1]}"
                                    counter += 1
                                
                                # Dosyayı yeniden adlandır
                                try:
                                    if suggested_path != file_path:
                                        file_path.rename(suggested_path)
                                        final_file_path = suggested_path
                                        print(f"{Fore.GREEN}✅ AI ile yeniden adlandırıldı: {suggested_path.name}{Style.RESET_ALL}")
                                        self.logger.info(f"AI rename: {file_path.name} -> {suggested_path.name}")
                                except Exception as e:
                                    print(f"{Fore.RED}❌ AI rename hatası: {e}{Style.RESET_ALL}")
                                    self.logger.error(f"AI rename hatası: {e}")
                            
                            # Masaüstünde kalma kontrolü
                            if result.get('keep_on_desktop', False):
                                # Dosyayı işlenmiş listesine ekle (tekrar işlenmemesi için)
                                # Hem orijinal hem de yeni path'i ekle (AI rename durumu için)
                                self.processed_desktop_files.add(original_file_key)
                                final_file_key = str(final_file_path.resolve())
                                self.processed_desktop_files.add(final_file_key)
                                print(f"{Fore.CYAN}🏠 {final_file_path.name} - Masaüstünde kaldı{Style.RESET_ALL}")
                                self.logger.info(f"Dosya masaüstünde kaldı ve işlenmiş listesine eklendi: {final_file_path.name}")
                                return  # Organize etme, masaüstünde bırak
                            
                            # Normal organize işlemi
                            action = result['action']
                            category = result['category']
                            
                            # Hatırla seçeneği işaretlenmişse kaydet
                            if result.get('remember', False):
                                self.user_preferences.remember_choice(file_extension, action, category)
                                print(f"{Fore.GREEN}💾 {file_extension} uzantısı için seçim hatırlandı{Style.RESET_ALL}")
                            
                            self._execute_file_action(final_file_path, action, category)
                        else:
                            print(f"{Fore.YELLOW}⏭️ {file_path.name} - Kullanıcı tarafından atlandı{Style.RESET_ALL}")
                            self.logger.info(f"Kullanıcı tarafından atlandı: {file_path.name}")
                    
                    except Exception as e:
                        self.logger.error(f"GUI dialog hatası: {e}")
                        print(f"{Fore.RED}❌ GUI hatası, otomatik işleniyor: {file_path.name}{Style.RESET_ALL}")
                        self._execute_file_action(file_path, 'move', suggested_category)
            
        except Exception as e:
            self.logger.error(f"Dosya organizasyon hatası: {e}", exc_info=True)
            print(f"{Fore.RED}❌ Hata: {file_path.name} işlenemedi{Style.RESET_ALL}")
    
    def _execute_file_action(self, file_path, action, category):
        """Dosya eylemini uygula (taşı, kopyala)"""
        try:
            if action == 'move':
                success = self.file_manager.move_file(file_path, category)
                if success:
                    print(f"{Fore.GREEN}✅ Taşındı: {file_path.name} -> {category}{Style.RESET_ALL}")
                    self.logger.info(f"MOVED: {file_path.name} -> {category}")
                else:
                    print(f"{Fore.RED}❌ Taşıma başarısız: {file_path.name}{Style.RESET_ALL}")
                    self.logger.error(f"MOVE FAILED: {file_path.name}")
            
            elif action == 'copy':
                success = self.file_manager.copy_file(file_path, category)
                if success:
                    print(f"{Fore.GREEN}📋 Kopyalandı: {file_path.name} -> {category}{Style.RESET_ALL}")
                    self.logger.info(f"COPIED: {file_path.name} -> {category}")
                else:
                    print(f"{Fore.RED}❌ Kopyalama başarısız: {file_path.name}{Style.RESET_ALL}")
                    self.logger.error(f"COPY FAILED: {file_path.name}")
                    
        except Exception as e:
            self.logger.error(f"Dosya eylem hatası ({action}): {e}", exc_info=True)
            print(f"{Fore.RED}❌ İşlem hatası: {file_path.name}{Style.RESET_ALL}")
    
    def start(self):
        """Uygulamayı başlat"""
        print(f"{Fore.CYAN}Akıllı Masaüstü Organizatörü Başlatılıyor...{Style.RESET_ALL}")
        print(f"{Fore.BLUE}İzlenen klasör: {self.config.WATCH_DIRECTORY}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Kategoriler: {', '.join(self.config.CATEGORIES.keys())}{Style.RESET_ALL}")
        
        # Kullanıcı modu bilgisi
        user_mode = self.user_preferences.get_mode()
        mode_text = {
            'ask': '❓ Her dosya için onay istenir',
            'auto': '🤖 Otomatik taşıma (onay istenmez)',
            'log_only': '📝 Sadece loglama (taşıma yapılmaz)'
        }
        print(f"{Fore.GREEN}Mod: {mode_text.get(user_mode, user_mode)}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}💡 Yeni dosya oluşturduğunuzda gerçek bir isim verinceye kadar beklerim{Style.RESET_ALL}")
        print(f"{Fore.BLUE}⏰ Varsayılan isim bırakırsanız {self.config.PENDING_FILE_TIMEOUT} saniye sonra otomatik işlerim{Style.RESET_ALL}")
        
        # AI durumu
        if self.config.AI_RENAME_ENABLED:
            ai_status = self.ai_renamer.get_ai_status()
            if ai_status['available']:
                ask_text = "sorarım" if self.config.AI_RENAME_ASK_USER else "otomatik uygularım"
                print(f"{Fore.CYAN}🤖 AI rename aktif - İçerik analizi sonrası {ask_text}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}🤖 AI rename aktif ama kullanılamıyor (GEMINI_API_KEY gerekli){Style.RESET_ALL}")
        else:
            print(f"{Fore.GRAY}🤖 AI rename devre dışı{Style.RESET_ALL}")
        
        print(f"{Fore.YELLOW}Çıkmak için Ctrl+C tuşlayın{Style.RESET_ALL}")
        print("-" * 60)
        
        try:
            self.watcher.start()
            self.logger.info("Desktop Organizer başlatıldı")
            
            # Ana döngü
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Uygulama kapatılıyor...{Style.RESET_ALL}")
            self.logger.info("Uygulama kullanıcı tarafından durduruldu")
            
        except Exception as e:
            print(f"{Fore.RED}Beklenmeyen hata: {e}{Style.RESET_ALL}")
            self.logger.error(f"Beklenmeyen hata: {e}")
            
        finally:
            self.watcher.stop()
            print(f"{Fore.GREEN}Güvenli şekilde kapatıldı{Style.RESET_ALL}")

def main():
    """Ana fonksiyon"""
    try:
        organizer = DesktopOrganizer()
        organizer.start()
    except Exception as e:
        print(f"{Fore.RED}Başlatma hatası: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
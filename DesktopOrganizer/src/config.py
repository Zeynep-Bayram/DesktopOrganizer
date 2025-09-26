#!/usr/bin/env python3
"""
Temel ayarlar dosyası
"""

import os
from pathlib import Path

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv yüklü değilse devam et

class Config:
    """Proje ayarları"""
    
    def __init__(self):
        # Ana dizinler
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.LOGS_DIR = self.DATA_DIR / "logs"
        
        
        # OneDrive desktop yolunu kullan
        desktop_path = Path(r"C:\Users\pc\OneDrive\Documents\OneDrive\Masaüstü")
        self.WATCH_DIRECTORY = str(desktop_path)
        self.CATEGORIES = {
             'Resimler': str(desktop_path / "Organize" / "Resimler"),
            'Belgeler': str(desktop_path / "Organize" / "Belgeler"),
            'Videolar': str(desktop_path / "Organize" / "Videolar"),
            'Müzikler': str(desktop_path / "Organize" / "Müzikler"),
            'Arşivler': str(desktop_path / "Organize" / "Arşivler"),
            'Kodlar': str(desktop_path / "Organize" / "Kodlar"),
            'Tablolar': str(desktop_path / "Organize" / "Tablolar"),    
            'Sunumlar': str(desktop_path / "Organize" / "Sunumlar"),     
            'Kurulumlar': str(desktop_path / "Organize" / "Kurulumlar"),
            'E-kitaplar': str(desktop_path / "Organize" / "E-kitaplar"),
            'Kısayollar': str(desktop_path / "Organize" / "Kısayollar"),
            'Diğer': str(desktop_path / "Organize" / "Diğer")          
        }
        
        # Dosya çakışması çözümü
        self.CONFLICT_RESOLUTION = 'rename'  # 'rename', 'overwrite', 'skip'
        
        # Log ayarları
        self.LOG_LEVEL = 'INFO'
        self.LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
        
        # GUI ayarları
        self.GUI_ENABLED = True
        self.SHOW_CONFIRMATION = True  # Her dosya için onay iste
        self.AUTO_ORGANIZE = False     # Otomatik organize etme modu
        
        # Timeout ayarları (.env'den okunur)
        self.PENDING_FILE_TIMEOUT = int(os.getenv('PENDING_FILE_TIMEOUT', '60'))  # Varsayılan 60 saniye
        self.CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', '20'))  # Varsayılan 20 saniye
        self.FILE_STABILITY_CHECK_INTERVAL = float(os.getenv('FILE_STABILITY_CHECK_INTERVAL', '0.5'))  # Varsayılan 0.5 saniye
        self.FILE_STABILITY_CHECKS = int(os.getenv('FILE_STABILITY_CHECKS', '3'))  # Varsayılan 3 kez kontrol
        
        # AI Rename ayarları (.env'den okunur)
        self.AI_RENAME_ENABLED = os.getenv('AI_RENAME_ENABLED', 'true').lower() == 'true'
        self.AI_RENAME_ASK_USER = os.getenv('AI_RENAME_ASK_USER', 'true').lower() == 'true'  # AI rename için kullanıcıya sor
        
        # Başlangıç ayarları (.env'den okunur)
        self.SHOW_STARTUP_PREFERENCES = os.getenv('SHOW_STARTUP_PREFERENCES', 'true').lower() == 'true'


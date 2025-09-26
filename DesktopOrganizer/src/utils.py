#!/usr/bin/env python3
"""
Yardımcı fonksiyonlar
"""

import os
import logging
from datetime import datetime
from pathlib import Path

def setup_logging():
    """Loglama sistemini kur"""
    # Logs klasörünü oluştur
    logs_dir = Path(__file__).parent.parent / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Log dosyası adı (bugünün tarihi)
    log_file = logs_dir / f"organizer_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Loglama ayarları
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Konsola da yazdır
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Loglama sistemi başlatıldı")
    
    return logger

def create_directories(categories):
    """Kategori klasörlerini oluştur"""
    created_dirs = []
    
    for category, directory in categories.items():
        try:
            os.makedirs(directory, exist_ok=True)
            created_dirs.append(f"✅ {category}: {directory}")
        except Exception as e:
            created_dirs.append(f"❌ {category}: HATA - {e}")
    
    return created_dirs

def get_file_size_readable(file_path):
    """Dosya boyutunu okunabilir formatta döndür"""
    try:
        size = os.path.getsize(file_path)
        
        # Byte cinsinden boyut
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} MB"
        else:
            return f"{size/(1024*1024*1024):.1f} GB"
    except:
        return "Bilinmiyor"

def is_hidden_file(file_path):
    """Dosyanın gizli olup olmadığını kontrol et"""
    filename = os.path.basename(file_path)
    
    # Gizli dosya işaretleri
    hidden_indicators = ['.', '~$', 'Thumbs.db', 'desktop.ini', '.DS_Store']
    
    for indicator in hidden_indicators:
        if filename.startswith(indicator):
            return True
    
    return False


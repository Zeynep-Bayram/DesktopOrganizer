#!/usr/bin/env python3
"""
Dosya Sınıflandırma Modülü - Dosyaları türüne göre kategorilere ayırır
"""

import os
import logging
from pathlib import Path
from config import Config

class FileClassifier:
    """Dosya sınıflandırma sınıfı"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Dosya uzantılarına göre kategori haritası
        self.extension_categories = {
            # Resim dosyaları
            'Resimler': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico'],
            
            # Video dosyaları
            'Videolar': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.3gp'],
            
            # Müzik dosyaları
            'Müzikler': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'],
            
            # Belgeler
            'Belgeler': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
            
            # Elektronik tablolar
            'Tablolar': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
            
            # Sunumlar
            'Sunumlar': ['.ppt', '.pptx', '.odp', '.key','pptx' ],
            
            # Kod dosyaları
            'Kodlar': ['.py', '.ipynb', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs'],
            
            # Arşiv dosyaları
            'Arşivler': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            
            # Kurulum dosyaları
            'Kurulumlar': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appimage'],
            
            # E-kitaplar
            'E-kitaplar': ['.epub', '.mobi', '.azw', '.azw3', '.fb2'],
            
            # Kısayollar
            'Kısayollar': ['.lnk', '.url', '.website']
        }
        
        # Dosya isimlerindeki anahtar kelimeler
        self.keyword_categories = {
            'Faturalar': ['fatura', 'invoice', 'receipt', 'makbuz', 'fiş'],
            'CV': ['cv', 'resume', 'özgeçmiş', 'resume'],
            'Projeler': ['proje', 'project', 'ödev', 'assignment'],
            'Dersler': ['ders', 'lecture', 'course', 'kurs', 'eğitim'],
            'Rapor': ['rapor', 'report', 'analiz', 'analysis'],
            'Sertifikalar': ['sertifika', 'certificate', 'diploma', 'belge']
        }
    
    def classify_file(self, file_path):
        """Dosyayı sınıflandır ve kategori döndür"""
        try:
            file_name = os.path.basename(file_path)
            file_extension = Path(file_path).suffix.lower()
            
            # 1. Uzantıya göre sınıflandırma
            category = self._classify_by_extension(file_extension)
            if category:
                self.logger.debug(f"Uzantıya göre sınıflandırıldı: {file_name} -> {category}")
                return category
            
            # 2. Dosya ismine göre sınıflandırma
            category = self._classify_by_filename(file_name)
            if category:
                self.logger.debug(f"Dosya ismine göre sınıflandırıldı: {file_name} -> {category}")
                return category
            
            # 3. Varsayılan kategori
            self.logger.debug(f"Sınıflandırılamadı: {file_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Sınıflandırma hatası: {e}")
            return None
    
    def _classify_by_extension(self, extension):
        """Dosya uzantısına göre sınıflandır"""
        for category, extensions in self.extension_categories.items():
            if extension in extensions:
                return category
        return None
    
    def _classify_by_filename(self, filename):
        """Dosya ismine göre sınıflandır"""
        filename_lower = filename.lower()
        
        for category, keywords in self.keyword_categories.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return category
        return None
    
    def get_file_info(self, file_path):
        """Dosya hakkında detaylı bilgi al"""
        try:
            stat = os.stat(file_path)
            return {
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'extension': Path(file_path).suffix.lower(),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'category': self.classify_file(file_path)
            }
        except Exception as e:
            self.logger.error(f"Dosya bilgisi alma hatası: {e}")
            return None
    
    def add_custom_rule(self, category, extensions=None, keywords=None):
        """Özel sınıflandırma kuralı ekle"""
        try:
            if extensions:
                if category not in self.extension_categories:
                    self.extension_categories[category] = []
                self.extension_categories[category].extend(extensions)
            
            if keywords:
                if category not in self.keyword_categories:
                    self.keyword_categories[category] = []
                self.keyword_categories[category].extend(keywords)
            
            self.logger.info(f"Özel kural eklendi: {category}")
            return True
            
        except Exception as e:
            self.logger.error(f"Özel kural ekleme hatası: {e}")
            return False
    
    def get_supported_categories(self):
        """Desteklenen kategorileri döndür"""
        return list(set(list(self.extension_categories.keys()) + list(self.keyword_categories.keys())))
    
    def get_category_extensions(self, category):
        """Belirli bir kategorinin uzantılarını döndür"""
        return self.extension_categories.get(category, [])
    
    def get_category_keywords(self, category):
        """Belirli bir kategorinin anahtar kelimelerini döndür"""
        return self.keyword_categories.get(category, [])
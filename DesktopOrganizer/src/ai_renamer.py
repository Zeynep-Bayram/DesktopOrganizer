#!/usr/bin/env python3
"""
AI Dosya Adlandırma Modülü - Gemini AI ile akıllı dosya adlandırma
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv yüklü değilse devam et

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIFileRenamer:
    """Gemini AI kullanarak dosya adlandırma sınıfı"""
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = "gemini-2.0-flash"
        
        if not GEMINI_AVAILABLE:
            logger.error("google-genai paketi yüklü değil. 'pip install google-genai' ile yükleyin.")
            self.available = False
            return
            
        if not self.api_key:
            logger.error("GEMINI_API_KEY çevre değişkeni ayarlanmamış.")
            self.available = False
            return
            
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.available = True
            logger.info("Gemini AI client başarıyla başlatıldı")
        except Exception as e:
            logger.error(f"Gemini AI client başlatma hatası: {e}")
            self.available = False
    
    def generate_filename(self, content: str, file_type: str) -> Optional[str]:
        """
        Dosya içeriğine göre akıllı dosya adı önerir
        
        Args:
            content: Dosya içeriği
            file_type: Dosya türü (pdf, docx, vb.)
            
        Returns:
            Önerilen dosya adı veya None
        """
        if not self.available:
            logger.warning("AI renamer kullanılamıyor")
            return None
            
        try:
            # System instruction için prompt hazırla
            system_prompt = """Sen bir akıllı dosya adlandırma asistanısın. Kullanıcıdan bir dosyanın içeriğini alacaksın ve bu içeriğe göre uygun, anlaşılır ve düzenli bir dosya adı önereceksin.

GÖREVIN:
- Dosya içeriğini analiz et
- İçeriğin ana konusunu, türünü ve amacını belirle
- Kısa, açık ve düzenli bir dosya adı öner

KURALLAR:
1. Dosya adı maksimum 50 karakter olmalı
2. Türkçe karakterler kullanabilirsin (ğ, ü, ş, ı, ö, ç)
3. Boşluk yerine alt çizgi (_) kullan
4. Özel karakterler kullanma (/, \\, :, *, ?, \", <, >, |)
5. Tarih varsa YYYY-MM-DD formatında ekle
6. Dosya uzantısını EKLEME (sadece isim öner)

DOSYA TÜRLERİNE GÖRE ÖNERİLER:
- Fatura/Makbuz: "fatura_sirket_adı_YYYY-MM-DD"
- Rapor: "rapor_konu_YYYY-MM-DD"
- Sunum: "sunum_konu_YYYY-MM-DD"
- Sözleşme: "sozlesme_tip_YYYY-MM-DD"
- Özgeçmiş: "ozgecmis_ad_soyad"
- Makale/Araştırma: "makale_konu"
- Görsel: "gorsel_aciklama" veya "foto_yer_tarih"
- Diğer: içeriğe uygun açıklayıcı isim

ÖRNEK ÇIKTILAR:
- "fatura_turkcell_2024-03-15"
- "rapor_satis_analizi_2024-Q1"
- "sunum_proje_sunumu"
- "sozlesme_kira_2024"
- "makale_yapay_zeka_trend"
- "foto_istanbul_bogazici"

Sadece önerilen dosya adını yaz, başka açıklama yapma."""

            # User prompt hazırla
            user_prompt = f"""DOSYA İÇERİĞİ:
{content[:2000]}  

DOSYA TÜRÜ: {file_type}

Yukarıdaki dosya içeriğine göre uygun bir dosya adı öner."""

            # API çağrısı
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_prompt)]
                )
            ]
            
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                system_instruction=[types.Part.from_text(text=system_prompt)],
                temperature=0.3,  # Daha tutarlı sonuçlar için düşük temperature
                max_output_tokens=100  # Kısa cevap için limit
            )
            
            # Stream yerine tek seferde al
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config
            )
            
            if response.text:
                suggested_name = response.text.strip()
                # Temizle ve doğrula
                suggested_name = self._clean_filename(suggested_name)
                logger.info(f"AI önerisi: {suggested_name}")
                return suggested_name
            else:
                logger.warning("AI'dan boş cevap geldi")
                return None
                
        except Exception as e:
            logger.error(f"AI dosya adı üretme hatası: {e}")
            return None
    
    def _clean_filename(self, filename: str) -> str:
        """
        Dosya adını temizler ve güvenli hale getirir
        
        Args:
            filename: Ham dosya adı
            
        Returns:
            Temizlenmiş dosya adı
        """
        # Satır sonlarını ve fazla boşlukları temizle
        filename = filename.strip().replace('\n', '').replace('\r', '')
        
        # Yasak karakterleri temizle
        forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in forbidden_chars:
            filename = filename.replace(char, '')
        
        # Boşlukları alt çizgi ile değiştir
        filename = filename.replace(' ', '_')
        
        # Çoklu alt çizgileri tek alt çizgi yap
        while '__' in filename:
            filename = filename.replace('__', '_')
        
        # Başında ve sonunda alt çizgi varsa kaldır
        filename = filename.strip('_')
        
        # Maksimum 50 karakter
        if len(filename) > 50:
            filename = filename[:50].rstrip('_')
        
        return filename
    
    def is_available(self) -> bool:
        """AI renamer'ın kullanılabilir olup olmadığını döndürür"""
        return self.available


class SmartFileRenamer:
    """Dosya yeniden adlandırma işlemlerini yöneten sınıf"""
    
    def __init__(self):
        self.ai_renamer = AIFileRenamer()
        self.logger = logging.getLogger(__name__)
    
    def rename_file_with_ai(self, file_path: Path, content: str, file_type: str) -> Tuple[bool, Path]:
        """
        AI önerisi ile dosyayı yeniden adlandırır
        
        Args:
            file_path: Mevcut dosya yolu
            content: Dosya içeriği
            file_type: Dosya türü
            
        Returns:
            (başarılı_mı, yeni_dosya_yolu) tuple'ı
        """
        try:
            if not self.ai_renamer.is_available():
                self.logger.warning("AI renamer kullanılamıyor, dosya adı değiştirilmedi")
                return False, file_path
            
            # AI'dan öneri al
            suggested_name = self.ai_renamer.generate_filename(content, file_type)
            
            if not suggested_name:
                self.logger.warning("AI'dan dosya adı önerisi alınamadı")
                return False, file_path
            
            # Yeni dosya yolunu oluştur
            new_filename = suggested_name + file_path.suffix
            new_file_path = file_path.parent / new_filename
            
            # Eğer aynı isimde dosya varsa numaralandır
            counter = 1
            while new_file_path.exists() and new_file_path != file_path:
                base_name = suggested_name
                new_filename = f"{base_name}_{counter}{file_path.suffix}"
                new_file_path = file_path.parent / new_filename
                counter += 1
            
            # Dosyayı yeniden adlandır
            if new_file_path != file_path:
                # Dosyanın hala var olup olmadığını kontrol et
                if not file_path.exists():
                    self.logger.warning(f"Dosya bulunamadı: {file_path}")
                    return False, file_path
                
                # Windows'ta dosya kilitleme sorunlarını önlemek için birkaç deneme
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        file_path.rename(new_file_path)
                        self.logger.info(f"Dosya AI ile yeniden adlandırıldı: {file_path.name} -> {new_filename}")
                        return True, new_file_path
                    except (FileExistsError, PermissionError, FileNotFoundError) as e:
                        if attempt < max_attempts - 1:
                            import time
                            time.sleep(0.5)  # Kısa bekleme
                            continue
                        else:
                            self.logger.warning(f"Dosya yeniden adlandırılamadı (3 deneme): {e}")
                            return False, file_path
            else:
                self.logger.info("Dosya adı zaten uygun, değiştirilmedi")
                return True, file_path
                
        except Exception as e:
            self.logger.error(f"AI ile dosya yeniden adlandırma hatası: {e}")
            return False, file_path
    
    def get_ai_status(self) -> Dict[str, Any]:
        """AI renamer durumunu döndürür"""
        return {
            'available': self.ai_renamer.is_available(),
            'api_key_set': bool(os.environ.get("GEMINI_API_KEY")),
            'gemini_installed': GEMINI_AVAILABLE
        }
    
    def get_ai_name_suggestion(self, file_path: Path, content: str) -> Dict[str, Any]:
        """
        GUI için AI isim önerisi al (dosyayı yeniden adlandırmadan)
        
        Args:
            file_path: Dosya yolu
            content: Dosya içeriği
            
        Returns:
            {'success': bool, 'suggested_name': str, 'error': str}
        """
        try:
            if not self.ai_renamer.is_available():
                return {
                    'success': False,
                    'suggested_name': None,
                    'error': 'AI renamer kullanılamıyor'
                }
            
            file_type = file_path.suffix.lower().lstrip('.')
            suggested_name = self.ai_renamer.generate_filename(content, file_type)
            
            if suggested_name:
                # Uzantıyı da ekle tam dosya adı için
                full_suggested_name = suggested_name + file_path.suffix
                return {
                    'success': True,
                    'suggested_name': full_suggested_name,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'suggested_name': None,
                    'error': 'AI\'dan öneri alınamadı'
                }
                
        except Exception as e:
            self.logger.error(f"AI öneri alma hatası: {e}")
            return {
                'success': False,
                'suggested_name': None,
                'error': str(e)
            }



#!/usr/bin/env python3
"""
GUI Yönetici Modülü - Kullanıcı arayüzü ve onay dialogları
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import logging
from pathlib import Path
from config import Config

class FileConfirmationDialog:
    """Dosya taşıma onay dialogu"""
    
    def __init__(self, file_path, suggested_category, ai_suggested_name=None):
        self.file_path = Path(file_path)
        self.suggested_category = suggested_category
        self.ai_suggested_name = ai_suggested_name
        self.result = None
        self.root = None
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
    def show(self):
        """Dialog'u göster ve kullanıcı seçimini döndür"""
        self.root = tk.Toplevel()
        self.root.title("Dosya Organizasyonu - Onay")
        # AI önerisi varsa daha geniş yap
        width = 650 if self.ai_suggested_name else 550
        height = 450 if self.ai_suggested_name else 380
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, False)
        
        # Pencereyi üstte tut
        self.root.attributes('-topmost', True)
        self.root.grab_set()  # Modal yap
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Dosya bilgileri
        ttk.Label(main_frame, text="Yeni dosya tespit edildi:", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="Dosya:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(main_frame, text=self.file_path.name, font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(main_frame, text="Önerilen kategori:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(main_frame, text=self.suggested_category, font=('Arial', 10, 'bold'), foreground='blue').grid(row=2, column=1, sticky=tk.W)
        
        current_row = 3
        
        # AI önerisi varsa göster
        if self.ai_suggested_name:
            ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            current_row += 1
            
            ttk.Label(main_frame, text="🤖 AI Dosya Adı Önerisi:", font=('Arial', 11, 'bold'), foreground='blue').grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
            current_row += 1
            
            # Mevcut isim
            ttk.Label(main_frame, text="Mevcut:", font=('Arial', 9)).grid(row=current_row, column=0, sticky=tk.W, padx=(20, 5))
            ttk.Label(main_frame, text=self.file_path.name, font=('Arial', 9), foreground='gray').grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1
            
            # AI önerisi
            ttk.Label(main_frame, text="AI Önerisi:", font=('Arial', 9, 'bold')).grid(row=current_row, column=0, sticky=tk.W, padx=(20, 5))
            ttk.Label(main_frame, text=self.ai_suggested_name, font=('Arial', 9, 'bold'), foreground='green').grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1
            
            # Dosya adı seçimi
            ttk.Label(main_frame, text="Dosya adı:", font=('Arial', 10, 'bold')).grid(row=current_row, column=0, sticky=tk.W, pady=(10, 5))
            current_row += 1
            
            self.filename_var = tk.StringVar(value="current")
            filename_frame = ttk.Frame(main_frame)
            filename_frame.grid(row=current_row, column=0, columnspan=2, sticky=tk.W, padx=(20, 0))
            
            ttk.Radiobutton(filename_frame, text="📝 Mevcut ismi kullan", 
                           variable=self.filename_var, value="current").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
            ttk.Radiobutton(filename_frame, text="🤖 AI önerisini kullan", 
                           variable=self.filename_var, value="ai").grid(row=0, column=1, sticky=tk.W)
            current_row += 1
        else:
            self.filename_var = None
        
        # Kategori seçimi
        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        current_row += 1
        
        ttk.Label(main_frame, text="Kategori seçin:", font=('Arial', 11, 'bold')).grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        self.category_var = tk.StringVar(value=self.suggested_category)
        category_frame = ttk.Frame(main_frame)
        category_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Kategori combobox
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                          values=list(self.config.CATEGORIES.keys()), 
                                          state="readonly", width=20)
        self.category_combo.grid(row=0, column=0, padx=(0, 10))
        current_row += 1
        
        # İşlem seçimi
        ttk.Label(main_frame, text="Ne yapmak istiyorsunuz?", font=('Arial', 11, 'bold')).grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=2, pady=10)
        
        if self.ai_suggested_name:
            # AI önerisi varsa, masaüstünde kalma seçeneği de ekle
            ttk.Button(button_frame, text="✅ Taşı", command=lambda: self._set_result('move'), 
                      style='Accent.TButton').grid(row=0, column=0, padx=3)
            ttk.Button(button_frame, text="📋 Kopyala", command=lambda: self._set_result('copy')).grid(row=0, column=1, padx=3)
            ttk.Button(button_frame, text="🏠 Masaüstünde Kal", command=lambda: self._set_result('stay_desktop')).grid(row=0, column=2, padx=3)
            ttk.Button(button_frame, text="❌ Atla", command=lambda: self._set_result('skip')).grid(row=0, column=3, padx=3)
        else:
            ttk.Button(button_frame, text="✅ Taşı", command=lambda: self._set_result('move'), 
                      style='Accent.TButton').grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="📋 Kopyala", command=lambda: self._set_result('copy')).grid(row=0, column=1, padx=5)
            ttk.Button(button_frame, text="❌ Atla", command=lambda: self._set_result('skip')).grid(row=0, column=2, padx=5)
        current_row += 1
        
        # Alt kısım - ayarlar
        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        current_row += 1
        
        # Bu kategori için hatırla checkbox
        self.remember_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text=f"Bu tür dosyalar için hatırla ({self.file_path.suffix})", 
                       variable=self.remember_var).grid(row=current_row, column=0, columnspan=2, sticky=tk.W)
        current_row += 1
        
        # Ayarlar butonu
        ttk.Button(main_frame, text="⚙️ Ayarlar", command=self._open_settings).grid(row=current_row, column=0, sticky=tk.W, pady=(10, 0))
        
        # Pencereyi ortala
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        # Enter ve Escape tuşları
        self.root.bind('<Return>', lambda e: self._set_result('move'))
        self.root.bind('<Escape>', lambda e: self._set_result('skip'))
        
        # Dialog'u bekle
        self.root.wait_window()
        
        return self.result
    
    def _set_result(self, action):
        """Sonucu ayarla ve pencereyi kapat"""
        selected_category = self.category_var.get()
        remember = self.remember_var.get()
        
        # AI dosya adı seçimi
        use_ai_name = False
        final_filename = self.file_path.name
        if self.filename_var and self.filename_var.get() == "ai":
            use_ai_name = True
            final_filename = self.ai_suggested_name
        
        self.result = {
            'action': action,
            'category': selected_category,
            'remember': remember,
            'extension': self.file_path.suffix.lower(),
            'use_ai_name': use_ai_name,
            'final_filename': final_filename,
            'keep_on_desktop': action == 'stay_desktop'
        }
        
        self.root.destroy()
    
    def _open_settings(self):
        """Ayarlar penceresini aç"""
        SettingsWindow()

class SettingsWindow:
    """Ayarlar penceresi"""
    
    def __init__(self):
        self.config = Config()
        self.root = tk.Toplevel()
        self.root.title("Dosya Organizatörü - Ayarlar")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Pencereyi üstte tut
        self.root.attributes('-topmost', True)
        self.root.grab_set()
        
        self._create_widgets()
        self._load_settings()
        
        # Pencereyi ortala
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Notebook (sekmeli arayüz)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Genel ayarlar sekmesi
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="🏠 Genel")
        
        # Otomatik işlem modu
        ttk.Label(general_frame, text="İşlem Modu:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.mode_var = tk.StringVar()
        ttk.Radiobutton(general_frame, text="🤖 Otomatik taşı (onay isteme)", 
                       variable=self.mode_var, value="auto").grid(row=1, column=0, sticky=tk.W, padx=20)
        ttk.Radiobutton(general_frame, text="❓ Her dosya için sor (önerilen)", 
                       variable=self.mode_var, value="ask").grid(row=2, column=0, sticky=tk.W, padx=20)
        ttk.Radiobutton(general_frame, text="📝 Sadece logla, taşıma", 
                       variable=self.mode_var, value="log_only").grid(row=3, column=0, sticky=tk.W, padx=20)
        
        # Kategori ayarları sekmesi
        categories_frame = ttk.Frame(notebook, padding="10")
        notebook.add(categories_frame, text="📁 Kategoriler")
        
        ttk.Label(categories_frame, text="Kategori Ayarları:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Kategori listesi
        self.category_vars = {}
        for i, category in enumerate(self.config.CATEGORIES.keys()):
            var = tk.BooleanVar(value=True)
            self.category_vars[category] = var
            ttk.Checkbutton(categories_frame, text=f"📂 {category}", 
                           variable=var).grid(row=i+1, column=0, sticky=tk.W, padx=20)
        
        # Uzantı ayarları sekmesi
        extensions_frame = ttk.Frame(notebook, padding="10")
        notebook.add(extensions_frame, text="🔧 Uzantılar")
        
        ttk.Label(extensions_frame, text="Uzantı Bazlı Ayarlar:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Scrollable frame for extensions
        canvas = tk.Canvas(extensions_frame, height=200)
        scrollbar = ttk.Scrollbar(extensions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Uzantı ayarları
        self.extension_vars = {}
        row = 0
        from file_classifier import FileClassifier
        classifier = FileClassifier()
        
        for category, extensions in classifier.extension_categories.items():
            ttk.Label(scrollable_frame, text=f"{category}:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
            row += 1
            
            for ext in extensions:
                var = tk.BooleanVar(value=True)
                self.extension_vars[ext] = var
                ttk.Checkbutton(scrollable_frame, text=ext, variable=var).grid(row=row, column=0, sticky=tk.W, padx=20)
                row += 1
        
        # Butonlar
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="💾 Kaydet", command=self._save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ İptal", command=self.root.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="🔄 Varsayılan", command=self._reset_settings).pack(side=tk.LEFT)
    
    def _load_settings(self):
        """Ayarları yükle"""
        try:
            settings_file = self.config.DATA_DIR / "user_settings.json"
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                self.mode_var.set(settings.get('mode', 'ask'))
                
                # Kategori ayarları
                disabled_categories = settings.get('disabled_categories', [])
                for category, var in self.category_vars.items():
                    var.set(category not in disabled_categories)
                
                # Uzantı ayarları
                disabled_extensions = settings.get('disabled_extensions', [])
                for ext, var in self.extension_vars.items():
                    var.set(ext not in disabled_extensions)
            else:
                self.mode_var.set('ask')  # Varsayılan
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar yüklenirken hata: {e}")
    
    def _save_settings(self):
        """Ayarları kaydet"""
        try:
            settings = {
                'mode': self.mode_var.get(),
                'disabled_categories': [cat for cat, var in self.category_vars.items() if not var.get()],
                'disabled_extensions': [ext for ext, var in self.extension_vars.items() if not var.get()]
            }
            
            settings_file = self.config.DATA_DIR / "user_settings.json"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilirken hata: {e}")
    
    def _reset_settings(self):
        """Varsayılan ayarlara dön"""
        if messagebox.askyesno("Onay", "Tüm ayarları varsayılana döndürmek istediğinize emin misiniz?"):
            self.mode_var.set('ask')
            for var in self.category_vars.values():
                var.set(True)
            for var in self.extension_vars.values():
                var.set(True)

class UserPreferences:
    """Kullanıcı tercihlerini yöneten sınıf"""
    
    def __init__(self):
        self.config = Config()
        self.settings_file = self.config.DATA_DIR / "user_settings.json"
        self.logger = logging.getLogger(__name__)
        self._load_settings()
    
    def _load_settings(self):
        """Ayarları yükle"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = self._get_default_settings()
        except Exception as e:
            self.logger.error(f"Ayarlar yüklenirken hata: {e}")
            self.settings = self._get_default_settings()
    
    def _get_default_settings(self):
        """Varsayılan ayarları döndür"""
        return {
            'mode': 'ask',  # 'auto', 'ask', 'log_only'
            'disabled_categories': [],
            'disabled_extensions': [],
            'remembered_choices': {}  # uzantı -> {'action': 'move', 'category': 'Belgeler'}
        }
    
    def get_mode(self):
        """İşlem modunu döndür"""
        return self.settings.get('mode', 'ask')
    
    def is_category_enabled(self, category):
        """Kategorinin aktif olup olmadığını kontrol et"""
        return category not in self.settings.get('disabled_categories', [])
    
    def is_extension_enabled(self, extension):
        """Uzantının aktif olup olmadığını kontrol et"""
        return extension not in self.settings.get('disabled_extensions', [])
    
    def get_remembered_choice(self, extension):
        """Uzantı için hatırlanan seçimi döndür"""
        return self.settings.get('remembered_choices', {}).get(extension)
    
    def remember_choice(self, extension, action, category):
        """Uzantı için seçimi hatırla"""
        if 'remembered_choices' not in self.settings:
            self.settings['remembered_choices'] = {}
        
        self.settings['remembered_choices'][extension] = {
            'action': action,
            'category': category
        }
        self._save_settings()
    
    def _save_settings(self):
        """Ayarları kaydet"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Ayarlar kaydedilirken hata: {e}")
    
    def get_remembered_preferences_count(self):
        """Hatırlanan tercih sayısını döndür"""
        return len(self.settings.get('remembered_choices', {}))
    
    def clear_remembered_preferences(self):
        """Hatırlanan tercihleri temizle"""
        self.settings['remembered_choices'] = {}
        self._save_settings()
        self.logger.info("Hatırlanan tercihler temizlendi")
    
    def get_remembered_preferences_summary(self):
        """Hatırlanan tercihlerin özetini döndür"""
        choices = self.settings.get('remembered_choices', {})
        summary = []
        for ext, choice in choices.items():
            summary.append({
                'extension': ext,
                'action': choice['action'],
                'category': choice['category']
            })
        return summary

class StartupPreferencesDialog:
    """Başlangıçta hatırlanan tercihleri gösteren dialog"""
    
    def __init__(self, preferences_summary):
        self.preferences_summary = preferences_summary
        self.result = None
        self.root = None
        
    def show(self):
        """Dialog'u göster ve kullanıcı seçimini döndür"""
        self.root = tk.Toplevel()
        self.root.title("Hatırlanan Tercihler")
        self.root.geometry("650x450")
        self.root.resizable(True, True)
        
        # Pencereyi üstte tut
        self.root.attributes('-topmost', True)
        self.root.grab_set()  # Modal yap
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Başlık
        ttk.Label(main_frame, text="🧠 Hatırlanan Tercihleriniz", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Açıklama
        explanation = f"Önceden {len(self.preferences_summary)} farklı dosya türü için tercih belirtmişsiniz.\nBu tercihler otomatik olarak uygulanacak."
        ttk.Label(main_frame, text=explanation, font=('Arial', 10)).grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # Tercih listesi
        ttk.Label(main_frame, text="Mevcut Tercihler:", font=('Arial', 11, 'bold')).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Scrollable liste
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # Treeview for better display
        columns = ('Uzantı', 'İşlem', 'Kategori')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # Define headings
        tree.heading('Uzantı', text='Dosya Uzantısı')
        tree.heading('İşlem', text='İşlem')
        tree.heading('Kategori', text='Kategori')
        
        # Configure column widths
        tree.column('Uzantı', width=120, anchor='center')
        tree.column('İşlem', width=120, anchor='center')
        tree.column('Kategori', width=150, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Populate treeview
        for pref in self.preferences_summary:
            action_text = {'move': '📁 Taşı', 'copy': '📋 Kopyala', 'skip': '⏭️ Atla'}.get(pref['action'], pref['action'])
            tree.insert('', tk.END, values=(pref['extension'], action_text, pref['category']))
        
        # Configure grid weights
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="✅ Tercihleri Kullan", 
                  command=lambda: self._set_result('keep'), 
                  style='Accent.TButton').grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="🗑️ Tercihleri Temizle", 
                  command=lambda: self._set_result('clear')).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="⚙️ Ayarları Aç", 
                  command=lambda: self._set_result('settings')).grid(row=0, column=2, padx=10)
        
        # Alt bilgi
        ttk.Label(main_frame, text="💡 Bu dialog sadece hatırlanan tercihleriniz varsa gösterilir", 
                 font=('Arial', 9), foreground='gray').grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Pencereyi ortala
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        # Tuş bağlamaları
        self.root.bind('<Return>', lambda e: self._set_result('keep'))
        self.root.bind('<Escape>', lambda e: self._set_result('keep'))
        
        # Grid weights
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Dialog'u bekle
        self.root.wait_window()
        
        return self.result
    
    def _set_result(self, choice):
        """Sonucu ayarla ve pencereyi kapat"""
        self.result = choice
        if choice == 'settings':
            # Ayarlar penceresini aç
            SettingsWindow()
        self.root.destroy()

def show_startup_preferences(preferences_summary):
    """Başlangıç tercih dialogunu göster"""
    try:
        # Tkinter root window oluştur (gizli)
        root = tk.Tk()
        root.withdraw()  # Ana pencereyi gizle
        
        dialog = StartupPreferencesDialog(preferences_summary)
        result = dialog.show()
        
        root.destroy()
        return result
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Startup preferences dialog hatası: {e}")
        return 'keep'  # Varsayılan olarak tercihleri tut


def show_file_confirmation(file_path, suggested_category, ai_suggested_name=None):
    """Dosya onay dialogunu göster - main fonksiyon"""
    try:
        # Tkinter root window oluştur (gizli)
        root = tk.Tk()
        root.withdraw()  # Ana pencereyi gizle
        
        dialog = FileConfirmationDialog(file_path, suggested_category, ai_suggested_name)
        result = dialog.show()
        
        root.destroy()
        return result
    
    except Exception as e:
        logging.getLogger(__name__).error(f"GUI dialog hatası: {e}")
        return {'action': 'skip', 'category': suggested_category, 'remember': False}

if __name__ == "__main__":
    # Test için
    root = tk.Tk()
    root.withdraw()
    
    result = show_file_confirmation(
        Path("C:/Users/test/Desktop/test.pdf"),
        "Belgeler",
        "Yeni_Dokuman.pdf"
    )
    
    print("Sonuç:", result)
    root.destroy()
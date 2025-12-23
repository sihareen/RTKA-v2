import json
import os
import config as default_cfg

# Dapatkan lokasi absolut file ini (modules/config_loader.py)
# Lalu naik satu level agar file json tersimpan di root folder proyek (sejajar main.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")

class ConfigManager:
    def __init__(self):
        self.use_user_config = False
        self.user_data = {}
        
        print(f"[CFG] Lokasi File Config: {CONFIG_FILE}")
        self.load_user_config()

    def load_user_config(self):
        """Membaca file JSON jika ada"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.user_data = json.load(f)
                print(f"[CFG] SUCCESS: User config loaded ({len(self.user_data)} keys)")
            except Exception as e:
                print(f"[CFG] ERROR: File ada tapi rusak! {e}")
                self.user_data = {}
        else:
            print("[CFG] WARNING: File user_config.json TIDAK DITEMUKAN. Menggunakan Default.")
            self.user_data = {}

    def save_user_config(self, new_config):
        """Menyimpan config dari App ke JSON"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(new_config, f, indent=4)
            self.user_data = new_config
            print(f"[CFG] SAVED: Config berhasil disimpan ke {CONFIG_FILE}")
            
            # Verifikasi ulang (Reload)
            self.load_user_config()
            
        except Exception as e:
            print(f"[CFG] SAVE FAILED: Gagal menulis file! {e}")

    def get_pin(self, category, key, default_value):
        """
        Logika Pengambilan Pin
        """
        # Debugging (Opsional: Nyalakan jika ingin melihat detail per pin)
        # if self.use_user_config:
        #     print(f"[CFG] Request {category}.{key}...", end="")

        if self.use_user_config and category in self.user_data:
            val = self.user_data[category].get(key)
            if val is not None:
                # print(f" FOUND: {val}")
                return val
        
        # print(f" FALLBACK: {default_value}")
        return default_value

# Instance Global
cfg_mgr = ConfigManager()
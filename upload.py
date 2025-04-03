import os
import sqlite3
import time
import json
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

# 設定 OneDrive 目錄
ONEDRIVE_PATH = os.path.expanduser(r"C:\Onedrive")  # 修改成你的 OneDrive 路徑
DB_FILE = "onedrive_monitor.db"
CONFIG_FILE = "config.json"

# 加載 API 設定
def load_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("❌ 設定檔格式錯誤！請檢查 JSON 格式")
                return {}
    return {}

# 讀取 API 設定
settings = load_settings()
API_URL = settings.get("upload_url", "").strip()

# 監控事件處理
class OneDriveEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        """ 當檔案或資料夾被創建時 """
        relative_path = os.path.relpath(event.src_path, ONEDRIVE_PATH)

        print(event)

        # 確保這不是「移動」的結果
        if hasattr(event, 'is_moved') and event.is_moved:
            return

        if event.is_directory:
            print(f"🆕 [新增資料夾] {relative_path}")
            self.log_event("📁 [新增資料夾]", event.src_path, None, None, True)
            api_create_folder(event.src_path)
        else:
            print(f"🆕 [新增檔案] {relative_path}")
            self.log_event("📄 [新增檔案]", event.src_path, None, None, False)

    def on_modified(self, event):
        """ 當檔案被修改時 """
        if not event.is_directory:
            print(f"✏️ [修改] {event.src_path}")
            self.log_event("✏️ [修改]", event.src_path, None, None, False)

    def on_deleted(self, event):
        """ 當檔案或資料夾被刪除時 """
        relative_path = os.path.relpath(event.src_path, ONEDRIVE_PATH)
        print(f"🗑️ [刪除] {relative_path}")
        self.log_event("🗑️ [刪除]", event.src_path, None, None, event.is_directory)

    def on_moved(self, event):
        """ 當檔案或資料夾被移動時 """
        old_relative_path = os.path.relpath(event.src_path, ONEDRIVE_PATH)
        new_relative_path = os.path.relpath(event.dest_path, ONEDRIVE_PATH)

        print(f"🔄 [移動] {old_relative_path} ➝ {new_relative_path}")
        self.log_event("🔄 [移動]", event.dest_path, event.src_path, event.dest_path, event.is_directory)

        # **修正：如果是資料夾，通知 API**
        if event.is_directory:
            api_update_folder(old_relative_path, new_relative_path)

        # 標記 `on_created()` 讓它不誤判為「新增」
        event.is_moved = True

    def log_event(self, event_type, file_path, old_path=None, new_path=None, is_directory=False):
        """ 記錄事件到資料庫 """
        relative_path = os.path.relpath(file_path, ONEDRIVE_PATH)
        item_name = os.path.basename(relative_path)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO file_changes (event_type, item_name, relative_path, old_location, new_location, is_directory) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_type, item_name, relative_path, old_path, new_path, int(is_directory)))
        conn.commit()
        conn.close()

def api_create_folder(folder_name):
    """ API - 創建資料夾 """
    if not os.path.isdir(folder_name):  # 確保只處理資料夾
        return

    folder_name = os.path.relpath(folder_name, ONEDRIVE_PATH).replace("\\", "/")
    print(f"📡 API - 創建資料夾: {folder_name}")

    data = {"mode": "I", "foldername": folder_name}
    requests.post(API_URL, json=data)

def api_update_folder(old_folder_name, new_folder_name):
    """ API - 更新資料夾名稱 """
    if not os.path.isdir(new_folder_name):  # 確保只處理資料夾
        return

    old_folder = os.path.relpath(old_folder_name, ONEDRIVE_PATH).replace("\\", "/")
    new_folder = os.path.relpath(new_folder_name, ONEDRIVE_PATH).replace("\\", "/")
    print(f"📡 API - 更新資料夾: {old_folder} ➝ {new_folder}")

    data = {"mode": "R", "foldername": old_folder, "newfoldername": new_folder}
    requests.post(API_URL, json=data)

def start_monitor():
    """ 啟動 OneDrive 監控 """
    if not os.path.exists(ONEDRIVE_PATH):
        print(f"❌ OneDrive 目錄不存在: {ONEDRIVE_PATH}")
        return

    event_handler = OneDriveEventHandler()
    observer = Observer()
    observer.schedule(event_handler, ONEDRIVE_PATH, recursive=True)
    observer.start()
    print(f"✅ 監控 OneDrive 目錄: {ONEDRIVE_PATH}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_monitor()

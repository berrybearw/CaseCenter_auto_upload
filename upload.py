

import time
from cytomine import Cytomine
from cytomine.models import Project, UploadedFileCollection, StorageCollection

# Cytomine 伺服器資訊
host = "http://10.40.4.67"  # 如果支援 HTTPS，請改成 "https://10.40.4.67"
public_key = "497c5ed2-3a63-4616-af93-0f5088fd14d6"
private_key = "0c46458c-0079-4426-9880-32af6ff9f37c"

# 目標專案 ID 和切片檔案
project_id = 10707720
wsi_path = r"C:\Users\Administrator\Downloads\5.svs"  # 確保路徑正確

try:
    with Cytomine(host, public_key, private_key) as cytomine:
        # 確認專案是否存在
        project = Project().fetch(project_id)
        if not project:
            print("❌ 指定的專案不存在。請檢查 project_id 是否正確！")
        else:
            print(f"✅ 找到專案 {project.id}，準備上傳切片...")

            # 取得 Storage ID
            storages = StorageCollection().fetch()

            storage_id = storages[0].id

            print("storage_id : ", storage_id)

            # 執行上傳
            help(cytomine)
            uploaded_file = cytomine.upload_image(upload_host="http://10.40.4.67:8083", id_project=project_id, id_storage=storage_id, filename=wsi_path)

            # 上傳完成後檢查回應
            if uploaded_file:
                print(f"✅ 檔案已提交，檔案 ID: {uploaded_file.id}")
            else:
                print("❌ 上傳失敗！請檢查 Cytomine 伺服器是否正常運行。")

    # **確認上傳狀態**
    print("\n⏳ 等待上傳狀態更新...\n")
    time.sleep(10)  # 等待 10 秒再查詢

    with Cytomine(host, public_key, private_key) as cytomine:
        uploaded_files = UploadedFileCollection().fetch()
        for file in uploaded_files:
            print(f"📌 ID: {file.id}, 狀態: {file.status}, 檔案: {file.filename}")

            if file.status == 0:
                print("🔄 上傳進行中...")
            elif file.status == 1:
                print("✅ 上傳完成，處理中...")
            elif file.status == 2:
                print("✅ 解析完成，影像已加入 Cytomine！")
            elif file.status == 3:
                print("❌ 解析失敗，請檢查影像格式是否正確。")

except Exception as e:
    print(f"🚨 發生錯誤: {e}")


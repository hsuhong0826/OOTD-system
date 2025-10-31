# Render 部署完整指南

這份指南說明如何將穿搭助理系統部署到 Render。

## 📋 部署前檢查清單

### ✅ 必要檔案 (已準備完成)
- ✅ `app.py` - 主程式
- ✅ `database.py` - 資料庫模組
- ✅ `weather.py` - 天氣 API 模組
- ✅ `email_notifier.py` - Email 通知模組
- ✅ `requirements.txt` - Python 套件列表
- ✅ `render.yaml` - Render 設定檔
- ✅ `.gitignore` - Git 忽略檔案設定

### ⚠️ 不會上傳到 GitHub 的檔案
- `.env` - 本地環境變數 (已在 .gitignore 中)
- `OOTD_venv/` - 虛擬環境
- `__pycache__/` - Python 快取
- `data/*.db` - 本地資料庫檔案

---

## 🚀 部署步驟

### 步驟 1️⃣: 推送程式碼到 GitHub

```bash
# 進入專案目錄
cd /path/to/OOTD

# 初始化 Git (如果還沒有)
git init

# 加入所有檔案
git add .

# 提交變更
git commit -m "準備部署到 Render"

# 加入遠端儲存庫 (替換成您的 GitHub 儲存庫網址)
git remote add origin https://github.com/您的帳號/OOTD.git

# 推送到 GitHub
git push -u origin main
```

---

### 步驟 2️⃣: 在 Render 建立服務

#### 方法一：使用 Blueprint（✅ 推薦）

此方法使用 `render.yaml` 配置檔，最簡單快速！

1. **登入 Render Dashboard**
   - 前往 https://dashboard.render.com/
   - 使用 GitHub 帳號登入

2. **建立新的 Blueprint**
   - 點擊右上角 **「New」** → **「Blueprint」**
   - 選擇您的 GitHub repository
   - Render 會自動偵測 `render.yaml` 檔案

3. **設定環境變數** ⭐ **重要!**
   
   在建立過程中，您需要設定以下環境變數：

   | Key (完全一樣複製) | Value (填入您的資料) | 說明 |
   |-------------------|---------------------|------|
   | `OPENWEATHER_API_KEY` | 您的 API 金鑰 | OpenWeatherMap API 金鑰<br>未設定會使用模擬天氣資料 |
   | `SMTP_EMAIL` | your_email@gmail.com | Gmail 帳號 (用於發送通知)<br>選用功能 |
   | `SMTP_PASSWORD` | 您的應用程式密碼 | Gmail 應用程式密碼<br>選用功能 |

   **💡 如何新增環境變數:**
   - 點選 **「Add Environment Variable」**
   - 在 **Key** 欄位輸入變數名稱
   - 在 **Value** 欄位貼上對應的值
   - **不需要**加引號
   - **完全複製**上方的 Key 名稱 (大小寫要一致)

4. **確認並部署**
   - 檢查配置無誤後，點擊 **「Apply」**
   - Render 會自動開始建置和部署

#### 方法二：手動建立 Web Service

如果不使用 Blueprint，可以手動建立：

1. **建立 Web Service**
   - 點擊 **「New」** → **「Web Service」**
   - 選擇 "Build and deploy from a Git repository"
   - 連接您的 GitHub repository

2. **基本設定**
   ```
   Name: ootd-assistant
   Region: Oregon (US West)
   Branch: main
   Root Directory: (留空)
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python app.py
   ```

3. **選擇方案**
   - 選擇 **「Free」** plan
   - 注意：免費方案會在無活動 15 分鐘後休眠

4. **進階設定**
   - 點擊 **「Advanced」** 按鈕
   - 新增環境變數（Environment Variables）：
     ```
     PYTHON_VERSION = 3.11.0
     OPENWEATHER_API_KEY = your_api_key（選用）
     SMTP_EMAIL = your_email@gmail.com（選用）
     SMTP_PASSWORD = your_app_password（選用）
     ```

5. **設定 Persistent Disk**（重要！）
   - 在 "Disks" 區塊點擊 **「Add Disk」**
   - 設定：
     ```
     Name: data
     Mount Path: /opt/render/project/src/data
     Size: 1 GB
     ```
   - 這樣資料庫檔案才不會在重啟後遺失

6. **建立 Service**
   - 點擊 **「Create Web Service」**
   - Render 會自動開始建置和部署

---

### 步驟 3️⃣: 等待部署完成

部署通常需要 3-5 分鐘，您可以在 Logs 查看建置進度。

**建置過程:**
```
==> Downloading Buildpack...
==> Installing dependencies from requirements.txt
==> Successfully installed gradio requests APScheduler...
==> Starting service with: python app.py
==> Your service is live 🎉
```

完成後，您的應用程式會在以下網址運行：
```
https://ootd-assistant.onrender.com
```
(實際網址會在部署完成後顯示)

---

### 步驟 4️⃣: 測試功能

**測試清單:**
1. ✅ 開啟網址
2. ✅ 註冊/登入帳號
3. ✅ 新增衣物
4. ✅ 查看天氣資訊 (台北、泰山等城市)
5. ✅ 設定每日通知
6. ✅ 查看穿搭建議
7. ✅ 資料在重啟後仍然存在（Persistent Disk 生效）

---

## ⚙️ 環境變數說明

在 Service → Settings → Environment 中設定：

| 變數名稱 | 必要性 | 說明 |
|---------|-------|------|
| `PYTHON_VERSION` | 建議 | Python 版本（建議 3.11.0）<br>已在 render.yaml 中設定 |
| `OPENWEATHER_API_KEY` | 選用 | OpenWeatherMap API 金鑰<br>**未設定會使用模擬天氣資料** |
| `SMTP_EMAIL` | 選用 | Gmail 帳號（用於發送通知） |
| `SMTP_PASSWORD` | 選用 | Gmail 應用程式密碼 |

**重要提醒:**
- Gmail 必須使用「**應用程式密碼**」，不是一般密碼
  1. 前往 Google 帳戶 → 安全性
  2. 啟用「兩步驟驗證」
  3. 建立「應用程式密碼」(16位字元)
  4. 將該密碼填入 `SMTP_PASSWORD`
- 未設定 API Key 時，系統會自動使用模擬資料
- 環境變數會在服務重啟後保留

---

## 🔧 常見問題與解決方案

### ❌ 問題 1: 建置失敗 - "No module named 'dotenv'"

**原因:** Render 環境不需要 python-dotenv

**解決方案:** ✅ 已解決!程式碼會檢查 `.env` 檔案是否存在,在 Render 上不會載入 dotenv

---

### ❌ 問題 2: 環境變數沒有生效

**檢查步驟:**
1. 到 Render Dashboard → 您的服務 → **Environment**
2. 確認環境變數都存在
3. 檢查 Key 的拼字和大小寫是否正確
4. 重新部署: **Manual Deploy** → **Deploy latest commit**

---

### ❌ 問題 3: 資料庫無法寫入或資料重啟後消失

**原因:** Render 需要設定 Persistent Disk

**解決方案:** 
- 使用 Blueprint 部署時會自動設定 (已在 `render.yaml` 中)
- 手動部署需要在 "Disks" 設定中加入:
  ```
  Name: data
  Mount Path: /opt/render/project/src/data
  Size: 1 GB
  ```

---

### ❌ 問題 4: 服務睡眠 (Free Plan 限制)

**Render 免費方案限制:**
- ⚠️ 15 分鐘無活動會進入睡眠
- ⚠️ 下次訪問時需要等待 30-60 秒喚醒

**這是正常行為:**
- 對於個人使用或展示專案已經足夠
- 如需永久運行，升級到付費方案 ($7/月)

---

### ❌ 問題 5: 應用程式啟動後馬上停止

**檢查步驟:**
1. 查看 Logs 了解錯誤訊息
2. 確認 Start Command: `python app.py`
3. 確認 `app.py` 中有正確啟動 Gradio server
4. 檢查 Python 版本是否設為 3.11.0

---

## 🔄 更新部署

當您修改程式碼後:

**方法一：自動部署**
```bash
# 提交變更
git add .
git commit -m "更新功能"
git push

# Render 會自動偵測並重新部署
```

**方法二：手動部署**
1. 到 Render Dashboard
2. 點選 **「Manual Deploy」**
3. 選擇 **「Deploy latest commit」**

---

## 📊 監控與維護

### 查看 Logs
- 在 Service Dashboard 點擊 **「Logs」**
- 可以即時查看應用程式輸出
- 錯誤訊息會顯示在這裡

### 查看資源使用
- Dashboard 會顯示 CPU 和記憶體使用狀況
- 免費方案提供 512 MB RAM

### 服務狀態
- **Live**: 服務正常運行
- **Deploying**: 正在部署中
- **Sleeping**: 休眠狀態 (免費方案)

---

## 🆓 免費方案限制

Render 免費方案包含：
- ✅ 750 小時/月的運行時間
- ✅ 512 MB RAM
- ✅ 1 GB 永久儲存空間 (Persistent Disk)
- ✅ 免費 SSL 憑證
- ✅ 支援自訂網域
- ⚠️ 15 分鐘無活動後休眠
- ⚠️ 每月流量限制（100 GB）

對於個人使用或展示專案來說，**免費方案已經足夠！**

---

## 📝 自訂網域（選用）

Render 支援自訂網域：

1. 在 Service Settings 找到 **「Custom Domains」**
2. 點擊 **「Add Custom Domain」**
3. 輸入您的網域名稱
4. 在您的 DNS 提供商設定 CNAME 記錄
5. 等待 SSL 憑證自動配置完成

免費方案也支援自訂網域和免費 SSL！

---

## 📞 需要協助?

- Render 官方文件: https://render.com/docs
- Render 社群論壇: https://community.render.com/
- Gradio 部署指南: https://www.gradio.app/guides/deploying-gradio-with-docker
- 專案 GitHub Issues: 在您的儲存庫建立 Issue

---

## 🎉 恭喜!

您的穿搭助理應用程式已成功部署到 Render!

**您的應用程式網址:**
```
https://ootd-assistant.onrender.com
```

---

**版本**：Render 部署指南 v2.0  
**更新日期**：2025-10-31
   Root Directory: (留空)
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python app.py
   ```

3. **選擇方案**
   - 選擇 "Free" plan
   - 注意：免費方案會在無活動 15 分鐘後休眠

4. **進階設定**
   - 點擊 "Advanced" 按鈕
   - 新增環境變數（Environment Variables）：
     ```
     PYTHON_VERSION = 3.11.0
     OPENWEATHER_API_KEY = your_api_key（選用）
     SMTP_EMAIL = your_email@gmail.com（選用）
     SMTP_PASSWORD = your_app_password（選用）
     ```

5. **設定 Persistent Disk**（重要！）
   - 在 "Disks" 區塊點擊 "Add Disk"
   - 設定：
     ```
     Name: data
     Mount Path: /opt/render/project/src/data
     Size: 1 GB
     ```
   - 這樣資料庫檔案才不會在重啟後遺失

6. **建立 Service**
   - 點擊 "Create Web Service"
   - Render 會自動開始建置和部署

### 步驟：等待部署完成

部署通常需要 3-5 分鐘，您可以在 Logs 查看建置進度。

完成後，您的應用程式會在以下網址運行：
```
https://ootd-assistant.onrender.com
```

## 🎯 部署後檢查清單

- [ ] Service 成功啟動，狀態顯示 "Live"
- [ ] 可以開啟應用程式介面
- [ ] 可以註冊新帳號
- [ ] 可以登入
- [ ] 可以新增衣物
- [ ] 資料在重啟後仍然存在（Persistent Disk 生效）
- [ ] 天氣功能正常（如有設定 API Key）
- [ ] Email 功能正常（如有設定 SMTP）

## ⚙️ 環境變數說明

在 Service → Settings → Environment 中設定：

| 變數名稱 | 必要性 | 說明 |
|---------|-------|------|
| `PYTHON_VERSION` | 建議 | Python 版本（建議 3.11.0） |
| `OPENWEATHER_API_KEY` | 選用 | OpenWeatherMap API 金鑰<br>未設定會使用模擬天氣資料 |
| `SMTP_EMAIL` | 選用 | Gmail 帳號（用於發送通知） |
| `SMTP_PASSWORD` | 選用 | Gmail 應用程式密碼 |

**注意**：
- 免費方案的環境變數會在服務重啟後保留
- Gmail 必須使用「應用程式密碼」，不是一般密碼
- 未設定 API Key 時，系統會自動降級使用模擬資料

## 📊 監控與維護

### 查看 Logs
- 在 Service Dashboard 點擊 "Logs"
- 可以即時查看應用程式輸出
- 錯誤訊息會顯示在這裡

### 重新部署
- 推送新的 commit 到 GitHub 會自動觸發重新部署
- 或在 Dashboard 點擊 "Manual Deploy" → "Deploy latest commit"

### 暫停服務
- 免費方案在無活動 15 分鐘後會自動休眠
- 下次訪問時會自動喚醒（約需 30 秒）
- 如需永久運行，請升級到付費方案

## 🆓 免費方案限制

Render 免費方案包含：
- ✅ 750 小時/月的運行時間
- ✅ 512 MB RAM
- ✅ 1 GB 永久儲存空間
- ⚠️ 15 分鐘無活動後休眠
- ⚠️ 每月有流量限制（100 GB）

對於個人使用或展示專案來說，免費方案已經足夠！

## 🔧 常見問題

### Q1: 部署失敗，顯示 "Build failed"
**A:** 檢查 Logs，常見原因：
- `requirements.txt` 有錯誤的套件版本
- Python 版本不相容
- 解決方法：確認 `PYTHON_VERSION` 環境變數設為 3.11.0

### Q2: 應用程式啟動後馬上停止
**A:** 檢查 Start Command 是否正確：
- 應該是：`python app.py`
- 確認 `app.py` 中有啟動 Gradio server

### Q3: 資料在重啟後消失
**A:** 確認 Persistent Disk 已正確設定：
- Mount Path: `/opt/render/project/src/data`
- 確認 `database.py` 的資料庫路徑正確

### Q4: 服務太久沒用就無法訪問
**A:** 這是免費方案的正常行為：
- 15 分鐘無活動後會休眠
- 重新訪問時會自動喚醒（約 30 秒）
- 如需永久運行，升級到付費方案（$7/月起）

### Q5: 如何更新應用程式？
**A:** 有兩種方法：
1. 推送新的 commit 到 GitHub（自動部署）
2. 在 Dashboard 點擊 "Manual Deploy"

## 📝 自訂網域（選用）

Render 支援自訂網域：

1. 在 Service Settings 找到 "Custom Domains"
2. 點擊 "Add Custom Domain"
3. 輸入您的網域名稱
4. 在您的 DNS 提供商設定 CNAME 記錄
5. 等待 SSL 憑證自動配置完成

免費方案也支援自訂網域和免費 SSL！

## 🔄 從 Hugging Face 遷移

如果您之前部署在 Hugging Face Spaces：

1. **資料備份**
   - 從 HF Spaces 下載 `data/clothes.db`
   - 將資料庫檔案放入新的 Render 部署

2. **環境變數**
   - 在 Render 中設定相同的環境變數
   - 格式完全相同，直接複製即可

3. **更新連結**
   - 更新所有指向舊 HF Spaces 的連結
   - 新連結格式：`https://your-service.onrender.com`

## 🎉 完成！

恭喜！您的穿搭助理系統已成功部署到 Render。

有任何問題，請參考：
- [Render 官方文檔](https://render.com/docs)
- [Gradio 部署指南](https://www.gradio.app/guides/deploying-gradio-with-docker)
- 專案 README 和完整說明

---

**版本**：Render 部署指南 v1.0  
**更新日期**：2025-10-30

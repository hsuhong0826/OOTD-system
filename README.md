---
title: 穿搭助理
emoji: 👔
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.20.0
app_file: app.py
pinned: false
license: mit
---

# 👔 穿搭助理系統

智能衣櫥管理與每日穿搭規劃 Web 應用程式，支援手機瀏覽、資料永久保存，可免費部署於 Hugging Face Spaces。

## ✨ 功能特色

### 🔐 使用者系統
- 帳號註冊與登入（密碼加密儲存）
- 多使用者支援，資料完全隔離
- Session 管理
- 忘記密碼功能

### 👕 衣物管理
- **新增衣物**：類別、顏色、材質、袖長、季節、場合
- **衣物名稱**：可選填自訂名稱（預設 "XXX"）
- **表格顯示**：Excel 風格表格，清晰易讀
- **查詢衣物**：支援多條件篩選
- **刪除衣物**：快速刪除功能
- **動態選項管理**：可自訂顏色、材質、場合選項
- **分類別管理**：每個類別（上衣、褲子、外套、襪子）擁有獨立選項

### 📅 穿搭行事曆
- 規劃未來 14 天的每日穿搭
- 每天可選擇多件衣物（不限類別）
- **新增模式**：不覆蓋原有穿搭
- 視覺化週檢視（週一至週日）
- 智能按鈕切換（上週/本週/下週）
- 支援快速篩選衣物
- CheckboxGroup 自動清除

### 🌤️ 天氣整合
- 整合 OpenWeatherMap API
- 顯示 7～14 天天氣預報
- 支援多地區管理（預設：泰山、板橋）
- **自動更新**：新增/刪除地區後下拉選單自動更新
- 溫度、天氣描述、降雨機率

### 📧 Email 通知
- 每日自動發送穿搭提醒
- 可自訂發送時間
- 開啟/關閉通知開關
- **隨時綁定**：註冊後可隨時綁定或修改 Email
- HTML 格式郵件，包含天氣與穿搭資訊
- 測試郵件功能

### 🎨 UI/UX 優化
- 響應式設計（支援手機、平板、桌面）
- **表格化顯示**：衣物清單使用 Dataframe 元件
- **粗體強調**：ID 和簡稱粗體顯示
- **單行格式**：使用 " | " 分隔，易於閱讀
- **Accordion 提示**：所有摺疊區塊標示 "(點選打開/收起)"
- **按鈕優化**：統一藍色，刪除按鈕尺寸調整
- Tab 分頁設計，功能清晰
- 頁面底部使用提示

## 🚀 快速開始

### 本地執行

```bash
# 1. 建立虛擬環境
cd OOTD
python -m venv OOTD_venv

# 2. 啟動虛擬環境
# Windows:
OOTD_venv\Scripts\activate
# Linux/Mac:
source OOTD_venv/bin/activate

# 3. 安裝相依套件
pip install -r requirements.txt

# 4. 執行應用程式
python app.py

# 5. 開啟瀏覽器
# http://127.0.0.1:7860
```

### 環境變數設定（選用）

建立 `config.py` 檔案：

```python
# OpenWeatherMap API（天氣功能）
OPENWEATHER_API_KEY = "your_api_key_here"

# SMTP 郵件發送（Gmail 範例）
SMTP_EMAIL = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"  # Gmail 應用程式密碼
```

**注意**：
- Gmail 需使用「應用程式密碼」，而非帳號密碼
- 申請方式：Google 帳戶 → 安全性 → 兩步驟驗證 → 應用程式密碼
- OpenWeatherMap 免費方案：https://openweathermap.org/api

## 📦 資料儲存

所有資料儲存在 SQLite 資料庫：`./data/clothes.db`

包含以下資料表：
- `users`：使用者帳號資訊
- `clothes`：衣物資料
- `outfits`：穿搭計畫
- `options`：動態選項（分類別管理）
- `locations`：天氣查詢地區

## ☁️ 部署到 Hugging Face Spaces

### 步驟 1：建立 Space

1. 登入 [Hugging Face](https://huggingface.co/)
2. 點擊右上角 → "New Space"
3. 填寫資訊：
   - **Space name**：`outfit-assistant`
   - **License**：MIT
   - **SDK**：Gradio
   - **Space hardware**：CPU basic（免費）
4. 點擊 "Create Space"

### 步驟 2：上傳檔案

上傳以下檔案：
- ✅ `app.py`
- ✅ `database.py`
- ✅ `weather.py`
- ✅ `email_notifier.py`
- ✅ `requirements.txt`
- ✅ `README.md`

### 步驟 3：啟用 Persistent Storage

1. 在 Space 頁面，點擊 "Settings"
2. 找到 "Storage" 區塊
3. 點擊 "Enable Persistent Storage"
4. 選擇 "Small" (20GB) 免費方案

**重要**：這樣資料庫檔案才不會在重啟後遺失！

### 步驟 4：設定環境變數（選用）

在 Settings → Repository secrets 新增：

```
OPENWEATHER_API_KEY=your_openweather_api_key
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

### 完成！

Space 會自動建置和部署，通常需要 2-5 分鐘。

建置完成後，您就可以在網址存取應用程式：
```
https://huggingface.co/spaces/YOUR_USERNAME/outfit-assistant
```

## 📖 文檔

- 📘 **快速上手指南.md**：詳細使用教學
- 📗 **專案完整說明.md**：完整專案架構與技術說明
- 📙 **版本更新說明.md**：所有版本更新記錄
- 📕 **專案檢查清單.md**：功能檢查清單
- 📓 **DEPLOY_HF.md**：Hugging Face 部署詳細指南

## 🛠️ 技術架構

- **前端**：Gradio 4.20.0
- **後端**：Python 3.11+
- **資料庫**：SQLite 3
- **排程**：APScheduler
- **天氣 API**：OpenWeatherMap
- **郵件**：smtplib（Python 內建）

## 📊 資料庫結構

```sql
-- 使用者
users (id, username, password_hash, plain_password, email, email_time, email_enabled, created_at)

-- 衣物
clothes (id, user_id, name, category, color, material, sleeve_type, seasons, occasions, created_at)

-- 穿搭計畫
outfits (id, user_id, date, clothes_ids, created_at)

-- 選項（分類別管理）
options (id, user_id, option_type, option_value)
-- option_type: color_上衣, color_褲子, material_上衣, sleeve_上衣, occasion 等

-- 地區
locations (id, user_id, city_name)
```

## 📈 版本資訊

**當前版本**：v1.4.5  
**發布日期**：2025-10-30

### v1.4.5 主要更新
- ✨ 衣物名稱預設值 "XXX"
- ✨ Email 隨時綁定/修改
- ✨ 穿搭新增模式（不覆蓋）
- ✨ 表格化顯示（Dataframe）
- ✨ 天氣地區自動更新
- ✨ Accordion 提示文字
- 🎨 ID 和簡稱粗體顯示
- 🎨 單行顯示格式優化
- 🎨 按鈕顏色統一（藍色）
- 🎨 刪除按鈕尺寸優化

查看完整更新記錄：[版本更新說明.md](版本更新說明.md)

## ⚠️ 注意事項

1. **安全性**：明文密碼儲存僅適用於個人使用或教學環境
2. **API 限制**：OpenWeatherMap 免費方案有請求次數限制
3. **Gmail 設定**：需使用應用程式密碼，非帳號密碼
4. **資料備份**：建議定期備份 `data/clothes.db` 檔案

## 🎓 學習價值

這個專案展示了：
- 全端開發（資料庫到前端 UI）
- 使用者系統（註冊、登入、Session 管理）
- CRUD 操作（完整的增刪改查）
- 資料庫設計（正規化設計、外鍵約束）
- API 整合（第三方天氣 API）
- 郵件發送（SMTP 協定）
- 響應式設計（跨裝置支援）
- 雲端部署（Hugging Face Spaces）

## 📝 授權

MIT License - 可自由使用、修改、分發

---

**專案類型**：個人衣物管理系統  
**技術棧**：Python + Gradio + SQLite  
**最後更新**：2025-10-30

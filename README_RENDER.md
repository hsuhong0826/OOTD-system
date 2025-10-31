# 👔 穿搭助理系統 - Render 部署版

智能衣櫥管理與每日穿搭規劃 Web 應用程式 - 讓您輕鬆管理衣物、規劃每日穿搭！

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## ✨ 主要功能

- 🔐 **多使用者系統**：帳號註冊、登入、忘記密碼
- 👕 **衣物管理**：新增、查詢、刪除衣物，表格化顯示
- 📅 **穿搭行事曆**：視覺化週檢視，規劃未來 14 天穿搭
- 🌤️ **天氣整合**：OpenWeatherMap API，7-14 天天氣預報
- 📧 **Email 通知**：每日自動發送穿搭提醒
- 📱 **響應式設計**：支援手機、平板、桌面裝置

## 🚀 快速部署到 Render

### 方式一：使用 Blueprint（推薦）⭐

1. 前往 [Render Dashboard](https://dashboard.render.com/)
2. 點擊 **「New」** → **「Blueprint」**
3. 選擇您的 GitHub repository
4. 設定環境變數（選用）
5. 點擊 **「Apply」** 開始部署

### 方式二：一鍵部署

點擊上方 "Deploy to Render" 按鈕，跟隨指引完成部署。

### 📖 詳細部署指南

完整的部署步驟、環境變數設定、常見問題解決方案，請參考：

👉 **[DEPLOY_RENDER.md](./DEPLOY_RENDER.md)**

---

## ⚙️ 環境變數（選用）

| 變數名稱 | 說明 | 必要性 |
|---------|------|-------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API 金鑰 | 選用<br>未設定會使用模擬資料 |
| `SMTP_EMAIL` | Gmail 帳號 | 選用<br>用於發送穿搭通知 |
| `SMTP_PASSWORD` | Gmail 應用程式密碼 | 選用 |

**注意：** Gmail 必須使用「應用程式密碼」，不是一般密碼。詳細設定請見 [DEPLOY_RENDER.md](./DEPLOY_RENDER.md)

---

## 📖 使用說明

### 1. 註冊與登入
- 首次使用請先註冊帳號
- 可選填 Email 接收每日穿搭通知

### 2. 新增衣物
1. 進入「👕 衣物管理」頁籤
2. 選擇類別（上衣/褲子/外套/襪子）
3. 填寫顏色、材質、季節、場合等資訊
4. 點擊「新增衣物」

### 3. 安排穿搭
1. 進入「📅 穿搭行事曆」頁籤
2. 選擇日期並勾選要穿的衣物
3. 點擊「儲存穿搭」

### 4. 查詢天氣
1. 進入「🌤️ 天氣查詢」頁籤
2. 選擇地區和天數
3. 點擊「查詢天氣」

---

## 💾 資料儲存

- 所有資料儲存在 SQLite 資料庫（`./data/clothes.db`）
- Render 使用 Persistent Disk，資料不會在重啟後遺失
- 免費方案提供 1 GB 永久儲存空間

---

## 🔧 技術架構

- **Framework**：Gradio 4.20.0
- **Database**：SQLite3
- **Scheduler**：APScheduler 3.10.4
- **API**：OpenWeatherMap、Gmail SMTP
- **Platform**：Render (Python 3.11)

---

## 🆓 Render 免費方案

- ✅ 750 小時/月運行時間
- ✅ 512 MB RAM
- ✅ 1 GB 永久儲存空間
- ✅ 免費 SSL 憑證
- ⚠️ 15 分鐘無活動後休眠
- ⚠️ 下次訪問需等待 30-60 秒喚醒

對於個人使用或展示專案來說，免費方案已經足夠！

---

## 📚 更多資訊

- **完整專案說明**：[README.md](./README.md)
- **部署指南**：[DEPLOY_RENDER.md](./DEPLOY_RENDER.md)
- **Render 官方文件**：https://render.com/docs

---

**版本**：v2.0  
**更新日期**：2025-10-31

## 📊 資料庫結構

### 主要資料表

1. **users** - 使用者帳號
2. **clothes** - 衣物資訊
3. **outfit_records** - 穿搭記錄
4. **options** - 分類別選項（顏色、材質、分類）

詳細 Schema 請參考 [專案完整說明.md](./專案完整說明.md)

## 📈 版本資訊

**當前版本**：v1.4.5  
**發布日期**：2025-10-30

### 最新更新
- ✨ 衣物名稱預設值、Email 隨時綁定
- ✨ 穿搭新增模式（不覆蓋）、表格化顯示
- 🎨 UI 優化（粗體、單行格式、按鈕優化）
- 📝 新增 Render 部署支援

完整更新記錄請參考 [版本更新說明.md](./版本更新說明.md)

## 📚 完整文檔

- **[快速上手指南](./快速上手指南.md)**：詳細使用教學
- **[專案完整說明](./專案完整說明.md)**：技術架構與資料庫設計
- **[版本更新說明](./版本更新說明.md)**：所有版本更新記錄
- **[DEPLOY_RENDER](./DEPLOY_RENDER.md)**：Render 部署指南
- **[DEPLOY_HF](./DEPLOY_HF.md)**：Hugging Face 部署指南

## ⚠️ 注意事項

### Render 免費方案
- ✅ 每月 750 小時運行時間
- ✅ 512 MB RAM
- ✅ 1 GB 永久儲存
- ⚠️ 15 分鐘無活動後休眠
- ⚠️ 重新喚醒需約 30 秒

### Gmail 設定
- 必須使用「應用程式密碼」，不是一般密碼
- 需在 Google 帳戶設定中啟用「兩步驟驗證」
- 詳細設定步驟請參考部署指南

### 天氣 API
- 免費帳號：每分鐘 60 次呼叫
- 未設定 API Key 會自動使用模擬資料
- 不影響其他功能正常運作

## 🤝 貢獻

歡迎提出 Issue 或 Pull Request！

## 📄 授權

MIT License

## 🔗 相關連結

- [Render 官方網站](https://render.com/)
- [Gradio 官方文檔](https://www.gradio.app/)
- [OpenWeatherMap API](https://openweathermap.org/api)

---

**專案維護**：OOTD Team  
**最後更新**：2025-10-30

如有任何問題或建議，歡迎透過 Issue 聯繫我們！

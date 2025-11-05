# 📧 Email 通知功能設定指南

## 1. 設定 Gmail 應用程式密碼

### 步驟 A: 啟用兩步驟驗證
1. 前往 [Google 帳戶安全性設定](https://myaccount.google.com/security)
2. 找到「兩步驟驗證」並啟用
3. 完成手機驗證設定

### 步驟 B: 產生應用程式密碼
1. 前往 [應用程式密碼](https://myaccount.google.com/apppasswords)
2. 選擇「其他（自訂名稱）」
3. 輸入名稱：`穿搭助理系統`
4. 點擊「產生」
5. **複製產生的 16 位密碼**（例如：`abcd efgh ijkl mnop`）
6. ⚠️ **注意**：密碼只會顯示一次，請立即複製

## 2. 在 Render 設定環境變數

1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 選擇你的 `ootd-system` 服務
3. 點擊左側選單的 **Environment**
4. 新增以下兩個環境變數：

### 環境變數設定

| Key | Value | 說明 |
|-----|-------|------|
| `SMTP_EMAIL` | `your-email@gmail.com` | 你的 Gmail 完整地址 |
| `SMTP_PASSWORD` | `abcd efgh ijkl mnop` | 應用程式密碼（16 位） |

**範例：**
```
SMTP_EMAIL = example@gmail.com
SMTP_PASSWORD = abcdefghijklmnop
```

5. 點擊 **Save Changes**
6. Render 會自動重新部署服務（約 2-3 分鐘）

## 3. 測試 Email 功能

部署完成後：

1. 登入穿搭助理系統
2. 前往「⚙️ Email 設定」頁面
3. 綁定收件人 Email
4. 點擊「📧 發送測試郵件」按鈕
5. 檢查收件匣（或垃圾郵件）

## 4. 常見問題排除

### ❌ 問題：「SMTP 認證失敗」
**解決方法：**
- 確認應用程式密碼複製正確（無空格）
- 確認 Gmail 帳號已啟用兩步驟驗證
- 重新產生應用程式密碼

### ❌ 問題：「未設定 SMTP 環境變數」
**解決方法：**
- 檢查 Render Environment 是否正確設定
- 確認變數名稱為 `SMTP_EMAIL` 和 `SMTP_PASSWORD`（大小寫要一致）
- 儲存後等待部署完成

### ❌ 問題：「連線逾時」
**解決方法：**
- 檢查網路連線
- Gmail SMTP 伺服器：`smtp.gmail.com:587`
- 確認 Render 服務可以對外連線

### ❌ 問題：「郵件進入垃圾郵件」
**解決方法：**
- 將寄件人加入聯絡人
- 標記為「非垃圾郵件」

## 5. 自動排程設定

如需設定每日自動發送：
1. 進入「⚙️ Email 設定」
2. 設定通知時間（例如：07:00）
3. 勾選「啟用每日郵件通知」
4. 點擊「儲存設定」

## 6. 安全性建議

✅ **建議做法：**
- 使用 Gmail 應用程式密碼（不是帳號密碼）
- 定期更換應用程式密碼
- 不要在程式碼中硬編碼密碼
- 使用環境變數儲存敏感資訊

❌ **避免做法：**
- 不要使用 Gmail 帳號的登入密碼
- 不要將密碼提交到 Git
- 不要分享應用程式密碼

---

## 📞 需要協助？

如果設定後仍無法發送郵件，請檢查：
1. Render 的 Logs 查看詳細錯誤訊息
2. 測試郵件的錯誤提示
3. Gmail 安全性設定

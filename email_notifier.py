"""
Email 通知模組
使用 smtplib 寄送每日穿搭提醒
"""

import os
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
import weather as wt

# 載入環境變數 (僅在本地開發時需要)
if Path(".env").exists():
    from dotenv import load_dotenv

    load_dotenv()


def send_outfit_email(
    to_email: str,
    outfit_items: List[Dict],
    weather_info: Dict = None,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    sender_email: str = None,
    sender_password: str = None,
) -> bool:
    """
    寄送每日穿搭提醒 Email

    Args:
        to_email: 收件人 Email
        outfit_items: 今日穿搭衣物列表
        weather_info: 今日天氣資訊
        smtp_server: SMTP 伺服器
        smtp_port: SMTP 埠號
        sender_email: 寄件人 Email（從環境變數取得）
        sender_password: 寄件人密碼（從環境變數取得）

    Returns:
        是否成功寄送
    """
    # 從環境變數取得寄件人資訊
    sender_email = sender_email or os.environ.get("SMTP_EMAIL", "")
    sender_password = sender_password or os.environ.get("SMTP_PASSWORD", "")

    if not sender_email or not sender_password:
        print("未設定 SMTP 寄件人資訊（SMTP_EMAIL, SMTP_PASSWORD）")
        return False

    if not to_email:
        print("未設定收件人 Email")
        return False

    try:
        # 建立郵件內容
        message = MIMEMultipart("alternative")
        message["Subject"] = f'☀️ 每日穿搭提醒 - {datetime.now().strftime("%Y/%m/%d")}'
        message["From"] = sender_email
        message["To"] = to_email

        # 建立 HTML 內容
        html_content = generate_email_html(outfit_items, weather_info)

        # 建立純文字內容（備用）
        text_content = generate_email_text(outfit_items, weather_info)

        # 附加內容
        part1 = MIMEText(text_content, "plain", "utf-8")
        part2 = MIMEText(html_content, "html", "utf-8")
        message.attach(part1)
        message.attach(part2)

        # 連接 SMTP 伺服器並寄送 (設定逾時 30 秒)
        print(f"嘗試連接到 {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            print("開始 TLS 加密...")
            server.starttls()
            print(f"使用帳號 {sender_email} 登入...")
            server.login(sender_email, sender_password)
            print("發送郵件...")
            server.send_message(message)

        print(f"✅ Email 已成功寄送至 {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP 認證失敗：請檢查 Email 和應用程式密碼是否正確 - {str(e)}"
        print(f"❌ {error_msg}")
        return False
    except smtplib.SMTPException as e:
        error_msg = f"SMTP 錯誤：{str(e)}"
        print(f"❌ {error_msg}")
        return False
    except Exception as e:
        error_msg = f"Email 寄送失敗：{str(e)}"
        print(f"❌ {error_msg}")
        return False


def generate_email_html(outfit_items: List[Dict], weather_info: Dict = None) -> str:
    """
    產生 Email HTML 內容
    """
    today = datetime.now().strftime("%Y年%m月%d日")
    weekday = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][
        datetime.now().weekday()
    ]

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Microsoft JhengHei', Arial, sans-serif;
                background-color: #f5f5f5;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            .date {{
                color: #7f8c8d;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            .weather {{
                background-color: #e8f4f8;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .outfit-section {{
                margin-top: 20px;
            }}
            .outfit-item {{
                background-color: #f8f9fa;
                padding: 12px;
                margin: 8px 0;
                border-left: 4px solid #3498db;
                border-radius: 4px;
            }}
            .outfit-item strong {{
                color: #2c3e50;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                color: #95a5a6;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>☀️ 每日穿搭提醒</h1>
            <p class="date">{today} ({weekday})</p>
    """

    # 天氣資訊
    if weather_info:
        html += f"""
            <div class="weather">
                <h3>🌤️ 今日天氣</h3>
                <p>🌡️ 溫度：{weather_info.get('temp_min', 'N/A')}°C ~ {weather_info.get('temp_max', 'N/A')}°C</p>
                <p>☁️ 天氣：{weather_info.get('description', '晴天')}</p>
                <p>🌧️ 降雨機率：{weather_info.get('rain_probability', 0):.0f}%</p>
                <p>👔 穿搭建議：{wt.get_temperature_suggestion(weather_info.get('temp_max', 25), weather_info.get('temp_min', 18))}</p>
            </div>
        """

    # 穿搭內容
    html += '<div class="outfit-section"><h3>👔 今日穿搭</h3>'

    if outfit_items:
        for item in outfit_items:
            html += f"""
                <div class="outfit-item">
                    <strong>{item.get('category', '衣物')}</strong> - 
                    {item.get('color', '')} / {item.get('material', '')}
                    {' / ' + item.get('sleeve_type', '') if item.get('sleeve_type') else ''}
                </div>
            """
    else:
        html += '<p style="color: #95a5a6;">今天沒有安排穿搭哦！</p>'

    html += """
            </div>
            <div class="footer">
                <p>此郵件由穿搭助理系統自動發送</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def generate_email_text(outfit_items: List[Dict], weather_info: Dict = None) -> str:
    """
    產生 Email 純文字內容
    """
    today = datetime.now().strftime("%Y年%m月%d日")
    weekday = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][
        datetime.now().weekday()
    ]

    text = f"☀️ 每日穿搭提醒\n{today} ({weekday})\n\n"

    # 天氣資訊
    if weather_info:
        text += "🌤️ 今日天氣\n"
        text += f"溫度：{weather_info.get('temp_min', 'N/A')}°C ~ {weather_info.get('temp_max', 'N/A')}°C\n"
        text += f"天氣：{weather_info.get('description', '晴天')}\n"
        text += f"降雨機率：{weather_info.get('rain_probability', 0):.0f}%\n"
        text += f"👔 穿搭建議：{wt.get_temperature_suggestion(weather_info.get('temp_max', 25), weather_info.get('temp_min', 18))}\n\n"

    # 穿搭內容
    text += "👔 今日穿搭\n"
    text += "=" * 40 + "\n"

    if outfit_items:
        for i, item in enumerate(outfit_items, 1):
            text += f"{i}. {item.get('category', '衣物')} - "
            text += f"{item.get('color', '')} / {item.get('material', '')}"
            if item.get("sleeve_type"):
                text += f" / {item.get('sleeve_type')}"
            text += "\n"
    else:
        text += "今天還沒有安排穿搭哦！\n"

    text += "\n" + "=" * 40 + "\n"
    text += "此郵件由穿搭助理系統自動發送\n"

    return text


if __name__ == "__main__":
    # 測試 Email 功能
    test_outfit = [
        {"category": "上衣", "color": "白", "material": "襯衫", "sleeve_type": "長袖"},
        {"category": "褲子", "color": "黑", "material": "西裝", "sleeve_type": ""},
    ]

    test_weather = {
        "temp_min": 18,
        "temp_max": 25,
        "description": "晴天",
        "rain_probability": 10,
    }

    print("測試 Email 內容：")
    print(generate_email_text(test_outfit, test_weather))

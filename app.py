"""
穿搭助理 Gradio Web App
主程式
"""

import os
from pathlib import Path
import gradio as gr
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import database as db
import weather as wt
import email_notifier as em
from apscheduler.schedulers.background import BackgroundScheduler
import json
from flask import Flask

# 載入環境變數 (僅在本地開發時需要)
if Path(".env").exists():
    from dotenv import load_dotenv

    load_dotenv()

# 初始化資料庫
db.init_database()

# 全域變數儲存當前使用者
current_user = {"id": None, "username": None}

# 初始化排程器
scheduler = BackgroundScheduler()
scheduler.start()

# 建立 Flask app 用於健康檢查
flask_app = Flask(__name__)


@flask_app.route("/ping")
def ping():
    return "pong"


# ==================== 登入/註冊功能 ====================


def login_user(username: str, password: str):
    """使用者登入"""
    if not username or not password:
        return "請輸入帳號和密碼", gr.update(visible=True), gr.update(visible=False)

    user_id = db.verify_user(username, password)
    if user_id:
        current_user["id"] = user_id
        current_user["username"] = username
        return (
            f"歡迎回來，{username}！",
            gr.update(visible=False),
            gr.update(visible=True),
        )
    else:
        return "帳號或密碼錯誤", gr.update(visible=True), gr.update(visible=False)


def register_user(
    username: str, password: str, password_confirm: str, email: str = None
):
    """使用者註冊"""
    if not username or not password:
        return "請輸入帳號和密碼"

    if password != password_confirm:
        return "兩次密碼輸入不一致"

    if len(password) < 6:
        return "密碼長度至少 6 個字元"

    # Email 是可選的，但如果提供就驗證格式
    if email and "@" not in email:
        return "Email 格式不正確"

    success, message = db.create_user(username, password, email)
    return message


def logout_user():
    """使用者登出"""
    current_user["id"] = None
    current_user["username"] = None
    # 返回：訊息、顯示登入區塊、隱藏主要區塊、清空帳號、清空密碼
    return "已登出", gr.update(visible=True), gr.update(visible=False), "", ""


def retrieve_password(username: str):
    """忘記密碼 - 取得密碼"""
    if not username:
        return "請輸入帳號"

    password = db.get_password_hint(username)
    if password:
        return f"您的密碼是：{password}"
    else:
        return "❌ 查無此帳號"


# ==================== 衣物管理功能 ====================


def get_current_user_id():
    """取得當前使用者 ID"""
    if not current_user["id"]:
        raise ValueError("請先登入")
    return current_user["id"]


def refresh_clothes_list(category="", color="", material="", season="", occasion=""):
    """刷新衣物列表"""
    try:
        user_id = get_current_user_id()
        clothes = db.get_user_clothes(
            user_id,
            category if category != "全部" else None,
            color if color != "全部" else None,
            material if material != "全部" else None,
            season if season != "全部" else None,
            occasion if occasion != "全部" else None,
        )

        if not clothes:
            return gr.update(
                value=None,
                headers=["ID", "簡稱", "類別", "顏色", "材質", "分類", "季節", "場合"],
            )

        # 準備表格資料
        table_data = []
        for cloth in clothes:
            row = [
                cloth["id"],
                cloth.get("name", "XXX"),
                cloth["category"],
                cloth["color"],
                cloth.get("material", "-"),
                cloth.get("sleeve_type", "-"),
                ", ".join(cloth["seasons"]),
                (
                    ", ".join(cloth.get("occasions", []))
                    if cloth.get("occasions")
                    else "-"
                ),
            ]
            table_data.append(row)

        return gr.update(
            value=table_data,
            headers=["ID", "簡稱", "類別", "顏色", "材質", "分類", "季節", "場合"],
        )
    except ValueError as e:
        return gr.update(
            value=None,
            headers=["ID", "簡稱", "類別", "顏色", "材質", "分類", "季節", "場合"],
        )


def add_new_clothing(category, color, material, sleeve_type, seasons, occasions, name):
    """新增衣物"""
    try:
        user_id = get_current_user_id()

        if not category or not color:
            return "請填寫類別和顏色", refresh_clothes_list()

        # 根據類別驗證必填欄位
        if category == "襪子":
            # 襪子不需要材質和場合
            material = None
            occasions = []
            if not sleeve_type:
                return "襪子請選擇分類（長/中/短）", refresh_clothes_list()
        elif category == "外套":
            # 外套不需要分類
            sleeve_type = None
            if not material:
                return "外套請選擇材質", refresh_clothes_list()
            if not occasions:
                return "外套請至少選擇一個場合", refresh_clothes_list()
        else:
            # 上衣和褲子需要材質、分類、場合
            if not material:
                return f"{category}請選擇材質", refresh_clothes_list()
            if not sleeve_type:
                return f"{category}請選擇分類", refresh_clothes_list()
            if not occasions:
                return f"{category}請至少選擇一個場合", refresh_clothes_list()

        if not seasons:
            return "請至少選擇一個季節", refresh_clothes_list()

        success = db.add_clothing(
            user_id, category, color, material, sleeve_type, seasons, occasions, name
        )

        if success:
            return "✅ 新增成功！", refresh_clothes_list()
        else:
            return "❌ 新增失敗", refresh_clothes_list()
    except ValueError as e:
        return str(e), ""


def delete_clothing(cloth_id):
    """刪除衣物"""
    try:
        user_id = get_current_user_id()

        if not cloth_id:
            return "請輸入要刪除的衣物 ID", refresh_clothes_list()

        try:
            cloth_id = int(cloth_id)
        except:
            return "衣物 ID 必須是數字", refresh_clothes_list()

        # 先檢查衣物是否存在
        cloth = db.get_clothing_by_id(cloth_id, user_id)
        if not cloth:
            return "❌ 沒有該衣物", refresh_clothes_list()

        success = db.delete_clothing(cloth_id, user_id)

        if success:
            return f"✅ 已刪除 ID {cloth_id}", refresh_clothes_list()
        else:
            return "❌ 刪除失敗", refresh_clothes_list()
    except ValueError as e:
        return str(e), ""


def refresh_option_choices(option_type):
    """刷新選項列表"""
    try:
        user_id = get_current_user_id()
        options = db.get_user_options(user_id, option_type)
        return gr.update(choices=options)
    except:
        return gr.update()


def update_filter_options(category):
    """根據類別更新篩選選項"""
    try:
        if category == "全部":
            return (
                gr.update(choices=["全部"], value="全部"),  # 顏色
                gr.update(choices=["全部"], value="全部"),  # 材質
                gr.update(visible=True),  # 場合
            )

        user_id = get_current_user_id()
        color_choices = ["全部"] + db.get_user_options(user_id, f"color_{category}")

        if category == "襪子":
            material_choices = ["全部"]
            occasion_visible = False
        else:
            material_choices = ["全部"] + db.get_user_options(
                user_id, f"material_{category}"
            )
            occasion_visible = True

        return (
            gr.update(choices=color_choices, value="全部"),
            gr.update(choices=material_choices, value="全部"),
            gr.update(visible=occasion_visible, value="全部"),
        )
    except:
        return gr.update(), gr.update(), gr.update()


def update_category_fields(category):
    """根據類別更新欄位顯示"""
    try:
        user_id = get_current_user_id()

        # 取得該類別的顏色選項
        color_choices = db.get_user_options(user_id, f"color_{category}")

        # 材質選項和可見性
        if category == "上衣":
            material_choices = db.get_user_options(user_id, "material_上衣")
            material_visible = True
            sleeve_choices = db.get_user_options(user_id, "sleeve_上衣")
            sleeve_label = "分類（袖長）"
            sleeve_visible = True
            occasion_visible = True
        elif category == "褲子":
            material_choices = db.get_user_options(user_id, "material_褲子")
            material_visible = True
            sleeve_choices = db.get_user_options(user_id, "sleeve_褲子")
            sleeve_label = "分類（褲長）"
            sleeve_visible = True
            occasion_visible = True
        elif category == "外套":
            material_choices = db.get_user_options(user_id, "material_外套")
            material_visible = True
            sleeve_choices = []
            sleeve_label = "分類"
            sleeve_visible = False
            occasion_visible = True
        elif category == "襪子":
            material_choices = []
            material_visible = False
            sleeve_choices = db.get_user_options(user_id, "sleeve_襪子")
            sleeve_label = "分類（長度）"
            sleeve_visible = True
            occasion_visible = False
        else:
            material_choices = []
            material_visible = True
            sleeve_choices = []
            sleeve_label = "分類"
            sleeve_visible = True
            occasion_visible = True

        return (
            gr.update(choices=color_choices, value=None),  # 顏色
            gr.update(
                choices=material_choices, visible=material_visible, value=None
            ),  # 材質
            gr.update(
                choices=sleeve_choices,
                label=sleeve_label,
                visible=sleeve_visible,
                value=None,
            ),  # 袖型
            gr.update(visible=occasion_visible, value=[]),  # 場合
        )
    except:
        return gr.update(), gr.update(), gr.update(), gr.update()


def add_option(option_type, option_value):
    """新增選項"""
    try:
        user_id = get_current_user_id()

        if not option_value:
            return "請輸入選項名稱"

        success = db.add_user_option(user_id, option_type, option_value)

        if success:
            return f"✅ 已新增選項：{option_value}"
        else:
            return "❌ 選項已存在或新增失敗"
    except ValueError as e:
        return str(e)


def delete_option(option_type, option_value):
    """刪除選項"""
    try:
        user_id = get_current_user_id()

        if not option_value:
            return "請選擇要刪除的選項"

        success = db.delete_user_option(user_id, option_type, option_value)

        if success:
            return f"✅ 已刪除選項：{option_value}"
        else:
            return "❌ 刪除失敗"
    except ValueError as e:
        return str(e)


# ==================== 穿搭行事曆功能 ====================


def get_current_week_range():
    """取得本週的日期範圍（週一到週日）"""
    today = datetime.now()
    # 計算今天是週幾（0=週一, 6=週日）
    weekday = today.weekday()
    # 計算本週一的日期
    monday = today - timedelta(days=weekday)

    dates = []
    for i in range(7):
        date = monday + timedelta(days=i)
        dates.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "weekday": ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][i],
                "display": f"{date.strftime('%m/%d')} ({['週一', '週二', '週三', '週四', '週五', '週六', '週日'][i]})",
            }
        )
    return dates


def get_date_range(days_offset=0):
    """取得日期範圍（今天開始的 7 天）- 保留用於日期選擇器"""
    start_date = datetime.now() + timedelta(days=days_offset)
    dates = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        dates.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "weekday": ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][
                    date.weekday()
                ],
                "display": f"{date.strftime('%m/%d')} ({'週一週二週三週四週五週六週日'[date.weekday()*2:date.weekday()*2+2]})",
            }
        )
    return dates


def refresh_calendar_view(week_offset=0):
    """刷新行事曆視圖 - 顯示本週（週一到週日）共7天"""
    try:
        user_id = get_current_user_id()

        # 計算目標週的週一
        today = datetime.now()
        current_monday = today - timedelta(days=today.weekday())
        week_monday = current_monday + timedelta(weeks=week_offset)

        # 決定週次標題
        if week_offset == 0:
            week_title = "本週"
        elif week_offset == -1:
            week_title = "上一週"
        elif week_offset == 1:
            week_title = "下一週"
        else:
            week_title = f"第 {week_offset} 週"

        output = f"### 📅 穿搭行事曆 - {week_title}\n\n"

        # 顯示該週的七天
        for day_idx in range(7):
            date = week_monday + timedelta(days=day_idx)
            date_str = date.strftime("%Y-%m-%d")
            weekday_name = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][
                day_idx
            ]
            display_str = f"{date_str} ({weekday_name})"

            # 取得該日期的穿搭
            outfit_ids = db.get_outfit(user_id, date_str)

            output += f"#### {display_str}\n"

            if outfit_ids:
                for cloth_id in outfit_ids:
                    cloth = db.get_clothing_by_id(cloth_id, user_id)
                    if cloth:
                        output += f"- **ID: {cloth['id']}**"
                        if cloth.get("name"):
                            output += f" **{cloth['name']}**"
                        output += f" | {cloth['category']}"
                        output += f" | 顏色: {cloth['color']}"
                        if cloth.get("material"):
                            output += f" | 材質: {cloth['material']}"
                        if cloth.get("sleeve_type"):
                            output += f" | 分類: {cloth['sleeve_type']}"
                        output += "\n"
            else:
                output += "*尚未安排穿搭*\n"

            output += "\n"

        # 返回 output 和按鈕可見性
        # 預設兩個按鈕都顯示
        # 可根據需求修改按鈕顯示邏輯
        prev_visible = True
        next_visible = True

        return output, gr.update(visible=prev_visible), gr.update(visible=next_visible)
    except ValueError as e:
        return str(e), gr.update(), gr.update()


def get_calendar_view_only():
    """僅取得行事曆顯示文字（用於登入初始化）"""
    try:
        result = refresh_calendar_view(0)
        return result[0]  # 只返回文字部分
    except:
        return "### 📅 穿搭行事曆\n\n*請先新增衣物*"


def get_clothes_choices_for_outfit(
    category="全部", color="全部", material="全部", season="全部", occasion="全部"
):
    """取得可選擇的衣物列表（用於穿搭安排）"""
    try:
        user_id = get_current_user_id()
        clothes = db.get_user_clothes(
            user_id,
            category if category != "全部" else None,
            color if color != "全部" else None,
            material if material != "全部" else None,
            season if season != "全部" else None,
            occasion if occasion != "全部" else None,
        )

        choices = []
        for cloth in clothes:
            name_prefix = f"{cloth.get('name', '')} - " if cloth.get("name") else ""
            label = f"[ID:{cloth['id']}] {name_prefix}{cloth['category']} - {cloth['color']}"
            if cloth.get("material"):
                label += f" {cloth['material']}"
            if cloth.get("sleeve_type"):
                label += f" ({cloth['sleeve_type']})"
            choices.append((label, cloth["id"]))

        return choices
    except:
        return []


def update_outfit_clothes_list(category, color, material, season, occasion):
    """更新穿搭衣物選單"""
    choices = get_clothes_choices_for_outfit(
        category, color, material, season, occasion
    )
    return gr.update(choices=choices)


def save_daily_outfit(date_str, selected_clothes_ids):
    """儲存每日穿搭"""
    try:
        user_id = get_current_user_id()

        if not date_str:
            return "請選擇日期"

        # selected_clothes_ids 可能是空列表（清空穿搭）
        clothes_ids = selected_clothes_ids if selected_clothes_ids else []

        success = db.save_outfit(user_id, date_str, clothes_ids)

        if success:
            if clothes_ids:
                return f"✅ 已儲存 {date_str} 的穿搭（{len(clothes_ids)} 件）"
            else:
                return f"✅ 已清空 {date_str} 的穿搭"
        else:
            return "❌ 儲存失敗"
    except ValueError as e:
        return str(e)


def delete_daily_outfit(date_str):
    """刪除每日穿搭"""
    try:
        user_id = get_current_user_id()

        if not date_str:
            return "請選擇日期"

        # 刪除穿搭（設定為空列表）
        success = db.save_outfit(user_id, date_str, [])

        if success:
            return f"✅ 已刪除 {date_str} 的穿搭"
        else:
            return "❌ 刪除失敗"
    except ValueError as e:
        return str(e)


# ==================== 歷史穿搭查詢功能 ====================


def search_outfit_history(cloth_ids):
    """查詢衣物的歷史穿搭記錄（支援多件衣物）"""
    try:
        user_id = get_current_user_id()

        if not cloth_ids or len(cloth_ids) == 0:
            return "請選擇要查詢的衣物"

        # 將選中的衣物ID字串轉換為整數列表
        try:
            cloth_ids_int = [int(cid) for cid in cloth_ids]
        except:
            return "衣物 ID 格式錯誤"

        output = f"### 🔍 查詢結果\n\n"
        output += f"**已選擇 {len(cloth_ids_int)} 件衣物**\n\n---\n\n"

        # 對每件衣物進行查詢
        for cloth_id in cloth_ids_int:
            # 取得衣物資訊
            cloth = db.get_clothing_by_id(cloth_id, user_id)
            if not cloth:
                output += f"找不到衣物 ID: {cloth_id}\n\n---\n\n"
                continue

            # 構建簡稱
            short_name = f"{cloth['color']}"
            if cloth.get("sleeve_type"):
                short_name += cloth["sleeve_type"]
            elif cloth["category"] == "外套":
                short_name += "外套"
            elif cloth["category"] == "襪子":
                short_name += "襪子"
            else:
                short_name += cloth["category"]

            # 查詢歷史記錄
            history = db.get_outfit_history_by_clothing(user_id, cloth_id)

            output += f"#### 衣物：**ID: {cloth['id']}**"
            if cloth.get("name"):
                output += f" **{cloth['name']}**"
            output += f" | {cloth['category']}"
            output += f" | 顏色: {cloth['color']}"
            if cloth.get("material"):
                output += f" | 材質: {cloth['material']}"
            if cloth["sleeve_type"]:
                output += f" | 分類: {cloth['sleeve_type']}"
            output += "\n\n"

            if not history:
                output += "暫無穿搭記錄\n\n---\n\n"
                continue

            output += f"**穿搭次數**: {len(history)} 次\n\n"

            # 統計搭配過的其他衣物
            companion_items = {}  # {cloth_id: count}

            for record in history:
                clothes_ids = record["clothes_ids"]

                # 記錄其他搭配的衣物
                for other_id in clothes_ids:
                    if other_id != cloth_id:
                        companion_items[other_id] = companion_items.get(other_id, 0) + 1

            # 顯示最常搭配的衣物
            if companion_items:
                output += "**最常搭配的衣物**\n\n"
                sorted_companions = sorted(
                    companion_items.items(), key=lambda x: x[1], reverse=True
                )

                for other_id, count in sorted_companions[:5]:  # 只顯示前 5 個
                    other_cloth = db.get_clothing_by_id(other_id, user_id)
                    if other_cloth:
                        output += f"- **ID: {other_cloth['id']}**"
                        if other_cloth.get("name"):
                            output += f" **{other_cloth['name']}**"
                        output += f" | {other_cloth['category']}"
                        output += f" | 顏色: {other_cloth['color']}"
                        if other_cloth.get("material"):
                            output += f" | 材質: {other_cloth['material']}"
                        if other_cloth["sleeve_type"]:
                            output += f" | 分類: {other_cloth['sleeve_type']}"
                        output += f" - 搭配 {count} 次\n"

                output += "\n"

            output += "---\n\n"

        return output

    except ValueError as e:
        return str(e)


# ==================== 衣物選單更新功能 ====================


def update_history_clothes_list(category, color, material, season, occasion):
    """更新歷史穿搭衣物選單（改為 CheckboxGroup）"""
    try:
        user_id = get_current_user_id()
        clothes = db.get_user_clothes(
            user_id,
            category if category != "全部" else None,
            color if color != "全部" else None,
            material if material != "全部" else None,
            season if season != "全部" else None,
            occasion if occasion != "全部" else None,
        )

        choices = []
        for cloth in clothes:
            label = f"ID: {cloth['id']}"
            if cloth.get("name"):
                label += f" {cloth['name']}"
            label += f" | {cloth['category']}"
            label += f" | 顏色: {cloth['color']}"
            if cloth.get("material"):
                label += f" | 材質: {cloth['material']}"
            if cloth.get("sleeve_type"):
                label += f" | 分類: {cloth['sleeve_type']}"

            choices.append((label, str(cloth["id"])))

        return gr.update(choices=choices, value=None)
    except:
        return gr.update()


# ==================== 天氣功能 ====================


def refresh_weather_display(city_name="泰山", days=7):
    """刷新天氣顯示"""
    if not city_name:
        city_name = "泰山"

    weather_data = wt.get_weather_forecast(city_name, days)
    return wt.format_weather_display(weather_data, city_name)


def add_location(city_name):
    """新增地區"""
    try:
        user_id = get_current_user_id()

        if not city_name:
            return "請輸入城市名稱", gr.update()

        success = db.add_user_location(user_id, city_name)

        if success:
            locations = db.get_user_locations(user_id)
            return f"✅ 已新增地區：{city_name}", gr.update(choices=locations)
        else:
            return "❌ 地區已存在或新增失敗", gr.update()
    except ValueError as e:
        return str(e), gr.update()


def delete_location(city_name):
    """刪除地區"""
    try:
        user_id = get_current_user_id()

        if not city_name:
            return "請選擇要刪除的地區", gr.update()

        success = db.delete_user_location(user_id, city_name)

        if success:
            locations = db.get_user_locations(user_id)
            return f"✅ 已刪除地區：{city_name}", gr.update(choices=locations)
        else:
            return "❌ 刪除失敗", gr.update()
    except ValueError as e:
        return str(e), gr.update()


# ==================== Email 設定功能 ====================


def bind_user_email(email_address):
    """綁定或更新用戶 Email"""
    try:
        user_id = get_current_user_id()

        if not email_address or "@" not in email_address:
            return "❌ 請輸入有效的 Email 地址", gr.update()

        success = db.update_user_email(user_id, email_address)

        if success:
            return f"✅ Email 已綁定：{email_address}", gr.update(value=email_address)
        else:
            return "❌ 綁定失敗", gr.update()
    except ValueError as e:
        return str(e), gr.update()


def save_email_settings(email_time, email_enabled):
    """儲存 Email 設定"""
    try:
        user_id = get_current_user_id()

        db.update_user_email_settings(user_id, email_time, email_enabled)

        status = "已開啟" if email_enabled else "已關閉"
        return f"✅ Email 設定已儲存（通知{status}）"
    except ValueError as e:
        return str(e)


def send_test_email():
    """發送測試 Email"""
    try:
        user_id = get_current_user_id()

        # 取得用戶 Email
        email, _, enabled = db.get_user_email_settings(user_id)

        if not email:
            return "❌ 尚未綁定 Email，請先在上方綁定 Email 地址"

        # 取得今天的穿搭
        today = datetime.now().strftime("%Y-%m-%d")
        outfit_ids = db.get_outfit(user_id, today)

        outfit_items = []
        for cloth_id in outfit_ids:
            cloth = db.get_clothing_by_id(cloth_id, user_id)
            if cloth:
                outfit_items.append(cloth)

        # 取得天氣
        locations = db.get_user_locations(user_id)
        city = locations[0] if locations else "泰山"
        weather_data = wt.get_weather_forecast(city, 1)
        weather_info = weather_data[0] if weather_data else None

        # 發送 Email
        success = em.send_outfit_email(email, outfit_items, weather_info)

        if success:
            return f"✅ 測試郵件已發送至 {email}"
        else:
            return "❌ 郵件發送失敗（請檢查 SMTP 設定）"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"❌ 發送失敗：{str(e)}"


# ==================== 建立 Gradio 介面 ====================


def create_gradio_app():
    """建立 Gradio 介面"""

    with gr.Blocks(title="穿搭助理", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 👔 穿搭助理系統")
        gr.Markdown("智能管理您的衣櫥，規劃每日穿搭，整合天氣與提醒功能")

        # 登入/註冊區塊
        with gr.Row(visible=True) as login_area:
            with gr.Column():
                gr.Markdown("### 🔐 登入")
                login_username = gr.Textbox(label="帳號", placeholder="請輸入帳號")
                login_password = gr.Textbox(
                    label="密碼", type="password", placeholder="請輸入密碼"
                )
                with gr.Row():
                    login_btn = gr.Button("登入", variant="primary")
                    forgot_btn = gr.Button("忘記密碼？", variant="secondary", size="sm")
                login_msg = gr.Textbox(label="訊息", interactive=False)

            with gr.Column():
                gr.Markdown("### ✏️ 註冊")
                reg_username = gr.Textbox(label="帳號", placeholder="請輸入帳號")
                reg_password = gr.Textbox(
                    label="密碼", type="password", placeholder="至少 6 個字元"
                )
                reg_password_confirm = gr.Textbox(
                    label="確認密碼", type="password", placeholder="再次輸入密碼"
                )
                reg_email = gr.Textbox(
                    label="Email（可選）", placeholder="example@email.com"
                )
                gr.Markdown("*綁定 Email 後可接收每日穿搭通知*")
                reg_btn = gr.Button("註冊", variant="primary")
                reg_msg = gr.Textbox(label="訊息", interactive=False)

        # 忘記密碼區塊（獨立）
        with gr.Row(visible=False) as forgot_area:
            with gr.Column():
                gr.Markdown("### 🔑 忘記密碼")
                forgot_username = gr.Textbox(
                    label="請輸入您的帳號", placeholder="輸入帳號以查詢密碼"
                )
                with gr.Row():
                    forgot_retrieve_btn = gr.Button("查詢密碼", variant="primary")
                    forgot_back_btn = gr.Button("返回登入", variant="secondary")
                forgot_msg = gr.Textbox(label="您的密碼", interactive=False)

        # 主功能區塊
        with gr.Column(visible=False) as main_area:
            with gr.Row():
                gr.Markdown("### 👤 已登入")
                logout_btn = gr.Button("登出", size="sm")

            with gr.Tabs():
                # Tab 1: 衣物管理
                with gr.Tab("👕 衣物管理"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("#### 新增衣物")
                            add_category = gr.Dropdown(
                                choices=["上衣", "褲子", "外套", "襪子"],
                                label="類別",
                                value="上衣",
                            )
                            add_color = gr.Dropdown(choices=["請先登入"], label="顏色")
                            add_material = gr.Dropdown(
                                choices=["請先登入"], label="材質", visible=True
                            )
                            add_sleeve = gr.Dropdown(
                                choices=["請先登入"], label="分類（袖長）", visible=True
                            )
                            add_seasons = gr.CheckboxGroup(
                                choices=["春", "夏", "秋", "冬"], label="季節", value=[]
                            )
                            add_occasions = gr.CheckboxGroup(
                                choices=[], label="場合", visible=True, value=[]
                            )
                            add_name = gr.Textbox(
                                label="衣物名稱（可選）", placeholder="例：藍色格子襯衫"
                            )
                            add_btn = gr.Button("新增衣物", variant="primary")
                            add_msg = gr.Textbox(label="訊息", interactive=False)

                        with gr.Column(scale=2):
                            gr.Markdown("#### 我的衣物")

                            with gr.Accordion(
                                "篩選條件 ( 點選打開或收起 )", open=False
                            ):
                                with gr.Row():
                                    filter_category = gr.Dropdown(
                                        choices=[
                                            "全部",
                                            "上衣",
                                            "褲子",
                                            "外套",
                                            "襪子",
                                        ],
                                        value="全部",
                                        label="類別",
                                    )
                                    filter_color = gr.Dropdown(
                                        choices=["全部"], value="全部", label="顏色"
                                    )
                                    filter_material = gr.Dropdown(
                                        choices=["全部"], value="全部", label="材質"
                                    )
                                with gr.Row():
                                    filter_season = gr.Dropdown(
                                        choices=["全部", "春", "夏", "秋", "冬"],
                                        value="全部",
                                        label="季節",
                                    )
                                    filter_occasion = gr.Dropdown(
                                        choices=["全部"], value="全部", label="場合"
                                    )
                                filter_btn = gr.Button("套用篩選")

                            gr.Markdown("#### 我的衣物清單")
                            clothes_list = gr.Dataframe(
                                headers=[
                                    "ID",
                                    "簡稱",
                                    "類別",
                                    "顏色",
                                    "材質",
                                    "分類",
                                    "季節",
                                    "場合",
                                ],
                                datatype=[
                                    "number",
                                    "str",
                                    "str",
                                    "str",
                                    "str",
                                    "str",
                                    "str",
                                    "str",
                                ],
                                col_count=(8, "fixed"),
                                interactive=False,
                                wrap=True,
                            )

                            with gr.Row():
                                delete_id = gr.Textbox(
                                    label="刪除衣物 ID", placeholder="輸入 ID"
                                )
                                delete_btn = gr.Button(
                                    "🗑️ 刪除", variant="primary", size="sm"
                                )

                    with gr.Accordion("⚙️ 選項管理 ( 點選打開或收起 )", open=False):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("##### 顏色選項")
                                color_option_category = gr.Dropdown(
                                    choices=["上衣", "褲子", "外套", "襪子"],
                                    value="上衣",
                                    label="選擇類別",
                                )
                                color_new = gr.Textbox(
                                    label="新增顏色", placeholder="例：紅"
                                )
                                color_add_btn = gr.Button("新增顏色", variant="primary")
                                color_delete = gr.Dropdown(choices=[], label="刪除顏色")
                                color_delete_btn = gr.Button(
                                    "🗑️ 刪除顏色", variant="primary"
                                )
                                color_msg = gr.Textbox(label="訊息", interactive=False)

                            with gr.Column():
                                gr.Markdown("##### 材質選項")
                                material_category = gr.Dropdown(
                                    choices=["上衣", "褲子", "外套"],
                                    value="上衣",
                                    label="選擇類別",
                                )
                                material_new = gr.Textbox(
                                    label="新增材質", placeholder="例：棉麻"
                                )
                                material_add_btn = gr.Button(
                                    "新增材質", variant="primary"
                                )
                                material_delete = gr.Dropdown(
                                    choices=[], label="刪除材質"
                                )
                                material_delete_btn = gr.Button(
                                    "🗑️ 刪除材質", variant="primary"
                                )
                                material_msg = gr.Textbox(
                                    label="訊息", interactive=False
                                )

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("##### 場合選項（全局）")
                                occasion_new = gr.Textbox(
                                    label="新增場合", placeholder="例：約會"
                                )
                                occasion_add_btn = gr.Button(
                                    "新增場合", variant="primary"
                                )
                                occasion_delete = gr.Dropdown(
                                    choices=[], label="刪除場合"
                                )
                                occasion_delete_btn = gr.Button(
                                    "🗑️ 刪除場合", variant="primary"
                                )
                                occasion_msg = gr.Textbox(
                                    label="訊息", interactive=False
                                )

                    gr.Markdown("---")
                    gr.Markdown(
                        """
                    **💡 使用提示**
                    - 先選擇類別後，會自動載入該類別的顏色、材質和分類選項
                    - 可在「選項管理」區塊為不同類別新增專屬的顏色、材質和分類
                    - 使用篩選功能快速找到特定條件的衣物
                    """
                    )

                # Tab 2: 穿搭行事曆
                with gr.Tab("📅 穿搭行事曆"):
                    # 週次偏移狀態（用於控制按鈕顯示）
                    week_offset_state = gr.State(0)

                    with gr.Row():
                        with gr.Column(scale=2):
                            calendar_view = gr.Markdown("載入中...")
                            with gr.Row():
                                prev_week_btn = gr.Button("◀ 前一週", visible=True)
                                curr_week_btn = gr.Button("本週", visible=True)
                                next_week_btn = gr.Button("下一週 ▶", visible=True)

                        with gr.Column(scale=1):
                            gr.Markdown("#### 安排穿搭")
                            outfit_date = gr.Dropdown(
                                choices=[], label="選擇日期", interactive=True
                            )

                            with gr.Accordion(
                                "篩選衣物 ( 點選打開或收起 )", open=False
                            ):
                                outfit_filter_category = gr.Dropdown(
                                    choices=["全部", "上衣", "褲子", "外套", "襪子"],
                                    value="全部",
                                    label="類別",
                                )
                                outfit_filter_color = gr.Dropdown(
                                    choices=["全部"], value="全部", label="顏色"
                                )
                                outfit_filter_material = gr.Dropdown(
                                    choices=["全部"], value="全部", label="材質"
                                )
                                outfit_filter_season = gr.Dropdown(
                                    choices=["全部", "春", "夏", "秋", "冬"],
                                    value="全部",
                                    label="季節",
                                )
                                outfit_filter_occasion = gr.Dropdown(
                                    choices=["全部"], value="全部", label="場合"
                                )
                                outfit_filter_btn = gr.Button("套用篩選")

                            outfit_clothes = gr.CheckboxGroup(
                                choices=[], label="選擇衣物（可多選）"
                            )
                            outfit_save_btn = gr.Button("儲存穿搭", variant="primary")
                            outfit_delete_btn = gr.Button("刪除穿搭", variant="primary")
                            outfit_msg = gr.Textbox(label="訊息", interactive=False)

                    gr.Markdown("---")
                    gr.Markdown(
                        """
                    **💡 使用提示**
                    - 點擊「本週」可返回當前週；點擊「上一週」或「下一週」可查看其他週次
                    - 使用篩選功能可快速找到符合條件的衣物（例如：只顯示適合當季的上衣）
                    - 點擊日期可為該日期安排穿搭，支援多選衣物
                    """
                    )

                # Tab 3: 歷史穿搭
                with gr.Tab("📜 歷史穿搭"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("#### 查詢某件衣物的搭配記錄")
                            gr.Markdown("選擇一件衣物，查看您曾經如何搭配它")

                            history_cloth_category = gr.Dropdown(
                                choices=["全部", "上衣", "褲子", "外套", "襪子"],
                                value="全部",
                                label="類別",
                                interactive=True,
                            )

                            history_cloth_color = gr.Dropdown(
                                choices=["全部"],
                                value="全部",
                                label="顏色",
                                interactive=True,
                            )

                            history_cloth_material = gr.Dropdown(
                                choices=["全部"],
                                value="全部",
                                label="材質",
                                interactive=True,
                            )

                            history_cloth_season = gr.Dropdown(
                                choices=["全部", "春", "夏", "秋", "冬"],
                                value="全部",
                                label="季節",
                                interactive=True,
                            )

                            history_cloth_occasion = gr.Dropdown(
                                choices=["全部"],
                                value="全部",
                                label="場合",
                                interactive=True,
                            )

                            history_filter_btn = gr.Button("套用篩選")

                            history_cloth_select = gr.CheckboxGroup(
                                choices=[],
                                label="選擇要查詢的衣物（可多選）",
                                interactive=True,
                            )

                            history_search_btn = gr.Button(
                                "🔍 查詢穿搭記錄", variant="primary"
                            )

                        with gr.Column(scale=2):
                            history_result = gr.Markdown(
                                "### 📊 穿搭分析\n\n請選擇左側的衣物開始查詢"
                            )

                    gr.Markdown("---")
                    gr.Markdown(
                        """
                    **💡 使用提示**
                    - 使用篩選功能可快速找到特定類別、顏色或材質的衣物
                    - 查詢結果會顯示該衣物的所有穿搭記錄和次數統計
                    - 可用於了解哪些衣物使用頻率較高或較低
                    """
                    )

                # Tab 4: 天氣查詢
                with gr.Tab("🌤️ 天氣查詢"):
                    with gr.Row():
                        with gr.Column():
                            weather_city = gr.Dropdown(
                                choices=[], label="選擇地區", value="泰山"
                            )
                            weather_days = gr.Slider(
                                minimum=1,
                                maximum=6,
                                value=6,
                                step=1,
                                label="預報天數（中央氣象署最多提供 6 天）",
                            )
                            weather_refresh_btn = gr.Button(
                                "查詢天氣", variant="primary"
                            )

                        with gr.Column():
                            gr.Markdown("#### 地區管理")
                            location_new = gr.Textbox(
                                label="新增地區", placeholder="例：台北"
                            )
                            location_add_btn = gr.Button("新增", variant="primary")
                            location_delete = gr.Dropdown(choices=[], label="刪除地區")
                            location_delete_btn = gr.Button("🗑️ 刪除", variant="primary")
                            location_msg = gr.Textbox(label="訊息", interactive=False)

                    gr.Markdown("---")
                    weather_display = gr.Markdown("請選擇地區查詢天氣")

                    gr.Markdown("---")
                    gr.Markdown(
                        """
                    **💡 使用提示**
                    - 在地區管理中新增常用地區，方便快速查詢天氣
                    - 天氣預報可顯示 1-6 天，建議查詢 6 天以規劃一週穿搭
                    - 天氣資訊包含溫度、降雨機率和天氣描述，可作為選衣參考
                    """
                    )

                # Tab 5: Email 設定
                with gr.Tab("📧 Email 設定"):
                    with gr.Column():
                        email_display = gr.Textbox(
                            label="綁定的 Email", interactive=False, value="尚未綁定"
                        )

                        with gr.Accordion(
                            "綁定/修改 Email ( 點選打開或收起 )", open=False
                        ):
                            email_input = gr.Textbox(
                                label="輸入 Email 地址", placeholder="example@email.com"
                            )
                            email_bind_btn = gr.Button("綁定 Email", variant="primary")
                            email_bind_msg = gr.Textbox(
                                label="綁定訊息", interactive=False
                            )

                        gr.Markdown("---")

                        email_enabled = gr.Checkbox(
                            label="開啟每日穿搭通知", value=True
                        )
                        email_time = gr.Textbox(
                            label="發送時間", value="07:00", placeholder="HH:MM 格式"
                        )

                        gr.Markdown(
                            """
                        **注意事項：**
                        - 未勾選「開啟通知」則不會發送郵件
                        """
                        )

                        with gr.Row():
                            email_save_btn = gr.Button("儲存設定", variant="primary")
                            email_test_btn = gr.Button("發送測試郵件")

                        email_msg = gr.Textbox(label="訊息", interactive=False)

                    gr.Markdown("---")
                    gr.Markdown(
                        """
                    **💡 使用提示**
                    - 可以在註冊時綁定 Email，或在此頁面綁定/修改
                    - 可設定每日發送通知的時間（例如：07:00）
                    - 使用「發送測試郵件」功能確認 Email 設定是否正確
                    """
                    )

        # ==================== 事件綁定 ====================

        # 衣物管理 - 定義初始化函式
        def on_login_success():
            """登入成功後初始化選項"""
            try:
                user_id = get_current_user_id()
            except ValueError:
                # 未登入，返回空更新
                return tuple([gr.update()] * 25)

            # 取得上衣的顏色、材質和袖型（因為預設類別是上衣）
            colors_shirt = db.get_user_options(user_id, "color_上衣")
            materials_shirt = db.get_user_options(user_id, "material_上衣")
            sleeves_shirt = db.get_user_options(user_id, "sleeve_上衣")
            occasions = db.get_user_options(user_id, "occasion")
            locations = db.get_user_locations(user_id)

            # 取得所有類別的顏色（用於篩選）
            all_colors = (
                colors_shirt
                + db.get_user_options(user_id, "color_褲子")
                + db.get_user_options(user_id, "color_外套")
                + db.get_user_options(user_id, "color_襪子")
            )
            all_colors = list(set(all_colors))  # 去重

            # 生成日期選項（未來 14 天）
            date_choices = []
            for i in range(14):
                date = datetime.now() + timedelta(days=i)
                weekday = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][
                    date.weekday()
                ]
                date_str = date.strftime("%Y-%m-%d")
                date_choices.append(f"{date_str} ({weekday})")

            # 準備歷史穿搭的衣物選項
            clothes = db.get_user_clothes(user_id)
            history_choices = []
            for cloth in clothes:
                name_prefix = f"{cloth.get('name', '')} - " if cloth.get("name") else ""
                label = f"{name_prefix}{cloth['category']} - {cloth['color']}"
                if cloth.get("material"):
                    label += f" {cloth['material']}"
                if cloth.get("sleeve_type"):
                    label += f" ({cloth['sleeve_type']})"
                history_choices.append((label, str(cloth["id"])))

            # 所有材質選項（用於篩選）
            all_materials = (
                materials_shirt
                + db.get_user_options(user_id, "material_褲子")
                + db.get_user_options(user_id, "material_外套")
            )
            all_materials = list(set(all_materials))  # 去重

            # Email 設定
            email, email_time_val, email_enabled_val = db.get_user_email_settings(
                user_id
            )
            email_display_text = email if email else "尚未綁定"

            return (
                gr.update(choices=colors_shirt),  # 1. add_color
                gr.update(choices=materials_shirt),  # 2. add_material
                gr.update(choices=sleeves_shirt),  # 3. add_sleeve
                gr.update(choices=occasions, value=[]),  # 4. add_occasions
                gr.update(
                    choices=["全部"] + all_colors, value="全部"
                ),  # 5. filter_color
                gr.update(
                    choices=["全部"] + all_materials, value="全部"
                ),  # 6. filter_material
                gr.update(
                    choices=["全部"] + occasions, value="全部"
                ),  # 7. filter_occasion
                gr.update(
                    choices=colors_shirt,
                    value=colors_shirt[0] if colors_shirt else None,
                ),  # 8. color_delete
                gr.update(choices=all_materials, value=None),  # 9. material_delete
                gr.update(
                    choices=occasions, value=occasions[0] if occasions else None
                ),  # 10. occasion_delete
                refresh_clothes_list(),  # 11. clothes_list
                gr.update(
                    choices=locations, value=locations[0] if locations else "泰山"
                ),  # 12. weather_city
                gr.update(
                    choices=locations, value=locations[0] if locations else None
                ),  # 13. location_delete
                gr.update(
                    choices=date_choices,
                    value=date_choices[0] if date_choices else None,
                ),  # 14. outfit_date
                get_calendar_view_only(),  # 15. calendar_view
                gr.update(
                    choices=history_choices, value=None
                ),  # 16. history_cloth_select
                gr.update(
                    choices=["全部"] + all_colors, value="全部"
                ),  # 17. outfit_filter_color
                gr.update(
                    choices=["全部"] + all_materials, value="全部"
                ),  # 18. outfit_filter_material
                gr.update(
                    choices=["全部"] + occasions, value="全部"
                ),  # 19. outfit_filter_occasion
                gr.update(
                    choices=["全部"] + all_colors, value="全部"
                ),  # 20. history_cloth_color
                gr.update(
                    choices=["全部"] + all_materials, value="全部"
                ),  # 21. history_cloth_material
                gr.update(
                    choices=["全部"] + occasions, value="全部"
                ),  # 22. history_cloth_occasion
                gr.update(value=email_display_text),  # 23. email_display
                gr.update(value=email_time_val),  # 24. email_time
                gr.update(value=email_enabled_val),  # 25. email_enabled
            )

        # 登入/註冊
        login_btn.click(
            login_user,
            inputs=[login_username, login_password],
            outputs=[login_msg, login_area, main_area],
        ).then(
            on_login_success,
            outputs=[
                add_color,
                add_material,
                add_sleeve,
                add_occasions,
                filter_color,
                filter_material,
                filter_occasion,
                color_delete,
                material_delete,
                occasion_delete,
                clothes_list,
                weather_city,
                location_delete,
                outfit_date,
                calendar_view,
                history_cloth_select,
                outfit_filter_color,
                outfit_filter_material,
                outfit_filter_occasion,
                history_cloth_color,
                history_cloth_material,
                history_cloth_occasion,
                email_display,
                email_time,
                email_enabled,
            ],
        )

        # 忘記密碼按鈕
        forgot_btn.click(
            lambda: (gr.update(visible=False), gr.update(visible=True), ""),
            outputs=[login_area, forgot_area, forgot_msg],
        )

        forgot_back_btn.click(
            lambda: (gr.update(visible=True), gr.update(visible=False), ""),
            outputs=[login_area, forgot_area, forgot_msg],
        )

        forgot_retrieve_btn.click(
            retrieve_password, inputs=[forgot_username], outputs=[forgot_msg]
        )

        reg_btn.click(
            register_user,
            inputs=[reg_username, reg_password, reg_password_confirm, reg_email],
            outputs=[reg_msg],
        )

        logout_btn.click(
            logout_user,
            outputs=[login_msg, login_area, main_area, login_username, login_password],
        )

        add_btn.click(
            add_new_clothing,
            inputs=[
                add_category,
                add_color,
                add_material,
                add_sleeve,
                add_seasons,
                add_occasions,
                add_name,
            ],
            outputs=[add_msg, clothes_list],
        ).then(
            lambda: (None, None, None, [], [], ""),
            outputs=[
                add_color,
                add_material,
                add_sleeve,
                add_seasons,
                add_occasions,
                add_name,
            ],
        )

        # 類別改變時動態更新欄位
        add_category.change(
            update_category_fields,
            inputs=[add_category],
            outputs=[add_color, add_material, add_sleeve, add_occasions],
        )

        # 篩選類別變更時更新選項
        filter_category.change(
            update_filter_options,
            inputs=[filter_category],
            outputs=[filter_color, filter_material, filter_occasion],
        )

        filter_btn.click(
            refresh_clothes_list,
            inputs=[
                filter_category,
                filter_color,
                filter_material,
                filter_season,
                filter_occasion,
            ],
            outputs=[clothes_list],
        )

        delete_btn.click(
            delete_clothing, inputs=[delete_id], outputs=[add_msg, clothes_list]
        ).then(lambda: "", outputs=[delete_id])

        # 選項管理
        # 顏色類別變更時更新下拉選單
        color_option_category.change(
            lambda cat: refresh_option_choices(f"color_{cat}"),
            inputs=[color_option_category],
            outputs=[color_delete],
        )

        # 材質類別變更時更新下拉選單
        material_category.change(
            lambda cat: refresh_option_choices(f"material_{cat}"),
            inputs=[material_category],
            outputs=[material_delete],
        )

        color_add_btn.click(
            lambda cat, x: add_option(f"color_{cat}", x),
            inputs=[color_option_category, color_new],
            outputs=[color_msg],
        ).then(
            lambda cat: refresh_option_choices(f"color_{cat}"),
            inputs=[color_option_category],
            outputs=[color_delete],
        )

        color_delete_btn.click(
            lambda cat, x: delete_option(f"color_{cat}", x),
            inputs=[color_option_category, color_delete],
            outputs=[color_msg],
        ).then(
            lambda cat: refresh_option_choices(f"color_{cat}"),
            inputs=[color_option_category],
            outputs=[color_delete],
        )

        material_add_btn.click(
            lambda cat, x: add_option(f"material_{cat}", x),
            inputs=[material_category, material_new],
            outputs=[material_msg],
        ).then(
            lambda cat: refresh_option_choices(f"material_{cat}"),
            inputs=[material_category],
            outputs=[material_delete],
        )

        material_delete_btn.click(
            lambda cat, x: delete_option(f"material_{cat}", x),
            inputs=[material_category, material_delete],
            outputs=[material_msg],
        ).then(
            lambda cat: refresh_option_choices(f"material_{cat}"),
            inputs=[material_category],
            outputs=[material_delete],
        )

        occasion_add_btn.click(
            lambda x: add_option("occasion", x),
            inputs=[occasion_new],
            outputs=[occasion_msg],
        ).then(
            lambda: refresh_option_choices("occasion"), outputs=[add_occasions]
        ).then(
            lambda: refresh_option_choices("occasion"), outputs=[occasion_delete]
        )

        # 穿搭行事曆

        outfit_filter_category.change(
            update_filter_options,
            inputs=[outfit_filter_category],
            outputs=[
                outfit_filter_color,
                outfit_filter_material,
                outfit_filter_occasion,
            ],
        ).then(
            lambda cat: update_outfit_clothes_list(cat, "全部", "全部", "全部", "全部"),
            inputs=[outfit_filter_category],
            outputs=[outfit_clothes],
        )

        def load_outfit_for_date(date_display):
            """載入指定日期的穿搭"""
            if not date_display:
                return gr.update()

            try:
                # 從顯示字串中提取日期
                date_str = date_display.split(" ")[0]
                user_id = get_current_user_id()
                outfit_ids = db.get_outfit(user_id, date_str)

                return gr.update(value=[str(x) for x in outfit_ids])
            except:
                return gr.update()

        outfit_date.change(
            load_outfit_for_date, inputs=[outfit_date], outputs=[outfit_clothes]
        )

        def save_outfit_wrapper(date_display, clothes_ids):
            """儲存穿搭並刷新行事曆、清空勾選"""
            if not date_display:
                return "請選擇日期", get_calendar_view_only(), []

            date_str = date_display.split(" ")[0]
            # 將字串 ID 轉換為整數
            clothes_ids_int = [int(x) for x in clothes_ids] if clothes_ids else []
            msg = save_daily_outfit(date_str, clothes_ids_int)
            # 返回訊息、更新的行事曆、清空的勾選框
            return msg, get_calendar_view_only(), []

        outfit_save_btn.click(
            save_outfit_wrapper,
            inputs=[outfit_date, outfit_clothes],
            outputs=[outfit_msg, calendar_view, outfit_clothes],
        )

        def delete_outfit_wrapper(date_display):
            """刪除穿搭並刷新行事曆"""
            if not date_display:
                return "請選擇日期", get_calendar_view_only()

            date_str = date_display.split(" ")[0]
            msg = delete_daily_outfit(date_str)
            return msg, get_calendar_view_only()

        outfit_delete_btn.click(
            delete_outfit_wrapper,
            inputs=[outfit_date],
            outputs=[outfit_msg, calendar_view],
        )

        curr_week_btn.click(
            lambda: (0,) + refresh_calendar_view(0),
            outputs=[week_offset_state, calendar_view, prev_week_btn, next_week_btn],
        )

        prev_week_btn.click(
            lambda offset: (offset - 1,) + refresh_calendar_view(offset - 1),
            inputs=[week_offset_state],
            outputs=[week_offset_state, calendar_view, prev_week_btn, next_week_btn],
        )

        next_week_btn.click(
            lambda offset: (offset + 1,) + refresh_calendar_view(offset + 1),
            inputs=[week_offset_state],
            outputs=[week_offset_state, calendar_view, prev_week_btn, next_week_btn],
        )

        # 歷史穿搭 - 類別篩選（簡單版本，只篩選類別）
        history_cloth_category.change(
            update_filter_options,
            inputs=[history_cloth_category],
            outputs=[
                history_cloth_color,
                history_cloth_material,
                history_cloth_occasion,
            ],
        ).then(
            lambda cat: update_history_clothes_list(
                cat, "全部", "全部", "全部", "全部"
            ),
            inputs=[history_cloth_category],
            outputs=[history_cloth_select],
        )

        history_search_btn.click(
            search_outfit_history,
            inputs=[history_cloth_select],
            outputs=[history_result],
        )

        # 穿搭安排篩選
        outfit_filter_btn.click(
            update_outfit_clothes_list,
            inputs=[
                outfit_filter_category,
                outfit_filter_color,
                outfit_filter_material,
                outfit_filter_season,
                outfit_filter_occasion,
            ],
            outputs=[outfit_clothes],
        )

        # 歷史穿搭篩選
        history_filter_btn.click(
            update_history_clothes_list,
            inputs=[
                history_cloth_category,
                history_cloth_color,
                history_cloth_material,
                history_cloth_season,
                history_cloth_occasion,
            ],
            outputs=[history_cloth_select],
        )

        # 天氣查詢
        weather_refresh_btn.click(
            refresh_weather_display,
            inputs=[weather_city, weather_days],
            outputs=[weather_display],
        )

        location_add_btn.click(
            add_location, inputs=[location_new], outputs=[location_msg, weather_city]
        ).then(lambda: "", outputs=[location_new]).then(
            lambda: gr.update(choices=db.get_user_locations(get_current_user_id())),
            outputs=[location_delete],
        )

        location_delete_btn.click(
            delete_location,
            inputs=[location_delete],
            outputs=[location_msg, weather_city],
        ).then(
            lambda: gr.update(choices=db.get_user_locations(get_current_user_id())),
            outputs=[location_delete],
        )

        # Email 設定
        email_bind_btn.click(
            bind_user_email,
            inputs=[email_input],
            outputs=[email_bind_msg, email_display],
        ).then(lambda: "", outputs=[email_input])

        email_save_btn.click(
            save_email_settings, inputs=[email_time, email_enabled], outputs=[email_msg]
        )

        email_test_btn.click(send_test_email, outputs=[email_msg])

    return app


# ==================== 啟動應用程式 ====================

if __name__ == "__main__":
    gradio_app = create_gradio_app()

    # 將 Gradio app 掛載到 Flask
    gradio_app_with_flask = gr.mount_gradio_app(flask_app, gradio_app, path="/")

    # 啟動 Flask app
    gradio_app_with_flask.run(host="0.0.0.0", port=7860, debug=False)

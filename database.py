"""
資料庫管理模組
負責所有 SQLite 資料庫操作
"""

import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "clothes.db")


def get_connection():
    """取得資料庫連線"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """初始化資料庫結構"""
    conn = get_connection()
    cursor = conn.cursor()

    # 使用者資料表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plain_password TEXT,
            email TEXT,
            email_time TEXT DEFAULT '07:00',
            email_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # 檢查並新增 email_enabled 欄位（向後相容）
    try:
        cursor.execute("SELECT email_enabled FROM users LIMIT 1")
    except:
        cursor.execute("ALTER TABLE users ADD COLUMN email_enabled INTEGER DEFAULT 1")

    # 檢查並新增 plain_password 欄位（向後相容）
    try:
        cursor.execute("SELECT plain_password FROM users LIMIT 1")
    except:
        cursor.execute("ALTER TABLE users ADD COLUMN plain_password TEXT")

    # 衣物資料表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clothes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            color TEXT NOT NULL,
            material TEXT,
            sleeve_type TEXT,
            seasons TEXT NOT NULL,
            occasions TEXT,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """
    )

    # 檢查並新增 name 欄位（向後相容）
    try:
        cursor.execute("SELECT name FROM clothes LIMIT 1")
    except:
        cursor.execute("ALTER TABLE clothes ADD COLUMN name TEXT")

    # 穿搭計畫資料表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            clothes_ids TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """
    )

    # 選項設定資料表（儲存動態選項）
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            option_type TEXT NOT NULL,
            option_value TEXT NOT NULL,
            UNIQUE(user_id, option_type, option_value),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """
    )

    # 地區設定資料表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city_name TEXT NOT NULL,
            UNIQUE(user_id, city_name),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """
    )

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()


# ========== 使用者管理 ==========


def create_user(username: str, password: str, email: str = None) -> Tuple[bool, str]:
    """建立新使用者"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, plain_password, email, email_enabled) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, password, email, 1 if email else 0),
        )
        conn.commit()

        # 初始化預設選項
        user_id = cursor.lastrowid
        init_default_options(user_id)
        init_default_locations(user_id)

        conn.close()
        return True, "註冊成功！"
    except sqlite3.IntegrityError:
        return False, "帳號已存在！"
    except Exception as e:
        return False, f"註冊失敗：{str(e)}"


def verify_user(username: str, password: str) -> Optional[int]:
    """驗證使用者，返回 user_id"""
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_password_hint(username: str) -> Optional[str]:
    """取得使用者密碼（明文）
    注意：儲存明文密碼不是安全的做法，僅供個人使用或教學用途"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT plain_password, password_hash FROM users WHERE username = ?",
        (username,),
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        if result[0]:  # plain_password 存在
            return result[0]
        else:  # 舊用戶沒有 plain_password
            return f"此帳號建立於舊版本，無法查詢密碼。\n密碼雜湊值開頭：{result[1][:12]}...\n建議重新註冊新帳號。"
    return None


def get_user_email_settings(user_id: int) -> Tuple[str, str, bool]:
    """取得使用者的 Email 設定"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT email, email_time, email_enabled FROM users WHERE id = ?", (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0] or "", result[1] or "07:00", bool(result[2])
    return "", "07:00", False


def update_user_email_settings(user_id: int, email_time: str, email_enabled: bool):
    """更新使用者的 Email 設定"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET email_time = ?, email_enabled = ? WHERE id = ?",
        (email_time, 1 if email_enabled else 0, user_id),
    )
    conn.commit()
    conn.close()


def update_user_email(user_id: int, email: str) -> bool:
    """更新使用者的 Email 地址"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"更新 Email 錯誤：{e}")
        return False


def get_user_email(user_id: int) -> Optional[str]:
    """
    取得使用者的 Email 地址

    Args:
        user_id: 使用者 ID

    Returns:
        str: 使用者的 Email,如果不存在則回傳 None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["email"] if result and result["email"] else None


# ========== 選項管理 ==========


def init_default_options(user_id: int):
    """初始化預設選項"""
    conn = get_connection()
    cursor = conn.cursor()

    default_options = {
        # 上衣
        "color_上衣": ["白", "黑", "灰", "卡其", "藍"],
        "material_上衣": ["襯衫", "外搭", "一般", "刷毛", "高領", "毛衣"],
        "sleeve_上衣": ["長袖", "短袖"],
        # 褲子
        "color_褲子": ["白", "黑"],
        "material_褲子": ["一般", "刷毛", "牛仔", "西裝"],
        "sleeve_褲子": ["長褲", "短褲"],
        # 外套
        "color_外套": ["白", "黑"],
        "material_外套": ["衝鋒", "休閒", "正式", "羽絨", "皮革"],
        # 襪子
        "color_襪子": ["白", "黑"],
        "sleeve_襪子": ["長襪", "中襪", "短襪"],
        # 場合（全局）
        "occasion": ["正式", "運動", "休閒"],
    }

    for option_type, values in default_options.items():
        for value in values:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO options (user_id, option_type, option_value) VALUES (?, ?, ?)",
                    (user_id, option_type, value),
                )
            except:
                pass

    conn.commit()
    conn.close()


def get_user_options(user_id: int, option_type: str) -> List[str]:
    """取得使用者的選項列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT option_value FROM options WHERE user_id = ? AND option_type = ? ORDER BY option_value",
        (user_id, option_type),
    )
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]


def add_user_option(user_id: int, option_type: str, option_value: str) -> bool:
    """新增使用者選項"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO options (user_id, option_type, option_value) VALUES (?, ?, ?)",
            (user_id, option_type, option_value),
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


def delete_user_option(user_id: int, option_type: str, option_value: str) -> bool:
    """刪除使用者選項"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM options WHERE user_id = ? AND option_type = ? AND option_value = ?",
            (user_id, option_type, option_value),
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


# ========== 衣物管理 ==========


def add_clothing(
    user_id: int,
    category: str,
    color: str,
    material: str,
    sleeve_type: str,
    seasons: List[str],
    occasions: List[str],
    name: str = None,
) -> bool:
    """新增衣物"""
    try:
        # 如果沒有填寫名稱，預設為 "XXX"
        if not name or name.strip() == "":
            name = "XXX"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO clothes (user_id, category, color, material, sleeve_type, seasons, occasions, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                category,
                color,
                material,
                sleeve_type,
                json.dumps(seasons, ensure_ascii=False),
                json.dumps(occasions, ensure_ascii=False) if occasions else None,
                name,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"新增衣物錯誤：{e}")
        return False


def get_user_clothes(
    user_id: int,
    category: str = None,
    color: str = None,
    material: str = None,
    season: str = None,
    occasion: str = None,
) -> List[Dict]:
    """取得使用者的衣物列表（支援篩選）"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM clothes WHERE user_id = ?"
    params = [user_id]

    if category:
        query += " AND category = ?"
        params.append(category)
    if color:
        query += " AND color = ?"
        params.append(color)
    if material:
        query += " AND material = ?"
        params.append(material)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    clothes = []
    for row in results:
        cloth = dict(row)
        cloth["seasons"] = json.loads(cloth["seasons"])
        cloth["occasions"] = json.loads(cloth["occasions"])

        # 季節和場合篩選
        if season and season not in cloth["seasons"]:
            continue
        if occasion and occasion not in cloth["occasions"]:
            continue

        clothes.append(cloth)

    return clothes


def update_clothing(
    cloth_id: int,
    user_id: int,
    category: str,
    color: str,
    material: str,
    sleeve_type: str,
    seasons: List[str],
    occasions: List[str],
) -> bool:
    """更新衣物資訊"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE clothes 
            SET category = ?, color = ?, material = ?, sleeve_type = ?, seasons = ?, occasions = ?
            WHERE id = ? AND user_id = ?
        """,
            (
                category,
                color,
                material,
                sleeve_type,
                json.dumps(seasons, ensure_ascii=False),
                json.dumps(occasions, ensure_ascii=False),
                cloth_id,
                user_id,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


def delete_clothing(cloth_id: int, user_id: int) -> bool:
    """刪除衣物"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM clothes WHERE id = ? AND user_id = ?", (cloth_id, user_id)
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_clothing_by_id(cloth_id: int, user_id: int) -> Optional[Dict]:
    """根據 ID 取得單一衣物"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM clothes WHERE id = ? AND user_id = ?", (cloth_id, user_id)
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        cloth = dict(result)
        cloth["seasons"] = json.loads(cloth["seasons"])
        cloth["occasions"] = json.loads(cloth["occasions"])
        return cloth
    return None


# ========== 穿搭計畫管理 ==========


def save_outfit(user_id: int, date: str, clothes_ids: List[int]) -> bool:
    """儲存穿搭計畫（新增模式，不覆蓋現有衣物）"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 先取得現有的衣物ID列表
        cursor.execute(
            "SELECT clothes_ids FROM outfits WHERE user_id = ? AND date = ?",
            (user_id, date),
        )
        result = cursor.fetchone()

        if result:
            # 如果已有穿搭，將新衣物加入現有列表（去重）
            existing_ids = json.loads(result[0])
            # 合併並去重
            merged_ids = list(set(existing_ids + clothes_ids))
            cursor.execute(
                """
                UPDATE outfits SET clothes_ids = ? WHERE user_id = ? AND date = ?
            """,
                (json.dumps(merged_ids), user_id, date),
            )
        else:
            # 如果沒有穿搭，直接新增
            cursor.execute(
                """
                INSERT INTO outfits (user_id, date, clothes_ids)
                VALUES (?, ?, ?)
            """,
                (user_id, date, json.dumps(clothes_ids)),
            )

        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_outfit(user_id: int, date: str) -> List[int]:
    """取得指定日期的穿搭計畫"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT clothes_ids FROM outfits WHERE user_id = ? AND date = ?",
        (user_id, date),
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return json.loads(result[0])
    return []


def get_outfits_range(
    user_id: int, start_date: str, end_date: str
) -> Dict[str, List[int]]:
    """取得日期範圍內的穿搭計畫"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, clothes_ids FROM outfits WHERE user_id = ? AND date BETWEEN ? AND ?",
        (user_id, start_date, end_date),
    )
    results = cursor.fetchall()
    conn.close()

    outfits = {}
    for row in results:
        outfits[row[0]] = json.loads(row[1])
    return outfits


def delete_outfit(user_id: int, date: str) -> bool:
    """刪除指定日期的穿搭計畫"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM outfits WHERE user_id = ? AND date = ?", (user_id, date)
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_outfit_history_by_clothing(user_id: int, cloth_id: int) -> List[Dict]:
    """查詢某件衣物的歷史穿搭記錄"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, clothes_ids FROM outfits WHERE user_id = ? ORDER BY date DESC",
        (user_id,),
    )
    results = cursor.fetchall()
    conn.close()

    history = []
    for row in results:
        clothes_ids = json.loads(row[1])
        # 檢查這件衣物是否在這天的穿搭中
        if cloth_id in clothes_ids:
            history.append({"date": row[0], "clothes_ids": clothes_ids})

    return history


def get_all_past_outfits(user_id: int) -> List[Dict]:
    """取得所有過去的穿搭記錄"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, clothes_ids FROM outfits WHERE user_id = ? AND date < ? ORDER BY date DESC",
        (user_id, today),
    )
    results = cursor.fetchall()
    conn.close()

    outfits = []
    for row in results:
        outfits.append({"date": row[0], "clothes_ids": json.loads(row[1])})

    return outfits


# ========== 地區管理 ==========


def init_default_locations(user_id: int):
    """初始化預設地區"""
    conn = get_connection()
    cursor = conn.cursor()

    default_locations = ["泰山", "板橋"]
    for location in default_locations:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO locations (user_id, city_name) VALUES (?, ?)",
                (user_id, location),
            )
        except:
            pass

    conn.commit()
    conn.close()


def get_user_locations(user_id: int) -> List[str]:
    """取得使用者的地區列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT city_name FROM locations WHERE user_id = ? ORDER BY id", (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]


def add_user_location(user_id: int, city_name: str) -> bool:
    """新增使用者地區"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO locations (user_id, city_name) VALUES (?, ?)",
            (user_id, city_name),
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


def delete_user_location(user_id: int, city_name: str) -> bool:
    """刪除使用者地區"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM locations WHERE user_id = ? AND city_name = ?",
            (user_id, city_name),
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


# 初始化資料庫
if __name__ == "__main__":
    init_database()
    print("資料庫初始化完成！")

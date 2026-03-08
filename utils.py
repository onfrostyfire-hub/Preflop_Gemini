import streamlit as st
import json
import pandas as pd
import os
import random
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

SPOTS_DIR = 'spots_data'
RANKS = 'AKQJT98765432'

# --- GOOGLE SHEETS SETUP ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SPREADSHEET_ID = '15ouWJYZuQET1-sy7k5Wrn1fAzNUX6ssk5K8SOM9uYOc'

@st.cache_resource
def get_gspread_client():
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_JSON"])
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Ошибка подключения к Google Sheets: Проверь секреты в Streamlit! {e}")
        st.stop()

def get_sheet(sheet_name):
    client = get_gspread_client()
    return client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)

ALL_HANDS = []
for i, r1 in enumerate(RANKS):
    for j, r2 in enumerate(RANKS):
        if i < j: ALL_HANDS.append(r1 + r2 + 's'); ALL_HANDS.append(r1 + r2 + 'o')
        elif i == j: ALL_HANDS.append(r1 + r2)

@st.cache_data(ttl=0)
def load_ranges():
    db = {}
    if not os.path.exists(SPOTS_DIR): return db
    for file in os.listdir(SPOTS_DIR):
        if file.endswith('.json'):
            with open(os.path.join(SPOTS_DIR, file), 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    src = data.get("source", "Unknown")
                    sc = data.get("scenario", "Unknown")
                    if src not in db: db[src] = {}
                    if sc not in db[src]: db[src][sc] = {}
                    db[src][sc].update(data.get("spots", {}))
                except Exception as e:
                    st.error(f"Ошибка чтения {file}: {e}")
    return db

def get_filtered_pool(ranges_db, selected_sources, selected_scenarios):
    pool = []
    for src in selected_sources:
        for sc in selected_scenarios:
            if sc not in ranges_db.get(src, {}): continue
            for sp in ranges_db[src][sc]:
                pool.append(f"{src}|{sc}|{sp}")
    return pool

# --- БУФЕРНАЯ ОБЛАЧНАЯ БАЗА ДАННЫХ ---

def init_cloud_data():
    if "srs_data" not in st.session_state:
        try:
            vals = get_sheet("SRS").get_all_values()
            st.session_state["srs_data"] = {str(r[0]): int(r[1]) for r in vals[1:]} if len(vals) > 1 else {}
        except:
            st.session_state["srs_data"] = {}
            
    if "history_buffer" not in st.session_state:
        st.session_state["history_buffer"] = []
        
    if "unsaved_count" not in st.session_state:
        st.session_state["unsaved_count"] = 0

def load_srs_data():
    init_cloud_data()
    return st.session_state["srs_data"]

def update_srs_smart(spot_id, hand, rating):
    init_cloud_data()
    data = st.session_state["srs_data"]
    key = f"{spot_id}_{hand}"
    w = data.get(key, 100)
    
    if rating == 'hard': w *= 2.5
    elif rating == 'normal': w = w / 1.5 if w > 100 else w * 1.2
    elif rating == 'easy': w /= 4.0
    
    data[key] = int(max(1, min(w, 2000)))
    st.session_state["unsaved_count"] += 1
    check_auto_sync()

def save_to_history(record):
    init_cloud_data()
    row = [
        str(record.get("Date", "")),
        str(record.get("Spot", "")),
        str(record.get("Hand", "")),
        str(record.get("Result", "")),
        str(record.get("CorrectAction", ""))
    ]
    st.session_state["history_buffer"].append(row)
    st.session_state["unsaved_count"] += 1
    check_auto_sync()

def check_auto_sync():
    # Ответ + Оценка = 2 действия. Синхронизируем каждые 5 раздач (10 действий)
    if st.session_state["unsaved_count"] >= 10:
        force_sync()

def force_sync():
    if st.session_state.get("unsaved_count", 0) == 0: return
    try:
        # Выгружаем веса одним обновлением
        if "srs_data" in st.session_state:
            rows = [["Key", "Weight"]] + [[k, v] for k, v in st.session_state["srs_data"].items()]
            get_sheet("SRS").update(values=rows, range_name="A1")

        # Выгружаем историю пачкой
        if "history_buffer" in st.session_state and st.session_state["history_buffer"]:
            get_sheet("History").append_rows(st.session_state["history_buffer"])
            st.session_state["history_buffer"] = []

        st.session_state["unsaved_count"] = 0
    except Exception as e:
        # Если Гугл лагает, просто проглатываем ошибку, буфер сохранится при следующем клике
        pass

@st.cache_data(ttl=600)
def load_user_settings():
    try:
        val = get_sheet("Settings").acell('A1').value
        return json.loads(val) if val else {}
    except:
        return {}

def save_user_settings(settings):
    try:
        get_sheet("Settings").update_acell('A1', json.dumps(settings))
        load_user_settings.clear()
    except:
        pass

@st.cache_data(ttl=60)
def load_history():
    try:
        vals = get_sheet("History").get_all_values()
        if not vals or len(vals) < 2:
            return pd.DataFrame(columns=["Date", "Spot", "Hand", "Result", "CorrectAction"])
        return pd.DataFrame(vals[1:], columns=vals[0])
    except:
        return pd.DataFrame(columns=["Date", "Spot", "Hand", "Result", "CorrectAction"])

def delete_history(days=None):
    try:
        sheet = get_sheet("History")
        if days is None:
            sheet.clear()
            sheet.append_row(["Date", "Spot", "Hand", "Result", "CorrectAction"])
        else:
            df = load_history()
            if df.empty: return
            df["Date"] = pd.to_datetime(df["Date"])
            now = datetime.now()
            cutoff = now - timedelta(days=days)
            df_new = df[df["Date"] >= cutoff] 
            
            sheet.clear()
            rows = [["Date", "Spot", "Hand", "Result", "CorrectAction"]] + df_new.astype(str).values.tolist()
            sheet.update(values=rows, range_name="A1")
        
        load_history.clear()
        st.session_state["history_buffer"] = []
    except Exception as e:
        st.error(f"Ошибка удаления истории: {e}")

# --- МАТЕМАТИКА И ОТРИСОВКА ---

def get_weight(hand, range_str):
    if not range_str or not isinstance(range_str, str): return 0.0
    cleaned = range_str.replace('\n', ' ').replace('\r', '')
    items = [x.strip() for x in cleaned.split(',')]
    for item in items:
        if ':' in item:
            h_part, w_part = item.split(':')
            try:
                weight = float(w_part)
                if weight <= 1.0: weight *= 100
            except:
                weight = 100.0
        else:
            h_part = item
            weight = 100.0
        if h_part == hand: return weight
        if len(h_part) == 2 and h_part[0] != h_part[1] and hand.startswith(h_part): return weight
    return 0.0

def parse_range_to_list(range_str):
    if not range_str or not isinstance(range_str, str) or "22+" in range_str or range_str == "ALL":
        return ALL_HANDS.copy()
        
    hand_list = []
    cleaned = range_str.replace('\n', ' ').replace('\r', '')
    items = [x.strip() for x in cleaned.split(',')]
    for item in items:
        if not item: continue
        h = item.split(':')[0]
        if h in ALL_HANDS: hand_list.append(h)
        elif len(h) == 2:
            if h[0] == h[1]: hand_list.append(h)
            else: hand_list.extend([h+'s', h+'o'])
            
    if not hand_list:
        return ALL_HANDS.copy()
        
    return list(set(hand_list))

def render_range_matrix(spot_data, target_hand=None):
    ranges = spot_data.get("ranges", spot_data)
    r_call = ranges.get("call", ranges.get("Call", ""))
    r_raise = ranges.get("4bet", ranges.get("3bet", ranges.get("Raise", "")))
    r_full = ranges.get("full", ranges.get("Full", ""))
    
    grid_html = '<div style="display:grid;grid-template-columns:repeat(13,1fr);gap:1px;background:#111;padding:1px;border:1px solid #444;">'
    for r1 in RANKS:
        for r2 in RANKS:
            if RANKS.index(r1) == RANKS.index(r2): h = r1 + r2
            elif RANKS.index(r1) < RANKS.index(r2): h = r1 + r2 + 's'
            else: h = r2 + r1 + 'o'
            
            w_c = get_weight(h, r_call)
            w_4 = get_weight(h, r_raise)
            w_f = get_weight(h, r_full)
            
            raise_w = w_4 if w_4 > 0 else w_f
            call_w = w_c
            
            total_w = raise_w + call_w
            if total_w > 100:
                raise_w = (raise_w / total_w) * 100
                call_w = (call_w / total_w) * 100
            
            style = "aspect-ratio:1;display:flex;justify-content:center;align-items:center;font-size:7px;cursor:default;color:#fff;"
            
            if raise_w == 0 and call_w == 0:
                bg = "#2c3034"
                style += "color:#495057;"
            elif raise_w >= 100:
                bg = "#d63384"
            elif call_w >= 100:
                bg = "#28a745"
            else:
                stops = []
                curr_pct = 0.0
                
                if raise_w > 0:
                    stops.append(f"#d63384 {curr_pct}%")
                    curr_pct += raise_w
                    stops.append(f"#d63384 {curr_pct}%")
                
                if call_w > 0:
                    stops.append(f"#28a745 {curr_pct}%")
                    curr_pct += call_w
                    stops.append(f"#28a745 {curr_pct}%")
                
                if curr_pct < 100:
                    stops.append(f"#2c3034 {curr_pct}%")
                    stops.append(f"#2c3034 100%")
                
                bg = f"linear-gradient(to right, {', '.join(stops)})"
            
            style += f"background:{bg};"
            if target_hand and h == target_hand: style += "border:1.5px solid #ffc107;z-index:10;box-shadow: 0 0 4px #ffc107;"
            grid_html += f'<div style="{style}">{h}</div>'
    grid_html += '</div>'

    stats = spot_data.get("stats", {})
    if stats:
        stats_html = '<div style="display:flex; gap:8px; justify-content:center; margin-top:10px; flex-wrap:wrap; font-size:12px; font-weight:bold; font-family:sans-serif;">'
        for k, v in stats.items():
            kl = k.lower()
            if "raise" in kl or "3bet" in kl or "4bet" in kl or "pfr" in kl:
                color = "#d63384" 
            elif "call" in kl:
                color = "#28a745" 
            elif "fold" in kl:
                color = "#6c757d" 
            else:
                color = "#adb5bd" 
            stats_html += f'<div style="background:#222; border:1px solid {color}; color:{color}; padding:4px 10px; border-radius:6px; box-shadow: 0 2px 4px rgba(0,0,0,0.4);">{k} {v}</div>'
        stats_html += '</div>'
        grid_html += stats_html

    return grid_html

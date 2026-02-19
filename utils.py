import streamlit as st
import json
import pandas as pd
import os
import random
from datetime import datetime, timedelta

SPOTS_DIR = 'spots_data'
HISTORY_FILE = 'history_log.csv'
SRS_FILE = 'srs_data.json'
SETTINGS_FILE = 'user_settings.json'
RANKS = 'AKQJT98765432'

ALL_HANDS = []
for i, r1 in enumerate(RANKS):
    for j, r2 in enumerate(RANKS):
        if i < j: ALL_HANDS.append(r1 + r2 + 's'); ALL_HANDS.append(r1 + r2 + 'o')
        elif i == j: ALL_HANDS.append(r1 + r2)

@st.cache_data(ttl=0)
def load_ranges():
    db = {}
    if not os.path.exists(SPOTS_DIR): return db
    # Читаем все файлы из папки spots_data
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
    """
    Выдает только те споты, которые принадлежат выбранным сценариям.
    Больше никаких хардкод-групп и каши.
    """
    pool = []
    for src in selected_sources:
        for sc in selected_scenarios:
            if sc not in ranges_db.get(src, {}): continue
            for sp in ranges_db[src][sc]:
                pool.append(f"{src}|{sc}|{sp}")
    return pool

# --- СТАНДАРТНЫЕ ФУНКЦИИ ПАМЯТИ И ЛОГОВ ---
def load_srs_data():
    if not os.path.exists(SRS_FILE): return {}
    with open(SRS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def save_srs_data(data):
    with open(SRS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f)

def load_user_settings():
    if not os.path.exists(SETTINGS_FILE): return {}
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def save_user_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(settings, f)

def load_history():
    if os.path.exists(HISTORY_FILE): return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["Date", "Spot", "Hand", "Result", "CorrectAction"])

def save_to_history(record):
    df_new = pd.DataFrame([record])
    if not os.path.exists(HISTORY_FILE): df_new.to_csv(HISTORY_FILE, index=False)
    else: df_new.to_csv(HISTORY_FILE, mode='a', header=False, index=False)

def delete_history(days=None):
    if not os.path.exists(HISTORY_FILE): return
    df = pd.read_csv(HISTORY_FILE)
    if df.empty: return
    if days is None: df_new = pd.DataFrame(columns=df.columns)
    else:
        df["Date"] = pd.to_datetime(df["Date"])
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        df_new = df[df["Date"] < cutoff]
    df_new.to_csv(HISTORY_FILE, index=False)

def update_srs_smart(spot_id, hand, rating):
    data = load_srs_data()
    key = f"{spot_id}_{hand}"
    w = data.get(key, 100)
    if rating == 'hard': w *= 2.5
    elif rating == 'normal': w = w / 1.5 if w > 100 else w * 1.2
    elif rating == 'easy': w /= 4.0
    data[key] = int(max(1, min(w, 2000)))
    save_srs_data(data)

def get_weight(hand, range_str):
    if not range_str or not isinstance(range_str, str): return 0.0
    cleaned = range_str.replace('\n', ' ').replace('\r', '')
    items = [x.strip() for x in cleaned.split(',')]
    for item in items:
        if ':' in item:
            h_part, w_part = item.split(':')
            weight = float(w_part)
            if weight <= 1.0: weight *= 100
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
    # Теперь мы извлекаем ренджи из вложенного блока "ranges", как указано в новых JSON
    ranges = spot_data.get("ranges", {})
    r_call = ranges.get("call", "")
    r_raise = ranges.get("4bet", ranges.get("3bet", ""))
    r_full = ranges.get("full", "")
    
    grid_html = '<div style="display:grid;grid-template-columns:repeat(13,1fr);gap:1px;background:#111;padding:1px;border:1px solid #444;">'
    for r1 in RANKS:
        for r2 in RANKS:
            if RANKS.index(r1) == RANKS.index(r2): h = r1 + r2
            elif RANKS.index(r1) < RANKS.index(r2): h = r1 + r2 + 's'
            else: h = r2 + r1 + 'o'
            
            w_c = get_weight(h, r_call)
            w_4 = get_weight(h, r_raise)
            w_f = get_weight(h, r_full)
            
            style = "aspect-ratio:1;display:flex;justify-content:center;align-items:center;font-size:7px;cursor:default;color:#fff;"
            bg = "#2c3034"
            if w_4 > 0 or w_c > 0:
                if w_4 > 0 and w_c > 0: bg = "linear-gradient(135deg, #d63384 50%, #28a745 50%)"
                elif w_4 > 0 and w_4 < 100: bg = "linear-gradient(135deg, #d63384 50%, #2c3034 50%)"
                elif w_c > 0 and w_c < 100: bg = "linear-gradient(135deg, #28a745 50%, #2c3034 50%)"
                elif w_4 >= 100: bg = "#d63384"
                elif w_c >= 100: bg = "#28a745"
            elif w_f > 0:
                if w_f < 100: bg = "linear-gradient(135deg, #28a745 50%, #2c3034 50%)"
                else: bg = "#28a745"
            else: style += "color:#495057;"
            style += f"background:{bg};"
            if target_hand and h == target_hand: style += "border:1.5px solid #ffc107;z-index:10;box-shadow: 0 0 4px #ffc107;"
            grid_html += f'<div style="{style}">{h}</div>'
    return grid_html + '</div>'

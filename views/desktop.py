import streamlit as st
import random
from datetime import datetime
import utils

def show():
    st.markdown("""
    <style>
        .stApp { background-color: #212529; color: #e9ecef; }
        .block-container { padding-top: 4rem; }
        .game-area { position: relative; width: 100%; max-width: 700px; height: 400px; margin: 0 auto; background: radial-gradient(ellipse at center, #2e7d32 0%, #1b5e20 100%); border: 15px solid #4a1c1c; border-radius: 200px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .table-info { position: absolute; top: 20%; width: 100%; text-align: center; pointer-events: none; }
        .info-spot { font-size: 24px; font-weight: 800; color: rgba(255,255,255,0.2); }
        .seat { position: absolute; width: 65px; height: 65px; background: #343a40; border: 2px solid #495057; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 5; }
        .seat-label { font-size: 11px; font-weight: bold; color: #adb5bd; margin-bottom: 2px; }
        .seat-amount { font-size: 14px; font-weight: 800; color: #fff; }
        .seat.hero { background: #007bff; border-color: #0056b3; box-shadow: 0 0 15px rgba(0,123,255,0.5); }
        .seat.villain { background: #dc3545; border-color: #a71d2a; box-shadow: 0 0 15px rgba(220,53,69,0.5); }
        .pos-btn { top: 85%; left: 50%; transform: translate(-50%, -50%); }
        .pos-sb { top: 75%; left: 20%; transform: translate(-50%, -50%); }
        .pos-bb { top: 50%; left: 10%; transform: translate(-50%, -50%); }
        .pos-utg { top: 20%; left: 25%; transform: translate(-50%, -50%); }
        .pos-mp { top: 15%; left: 50%; transform: translate(-50%, -50%); }
        .pos-co { top: 25%; left: 80%; transform: translate(-50%, -50%); }
        .cards-container { position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); display: flex; gap: 5px; z-index: 10; }
        .card { width: 60px; height: 85px; background: white; border-radius: 5px; border: 1px solid #ccc; display: flex; justify-content: center; align-items: center; font-size: 28px; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
        .card.red { color: #dc3545; }
        .card.black { color: #212529; }
        .dealer-btn { position: absolute; width: 25px; height: 25px; background: white; border-radius: 50%; border: 2px solid #333; color: black; font-weight: bold; font-size: 12px; display: flex; justify-content: center; align-items: center; z-index: 6; }
        .desk-controls { display: flex; justify-content: center; gap: 15px; margin-top: 30px; }
        .desk-controls button { width: 140px; height: 50px; font-weight: 800; font-size: 18px; border-radius: 8px; border: none; text-transform: uppercase; cursor: pointer; transition: 0.2s; }
        .fold-btn button { background: #495057; color: #adb5bd; }
        .call-btn button { background: #28a745; color: white; }
        .raise-btn button { background: #d63384; color: white; }
        .open-raise-btn button { background: #2e7d32; color: white; }
        .chip { width: 20px; height: 20px; background: radial-gradient(circle, #ffeb3b, #fbc02d); border-radius: 50%; color: #000; font-weight: bold; font-size: 11px; display: flex; justify-content: center; align-items: center; z-index: 15; position: absolute; border: 1px solid #bfa006; }
        .bet-txt { font-size: 12px; font-weight: bold; color: #fff; text-shadow: 1px 1px 2px #000; background: rgba(0,0,0,0.6); padding: 1px 4px; border-radius: 4px; margin-top: -5px; z-index: 20; }
        .hero-panel { position: absolute; bottom: -45px; left: 50%; transform: translateX(-50%); background: #212529; border: 1px solid #495057; border-radius: 8px; padding: 5px 15px; display: flex; gap: 10px; z-index: 20; }
    </style>
    """, unsafe_allow_html=True)

    ranges_db = utils.load_ranges()
    if not ranges_db: st.error("База ренджей пуста."); return
    
    scenario_map = {}
    for src, sc_dict in ranges_db.items():
        for sc, sp_dict in sc_dict.items():
            mapped_sc = sc
            sc_lower = sc.lower()
            if "def" in sc_lower and "3bet" in sc_lower: mapped_sc = "Def vs 3bet"
            elif "3bet" in sc_lower: mapped_sc = "3bet"
            elif "pfr" in sc_lower or "bbvsbu" in sc_lower or "bb def" in sc_lower: mapped_sc = "BB def vs PFR"
            elif "open raise" in sc_lower: mapped_sc = "Open Raise"
            
            if mapped_sc not in scenario_map: scenario_map[mapped_sc] = []
            for sp in sp_dict.keys():
                scenario_map[mapped_sc].append((sp, f"{src}|{sc}|{sp}"))
    
    all_scenarios = ["Open Raise", "BB def vs PFR", "Def vs 3bet", "3bet"]
    all_scenarios = [s for s in all_scenarios if s in scenario_map]

    with st.sidebar:
        st.header("⚙️ Фильтры")
        saved = utils.load_user_settings()
        
        saved_sc = [s for s in saved.get("scenarios", []) if s in all_scenarios]
        sel_sc = st.multiselect("Сценарий", all_scenarios, default=saved_sc if saved_sc else (all_scenarios[:1] if all_scenarios else []))
        
        sel_spots_keys = []
        for sc in sel_sc:
            opts = scenario_map[sc]
            opts_names = [o[0] for o in opts]
            saved_sp = [s for s in saved.get("spots", []) if s in opts_names]
            sel = st.multiselect(sc, opts_names, default=saved_sp if saved_sp else opts_names)
            sel_spots_keys.extend([o[1] for o in opts if o[0] in sel])
            
        if sel_sc != saved.get("scenarios") or [k.split('|')[-1] for k in sel_spots_keys] != saved.get("spots"):
            utils.save_user_settings({"scenarios": sel_sc, "spots": [k.split('|')[-1] for k in sel_spots_keys]})

    if not sel_spots_keys: st.info("Выбери споты."); return

    if "srs_mode" not in st.session_state:
        st.session_state.srs_mode = False
        st.session_state.hand = None
        st.session_state.spot_key = None
        st.session_state.msg = ""

    def get_next():
        srs = utils.load_srs_data()
        w_pool = []
        for pk in sel_spots_keys:
            src, sc, sp = pk.split('|')
            d = ranges_db[src][sc][sp]
            r = d.get("ranges", {})
            t = r.get("training", r.get("full", "ALL"))
            hands = utils.parse_range_to_list(t)
            sid = f"{src}_{sc}_{sp}".replace(" ","_")
            for h in hands:
                w_pool.append({"k": pk, "h": h, "w": srs.get(f"{sid}_{h}", 100)})
        
        if not w_pool: return None
        tot = sum(x["w"] for x in w_pool)
        r = random.uniform(0, tot)
        c = 0
        for x in w_pool:
            c += x["w"]
            if c >= r: return x
        return w_pool[-1]

    if not st.session_state.srs_mode and not st.session_state.hand:
        nxt = get_next()
        if nxt:
            st.session_state.spot_key = nxt["k"]
            st.session_state.hand = nxt["h"]
        else:
            st.warning("Нет рук"); return

    src, sc, sp = st.session_state.spot_key.split('|')
    data = ranges_db[src][sc][sp]
    ranges = data.get("ranges", data)
    
    r_raise = ranges.get("4bet", ranges.get("3bet", ranges.get("Raise", "")))
    r_call = ranges.get("call", ranges.get("Call", ""))
    
    w_raise_val = utils.get_weight(st.session_state.hand, r_raise)
    w_c = utils.get_weight(st.session_state.hand, r_call)
    
    rng = random.uniform(0, 100)
    w = w_raise_val + w_c
    if w == 0:
        correct_act = "FOLD"
    elif w < 100 and rng > w:
        correct_act = "FOLD"
    else:
        rng = random.uniform(0, w)
        if rng < w_raise_val: correct_act = "RAISE"
        elif rng < (w_raise_val + w_c): correct_act = "CALL"
        else:
            if w > 0: correct_act = "RAISE"
            else: correct_act = "FOLD"

    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        hero = data.get("hero", "BTN")
        villain = data.get("villain", "")
        dealer = data.get("dealer", "BTN")
        hero_bet = data.get("hero_bet", "")
        villain_bet = data.get("villain_bet", "")

        pos_map = {"BTN": "pos-btn", "SB": "pos-sb", "BB": "pos-bb", "UTG": "pos-utg", "MP": "pos-mp", "CO": "pos-co"}
        dealer_coords = {"BTN": (80, 50), "SB": (70, 25), "BB": (45, 15), "UTG": (25, 30), "MP": (50, 20), "CO": (80, 25)}
        dc = dealer_coords.get(dealer, (80, 50))

        h_val = st.session_state.hand
        c1, c2 = h_val[0], h_val[1]
        suit = h_val[2] if len(h_val) > 2 else ""
        if suit == 's': c1_s, c2_s = '♠', '♠'; c1_c, c2_c = 'black', 'black'
        elif suit == 'o': c1_s, c2_s = '♠', '♥'; c1_c, c2_c = 'black', 'red'
        else: c1_s, c2_s = '♠', '♠'; c1_c, c2_c = 'black', 'black'

        html = f"""
        <div class="game-area">
            <div class="table-info"><div class="info-spot">{sp}</div></div>
            <div class="dealer-btn" style="top:{dc[0]}%; left:{dc[1]}%;">D</div>
        """
        for p, css in pos_map.items():
            if p == hero: html += f'<div class="seat hero {css}"><div class="seat-label">{p}</div></div>'
            elif p == villain: html += f'<div class="seat villain {css}"><div class="seat-label">{p}</div><div class="seat-amount">{villain_bet}</div></div>'
            else: html += f'<div class="seat {css}"><div class="seat-label">{p}</div></div>'
            
        if hero_bet:
            html += f'<div style="position:absolute; bottom:25%; left:50%; transform:translate(-50%, 0); display:flex; flex-direction:column; align-items:center; z-index:15;"><div class="chip">$</div><div class="bet-txt">{hero_bet}</div></div>'
            
        html += f"""
            <div class="cards-container">
                <div class="card {c1_c}">{c1}{c1_s}</div>
                <div class="card {c2_c}">{c2}{c2_s}</div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

        if not st.session_state.srs_mode:
            st.markdown('<div class="desk-controls">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="fold-btn">', unsafe_allow_html=True)
                if st.button("FOLD", use_container_width=True):
                    corr = (correct_act == "FOLD")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="call-btn">', unsafe_allow_html=True)
                if st.button("CALL", use_container_width=True):
                    corr = (correct_act == "CALL")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c3:
                btn_class = "open-raise-btn" if "open raise" in sc.lower() else "raise-btn"
                st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                if st.button("RAISE", use_container_width=True):
                    corr = (correct_act == "RAISE")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if "open raise" in sc.lower():
                st.markdown('<script>parent.document.querySelectorAll("div[data-testid=\'column\'] button")[2].classList.add("open-raise-btn");</script>', unsafe_allow_html=True)
        else:
            if st.session_state.last_error:
                st.error(st.session_state.msg)
                if st.button("FOLD", key="e_f", use_container_width=True):
                    corr = (correct_act == "FOLD")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.rerun()
                if st.button("CALL", key="e_c", use_container_width=True):
                    corr = (correct_act == "CALL")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.rerun()
                if st.button("RAISE", key="e_r", use_container_width=True):
                    corr = (correct_act == "RAISE")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.rerun()
            else:
                st.success(st.session_state.msg)
                s1, s2, s3 = st.columns(3)
                k = f"{src}_{sc}_{sp}".replace(" ","_")
                if s1.button("HARD", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'hard'); st.session_state.hand = None; st.session_state.srs_mode = False; st.rerun()
                if s2.button("NORM", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'normal'); st.session_state.hand = None; st.session_state.srs_mode = False; st.rerun()
                if s3.button("EASY", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'easy'); st.session_state.hand = None; st.session_state.srs_mode = False; st.rerun()

    with col_right:
        if st.session_state.srs_mode:
            st.markdown(f"**{sp}** Range ({correct_act})")
            st.markdown(utils.render_range_matrix(data, st.session_state.hand), unsafe_allow_html=True)

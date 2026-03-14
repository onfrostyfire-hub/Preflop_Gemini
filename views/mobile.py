import streamlit as st
import random
from datetime import datetime
import utils

def show():
    st.markdown("""
    <style>
        .block-container { padding-top: 3rem !important; padding-bottom: 5rem !important; }
        .mobile-controls { display: flex; gap: 8px; margin-top: 8px; width: 100%; }
        .mobile-controls div[data-testid="column"] { flex: 1; min-width: 0; }
        .mobile-controls button { width: 100%; height: 65px; font-weight: 800; font-size: 18px; border-radius: 12px; border: none; text-transform: uppercase; }
        .fold-btn button { background: #495057; color: #adb5bd; border: 1px solid #6c757d; }
        .call-btn button { background: #28a745; color: white; box-shadow: 0 4px 0 #1e7e34; }
        .raise-btn button { background: #d63384; color: white; box-shadow: 0 4px 0 #a02561; }
        .open-raise-btn button { background: #2e7d32; color: white; box-shadow: 0 4px 0 #1b5e20; }
        .mobile-game-area { position: relative; width: 100%; height: 280px; margin: 0 auto; background: radial-gradient(ellipse at center, #2e7d32 0%, #1b5e20 100%); border: 8px solid #4a1c1c; border-radius: 120px; margin-bottom: 15px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5); }
        .m-table-info { position: absolute; top: 15%; width: 100%; text-align: center; }
        .m-info-spot { font-size: 16px; font-weight: 800; color: rgba(255,255,255,0.3); line-height: 1.1; padding: 0 20px; }
        .m-seat { position: absolute; width: 50px; height: 50px; background: #343a40; border: 2px solid #495057; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 5; }
        .m-seat-label { font-size: 10px; font-weight: bold; color: #adb5bd; margin-bottom: 1px; }
        .m-seat-amount { font-size: 11px; font-weight: 800; color: #fff; }
        .m-seat.hero { background: #007bff; border-color: #0056b3; box-shadow: 0 0 10px rgba(0,123,255,0.6); }
        .m-seat.villain { background: #dc3545; border-color: #a71d2a; box-shadow: 0 0 10px rgba(220,53,69,0.6); }
        .m-pos-btn { top: 82%; left: 50%; transform: translate(-50%, -50%); }
        .m-pos-sb { top: 72%; left: 22%; transform: translate(-50%, -50%); }
        .m-pos-bb { top: 50%; left: 12%; transform: translate(-50%, -50%); }
        .m-pos-utg { top: 22%; left: 25%; transform: translate(-50%, -50%); }
        .m-pos-mp { top: 18%; left: 50%; transform: translate(-50%, -50%); }
        .m-pos-co { top: 25%; left: 78%; transform: translate(-50%, -50%); }
        .m-cards-container { position: absolute; top: 52%; left: 50%; transform: translate(-50%, -50%); display: flex; gap: 4px; z-index: 10; }
        .m-card { width: 45px; height: 65px; background: white; border-radius: 4px; border: 1px solid #999; display: flex; justify-content: center; align-items: center; font-size: 22px; font-weight: bold; box-shadow: 0 3px 6px rgba(0,0,0,0.4); }
        .m-card.red { color: #dc3545; }
        .m-card.black { color: #212529; }
        .m-dealer-btn { position: absolute; width: 18px; height: 18px; background: white; border-radius: 50%; border: 1px solid #333; color: black; font-weight: bold; font-size: 10px; display: flex; justify-content: center; align-items: center; z-index: 6; }
        .srs-container button { height: 50px; font-size: 14px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

    ranges_db = utils.load_ranges()
    if not ranges_db: st.error("База пуста"); return

    saved_settings = utils.load_user_settings()

    with st.expander("⚙️ Фильтры", expanded=False):
        all_src = list(ranges_db.keys())
        def_src = [s for s in saved_settings.get("sources", all_src) if s in all_src]
        sel_src = st.multiselect("Источники", all_src, default=def_src, label_visibility="collapsed")
        
        all_scenarios = ["Open Raise", "BB def vs PFR", "Def vs 3bet", "SB vs BB", "SQZ", "vs SQZ", "3bet"]
        def_sc = [s for s in saved_settings.get("scenarios", all_scenarios) if s in all_scenarios]
        sel_sc = st.multiselect("Сценарии", all_scenarios, default=def_sc, label_visibility="collapsed")
        
        if sel_src != saved_settings.get("sources") or sel_sc != saved_settings.get("scenarios"):
            utils.save_user_settings({"sources": sel_src, "scenarios": sel_sc})

    pool = utils.get_filtered_pool(ranges_db, sel_src, sel_sc)
    if not pool: st.info("Нет спотов"); return

    if "srs_mode" not in st.session_state:
        st.session_state.srs_mode = False
        st.session_state.hand = None
        st.session_state.spot_key = None
        st.session_state.last_error = False
        st.session_state.msg = ""

    def get_next():
        srs = utils.load_srs_data()
        w_pool = []
        for pk in pool:
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
    r_call = ranges.get("call", ranges.get("Call", ""))
    r_raise = ranges.get("4bet", ranges.get("3bet", ranges.get("Raise", "")))
    w_call = utils.get_weight(st.session_state.hand, r_call)
    w_raise = utils.get_weight(st.session_state.hand, r_raise)

    if w_raise > 0 and w_call > 0: correct_act = "MIX"
    elif w_raise > 0: correct_act = "RAISE"
    elif w_call > 0: correct_act = "CALL"
    else: correct_act = "FOLD"

    hero = data.get("hero", "BTN")
    villain = data.get("villain", "")
    dealer = data.get("dealer", "BTN")
    hero_bet = data.get("hero_bet", "")
    villain_bet = data.get("villain_bet", "")

    pos_map = {"BTN": "m-pos-btn", "SB": "m-pos-sb", "BB": "m-pos-bb", "UTG": "m-pos-utg", "MP": "m-pos-mp", "CO": "m-pos-co"}
    dealer_coords = {"BTN": (80, 50), "SB": (68, 28), "BB": (45, 18), "UTG": (28, 30), "MP": (50, 24), "CO": (78, 28)}
    dc = dealer_coords.get(dealer, (80, 50))

    h_val = st.session_state.hand
    c1, c2 = h_val[0], h_val[1]
    suit = h_val[2] if len(h_val) > 2 else ""
    if suit == 's': c1_s, c2_s = '♠', '♠'; c1_c, c2_c = 'black', 'black'
    elif suit == 'o': c1_s, c2_s = '♠', '♥'; c1_c, c2_c = 'black', 'red'
    else: c1_s, c2_s = '♠', '♠'; c1_c, c2_c = 'black', 'black'

    html = f"""
    <div class="mobile-game-area">
        <div class="m-table-info"><div class="m-info-spot">{sp}</div></div>
        <div class="m-dealer-btn" style="top:{dc[0]}%; left:{dc[1]}%;">D</div>
    """
    for p, css in pos_map.items():
        if p == hero: html += f'<div class="m-seat hero {css}"><div class="m-seat-label">{p}</div><div class="m-seat-amount">{hero_bet}</div></div>'
        elif p == villain: html += f'<div class="m-seat villain {css}"><div class="m-seat-label">{p}</div><div class="m-seat-amount">{villain_bet}</div></div>'
        else: html += f'<div class="m-seat {css}"><div class="m-seat-label">{p}</div></div>'
        
    html += f"""
        <div class="m-cards-container">
            <div class="m-card {c1_c}">{c1}{c1_s}</div>
            <div class="m-card {c2_c}">{c2}{c2_s}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    if not st.session_state.srs_mode:
        st.markdown('<div class="mobile-controls">', unsafe_allow_html=True)
        is_or = "open raise" in sc.lower()
        if is_or:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="fold-btn">', unsafe_allow_html=True)
                if st.button("FOLD", use_container_width=True):
                    corr = (correct_act == "FOLD")
                    st.session_state.last_error = not corr; st.session_state.msg = "✅ ВЕРНО" if corr else f"❌ Надо: {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="open-raise-btn">', unsafe_allow_html=True)
                if st.button("RAISE", use_container_width=True):
                    corr = (correct_act in ["RAISE", "MIX"])
                    st.session_state.last_error = not corr; st.session_state.msg = "✅ ВЕРНО" if corr else f"❌ Надо: {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('<script>parent.document.querySelectorAll("div[data-testid=\'column\'] button")[1].classList.add("open-raise-btn");</script>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="fold-btn">', unsafe_allow_html=True)
                if st.button("FOLD", use_container_width=True):
                    corr = (correct_act == "FOLD")
                    st.session_state.last_error = not corr; st.session_state.msg = "✅ ВЕРНО" if corr else f"❌ Надо: {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="call-btn">', unsafe_allow_html=True)
                if st.button("CALL", use_container_width=True):
                    corr = (correct_act in ["CALL", "MIX"])
                    st.session_state.last_error = not corr; st.session_state.msg = "✅ ВЕРНО" if corr else f"❌ Надо: {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c3:
                st.markdown('<div class="raise-btn">', unsafe_allow_html=True)
                if st.button("RAISE", use_container_width=True):
                    corr = (correct_act in ["RAISE", "MIX"])
                    st.session_state.last_error = not corr; st.session_state.msg = "✅ ВЕРНО" if corr else f"❌ Надо: {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.srs_mode:
        if st.session_state.last_error:
            st.error(st.session_state.msg)
            with st.expander(f"Show Range ({correct_act})", expanded=True):
                st.markdown(utils.render_range_matrix(data, st.session_state.hand), unsafe_allow_html=True)
        else:
            st.success(st.session_state.msg)
            with st.expander(f"🔍 View Range ({correct_act})", expanded=False):
                st.markdown(utils.render_range_matrix(data, st.session_state.hand), unsafe_allow_html=True)
        
        st.markdown('<div class="mobile-controls srs-container">', unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        k = f"{src}_{sc}_{sp}".replace(" ","_")
        if s1.button("HARD", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'hard'); st.session_state.hand = None; st.session_state.srs_mode = False; st.rerun()
        if s2.button("NORM", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'normal'); st.session_state.hand = None; st.session_state.srs_mode = False; st.rerun()
        if s3.button("EASY", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'easy'); st.session_state.hand = None; st.session_state.srs_mode = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

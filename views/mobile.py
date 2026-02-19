import streamlit as st
import random
from datetime import datetime
import utils

def show():
    # --- CSS ---
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
        .mobile-game-area { position: relative; width: 100%; height: 280px; margin: 0 auto; background: radial-gradient(ellipse at center, #1b5e20 0%, #0a2e0b 100%); border: 6px solid #3e2723; border-radius: 140px; box-shadow: 0 4px 15px rgba(0,0,0,0.8); }
        .mob-info { position: absolute; top: 25%; width: 100%; text-align: center; pointer-events: none; }
        .mob-info-src { font-size: 10px; color: #888; text-transform: uppercase; }
        .mob-info-spot { font-size: 22px; font-weight: 900; color: rgba(255,255,255,0.15); }
        .seat { position: absolute; width: 44px; height: 44px; background: #222; border: 1px solid #444; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 5; }
        .seat-label { font-size: 9px; color: #fff; font-weight: bold; margin-top: auto; margin-bottom: 2px; }
        .seat-active { border-color: #ffc107; background: #2a2a2a; }
        .seat-folded { opacity: 0.4; border-color: #333; }
        .m-pos-1 { bottom: 20%; left: 5%; } .m-pos-2 { top: 20%; left: 5%; } .m-pos-3 { top: -15px; left: 50%; transform: translateX(-50%); } 
        .m-pos-4 { top: 20%; right: 5%; } .m-pos-5 { bottom: 20%; right: 5%; }
        .chip-container { position: absolute; z-index: 10; display: flex; flex-direction: column; align-items: center; pointer-events: none; }
        .chip-mob { width: 14px; height: 14px; background: #111; border: 2px dashed #d32f2f; border-radius: 50%; box-shadow: 1px 1px 2px rgba(0,0,0,0.8); }
        .chip-3bet { width: 16px; height: 16px; background: #d32f2f; border: 2px solid #fff; border-radius: 50%; box-shadow: 0 2px 5px rgba(0,0,0,0.8); }
        .dealer-mob { width: 16px; height: 16px; background: #ffc107; border-radius: 50%; color: #000; font-weight: bold; font-size: 9px; display: flex; justify-content: center; align-items: center; border: 1px solid #bfa006; position: absolute; z-index: 11; }
        .bet-txt { font-size: 10px; font-weight: bold; color: #fff; text-shadow: 1px 1px 2px #000; background: rgba(0,0,0,0.6); padding: 1px 3px; border-radius: 4px; margin-top: -5px; z-index: 20; }
        .hero-mob { position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%); display: flex; gap: 5px; z-index: 20; background: #222; padding: 5px 10px; border-radius: 12px; border: 1px solid #ffc107; }
        .card-mob { width: 45px; height: 64px; background: white; border-radius: 4px; position: relative; color: black; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
        .tl-mob { position: absolute; top: 1px; left: 3px; font-weight: bold; font-size: 14px; line-height: 1; }
        .c-mob { position: absolute; top: 55%; left: 50%; transform: translate(-50%,-50%); font-size: 26px; }
        .suit-red { color: #d32f2f; } .suit-blue { color: #0056b3; } .suit-black { color: #111; }
        .rng-badge { position: absolute; bottom: 50px; right: -15px; width: 30px; height: 30px; background: #6f42c1; border: 2px solid #fff; border-radius: 50%; color: white; font-weight: bold; font-size: 12px; display: flex; justify-content: center; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.5); z-index: 40; }
        .rng-hint { text-align: center; color: #888; font-size: 11px; margin-bottom: 5px; font-family: monospace; }
        .srs-container button { height: 50px; font-size: 13px; background: #343a40; color: #aaa; border: 1px solid #555; }
    </style>
    """, unsafe_allow_html=True)

    ranges_db = utils.load_ranges()
    if not ranges_db: st.error("База ренджей пуста. Проверь папку spots_data."); return

    with st.expander("⚙️ Settings", expanded=False):
        saved = utils.load_user_settings()
        sel_src = st.multiselect("Source", list(ranges_db.keys()), default=saved.get("sources", [list(ranges_db.keys())[0]]))
        
        avail_sc = set()
        for s in sel_src: avail_sc.update(ranges_db[s].keys())
        avail_sc = sorted(list(avail_sc))
        
        sel_sc = st.multiselect("Scenario", avail_sc, default=saved.get("scenarios", [avail_sc[0]] if avail_sc else []))
        
        if st.button("🚀 Apply"):
            utils.save_user_settings({"sources": sel_src, "scenarios": sel_sc})
            st.session_state.hand = None; st.rerun()

    pool = utils.get_filtered_pool(ranges_db, sel_src, sel_sc)
    if not pool:
        st.warning("⚠️ Нет раздач для выбранных фильтров.")
        st.stop()

    if 'hand' not in st.session_state: st.session_state.hand = None
    if 'rng' not in st.session_state: st.session_state.rng = 0
    if 'suits' not in st.session_state: st.session_state.suits = None
    if 'srs_mode' not in st.session_state: st.session_state.srs_mode = False
    if 'last_error' not in st.session_state: st.session_state.last_error = False
    if 'msg' not in st.session_state: st.session_state.msg = None
    if 'current_spot_key' not in st.session_state: st.session_state.current_spot_key = None 

    if st.session_state.hand is None or st.session_state.current_spot_key is None:
        chosen = random.choice(pool)
        st.session_state.current_spot_key = chosen
        src, sc, sp = chosen.split('|')
        data = ranges_db[src][sc][sp]
        ranges_data = data.get("ranges", {})
        t_range = ranges_data.get("training", ranges_data.get("source", ranges_data.get("full", "")))
        poss = utils.parse_range_to_list(t_range)
        srs = utils.load_srs_data()
        w = [srs.get(f"{src}_{sc}_{sp}_{h}".replace(" ","_"), 100) for h in poss]
        st.session_state.hand = random.choices(poss, weights=w, k=1)[0]
        st.session_state.rng = random.randint(0, 99)
        ps = ['♠','♥','♦','♣']; s1 = random.choice(ps)
        st.session_state.suits = [s1, s1 if 's' in st.session_state.hand else random.choice([x for x in ps if x!=s1])]
        st.session_state.srs_mode = False

    src, sc, sp = st.session_state.current_spot_key.split('|')
    data = ranges_db[src][sc][sp]
    setup = data.get("setup", {})
    ranges_data = data.get("ranges", {})
    
    hero_pos = setup.get("hero_pos", "EP")
    villain_pos = setup.get("villain_pos")
    btn_pos = setup.get("btn_pos", "BTN")
    hero_bet = setup.get("hero_bet")
    villain_bet = setup.get("villain_bet")
    
    is_defense = villain_pos is not None
    
    rng = st.session_state.rng
    correct_act = "FOLD"
    
    if is_defense:
        w_c = utils.get_weight(st.session_state.hand, ranges_data.get("call", ""))
        w_raise = utils.get_weight(st.session_state.hand, ranges_data.get("4bet", ranges_data.get("3bet", "")))
        
        if rng < w_raise: correct_act = "RAISE"
        elif rng < (w_raise + w_c): correct_act = "CALL"
    else:
        w = utils.get_weight(st.session_state.hand, ranges_data.get("full", ""))
        if w > 0: correct_act = "RAISE"

    h_val = st.session_state.hand; s1, s2 = st.session_state.suits
    c1 = "suit-red" if s1 in '♥' else "suit-blue" if s1 in '♦' else "suit-black"
    c2 = "suit-red" if s2 in '♥' else "suit-blue" if s2 in '♦' else "suit-black"

    order = ["EP", "MP", "CO", "BTN", "SB", "BB"]
    try:
        hero_idx = order.index(hero_pos)
    except ValueError:
        hero_idx = 0
        
    rot = order[hero_idx:] + order[:hero_idx]

    opp_html = ""; chips_html = ""
    def get_pos_style(idx):
        return {0: "bottom:28%;left:47%;", 1: "bottom:28%;left:22%;", 2: "top:28%;left:22%;", 
                3: "top:12%;left:47%;", 4: "top:28%;right:22%;", 5: "bottom:28%;right:22%;"}.get(idx, "")
    def get_btn_style(idx):
        return {0: "bottom:25%;left:55%;", 1: "bottom:25%;left:18%;", 2: "top:25%;left:18%;", 
                3: "top:10%;left:55%;", 4: "top:25%;right:18%;", 5: "bottom:25%;right:18%;"}.get(idx, "")

    for i in range(1, 6):
        p = rot[i]
        is_act = (p == villain_pos)
        cls = "seat-active" if is_act else "seat-folded"
        cards = '<div class="opp-cards-mob"></div>' if is_act else ""
        opp_html += f'<div class="seat m-pos-{i} {cls}">{cards}<span class="seat-label">{p}</span></div>'
        s = get_pos_style(i)
        
        if is_act and villain_bet:
            bet_txt = f'<div class="bet-txt">{villain_bet}bb</div>'
            chips_html += f'<div class="chip-container" style="{s}"><div class="chip-3bet"></div><div class="chip-3bet" style="margin-top:-12px;"></div>{bet_txt}</div>'
        elif p in ["SB", "BB"] and not is_act:
            chips_html += f'<div class="chip-container" style="{s}"><div class="chip-mob"></div></div>'
            
        if p == btn_pos:
            bs = get_btn_style(i)
            chips_html += f'<div class="dealer-mob" style="{bs}">D</div>'

    hs = get_pos_style(0)
    if hero_bet: 
        bet_txt = f'<div class="bet-txt">{hero_bet}bb</div>'
        chips_html += f'<div class="chip-container" style="{hs}"><div class="chip-mob"></div><div class="chip-mob" style="margin-top:-5px;"></div>{bet_txt}</div>'
        
    if rot[0] == btn_pos:
        bs = get_btn_style(0)
        chips_html += f'<div class="dealer-mob" style="{bs}">D</div>'

    html = f"""
    <div class="mobile-game-area">
        <div class="mob-info"><div class="mob-info-src">{sc}</div><div class="mob-info-spot">{sp}</div></div>
        {opp_html} {chips_html}
        <div class="hero-mob">
            <div class="card-mob"><div class="tl-mob {c1}">{h_val[0]}<br>{s1}</div><div class="c-mob {c1}">{s1}</div></div>
            <div class="card-mob"><div class="tl-mob {c2}">{h_val[1]}<br>{s2}</div><div class="c-mob {c2}">{s2}</div></div>
            <div class="rng-badge">{rng}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    if is_defense:
        st.markdown('<div class="rng-hint">📉 0..Freq → Action | 📈 Freq..100 → Fold</div>', unsafe_allow_html=True)

    st.markdown('<div class="mobile-controls">', unsafe_allow_html=True)
    if not st.session_state.srs_mode:
        if is_defense:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("FOLD", key="f", use_container_width=True):
                    corr = (correct_act == "FOLD")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('<script>parent.document.querySelectorAll("div[data-testid=\'column\'] button")[0].classList.add("fold-btn");</script>', unsafe_allow_html=True)
            with c2:
                if st.button("CALL", key="c", use_container_width=True):
                    corr = (correct_act == "CALL")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('<script>parent.document.querySelectorAll("div[data-testid=\'column\'] button")[1].classList.add("call-btn");</script>', unsafe_allow_html=True)
            with c3:
                if st.button("RAISE", key="r", use_container_width=True):
                    corr = (correct_act == "RAISE")
                    st.session_state.last_error = not corr
                    st.session_state.msg = f"✅ Correct" if corr else f"❌ Err! RNG {rng} -> {correct_act}"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('<script>parent.document.querySelectorAll("div[data-testid=\'column\'] button")[2].classList.add("raise-btn");</script>', unsafe_allow_html=True)
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("FOLD", key="f", use_container_width=True):
                    corr = (correct_act == "FOLD")
                    st.session_state.last_error = not corr
                    st.session_state.msg = "✅ Correct" if corr else "❌ Err"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('<script>parent.document.querySelectorAll("div[data-testid=\'column\'] button")[0].classList.add("fold-btn");</script>', unsafe_allow_html=True)
            with c2:
                if st.button("RAISE", key="r", use_container_width=True):
                    corr = (correct_act == "RAISE")
                    st.session_state.last_error = not corr
                    st.session_state.msg = "✅ Correct" if corr else "❌ Err"
                    utils.save_to_history({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Spot": sp, "Hand": f"{h_val}", "Result": int(corr), "CorrectAction": correct_act})
                    st.session_state.srs_mode = True; st.rerun()
                st.markdown('<script>parent.document.querySelectorAll("div[data-testid=\'column\'] button")[1].classList.add("open-raise-btn");</script>', unsafe_allow_html=True)
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
        if s1.button("HARD", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'hard'); st.session_state.hand = None; st.rerun()
        if s2.button("NORM", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'normal'); st.session_state.hand = None; st.rerun()
        if s3.button("EASY", use_container_width=True): utils.update_srs_smart(k, st.session_state.hand, 'easy'); st.session_state.hand = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

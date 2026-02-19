import streamlit as st
import utils

def render_popover_selector(ranges_db, suffix, emoji):
    k_sc = f"sc_{suffix}"
    k_sp = f"sp_{suffix}"

    sc_map = {}
    for src, sc_dict in ranges_db.items():
        for sc, sp_dict in sc_dict.items():
            if sc not in sc_map: sc_map[sc] = []
            for sp in sp_dict.keys():
                sc_map[sc].append((sp, src)) 

    curr_sc = st.session_state.get(k_sc)
    curr_sp = st.session_state.get(k_sp)

    if curr_sp and curr_sc:
        short_sc = curr_sc.replace("Def vs 3bet", "Def3B").replace("Open Raise", "OR")
        display_text = f"<div style='font-weight:bold;font-size:14px;color:#ffc107;margin-bottom:5px;'>{emoji} {short_sc}</div><div style='font-size:12px;color:#ccc;'>{curr_sp}</div>"
    else:
        display_text = f"<div style='color:#888;font-style:italic;'>{emoji} Нажми кнопку ниже...</div>"

    st.markdown(display_text, unsafe_allow_html=True)

    with st.popover("⚙️ Настроить", use_container_width=True):
        opts_sc = sorted(list(sc_map.keys()))
        idx_sc = opts_sc.index(curr_sc) if curr_sc in opts_sc else 0
        sc = st.selectbox("Сценарий", opts_sc, key=k_sc, index=idx_sc) if opts_sc else None
        
        opts_sp = [x[0] for x in sc_map[sc]] if sc else []
        idx_sp = opts_sp.index(curr_sp) if curr_sp in opts_sp else 0
        sp = st.selectbox("Спот", opts_sp, key=k_sp, index=idx_sp) if opts_sp else None

    if sc and sp:
        src = next((x[1] for x in sc_map[sc] if x[0] == sp), None)
        return ranges_db[src][sc][sp]
    return None

def show():
    st.markdown("""
        <style>
            .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }
            [data-testid="column"] { margin-bottom: 1rem; }
            .matrix-box { border: 1px solid #333; border-radius: 8px; padding: 5px; background: #1e1e1e; margin-top: 5px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🔬 Range Lab")

    ranges_db = utils.load_ranges()
    if not ranges_db: st.error("База ренджей пуста."); return

    col1, col2 = st.columns(2)

    with col1:
        data_a = render_popover_selector(ranges_db, "A", "🅰️")
        if data_a:
            st.markdown('<div class="matrix-box">', unsafe_allow_html=True)
            st.markdown(utils.render_range_matrix(data_a), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        data_b = render_popover_selector(ranges_db, "B", "🅱️")
        if data_b:
            st.markdown('<div class="matrix-box">', unsafe_allow_html=True)
            st.markdown(utils.render_range_matrix(data_b), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

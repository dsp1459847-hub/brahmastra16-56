import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="MAYA AI - Result Freezer Engine", layout="wide")

st.title("MAYA AI 🦅: Result Freezer Sniper Engine ⚡")
st.markdown("Aapke logic par aadharit: **Result Screenshot Mode!** Ek baar shift calculate hone ke baad uska result 'Freeze' ho jayega. Processor free rahega aur speed super-fast!")

# --- RESULT MEMORY (DIARY) INITIALIZATION ---
if 'results_cache' not in st.session_state:
    st.session_state.results_cache = {}

# Reset memory if Date or File changes
def reset_memory():
    st.session_state.results_cache = {}

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'], on_change=reset_memory)
selected_end_date = st.sidebar.date_input("Calculation Date (T)", on_change=reset_memory)
max_limit = st.sidebar.slider("Elimination Limit", 2, 5, 4)

if st.sidebar.button("Clear All Results & Re-Run"):
    reset_memory()
    st.rerun()

shift_order = ["DB", "SG", "FD", "GD", "ZA", "GL", "DS"]

@st.cache_data
def load_data(file_val):
    if file_val.name.endswith('.csv'): df = pd.read_csv(file_val)
    else: df = pd.read_excel(file_val)
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df = df.sort_values(by='DATE').reset_index(drop=True)
    for col in shift_order:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)
        filtered_df = df[df['DATE'].dt.date <= selected_end_date].copy()
        if len(filtered_df) == 0: st.stop()
        
        target_date_next = selected_end_date + timedelta(days=1)
        st.info(f"📅 **Data Read Up To:** {selected_end_date.strftime('%d %B %Y')} | 🎯 **Target Date:** {target_date_next.strftime('%A, %d %B %Y')}")

        # --- CORE FUNCTIONS (CACHED) ---
        @st.cache_data
        def get_all_tiers_cached(past_tuple):
            scores = {n: 0 for n in range(100)}
            for days in range(1, min(46, len(past_tuple) + 1)):
                sheet = past_tuple[-days:]
                for num, freq in Counter(sheet).items(): scores[num] += freq * (1 + (1/days)) 
            ranked = sorted(range(100), key=lambda x: scores[x], reverse=True)
            return {'H': ranked[0:33], 'M': ranked[33:66], 'L': ranked[66:100]}

        def get_tier_name(num, tiers_dict):
            if num in tiers_dict['H']: return 'H'
            elif num in tiers_dict['M']: return 'M'
            elif num in tiers_dict['L']: return 'L'
            return 'FAIL'

        @st.cache_data
        def get_best_main_timeframe_fast(history_tuple):
            h_list = list(history_tuple)
            if len(h_list) < 30: return 15
            tf_scores = {}
            for tf in range(1, 46):
                succ = 0
                for i in range(len(h_list)-15, len(h_list)-1):
                    pat = h_list[:i][-tf:]
                    nxt = [h_list[:i][k+tf] for k in range(len(h_list[:i])-tf) if h_list[:i][k:k+tf] == pat]
                    if nxt:
                        top = Counter(nxt).most_common(1)[0][0]
                        td = get_all_tiers_cached(tuple(h_list[:i]))
                        if get_tier_name(top, td) == get_tier_name(h_list[i], td): succ += 1
                tf_scores[tf] = succ
            return max(tf_scores, key=tf_scores.get) if tf_scores else 15

        @st.cache_data
        def get_sniper_timeframe_smart(history_tuple, dates_tuple):
            h_list = list(history_tuple)
            d_list = list(dates_tuple)
            valid_tfs = []
            
            for tf in range(1, 46):
                def check_hit(day_idx):
                    pat = h_list[:day_idx][-tf:]
                    nxt = [h_list[:day_idx][k+tf] for k in range(len(h_list[:day_idx])-tf) if h_list[:day_idx][k:k+tf] == pat]
                    if not nxt: return False
                    top = Counter(nxt).most_common(1)[0][0]
                    td = get_all_tiers_cached(tuple(h_list[:day_idx]))
                    return get_tier_name(top, td) == get_tier_name(h_list[day_idx], td)

                if not check_hit(len(h_list)-1): continue 
                if check_hit(len(h_list)-2): continue     

                fail_streak = 1
                for b in range(3, 25):
                    idx = len(h_list) - b
                    if idx < 15 or check_hit(idx): break
                    fail_streak += 1
                
                hit_history = [check_hit(i) for i in range(15, len(h_list))]
                jan_apr = 0
                for i in range(1, len(hit_history)):
                    if hit_history[i] and hit_history[i-1] and (1 <= d_list[i+15].month <= 4): jan_apr += 1

                max_fail = 0
                cur_f = 0
                for h in hit_history:
                    if not h: cur_f += 1
                    else: max_fail = max(max_fail, cur_f); cur_f = 0

                valid_tfs.append({'tf': tf, 'streak': fail_streak, 'score': jan_apr, 'max_f': max_fail})

            if not valid_tfs: return 15, "No Match", 0, 0, 99
            best = sorted(valid_tfs, key=lambda x: (x['max_f'], -x['score']))[0]
            return best['tf'], "SNIPER FILTER", best['streak'], best['score'], best['max_f']

        # --- PROCESS ALL SHIFTS ---
        for shift in shift_order:
            if shift not in df.columns: continue
            
            st.markdown("---")
            
            # 🚀 STEP-BY-STEP CALCULATION WITH SCREENSHOT CACHE
            if shift not in st.session_state.results_cache:
                with st.spinner(f"Searching {shift}... Sniper Filter processing!"):
                    s_data = filtered_df[['DATE', shift]].dropna()
                    hist = s_data[shift].astype(int).tolist()
                    d_list = s_data['DATE'].tolist()
                    
                    if len(hist) < 60: continue
                    
                    # Logic: Streak Checker
                    streak = 0
                    for j in range(len(hist)-1, len(hist)-10, -1):
                        tf = get_best_main_timeframe(tuple(hist[:j]))
                        nxt = [hist[:j][k+tf] for k in range(len(hist[:j])-tf) if hist[:j][k:k+tf] == hist[:j][-tf:]]
                        if nxt and get_tier_name(Counter(nxt).most_common(1)[0][0], get_all_tiers_cached(tuple(hist[:j]))) == get_tier_name(hist[j], get_all_tiers_cached(tuple(hist[:j]))):
                            break
                        streak += 1

                    if streak == 0:
                        tf = get_best_main_timeframe(tuple(hist)); logic = "MAIN ENGINE (Pass)"
                        res_vals = (tf, logic, 0, 0, 0)
                    elif streak == 1:
                        tf = get_best_main_timeframe(tuple(hist[:-1])); logic = "MAIN ENGINE (Retry)"
                        res_vals = (tf, logic, 0, 0, 0)
                    else:
                        res_vals = get_sniper_timeframe_smart(tuple(hist), tuple(d_list))
                    
                    # Store everything in "Screenshot"
                    tf_final = res_vals[0]
                    tiers = get_all_tiers_cached(tuple(hist))
                    nxt = [hist[i+tf_final] for i in range(len(hist)-tf_final) if hist[i:i+tf_final] == hist[-tf_final:]]
                    tier_best = get_tier_name(Counter(nxt).most_common(1)[0][0], tiers) if nxt else 'H'
                    
                    # Trap & Final Nums
                    traps = set([(hist[-1]+1)%100, (hist[-1]-1)%100, int(str(hist[-1]).zfill(2)[::-1])])
                    green_nums = [n for n in tiers[tier_best] if n not in traps]
                    
                    # Save to Cache
                    st.session_state.results_cache[shift] = {
                        'logic': res_vals[1], 'tf': tf_final, 'streak': res_vals[2], 
                        'score': res_vals[3], 'max_f': res_vals[4], 'tier': tier_best,
                        'nums': green_nums, 'cur_streak': streak
                    }

            # --- DISPLAY FROM "SCREENSHOT" (No Calculation) ---
            res = st.session_state.results_cache[shift]
            st.subheader(f"🧩 Shift: {shift}")
            
            c1, c2 = st.columns([1, 2.5])
            with c1:
                st.markdown(f"<div style='background:#555; padding:15px; border-radius:10px; text-align:center; color:white;'>"
                            f"Shift: {shift}<br><b>State: {res['cur_streak']} Fail</b></div>", unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"<div style='border:2px solid #00FF7F; padding:10px; border-radius:10px; background:#00FF7F15;'>"
                            f"<b>Logic:</b> {res['logic']} | <b>Gear:</b> {res['tf']}-TF<br>"
                            f"<i>📌 Streak: {res['streak']} | Jan-Apr: {res['score']} | Max Fail: {res['max_f']}</i></div>", unsafe_allow_html=True)

            # Display Numbers
            nums_html = "<div style='display:flex; flex-wrap:wrap; gap:5px; margin-top:10px;'>"
            for n in res['nums']:
                nums_html += f"<div style='background:#00FF7F; padding:8px; border-radius:5px; color:black; font-weight:bold;'>{n:02d}</div>"
            nums_html += "</div>"
            st.markdown(nums_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
                      

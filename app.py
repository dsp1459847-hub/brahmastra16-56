import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="MAYA AI - Master Engine", layout="wide")

st.title("MAYA AI 🦅: The Master Sniper Engine ⚡")
st.markdown("Aapki saari conditions ek sath: **1. Result Freezer (No Hang), 2. Pahada Trap Blocked, 3. Kal Pass/Parso Fail, 4. Min Max-Fail, 5. Jan-Apr Score!**")

# ==========================================
# 🛑 OPERATOR TRAP TIMEFRAMES (BLACKLIST)
# ==========================================
TRAP_TIMEFRAMES = {
    3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 21, 24, 25, 
    27, 28, 30, 32, 33, 35, 36, 39, 40, 42, 45
}

# --- RESULT MEMORY (DIARY) INITIALIZATION ---
if 'results_cache' not in st.session_state:
    st.session_state.results_cache = {}

def reset_memory():
    st.session_state.results_cache = {}

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'], on_change=reset_memory)
selected_end_date = st.sidebar.date_input("Calculation Date (T)", on_change=reset_memory)

if st.sidebar.button("Clear Memory & Re-Run"):
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

        # --- CORE CACHED FUNCTIONS ---
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
            if len(h_list) < 30: return 13
            tf_scores = {}
            for tf in range(1, 46):
                if tf in TRAP_TIMEFRAMES: continue # Trap Hatao
                
                succ = 0
                for i in range(len(h_list)-15, len(h_list)-1):
                    pat = h_list[:i][-tf:]
                    nxt = [h_list[:i][k+tf] for k in range(len(h_list[:i])-tf) if h_list[:i][k:k+tf] == pat]
                    if nxt:
                        top = Counter(nxt).most_common(1)[0][0]
                        td = get_all_tiers_cached(tuple(h_list[:i]))
                        if get_tier_name(top, td) == get_tier_name(h_list[i], td): succ += 1
                tf_scores[tf] = succ
            return max(tf_scores, key=tf_scores.get) if tf_scores else 13

        @st.cache_data
        def get_sniper_timeframe_smart(history_tuple, dates_tuple):
            h_list = list(history_tuple)
            d_list = list(dates_tuple)
            valid_tfs = []
            
            for tf in range(1, 46):
                if tf in TRAP_TIMEFRAMES: continue # Trap Hatao
                
                def check_hit(day_idx):
                    pat = h_list[:day_idx][-tf:]
                    nxt = [h_list[:day_idx][k+tf] for k in range(len(h_list[:day_idx])-tf) if h_list[:day_idx][k:k+tf] == pat]
                    if not nxt: return False
                    top = Counter(nxt).most_common(1)[0][0]
                    td = get_all_tiers_cached(tuple(h_list[:day_idx]))
                    return get_tier_name(top, td) == get_tier_name(h_list[day_idx], td)

                # Condition 1 & 2: Kal Pass aur Parso Fail
                if not check_hit(len(h_list)-1): continue 
                if check_hit(len(h_list)-2): continue     

                fail_streak = 1
                for b in range(3, 25):
                    idx = len(h_list) - b
                    if idx < 15 or check_hit(idx): break
                    fail_streak += 1
                
                # Condition 3: No Double Big Fall
                if fail_streak >= 3:
                    idx_after_fall = len(h_list) - 1 - fail_streak - 1
                    prev_fail_count = 0
                    if idx_after_fall >= 15:
                        for b_day in range(idx_after_fall, 14, -1):
                            if not check_hit(b_day): prev_fail_count += 1
                            else: break
                    if prev_fail_count >= 3: continue 

                # History Scan
                hit_history = [check_hit(i) for i in range(15, len(h_list))]
                
                # Condition 4: Jan-Apr Score
                jan_apr = 0
                for i in range(1, len(hit_history)):
                    if hit_history[i] and hit_history[i-1] and (1 <= d_list[i+15].month <= 4): jan_apr += 1

                # Condition 5: Minimum Historical Max-Fail
                max_fail = 0
                cur_f = 0
                for h in hit_history:
                    if not h: 
                        cur_f += 1
                        if cur_f > max_fail: max_fail = cur_f
                    else: cur_f = 0

                valid_tfs.append({'tf': tf, 'streak': fail_streak, 'score': jan_apr, 'max_f': max_fail})

            if not valid_tfs: return 13, "Safe Trap-Free Default", 0, 0, 99
            
            # SORTING: Lowest Max Fail First!
            best = sorted(valid_tfs, key=lambda x: (x['max_f'], -x['score']))[0]
            return best['tf'], "MASTER SNIPER FILTER", best['streak'], best['score'], best['max_f']

        # --- PROCESS ALL SHIFTS ---
        for shift in shift_order:
            if shift not in df.columns: continue
            
            st.markdown("---")
            
            # 🚀 RESULT FREEZER LOGIC (Screenshot Mode)
            if shift not in st.session_state.results_cache:
                with st.spinner(f"Searching {shift}... Sabhi 5 conditions lag rahi hain!"):
                    s_data = filtered_df[['DATE', shift]].dropna()
                    hist = s_data[shift].astype(int).tolist()
                    d_list = s_data['DATE'].tolist()
                    
                    if len(hist) < 60: continue
                    
                    # 1. Check Current Streak
                    streak = 0
                    for j in range(len(hist)-1, max(20, len(hist)-20), -1):
                        tf = get_best_main_timeframe_fast(tuple(hist[:j]))
                        nxt = [hist[:j][k+tf] for k in range(len(hist[:j])-tf) if hist[:j][k:k+tf] == hist[:j][-tf:]]
                        if nxt and get_tier_name(Counter(nxt).most_common(1)[0][0], get_all_tiers_cached(tuple(hist[:j]))) == get_tier_name(hist[j], get_all_tiers_cached(tuple(hist[:j]))):
                            break
                        streak += 1

                    # 2. Apply Logic based on Streak
                    if streak == 0:
                        tf_final = get_best_main_timeframe_fast(tuple(hist))
                        res_vals = (tf_final, "MAIN ENGINE (Continuous Pass)", 0, 0, 0)
                    elif streak == 1:
                        tf_final = get_best_main_timeframe_fast(tuple(hist[:-1]))
                        res_vals = (tf_final, "MAIN ENGINE (Usi Timeframe par Dobara Retry)", 0, 0, 0)
                    else:
                        res_vals = get_sniper_timeframe_smart(tuple(hist), tuple(d_list))
                    
                    tf_final = res_vals[0]
                    
                    # 3. Final Predictions
                    tiers = get_all_tiers_cached(tuple(hist))
                    nxt = [hist[i+tf_final] for i in range(len(hist)-tf_final) if hist[i:i+tf_final] == hist[-tf_final:]]
                    tier_best = get_tier_name(Counter(nxt).most_common(1)[0][0], tiers) if nxt else 'H'
                    
                    # Trap Checking
                    last_n = hist[-1]
                    prev_n = hist[-2]
                    traps = set([(last_n+1)%100, (last_n-1)%100, int(str(last_n).zfill(2)[::-1]), (last_n + (last_n - prev_n))%100])
                    for n, count in Counter(hist[-5:]).items():
                        if count >= 2: traps.add(n)
                        
                    green_nums = [n for n in tiers[tier_best] if n not in traps]
                    
                    # 4. SAVE TO SCREENSHOT DIARY
                    st.session_state.results_cache[shift] = {
                        'logic': res_vals[1], 'tf': tf_final, 'streak_before': res_vals[2], 
                        'score': res_vals[3], 'max_f': res_vals[4], 'tier': tier_best,
                        'nums': green_nums, 'cur_fail_streak': streak, 'traps': list(traps),
                        'raw_tier_nums': tiers[tier_best]
                    }

            # --- DISPLAY FROM "SCREENSHOT" (No Calculation) ---
            res = st.session_state.results_cache[shift]
            
            # Date Formatting for Display
            dates_today = filtered_df[filtered_df[shift].notna()]['DATE'].tolist()
            date_kal_pass = dates_today[-1].strftime('%d %b %Y')
            
            if res['streak_before'] > 0:
                date_fail_start = dates_today[-1 - res['streak_before']].strftime('%d %b %Y')
                date_fail_end = dates_today[-2].strftime('%d %b %Y')
                if res['streak_before'] == 1:
                    d_text = f"Yeh Timeframe <b>{date_fail_end}</b> ko (1 din) fail hone ke baad, kal <b>{date_kal_pass}</b> ko PAAS hua tha!"
                else:
                    d_text = f"Yeh Timeframe <b>{date_fail_start}</b> se <b>{date_fail_end}</b> tak ({res['streak_before']} din) lagatar fail hone ke baad, kal <b>{date_kal_pass}</b> ko PAAS hua tha!"
            else:
                d_text = "Safe/Default Timeframe applied."

            # UI Banners
            st.subheader(f"🧩 Shift: {shift}")
            
            if res['cur_fail_streak'] == 0:
                st.markdown(f"<div style='background:#28a745; padding:10px; border-radius:8px; border: 2px solid #1e7e34; text-align:center; color:white; margin-bottom:10px;'>✅ <b>PICHLA DIN PAAS THA (Streak: 0 Fail)</b></div>", unsafe_allow_html=True)
            elif res['cur_fail_streak'] == 1:
                st.markdown(f"<div style='background:#ffc107; padding:10px; border-radius:8px; border: 2px solid #d39e00; text-align:center; color:black; margin-bottom:10px;'>⚠️ <b>1 DIN FAIL HUA HAI!</b> Kal wala same timeframe use hoga.</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background:#FF4B4B; padding:10px; border-radius:8px; border: 2px solid #c82333; text-align:center; color:white; margin-bottom:10px;'>🔥 <b>GEAR SHIFTED ({res['cur_fail_streak']} Din Se Fail)</b> Master Sniper lagaya gaya!</div>", unsafe_allow_html=True)

            c1, c2 = st.columns([1, 2.5])
            with c1:
                actual_row = df[df['DATE'].dt.date == target_date_next]
                actual_val = int(actual_row.iloc[0][shift]) if not actual_row.empty and pd.notna(actual_row.iloc[0][shift]) else None
                is_hit = actual_val in res['nums'] if actual_val is not None else False
                
                if actual_val is not None:
                    m_color = "#28a745" if is_hit else "#FF4B4B"
                    st.markdown(f"<div style='background:{m_color}; padding:10px; border-radius:8px; text-align:center; color:white;'>Match Result:<br><b style='font-size:26px;'>{actual_val:02d}</b><br>{'HIT! ✅' if is_hit else 'MISS ❌'}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#555; padding:10px; border-radius:8px; text-align:center; color:white;'>Result:<br><b>Waiting...</b></div>", unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"<div style='border:2px solid #00FF7F; padding:10px; border-radius:8px; background:#00FF7F15; font-size:14px;'>"
                            f"<b>Logic:</b> {res['logic']} | <b>Selected Gear:</b> <code>{res['tf']}-Din TF</code><br>")
                
                if res['cur_fail_streak'] >= 2:
                    st.markdown(f"<i>📌 {d_text}<br>❄️ Jan-Apr Score: <b>{res['score']} baar</b> direct paas.<br>🔥 <b>SABSE BADI BAAT:</b> Is timeframe ki poori history mein <b>sabse lamba fail sirf {res['max_f']} din</b> gaya hai!</i>", unsafe_allow_html=True)
                
                st.markdown(f"<hr style='margin:5px 0; border-top:1px solid #444;'>🥇 Prediction Tier: <b style='color:#00FF7F; font-size:18px;'>{res['tier']}</b></div>", unsafe_allow_html=True)

            # Display Numbers with Traps crossed out
            nums_html = "<div style='display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;'>"
            for n in sorted(res['raw_tier_nums']):
                if n in res['traps']:
                    bg = "#1a1a1a"; border = "#333"; font_c = "#555"; extra = "text-decoration: line-through;"
                else:
                    bg = "#00FF7F"; border = "#008000"; font_c = "black"; extra = ""
                nums_html += f"<div style='background:{bg}; padding:10px; border-radius:8px; text-align:center; min-width:45px; border:2px solid {border}; box-shadow: 2px 2px 5px rgba(0,0,0,0.5); {extra}'><span style='font-size:20px; font-weight:bold; color:{font_c};'>{n:02d}</span></div>"
            nums_html += "</div>"
            st.markdown(nums_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
                              

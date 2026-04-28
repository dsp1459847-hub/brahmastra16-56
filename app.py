import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="MAYA AI - Anti-Trap Cloud Engine", layout="wide")

st.title("MAYA AI 🦅: Anti-Trap Cloud Engine ⚡")
st.markdown("Aapke naye Master Logic par aadharit: **Pahade Wale Sequence Blocked! (No 3,6,9... No 5,10,15...).** Kachra timeframes ko list se hata diya gaya hai taaki sirf 'Ajeeb' aur 'Safe' timeframes par hi game kheli jaye!")

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
selected_end_date = st.sidebar.date_input("Calculation Date (T)")
max_limit = st.sidebar.slider("Elimination Limit", 2, 5, 4)

shift_order = ["DB", "SG", "FD", "GD", "ZA", "GL", "DS"]

# ==========================================
# 🛑 OPERATOR TRAP TIMEFRAMES (BLACKLIST)
# ==========================================
# Inme 3 ka pahada, 5 ka pahada, 4 ka pahada aur 10 ke aasaan sequence shamil hain
TRAP_TIMEFRAMES = {
    3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 21, 24, 25, 
    27, 28, 30, 32, 33, 35, 36, 39, 40, 42, 45
}

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
        def detect_player_load_trap(history_tuple):
            history_list = list(history_tuple)
            player_traps = []
            if len(history_list) < 2: return player_traps
            last_num = history_list[-1]
            prev_num = history_list[-2]
            player_traps.append((last_num + 1) % 100)
            player_traps.append((last_num - 1) % 100)
            player_traps.append(int(str(last_num).zfill(2)[::-1]))
            gap = last_num - prev_num
            player_traps.append((last_num + gap) % 100)
            for num, count in Counter(history_list[-5:]).items():
                if count >= 2: player_traps.append(num)
            return list(set(player_traps))

        @st.cache_data
        def get_best_main_timeframe(history_tuple, max_lookback=45):
            history_list = list(history_tuple)
            if len(history_list) < 30: return 13, 'H' # Default fallback to a prime number
            tf_scores = {}
            for tf in range(1, min(max_lookback, len(history_list)-10)):
                # 🛑 TRAP BYPASS: Agar tf "Pahada" sequence mein hai, toh skip karo!
                if tf in TRAP_TIMEFRAMES: continue
                
                success_count = 0
                for i in range(15, len(history_list)-1):
                    pat = history_list[:i][-tf:]
                    nxt = [history_list[:i][k+tf] for k in range(len(history_list[:i])-tf) if history_list[:i][k:k+tf] == pat]
                    if nxt:
                        top = Counter(nxt).most_common(1)[0][0]
                        td = get_all_tiers_cached(tuple(history_list[:i]))
                        if get_tier_name(top, td) == get_tier_name(history_list[i], td): success_count += 1
                tf_scores[tf] = success_count
            if not tf_scores: return 13
            return max(tf_scores, key=tf_scores.get)

        # ==========================================
        # SMART SEQUENTIAL FILTER (Fastest)
        # ==========================================
        @st.cache_data
        def get_sniper_timeframe_smart(history_tuple, dates_tuple, max_lookback=45):
            history_list = list(history_tuple)
            dates_list = list(dates_tuple)
            
            def check_hit_for_day(day_idx, tf_val):
                pat = history_list[:day_idx][-tf_val:]
                nxt = [history_list[:day_idx][k+tf_val] for k in range(len(history_list[:day_idx])-tf_val) if history_list[:day_idx][k:k+tf_val] == pat]
                if not nxt: return False
                top = Counter(nxt).most_common(1)[0][0]
                td = get_all_tiers_cached(tuple(history_list[:day_idx]))
                return get_tier_name(top, td) == get_tier_name(history_list[day_idx], td)

            surviving_tfs = []
            
            # STEP 1: FAST ELIMINATION
            for tf in range(1, min(max_lookback, len(history_list)-10)):
                # 🛑 TRAP BYPASS
                if tf in TRAP_TIMEFRAMES: continue
                
                if not check_hit_for_day(len(history_list)-1, tf): continue # Kal Pass nahi hua? Reject!
                if check_hit_for_day(len(history_list)-2, tf): continue     # Parso bhi Pass tha? Reject!
                
                surviving_tfs.append(tf)

            valid_tfs = []
            
            # STEP 2: HEAVY CHECKS ON SURVIVORS ONLY
            for tf in surviving_tfs:
                fail_count_before_pass = 1 
                for back_day in range(3, 25): 
                    idx = len(history_list) - back_day
                    if idx < 15: break
                    if not check_hit_for_day(idx, tf): fail_count_before_pass += 1
                    else: break
                
                # Rule 3: No Double Big Fall
                if fail_count_before_pass >= 3:
                    idx_after_first_fall = len(history_list) - 1 - fail_count_before_pass - 1
                    prev_fail_count = 0
                    if idx_after_first_fall >= 15:
                        for back_day in range(idx_after_first_fall, 14, -1):
                            if not check_hit_for_day(back_day, tf): prev_fail_count += 1
                            else: break
                    if prev_fail_count >= 3: continue 

                hit_history = [check_hit_for_day(i, tf) for i in range(15, len(history_list))]
                
                jan_apr_score = 0
                max_hist_fails = 0
                current_fails = 0
                
                for i in range(1, len(hit_history)):
                    if hit_history[i] and hit_history[i-1]: 
                        dt = dates_list[i + 15] 
                        if 1 <= dt.month <= 4: jan_apr_score += 1
                        
                for is_hit in hit_history:
                    if not is_hit:
                        current_fails += 1
                        if current_fails > max_hist_fails: max_hist_fails = current_fails
                    else:
                        current_fails = 0

                valid_tfs.append({
                    'tf': tf, 
                    'fails_before_pass': fail_count_before_pass,
                    'jan_apr_score': jan_apr_score, 
                    'max_hist_fails': max_hist_fails
                })

            if not valid_tfs: return 13, "No Match", 0, 0, 99 # Default safe prime number
            
            # SORTING: Lowest Historical Fails first!
            valid_tfs = sorted(valid_tfs, key=lambda x: (x['max_hist_fails'], -x['jan_apr_score']))
            best_match = valid_tfs[0]
            
            return best_match['tf'], "SMART SEQUENTIAL FILTER", best_match['fails_before_pass'], best_match['jan_apr_score'], best_match['max_hist_fails']

        def render_ank(nums, traps):
            nums = list(set(nums)); nums.sort()
            html = "<div style='display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;'>"
            for n in nums:
                if n in traps:
                    bg = "#1a1a1a"; border = "#333"; font_c = "#555"; extra = "text-decoration: line-through;"
                else:
                    bg = "#00FF7F"; border = "#008000"; font_c = "black"; extra = ""
                html += f"<div style='background:{bg}; padding:10px; border-radius:8px; text-align:center; min-width:45px; border:2px solid {border}; box-shadow: 2px 2px 5px rgba(0,0,0,0.5); {extra}'>" \
                        f"<span style='font-size:20px; font-weight:bold; color:{font_c};'>{n:02d}</span></div>"
            html += "</div>"
            return html

        # --- SHIFT PROCESSING ---
        for shift in shift_order:
            if shift not in df.columns: continue
            
            shift_data = filtered_df[['DATE', shift]].dropna()
            
            history_today = shift_data[shift].astype(int).tolist()
            dates_today = shift_data['DATE'].tolist()
            
            if len(history_today) >= 60:
                st.markdown("---")
                st.subheader(f"🧩 Shift: {shift} (Anti-Trap Mode ⚡)")

                with st.spinner(f"Operator ke Traps hataye jaa rahe hain... Fatak se load ho raha hai!"):
                    
                    today_tiers = get_all_tiers_cached(tuple(history_today))
                    player_trap_nums = detect_player_load_trap(tuple(history_today))
                    
                    # STREAK CHECKER
                    current_fail_streak = 0
                    for j in range(len(history_today)-1, max(20, len(history_today)-20), -1):
                        h_slice = history_today[:j]
                        act_val = history_today[j]
                        
                        if current_fail_streak == 0:
                            temp_tf = get_best_main_timeframe(tuple(h_slice), 45)
                        elif current_fail_streak == 1:
                            temp_tf = get_best_main_timeframe(tuple(h_slice[:-1]), 45
            

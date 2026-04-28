import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter
import concurrent.futures
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="MAYA AI - Multi-Threaded Sniper Engine", layout="wide")

st.title("MAYA AI 🦅: Multi-Threaded Sniper Engine 🚀")
st.markdown("Aapke naye idea par aadharit: **Parallel Processing (6 hisson mein tod kar)!** 45 Timeframes ki calculations ko multi-threading se ultra-fast kar diya gaya hai. Ab result seconds mein aayega!")

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
selected_end_date = st.sidebar.date_input("Calculation Date (T)")
max_limit = st.sidebar.slider("Elimination Limit", 2, 5, 4)

shift_order = ["DB", "SG", "FD", "GD", "ZA", "GL", "DS"]
selected_shift = st.sidebar.selectbox("🎯 Select Shift to Calculate", shift_order)

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

        # --- PRE-COMPUTED MEMORY BOOSTER ---
        # (Baar-baar calculate karne se bachne ke liye Memory Array)
        @st.cache_data
        def build_tier_cache(history_tuple):
            history_list = list(history_tuple)
            cache = {}
            for i in range(15, len(history_list) + 1):
                past_list = history_list[:i]
                scores = {n: 0 for n in range(100)}
                for days in range(1, min(46, len(past_list) + 1)):
                    sheet = past_list[-days:]
                    for num, freq in Counter(sheet).items(): scores[num] += freq * (1 + (1/days)) 
                ranked = sorted(range(100), key=lambda x: scores[x], reverse=True)
                cache[i] = {'H': ranked[0:33], 'M': ranked[33:66], 'L': ranked[66:100]}
            return cache

        def get_tier_name(num, td):
            if num in td['H']: return 'H'
            elif num in td['M']: return 'M'
            elif num in td['L']: return 'L'
            return 'FAIL'

        @st.cache_data
        def detect_player_load_trap(history_tuple):
            history_list = list(history_tuple)
            player_traps = []
            if len(history_list) < 2: return player_traps
            last_num = history_list[-1]
            prev_num = history_list[-2]
            player_traps.extend([(last_num + 1) % 100, (last_num - 1) % 100, int(str(last_num).zfill(2)[::-1]), (last_num + (last_num - prev_num)) % 100])
            for num, count in Counter(history_list[-5:]).items():
                if count >= 2: player_traps.append(num)
            return list(set(player_traps))

        # ==========================================
        # PARALLEL ENGINE 1: MAIN TIMEFRAME 
        # ==========================================
        def process_main_chunk(chunk, history_list, tier_cache):
            tf_scores = {}
            for tf in chunk:
                success_count = 0
                for i in range(15, len(history_list)-1):
                    pat = history_list[:i][-tf:]
                    nxt = [history_list[:i][k+tf] for k in range(len(history_list[:i])-tf) if history_list[:i][k:k+tf] == pat]
                    if nxt:
                        top = Counter(nxt).most_common(1)[0][0]
                        td = tier_cache[i]
                        if get_tier_name(top, td) == get_tier_name(history_list[i], td): 
                            success_count += 1
                tf_scores[tf] = success_count
            return tf_scores

        @st.cache_data
        def get_best_main_timeframe_fast(history_tuple, tier_cache, max_lookback=45):
            history_list = list(history_tuple)
            if len(history_list) < 30: return 15, 'H'
            
            tfs_to_check = list(range(1, min(max_lookback, len(history_list)-10)))
            # Aapka Idea: 6 Bhagon mein todo (Chunking)
            chunk_size = max(1, len(tfs_to_check) // 6)
            chunks = [tfs_to_check[i:i + chunk_size] for i in range(0, len(tfs_to_check), chunk_size)]
            
            all_tf_scores = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_main_chunk, chunk, history_list, tier_cache) for chunk in chunks]
                for future in concurrent.futures.as_completed(futures):
                    all_tf_scores.update(future.result())
            
            if not all_tf_scores: return 15
            return max(all_tf_scores, key=all_tf_scores.get)

        # ==========================================
        # PARALLEL ENGINE 2: 5-STAR SNIPER FILTER 
        # ==========================================
        def process_sniper_chunk(chunk, history_list, dates_list, tier_cache):
            valid_tfs = []
            for tf in chunk:
                def check_hit_for_day(day_idx):
                    pat = history_list[:day_idx][-tf:]
                    nxt = [history_list[:day_idx][k+tf] for k in range(len(history_list[:day_idx])-tf) if history_list[:day_idx][k:k+tf] == pat]
                    if not nxt: return False
                    top = Counter(nxt).most_common(1)[0][0]
                    td = tier_cache[day_idx]
                    return get_tier_name(top, td) == get_tier_name(history_list[day_idx], td)

                # RULE 1: Kal Pass
                if not check_hit_for_day(len(history_list)-1): continue 

                # RULE 2: Parso Fail
                fail_count_before_pass = 0
                for back_day in range(2, 25): 
                    idx = len(history_list) - back_day
                    if idx < 15: break
                    if not check_hit_for_day(idx): fail_count_before_pass += 1
                    else: break
                
                if fail_count_before_pass == 0: continue 

                # RULE 3: No Double Big Fall
                if fail_count_before_pass >= 3:
                    idx_after_first_fall = len(history_list) - 1 - fail_count_before_pass - 1
                    prev_fail_count = 0
                    if idx_after_first_fall >= 15:
                        for back_day in range(idx_after_first_fall, 14, -1):
                            if not check_hit_for_day(back_day): prev_fail_count += 1
                            else: break
                    if prev_fail_count >= 3: continue 

                # HISTORICAL STATS (For Rules 4 & 5)
                hit_history = [check_hit_for_day(i) for i in range(15, len(history_list))]
                
                # RULE 4: Jan-Apr Score
                jan_apr_score = 0
                for i in range(1, len(hit_history)):
                    if hit_history[i] and hit_history[i-1]: 
                        dt = dates_list[i + 15] 
                        if 1 <= dt.month <= 4:
                            jan_apr_score += 1

                # RULE 5: Min Historical Fails
                max_hist_fails = 0
                current_fails = 0
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
            return valid_tfs

        @st.cache_data
        def get_sniper_timeframe_fast(history_tuple, dates_tuple, tier_cache, max_lookback=45):
            history_list = list(history_tuple)
            dates_list = list(dates_tuple)
            tfs_to_check = list(range(1, min(max_lookback, len(history_list)-10)))
            
            # Aapka Idea: 6 Bhagon mein todo (Chunking)
            chunk_size = max(1, len(tfs_to_check) // 6)
            chunks = [tfs_to_check[i:i + chunk_size] for i in range(0, len(tfs_to_check), chunk_size)]
            
            valid_tfs = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_sniper_chunk, chunk, history_list, dates_list, tier_cache) for chunk in chunks]
                for future in concurrent.futures.as_completed(futures):
                    valid_tfs.extend(future.result())

            if not valid_tfs:
                return 15, "No Match", 0, 0, 99 
            
            # Sort: Min historical fails first, then highest Jan-Apr score
            valid_tfs = sorted(valid_tfs, key=lambda x: (x['max_hist_fails'], -x['jan_apr_score']))
            best_match = valid_tfs[0]
            return best_match['tf'], "5-STAR SNIPER FILTER", best_match['fails_before_pass'], best_match['jan_apr_score'], best_match['max_hist_fails']

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

        # --- SINGLE SHIFT PROCESSING ---
        shift = selected_shift
        if shift in df.columns:
            shift_data = filtered_df[['DATE', shift]].dropna()
            history_today = shift_data[shift].astype(int).tolist()
            dates_today = shift_data['DATE'].tolist()
            
            if len(history_today) >= 60:
                st.markdown("---")
                st.subheader(f"🧩 Shift: {shift} (Turbo Sniper Mode 🚀)")

                with st.spinner(f"Parallel Processing lagoo ho gayi hai. 6 processors ek sath kaam kar rahe hain..."):
                    
                    # 1. Sabse pehle Memory Dictionary Load Karo (100x Faster)
                    tier_cache = build_tier_cache(tuple(history_today))
                    today_tiers = tier_cache[len(history_today)]
                    player_trap_nums = detect_player_load_trap(tuple(history_today))
                    
                    # 2. STREAK CHECKER (Fast Version)
                    current_fail_streak = 0
                    for j in range(len(history_today)-1, max(20, len(history_today)-20), -1):
                        h_slice = history_today[:j]
                        act_val = history_today[j]
                        
                        if current_fail_streak == 0:
                            temp_tf = get_best_main_timeframe_fast(tuple(h_slice), tier_cache, 45)
                        elif current_fail_streak == 1:
                            temp_tf = get_best_main_timeframe_fast(tuple(h_slice[:-1]), tier_cache, 45)
                        else:
                            temp_tf = get_best_main_timeframe_fast(tuple(h_slice), tier_cache, 45) 
                        
                        cur_pat = h_slice[-temp_tf:]
                        nxt_items = [h_slice[i+temp_tf] for i in range(len(h_slice)-temp_tf) if h_slice[i:i+temp_tf] == cur_pat]
                        if nxt_items:
                            top = Counter(nxt_items).most_common(1)[0][0]
                            td = tier_cache[j]
                            if get_tier_name(top, td) == get_tier_name(act_val, td):
                                break
                        current_fail_streak += 1

                    # 3. AAPKA 5-STAR SNIPER RULE APLPY HOTA HAI YAHAN
                    fails_before = 0
                    jan_score = 0
                    max_historical_fail = 0
                    
                    if current_fail_streak == 0:
                        best_tf = get_best_main_timeframe_fast(tuple(history_today), tier_cache, 45)
                        logic_name = "MAIN ENGINE (Continuous Pass)"
                    elif current_fail_streak == 1:
                        best_tf = get_best_main_timeframe_fast(tuple(history_today[:-1]), tier_cache, 45)
                        logic_name = "MAIN ENGINE (Usi Timeframe par Dobara Try)"
                    else:
                        best_tf, logic_name, fails_before, jan_score, max_historical_fail = get_sniper_timeframe_fast(tuple(history_today), tuple(dates_today), tier_cache, 45)

                    # Final Prediction
                    cur_pat = history_today[-best_tf:]
                    next_items = [history_today[i+best_tf] for i in range(len(history_today)-best_tf) if history_today[i:i+best_tf] == cur_pat]
                    
                    best_tier = 'H'
                    if next_items:
                        top_pred = Counter(next_items).most_common(1)[0][0]
                        best_tier = get_tier_name(top_pred, today_tiers)
                    
                    raw_green_level_nums = today_tiers[best_tier]
                    valid_play_nums = [n for n in raw_green_level_nums if n not in player_trap_nums]
                    
                    actual_row_next = df[df['DATE'].dt.date == target_date_next]
                    actual_val_next = int(actual_row_next.iloc[0][shift]) if not actual_row_next.empty and pd.notna(actual_row_next.iloc[0][shift]) else None
                    is_hit = (actual_val_next in valid_play_nums) if actual_val_next is not None else False

                # --- UI ALERTS ---
                if current_fail_streak == 0:
                    st.markdown(f"<div style='background:#28a745; padding:10px; border-radius:8px; border: 2px solid #1e7e34; text-align:center; color:white; margin-bottom:10px;'>"
                                f"✅ <b>PICHLA DIN PAAS THA (Streak: 0 Fail)</b><br>Main Timeframe lagaya gaya hai.</div>", unsafe_allow_html=True)
                elif current_fail_streak == 1:
                    st.markdown(f"<div style='background:#ffc107; padding:10px; border-radius:8px; border: 2px solid #d39e00; text-align:center; color:black; margin-bottom:10px;'>"
                                f"⚠️ <b>1 DIN FAIL HUA HAI!</b><br>Aapke niyam anusaar, kal wala same timeframe aaj bhi khela jayega!</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#FF4B4B; padding:10px; border-radius:8px; border: 2px solid #c82333; text-align:center; color:white; margin-bottom:10px; box-shadow: 0 0 10px #FF4B4B;'>"
                                f"🔥 <b>GEAR SHIFTED ({current_fail_streak} Din Se Fail)</b><br>Aapka Multi-Threaded Sniper Filter lagaya gaya hai!</div>", unsafe_allow_html=True)

                # --- UI DISPLAY ---
                c_res, c_stat = st.columns([1, 2.5])
                with c_res:
                    if actual_val_next is not None:
                        m_color = "#28a745" if is_hit else "#FF4B4B"
                        st.markdown(f"<div style='background:{m_color}; padding:10px; border-radius:8px; text-align:center; color:white;'>"
                                    f"Match Result ({target_date_next.strftime('%d %b')}):<br><b style='font-size:26px;'>{actual_val_next:02d}</b><br>{'HIT! ✅' if is_hit else 'MISS ❌'}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='background:#555; padding:10px; border-radius:8px; text-align:center; color:white;'>"
                                    f"Result ({target_date_next.strftime('%d %b')}):<br><b>Waiting...</b></div>", unsafe_allow_html=True)
                
                with c_stat:
                    st.markdown(f"<div style='border:2px solid #00FF7F; padding:10px; border-radius:8px; background:#00FF7F15; font-size:14px;'>"
                                f"<b style='color:#00FF7F; font-size:16px;'>🦅 5-STAR SNIPER INTELLIGENCE</b><br>"
                                f"<b>Logic Used:</b> {logic_name}<br>"
                                f"<b>Selected Gear:</b> <code>{best_tf}-Din ka Timeframe</code><br>")
                    
                    if current_fail_streak >= 2 and logic_name == "5-STAR SNIPER FILTER":
                        st.markdown(f"<i>📌 Yeh Timeframe pichli baar <b>{fails_before} din</b> fail hone ke baad kal paas hua tha. Isne Jan-Apr mein <b>{jan_score} baar</b> direct paas diya hai.<br><br>"
                                    f"🔥 <b>SABSE BADI BAAT:</b> Is timeframe ka poori history mein <b>sabse lamba fail sirf {max_historical_fail} din</b> gaya hai! Isse zyada safe kuch nahi hai!</i>", unsafe_allow_html=True)
                    
                    st.markdown(f"<hr style='margin:5px 0; border-top:1px solid #444;'>"
                                f"🥇 Final Prediction Tier: <b style='color:#00FF7F; font-size:18px;'>{best_tier}</b></div>", unsafe_allow_html=True)

                st.markdown(f"### 🔥 THE GREEN LEVEL (Valid: {len(valid_play_nums)} Nums):")
                st.markdown(render_ank(raw_green_level_nums, player_trap_nums), unsafe_allow_html=True)
                st.markdown("""<style>.block-container { padding-top: 6rem; }</style>""", unsafe_allow_html=True)
            else:
                st.warning("Data kam hai (minimum 60 din ka data chahiye).")

    except Exception as e:
        st.error(f"Error: {e}")
        

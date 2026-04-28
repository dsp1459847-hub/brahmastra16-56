import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="MAYA AI - All Shifts Fast Engine", layout="wide")

st.title("MAYA AI 🦅: All Shifts Fast Sniper Engine 🚀")
st.markdown("Aapke niyam par aadharit: **Saari Shifts Ek Sath!** 0 aur 1 fail par Same Timeframe, 2 Fail par 5-Star Sniper Filter. Code ko without multi-threading (Pure Fast Cache) par set kiya gaya hai taaki fatak se load ho!")

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
selected_end_date = st.sidebar.date_input("Calculation Date (T)")
max_limit = st.sidebar.slider("Elimination Limit", 2, 5, 4)

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

        # FLOATING BOX
        five_days_ago = selected_end_date - timedelta(days=4)
        history_5_days = filtered_df[(filtered_df['DATE'].dt.date >= five_days_ago) & (filtered_df['DATE'].dt.date <= selected_end_date)].copy()
        
        table_html = "<table style='width: 100%; border-collapse: collapse; text-align: center; font-size: 14px;'><tr><th style='border: 1px solid #444; padding: 5px; background: #00FF7F; color: black;'>DATE</th>"
        for shift in shift_order: table_html += f"<th style='border: 1px solid #444; padding: 5px; background: #00FF7F; color: black;'>{shift}</th>"
        table_html += "</tr>"
        if not history_5_days.empty:
            history_5_days['DATE_STR'] = history_5_days['DATE'].dt.strftime('%d %b %Y')
            for _, row in history_5_days.iterrows():
                table_html += f"<tr><td style='border: 1px solid #444; padding: 5px; color: white;'><b>{row['DATE_STR']}</b></td>"
                for shift in shift_order:
                    val = row[shift] if pd.notna(row[shift]) else "-"
                    disp_val = f"{int(val):02d}" if val != "-" else "-"
                    table_html += f"<td style='border: 1px solid #444; padding: 5px; color: white;'>{disp_val}</td>"
                table_html += "</tr>"
        else:
            table_html += "<tr><td colspan='8' style='border: 1px solid #444; padding: 10px; color: white;'>Data nahi hai</td></tr>"
        table_html += "</table>"

        st.markdown(f"""
        <style>
        .floating-header {{ position: fixed; top: 55px; left: 50%; transform: translateX(-50%); width: 85%; max-width: 900px; background-color: #1e1e1e; border: 2px solid #00FF7F; border-radius: 8px; z-index: 99999; box-shadow: 0 4px 15px rgba(0,0,0,0.8); }}
        .floating-summary {{ padding: 12px; font-weight: bold; color: #00FF7F; cursor: pointer; font-size: 16px; text-align: center; list-style: none; }}
        .floating-summary::-webkit-details-marker {{ display: none; }}
        .floating-content {{ padding: 15px; background-color: #121212; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }}
        </style>
        <div class="floating-header"><details><summary class="floating-summary">🔽 📜 PICHLE 5 DIN KA OPEN RECORD (Click Here) 🔽</summary><div class="floating-content">{table_html}</div></details></div>
        """, unsafe_allow_html=True)

        # --- CORE CACHED FUNCTIONS (FAST) ---
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

        # ENGINE 1 (Main Logic)
        @st.cache_data
        def get_best_main_timeframe_fast(history_tuple, max_lookback=45):
            history_list = list(history_tuple)
            if len(history_list) < 30: return 15
            tf_scores = {}
            for tf in range(1, min(max_lookback, len(history_list)-10)):
                success_count = 0
                for i in range(15, len(history_list)-1):
                    pat = history_list[:i][-tf:]
                    nxt = [history_list[:i][k+tf] for k in range(len(history_list[:i])-tf) if history_list[:i][k:k+tf] == pat]
                    if nxt:
                        top = Counter(nxt).most_common(1)[0][0]
                        td = get_all_tiers_cached(tuple(history_list[:i]))
                        if get_tier_name(top, td) == get_tier_name(history_list[i], td): success_count += 1
                tf_scores[tf] = success_count
            if not tf_scores: return 15
            return max(tf_scores, key=tf_scores.get)

        # ENGINE 2 (5-Star Sniper Logic)
        @st.cache_data
        def get_sniper_timeframe_fast(history_tuple, dates_tuple, max_lookback=45):
            history_list = list(history_tuple)
            dates_list = list(dates_tuple)
            valid_tfs = []
            
            for tf in range(1, min(max_lookback, len(history_list)-10)):
                def check_hit_for_day(day_idx):
                    pat = history_list[:day_idx][-tf:]
                    nxt = [history_list[:day_idx][k+tf] for k in range(len(history_list[:day_idx])-tf) if history_list[:day_idx][k:k+tf] == pat]
                    if not nxt: return False
                    top = Counter(nxt).most_common(1)[0][0]
                    td = get_all_tiers_cached(tuple(history_list[:day_idx]))
                    return get_tier_name(top, td) == get_tier_name(history_list[day_idx], td)

                # Rule 1
                if not check_hit_for_day(len(history_list)-1): continue 

                # Rule 2
                fail_count_before_pass = 0
                for back_day in range(2, 25): 
                    idx = len(history_list) - back_day
                    if idx < 15: break
                    if not check_hit_for_day(idx): fail_count_before_pass += 1
                    else: break
                if fail_count_before_pass == 0: continue 

                # Rule 3
                if fail_count_before_pass >= 3:
                    idx_after_first_fall = len(history_list) - 1 - fail_count_before_pass - 1
                    prev_fail_count = 0
                    if idx_after_first_fall >= 15:
                        for back_day in range(idx_after_first_fall, 14, -1):
                            if not check_hit_for_day(back_day): prev_fail_count += 1
                            else: break
                    if prev_fail_count >= 3: continue 

                # Full History for Rules 4 & 5
                hit_history = [check_hit_for_day(i) for i in range(15, len(history_list))]
                
                # Rule 4
                jan_apr_score = 0
                for i in range(1, len(hit_history)):
                    if hit_history[i] and hit_history[i-1]: 
                        dt = dates_list[i + 15] 
                        if 1 <= dt.month <= 4: jan_apr_score += 1

                # Rule 5
                max_hist_fails = 0
                current_fails = 0
                for is_hit in hit_history:
                    if not is_hit:
                        current_fails += 1
                        if current_fails > max_hist_fails: max_hist_fails = current_fails
                    else:
                        current_fails = 0

                valid_tfs.append({
                    'tf': tf, 'fails_before_pass': fail_count_before_pass,
                    'jan_apr_score': jan_apr_score, 'max_hist_fails': max_hist_fails
                })

            if not valid_tfs: return 15, "No Match", 0, 0, 99 
            
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

        # --- PROCESS ALL SHIFTS ---
        for shift in shift_order:
            if shift not in df.columns: continue
            
            shift_data = filtered_df[['DATE', shift]].dropna()
            history_today = shift_data[shift].astype(int).tolist()
            dates_today = shift_data['DATE'].tolist()
            
            if len(history_today) >= 60:
                st.markdown("---")
                st.subheader(f"🧩 Shift: {shift}")

                # Fast Streak Calculation
                today_tiers = get_all_tiers_cached(tuple(history_today))
                player_trap_nums = detect_player_load_trap(tuple(history_today))
                
                current_fail_streak = 0
                for j in range(len(history_today)-1, max(20, len(history_today)-20), -1):
                    h_slice = tuple(history_today[:j])
                    act_val = history_today[j]
                    
                    if current_fail_streak == 0:
                        temp_tf = get_best_main_timeframe_fast(h_slice, 45)
                    elif current_fail_streak == 1:
                        temp_tf = get_best_main_timeframe_fast(tuple(history_today[:j-1]), 45)
                    else:
                        temp_tf = get_best_main_timeframe_fast(h_slice, 45) 
                    
                    h_list = list(h_slice)
                    cur_pat = h_list[-temp_tf:]
                    nxt_items = [h_list[i+temp_tf] for i in range(len(h_list)-temp_tf) if h_list[i:i+temp_tf] == cur_pat]
                    t_dict = get_all_tiers_cached(h_slice)
                    
                    if nxt_items:
                        top = Counter(nxt_items).most_common(1)[0][0]
                        if get_tier_name(top, t_dict) == get_tier_name(act_val, t_dict): break
                    current_fail_streak += 1

                # AAPKA 5-STAR SNIPER RULE
                fails_before = 0
                jan_score = 0
                max_historical_fail = 0
                
                if current_fail_streak == 0:
                    best_tf = get_best_main_timeframe_fast(tuple(history_today), 45)
                    logic_name = "MAIN ENGINE (Continuous Pass)"
                elif current_fail_streak == 1:
                    best_tf = get_best_main_timeframe_fast(tuple(history_today[:-1]), 45)
                    logic_name = "MAIN ENGINE (Usi Timeframe par Dobara Try)"
                else:
                    best_tf, logic_name, fails_before, jan_score, max_historical_fail = get_sniper_timeframe_fast(tuple(history_today), tuple(dates_today), 45)

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
                                f"⚠️ <b>1 DIN FAIL HUA HAI!</b><br>Kal wala same timeframe aaj bhi khela jayega!</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#FF4B4B; padding:10px; border-radius:8px; border: 2px solid #c82333; text-align:center; color:white; margin-bottom:10px; box-shadow: 0 0 10px #FF4B4B;'>"
                                f"🔥 <b>GEAR SHIFTED ({current_fail_streak} Din Se Fail)</b><br>Aapka 5-Star Sniper Filter lagaya gaya hai!</div>", unsafe_allow_html=True)

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
                        st.markdown(f"<i>📌 Pichli baar <b>{fails_before} din</b> fail hone ke baad kal paas hua tha. Jan-Apr Score: <b>{jan_score}</b>.<br><br>"
                                    f"🔥 <b>SABSE BADI BAAT:</b> Is timeframe ka poori history mein <b>sabse lamba fail sirf {max_historical_fail} din</b> gaya hai!</i>", unsafe_allow_html=True)
                    
                    st.markdown(f"<hr style='margin:5px 0; border-top:1px solid #444;'>"
                                f"🥇 Final Prediction Tier: <b style='color:#00FF7F; font-size:18px;'>{best_tier}</b></div>", unsafe_allow_html=True)

                st.markdown(f"### 🔥 THE GREEN LEVEL (Valid: {len(valid_play_nums)} Nums):")
                st.markdown(render_ank(raw_green_level_nums, player_trap_nums), unsafe_allow_html=True)

        st.markdown("""<style>.block-container { padding-top: 6rem; }</style>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
        

import streamlit as st
import random
import time

st.set_page_config(page_title="Ultimate Bingo", layout="wide")

# ==========================================
# 1. ตั้งค่า State พื้นฐาน
# ==========================================
if "grid_size" not in st.session_state:
    st.session_state.grid_size = 5
if "drawn_numbers" not in st.session_state:
    st.session_state.drawn_numbers = []
if "current_draw" not in st.session_state:
    st.session_state.current_draw = None
if "bingo_won" not in st.session_state:
    st.session_state.bingo_won = False
if "play_sound" not in st.session_state:
    st.session_state.play_sound = None

# ฟังก์ชันรีเซ็ตและสร้างช่องตารางใหม่
def init_grid():
    size = st.session_state.grid_size
    for r in range(size):
        for c in range(size):
            key = f"cell_{r}_{c}"
            if key not in st.session_state:
                st.session_state[key] = ""

init_grid()

# ==========================================
# 2. ฟังก์ชันระบบเกม
# ==========================================
def reset_game():
    st.session_state.drawn_numbers = []
    st.session_state.current_draw = None
    st.session_state.bingo_won = False
    st.session_state.play_sound = None
    size = st.session_state.grid_size
    for r in range(size):
        for c in range(size):
            st.session_state[f"cell_{r}_{c}"] = ""

def change_grid_size(new_size):
    st.session_state.grid_size = new_size
    reset_game()

def autofill_numbers(min_val, max_val):
    size = st.session_state.grid_size
    pool = [str(i) for i in range(min_val, max_val + 1)]
    
    current_board = [st.session_state[f"cell_{r}_{c}"] for r in range(size) for c in range(size) if st.session_state[f"cell_{r}_{c}"]]
    available = [n for n in pool if n not in current_board]
    
    for r in range(size):
        for c in range(size):
            key = f"cell_{r}_{c}"
            if st.session_state[key] == "" and available:
                chosen = random.choice(available)
                st.session_state[key] = chosen
                available.remove(chosen)

def check_bingo():
    """ตรวจสอบว่าบิงโกหรือไม่ (แนวนอน, แนวตั้ง, ทแยง)"""
    size = st.session_state.grid_size
    drawn = st.session_state.drawn_numbers
    
    if not drawn: return False

    # เช็คแนวนอน
    for r in range(size):
        if all(st.session_state[f"cell_{r}_{c}"] in drawn and st.session_state[f"cell_{r}_{c}"] != "" for c in range(size)):
            return True
    
    # เช็คแนวตั้ง
    for c in range(size):
        if all(st.session_state[f"cell_{r}_{c}"] in drawn and st.session_state[f"cell_{r}_{c}"] != "" for r in range(size)):
            return True
            
    # เช็คแนวทแยง (ซ้ายบนไปขวาล่าง)
    if all(st.session_state[f"cell_{i}_{i}"] in drawn and st.session_state[f"cell_{i}_{i}"] != "" for i in range(size)):
        return True
        
    # เช็คแนวทแยง (ขวาบนไปซ้ายล่าง)
    if all(st.session_state[f"cell_{i}_{size-1-i}"] in drawn and st.session_state[f"cell_{i}_{size-1-i}"] != "" for i in range(size)):
        return True

    return False

def generate_board_html():
    size = st.session_state.grid_size
    html = f"<div style='display: grid; grid-template-columns: repeat({size}, 1fr); gap: 10px;'>"
    for r in range(size):
        for c in range(size):
            val = st.session_state[f"cell_{r}_{c}"]
            is_drawn = val in st.session_state.drawn_numbers and val != ""
            
            bg_color = "#4CAF50" if is_drawn else "#f8f9fa"
            text_color = "white" if is_drawn else "#333"
            border = "2px solid #2e7d32" if is_drawn else "1px solid #ddd"
            shadow = "box-shadow: 0 4px 8px rgba(76, 175, 80, 0.4);" if is_drawn else ""
            
            html += f"""
                <div style='background-color: {bg_color}; color: {text_color}; border: {border}; {shadow}
                            border-radius: 10px; padding: 15px; text-align: center; font-weight: bold;
                            font-size: 24px; min-height: 70px; display: flex; align-items: center; 
                            justify-content: center; transition: 0.3s;'>
                    {val if val else "-"}
                </div>
            """
    html += "</div>"
    return html

# ฟังก์ชันเล่นเสียงด้วย HTML Audio (ดึงเสียงฟรีจาก Google Actions Sound Library)
def render_audio():
    if st.session_state.play_sound == "spin":
        url = "https://actions.google.com/sounds/v1/foley/spinning_bicycle_wheel.ogg"
    elif st.session_state.play_sound == "ding":
        url = "https://actions.google.com/sounds/v1/fantasy/magic_chime.ogg"
    elif st.session_state.play_sound == "bingo":
        url = "https://actions.google.com/sounds/v1/crowds/crowd_cheering.ogg"
    else:
        return
        
    st.markdown(f'<audio autoplay="true" style="display:none;"><source src="{url}" type="audio/ogg"></audio>', unsafe_allow_html=True)
    st.session_state.play_sound = None # ล้างค่าหลังเรนเดอร์

# ==========================================
# 3. สร้าง UI ของแอป
# ==========================================
st.title("🏆 Ultimate Bingo Generator")

tab_play, tab_setup = st.tabs(["🎮 โหมดเล่นเกม", "⚙️ ตั้งค่ากระดาน (Host)"])

# ----------------- จัดเตรียมกระดาน -----------------
with tab_setup:
    col_set1, col_set2, col_set3 = st.columns(3)
    
    with col_set1:
        new_size = st.selectbox("ขนาดตาราง", [3, 4, 5, 6, 7], index=[3, 4, 5, 6, 7].index(st.session_state.grid_size))
        if new_size != st.session_state.grid_size:
            change_grid_size(new_size)
            st.rerun()
            
    with col_set2:
        min_val = st.number_input("ตัวเลขต่ำสุด", value=1, step=1)
    with col_set3:
        max_val = st.number_input("ตัวเลขสูงสุด", value=75, step=1)

    st.markdown("---")
    
    total_cells = st.session_state.grid_size ** 2
    if (max_val - min_val + 1) < total_cells:
        st.error(f"⚠️ ช่วงตัวเลขแคบเกินไป (ต้องมีอย่างน้อย {total_cells} ตัว เพื่อให้พอดีกับตาราง)")
    else:
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            st.button("✨ สุ่มเติมช่องว่าง", on_click=autofill_numbers, args=(min_val, max_val), use_container_width=True)
        with col_btn2:
            st.button("🔄 ล้างกระดาน", on_click=reset_game, type="secondary", use_container_width=True)

        st.markdown("---")
        
        # วาด Grid สำหรับ Input
        size = st.session_state.grid_size
        for r in range(size):
            cols = st.columns(size)
            for c in range(size):
                with cols[c]:
                    st.text_input(f"R{r}C{c}", key=f"cell_{r}_{c}", label_visibility="collapsed", placeholder="-")

# ----------------- หน้าเล่นเกม -----------------
with tab_play:
    # เล่นเสียงถ้ามีค้างอยู่ใน state
    render_audio()
    
    col_left, col_right = st.columns([1.2, 2.8], gap="large")
    
    with col_left:
        st.subheader("🎰 หมุนตัวเลข")
        spin_placeholder = st.empty()
        
        pool_numbers = [str(i) for i in range(min_val, max_val + 1)]
        
        if st.button("🎯 กดเพื่อสุ่มเลข!", use_container_width=True, type="primary"):
            available_to_draw = [n for n in pool_numbers if n not in st.session_state.drawn_numbers]
            
            if available_to_draw:
                # 1. แอนิเมชันสับเลข และฝังเสียงหมุน
                spin_placeholder.markdown(
                    '<audio autoplay="true" style="display:none;"><source src="https://actions.google.com/sounds/v1/foley/spinning_bicycle_wheel.ogg" type="audio/ogg"></audio>',
                    unsafe_allow_html=True
                )
                for _ in range(15):
                    temp_num = random.choice(pool_numbers)
                    spin_placeholder.markdown(
                        f"<div style='text-align:center; font-size: 60px; color: #ccc; padding: 20px; border: 3px dashed #eee; border-radius: 15px;'>{temp_num}</div>", 
                        unsafe_allow_html=True
                    )
                    time.sleep(0.06)
                
                # 2. ผลลัพธ์เลข
                final_draw = random.choice(available_to_draw)
                st.session_state.drawn_numbers.append(final_draw)
                st.session_state.current_draw = final_draw
                
                # 3. ตรวจสอบว่าบิงโกไหม
                if check_bingo() and not st.session_state.bingo_won:
                    st.session_state.bingo_won = True
                    st.session_state.play_sound = "bingo"
                    st.balloons() # ยิงพลุลูกโป่ง!
                else:
                    st.session_state.play_sound = "ding"
                
                st.rerun() # รีโหลดเพื่อเรนเดอร์เสียงและไฮไลต์
            else:
                st.warning("สุ่มตัวเลขครบหมดแล้ว!")

        # แสดงกล่องตัวเลขล่าสุด
        if st.session_state.current_draw:
            # เปลี่ยนสีกล่องถ้าบิงโก
            bg_gradient = "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)" if st.session_state.bingo_won else "linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%)"
            title_text = "🎉 BINGO! 🎉" if st.session_state.bingo_won else "เลขที่ออก"
            
            spin_placeholder.markdown(
                f"""
                <div style='text-align:center; padding: 30px; background: {bg_gradient}; 
                            border-radius: 15px; color: white; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);'>
                    <h3 style='margin:0; opacity: 0.9;'>{title_text}</h3>
                    <h1 style='margin:0; font-size: 80px; font-weight: 900;'>{st.session_state.current_draw}</h1>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            spin_placeholder.markdown(
                "<div style='text-align:center; font-size: 24px; color: gray; padding: 40px; border: 3px dashed #eee; border-radius: 15px;'>รอการสุ่ม...</div>", 
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.write(f"**ประวัติ ({len(st.session_state.drawn_numbers)}):**")
        if st.session_state.drawn_numbers:
            history_html = "".join([f"<span style='background:#f0f2f6; color:#333; padding:5px 10px; border-radius:15px; margin:2px; display:inline-block; font-weight:bold;'>{n}</span>" for n in st.session_state.drawn_numbers])
            st.markdown(history_html, unsafe_allow_html=True)

    with col_right:
        header_text = "🏆 กระดานบิงโกแตกแล้ว!" if st.session_state.bingo_won else f"📋 กระดานของคุณ ({st.session_state.grid_size}x{st.session_state.grid_size})"
        st.subheader(header_text)
        st.markdown(generate_board_html(), unsafe_allow_html=True)

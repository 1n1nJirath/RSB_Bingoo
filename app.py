import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random

st.set_page_config(page_title="Bingo Mega Wheel", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 0. Custom CSS & คีย์ลัด (Smooth Transition & Shortcuts)
# ==========================================
# ใส่ CSS ให้ Streamlit เฟดอินอย่างนุ่มนวลตอนสลับหน้า
st.markdown("""
    <style>
        .stApp {
            animation: fadeIn 0.6s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.98); }
            to { opacity: 1; transform: scale(1); }
        }
    </style>
""", unsafe_allow_html=True)

def inject_keyboard_shortcuts():
    js = """
    <script>
    const doc = window.parent.document;
    if (!doc.getElementById('bingo-shortcuts')) {
        const script = doc.createElement('script');
        script.id = 'bingo-shortcuts';
        script.innerHTML = `
            document.addEventListener('keydown', function(e) {
                if ((e.code === 'Space' || e.code === 'Enter') && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    const btns = document.querySelectorAll('button');
                    btns.forEach(b => {
                        if (b.innerText.includes('กดเพื่อสุ่ม! (Spacebar)')) b.click();
                        if (b.innerText.includes('กลับกระดาน')) b.click();
                    });
                }
            });
        `;
        doc.body.appendChild(script);
    }
    </script>
    """
    components.html(js, height=0, width=0)

inject_keyboard_shortcuts()

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
if "categories_map" not in st.session_state:
    st.session_state.categories_map = {} 
if "pool_numbers" not in st.session_state:
    st.session_state.pool_numbers = []
if "is_spinning" not in st.session_state:
    st.session_state.is_spinning = False
if "pending_target" not in st.session_state:
    st.session_state.pending_target = None
if "raw_text_input" not in st.session_state:
    st.session_state.raw_text_input = "\n".join([f"หมวดที่ {i}" for i in range(1, 51)])

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
    size = st.session_state.grid_size
    for r in range(size):
        for c in range(size):
            st.session_state[f"cell_{r}_{c}"] = ""

def autofill_numbers():
    size = st.session_state.grid_size
    if not st.session_state.pool_numbers:
        st.warning("⚠️ กรุณาสุ่มจับคู่หมวดหมู่กับตัวเลขก่อนเติมช่องว่าง!")
        return
    pool = st.session_state.pool_numbers.copy()
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
    size = st.session_state.grid_size
    drawn = st.session_state.drawn_numbers
    if not drawn: return False
    for r in range(size):
        if all(st.session_state[f"cell_{r}_{c}"] in drawn and st.session_state[f"cell_{r}_{c}"] != "" for c in range(size)): return True
    for c in range(size):
        if all(st.session_state[f"cell_{r}_{c}"] in drawn and st.session_state[f"cell_{r}_{c}"] != "" for r in range(size)): return True
    if all(st.session_state[f"cell_{i}_{i}"] in drawn and st.session_state[f"cell_{i}_{i}"] != "" for i in range(size)): return True
    if all(st.session_state[f"cell_{i}_{size-1-i}"] in drawn and st.session_state[f"cell_{i}_{size-1-i}"] != "" for i in range(size)): return True
    return False

def generate_board_html():
    size = st.session_state.grid_size
    html = f"<div style='display: grid; grid-template-columns: repeat({size}, 1fr); gap: 10px;'>"
    for r in range(size):
        for c in range(size):
            val = st.session_state[f"cell_{r}_{c}"]
            is_drawn = val in st.session_state.drawn_numbers and val != ""
            bg_color = "#4CAF50" if is_drawn else "#262730"
            text_color = "white" if is_drawn else "#ffffff"
            border = "2px solid #4CAF50" if is_drawn else "1px solid #444"
            shadow = "box-shadow: 0 0 15px rgba(76,175,80,0.6);" if is_drawn else ""
            html += f"<div style='background-color:{bg_color}; color:{text_color}; border:{border}; {shadow} border-radius:10px; padding:15px; text-align:center; font-weight:bold; font-size:28px; min-height:80px; display:flex; align-items:center; justify-content:center; transition:0.3s;'>{val if val else '-'}</div>"
    html += "</div>"
    return html

# ==========================================
# 3. โค้ด HTML วงล้อไซส์ยักษ์ (รองรับการบังคับเลือกเอฟเฟกต์)
# ==========================================
def get_mega_wheel_html(target_number, target_category, all_numbers, forced_effect=-1):
    formatted_items = [f"{st.session_state.categories_map[n]} ({n})" for n in all_numbers]
    random.shuffle(formatted_items)
    
    js_items = str(formatted_items) 
    target_str = f"{target_category} ({target_number})"
    
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;700&display=swap');
            body {{ font-family: 'Kanit', sans-serif; background-color: transparent; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 95vh; margin: 0; overflow: hidden; cursor: pointer; }}
            
            .picker-container {{ position: relative; width: 600px; height: 400px; background: #1a1c23; border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.8); overflow: hidden; -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%); margin-bottom: 50px; }}
            .picker-overlay {{ position: absolute; top: 50%; left: 0; right: 0; height: 80px; transform: translateY(-50%); border-top: 3px solid #FF4B4B; border-bottom: 3px solid #FF4B4B; background: rgba(255, 75, 75, 0.1); pointer-events: none; z-index: 10; box-shadow: inset 0 0 15px rgba(255, 75, 75, 0.2); }}
            
            .pointer {{ position: absolute; top: 50%; left: 15px; transform: translateY(-50%); z-index: 20; transition: top 0.4s ease-in-out; display: flex; align-items: center; animation: pulseArrow 1s infinite alternate; }}
            @keyframes pulseArrow {{ 0% {{ transform: translateY(-50%) scale(1); filter: drop-shadow(0 0 5px #FFD700); }} 100% {{ transform: translateY(-50%) scale(1.1); filter: drop-shadow(0 0 15px #FFD700); }} }}
            
            .picker-wheel {{ margin: 0; padding: 0; list-style: none; text-align: center; transform: translateY(160px); }}
            .picker-item {{ height: 80px; line-height: 80px; font-size: 36px; font-weight: bold; color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 20px 0 50px; }}
            
            .result-container {{ display: none; opacity: 0; text-align: center; padding: 50px 30px; background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%); border-radius: 20px; box-shadow: 0 15px 30px rgba(255,75,43,0.5); transition: opacity 0.8s; width: 100%; max-width: 650px; }}
            .result-container h3 {{ margin: 0; font-size: 32px; color: #FFD700; }}
            .result-container h1 {{ margin: 20px 0; font-size: 56px; font-weight: 900; line-height: 1.2; text-shadow: 3px 3px 6px rgba(0,0,0,0.4); }}
            
            .instruction {{ display: none; margin-top: 25px; font-size: 20px; color: #fff; text-align: center; background: rgba(0,0,0,0.4); padding: 10px 20px; border-radius: 30px; animation: pulseText 1.5s infinite; }}
            @keyframes pulseText {{ 0% {{ opacity: 0.7; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.7; }} }}
        </style>
    </head>
    <body>
        <audio id="spin-sound" src="https://actions.google.com/sounds/v1/foley/spinning_bicycle_wheel.ogg"></audio>
        <audio id="win-sound" src="https://actions.google.com/sounds/v1/fantasy/magic_chime.ogg"></audio>

        <div class="picker-container" id="picker">
            <div class="picker-overlay"></div>
            <div class="pointer" id="pointer">
                <svg width="45" height="45" viewBox="0 0 24 24" fill="#FFD700" xmlns="http://www.w3.org/2000/svg"><path d="M4 4L20 12L4 20V4Z"/></svg>
            </div>
            <ul class="picker-wheel" id="wheel"></ul>
        </div>

        <div class="result-container" id="result">
            <h3>🎉 ยินดีด้วย 🎉</h3>
            <h1 id="res-cat"></h1>
            <div class="instruction" id="instruction">🖱️ คลิกหน้าจอ หรือ กด <b>Spacebar</b> เพื่อกลับไปที่กระดาน</div>
        </div>

        <script>
            const targetStr = "{target_str}";
            const itemsList = {js_items}; 
            const forcedEffect = {forced_effect}; // รับค่าบังคับเอฟเฟกต์จาก Python
            const wheel = document.getElementById('wheel');
            const pointer = document.getElementById('pointer');
            const itemHeight = 80;
            const visibleCenterOffset = 160;

            const trackItems = [...itemsList, ...itemsList, ...itemsList, ...itemsList, ...itemsList, ...itemsList, ...itemsList];
            const targetBaseIndex = itemsList.indexOf(targetStr);
            const finalTargetIndex = (itemsList.length * 5) + targetBaseIndex;

            trackItems.forEach(text => {{
                const li = document.createElement('li');
                li.className = 'picker-item';
                li.innerText = text;
                wheel.appendChild(li);
            }});

            function closeToBoard() {{
                const btns = window.parent.document.querySelectorAll('button');
                btns.forEach(b => {{ if (b.innerText.includes('กลับกระดาน')) b.click(); }});
            }}

            window.onload = () => {{
                document.getElementById('spin-sound').play().catch(e => console.log(e));
                
                wheel.style.transition = 'none';
                wheel.style.transform = `translateY(${{visibleCenterOffset - (targetBaseIndex * itemHeight)}}px)`;
                wheel.offsetHeight; 
                
                let effectType = forcedEffect;
                
                // ถ้าระบบไม่ได้ถูกบังคับ (-1) ให้สุ่มตามเรทปกติ
                if (effectType === -1) {{
                    const rand = Math.random() * 100;
                    if (rand < 25) effectType = 0;      
                    else if (rand < 35) effectType = 1; 
                    else if (rand < 45) effectType = 2; 
                    else if (rand < 55) effectType = 3; 
                    else if (rand < 65) effectType = 4; 
                    else if (rand < 70) effectType = 5; 
                    else if (rand < 80) effectType = 6; 
                    else if (rand < 85) effectType = 7; 
                    else if (rand < 90) effectType = 8; 
                    else effectType = 9;                
                }}
                
                const finalY = visibleCenterOffset - (finalTargetIndex * itemHeight);
                let revealDelay = 5200; 
                
                // ... (ตรรกะแอนิเมชัน 0-9 เหมือนเดิมเป๊ะ)
                if (effectType === 0) {{ 
                    wheel.style.transition = 'transform 3.8s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{finalY}}px)`;
                }} 
                else if (effectType === 1) {{ 
                    wheel.style.transition = 'transform 1.8s cubic-bezier(0.2, 0.8, 0.2, 1)';
                    wheel.style.transform = `translateY(${{finalY}}px)`;
                    revealDelay = 3000;
                }} 
                else if (effectType === 2) {{ 
                    const overshootY = visibleCenterOffset - ((finalTargetIndex + 2) * itemHeight);
                    wheel.style.transition = 'transform 2.5s cubic-bezier(0.1, 0.8, 0.2, 1)';
                    wheel.style.transform = `translateY(${{overshootY}}px)`;
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)'; wheel.style.transform = `translateY(${{finalY}}px)`; }}, 2600);
                }}
                else if (effectType === 3) {{ 
                    const earlyY = visibleCenterOffset - ((finalTargetIndex - 3) * itemHeight);
                    wheel.style.transition = 'transform 2.5s cubic-bezier(0.1, 0.9, 0.3, 1)';
                    wheel.style.transform = `translateY(${{earlyY}}px)`;
                    setTimeout(() => {{ wheel.style.transition = 'transform 1.2s ease-in-out'; wheel.style.transform = `translateY(${{finalY}}px)`; }}, 2600);
                }}
                else if (effectType === 4) {{ 
                    const teaseY = visibleCenterOffset - ((finalTargetIndex + 0.8) * itemHeight);
                    wheel.style.transition = 'transform 3.5s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{teaseY}}px)`;
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.3s ease-out'; wheel.style.transform = `translateY(${{finalY}}px)`; }}, 3700);
                }}
                else if (effectType === 5) {{ 
                    const nearY = visibleCenterOffset - ((finalTargetIndex - 1) * itemHeight);
                    wheel.style.transition = 'transform 2.5s cubic-bezier(0.1, 0.8, 0.5, 1)';
                    wheel.style.transform = `translateY(${{nearY}}px)`;
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.1s linear'; wheel.style.transform = `translateY(${{visibleCenterOffset - ((finalTargetIndex + 1) * itemHeight)}}px)`; }}, 2600);
                    setTimeout(() => {{ wheel.style.transform = `translateY(${{visibleCenterOffset - ((finalTargetIndex - 2) * itemHeight)}}px)`; }}, 2750);
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.2s ease-out'; wheel.style.transform = `translateY(${{finalY}}px)`; }}, 2950);
                }}
                else if (effectType === 6) {{ 
                    const wrongY = visibleCenterOffset - ((finalTargetIndex - 1) * itemHeight);
                    wheel.style.transition = 'transform 2.8s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{wrongY}}px)`;
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)'; wheel.style.transform = `translateY(${{finalY}}px)`; }}, 4000);
                }}
                else if (effectType === 7) {{
                    const fakeTargetIndex = finalTargetIndex - 1;
                    const fakeY = visibleCenterOffset - (fakeTargetIndex * itemHeight);
                    wheel.style.transition = 'transform 3.2s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{fakeY}}px)`;
                    setTimeout(() => {{ pointer.style.transition = 'top 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'; pointer.style.top = `calc(50% - ${{itemHeight}}px)`; }}, 3900);
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)'; wheel.style.transform = `translateY(${{finalY}}px)`; pointer.style.transition = 'top 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)'; pointer.style.top = '50%'; }}, 4700);
                    revealDelay = 5800;
                }}
                else if (effectType === 8) {{
                    const offsetY = finalY + itemHeight; 
                    wheel.style.transition = 'transform 3.2s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{offsetY}}px)`;
                    setTimeout(() => {{ pointer.style.transition = 'top 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)'; pointer.style.top = `calc(50% + ${{itemHeight}}px)`; }}, 3600);
                    revealDelay = 4800;
                }}
                else if (effectType === 9) {{
                    wheel.style.transition = 'transform 3.2s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{finalY}}px)`;
                    setTimeout(() => {{ pointer.style.transition = 'top 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'; pointer.style.top = `calc(50% - ${{itemHeight}}px)`; }}, 3600);
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)'; wheel.style.transform = `translateY(${{finalY - itemHeight}}px)`; }}, 4600);
                    revealDelay = 5700;
                }}

                setTimeout(() => {{
                    document.getElementById('picker').style.display = 'none';
                    const res = document.getElementById('result');
                    res.style.display = 'block';
                    document.getElementById('res-cat').innerText = targetStr;

                    setTimeout(() => {{
                        res.style.opacity = '1';
                        document.getElementById('win-sound').play().catch(e => console.log(e));
                        
                        setTimeout(() => {{
                            document.getElementById('instruction').style.display = 'block';
                            window.addEventListener('click', closeToBoard);
                            window.addEventListener('keydown', (e) => {{ if (e.code === 'Space' || e.code === 'Enter') closeToBoard(); }});
                        }}, 1000);
                        
                    }}, 50);
                }}, revealDelay);
            }};
        </script>
    </body>
    </html>
    """

def get_static_result_html(target_number, target_category, is_bingo=False):
    bg = "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)" if is_bingo else "linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%)"
    title = "🎉 BINGO แตกแล้ว! 🎉" if is_bingo else "ได้แก่..."
    title_color = "#fff" if is_bingo else "#FFD700"
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;700&display=swap');
            body {{ font-family: 'Kanit', sans-serif; background-color: transparent; color: white; display: flex; flex-direction: column; align-items: center; margin: 0; }}
            .result-container {{ text-align: center; padding: 40px 20px; background: {bg}; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.4); margin-top: 20px; width: 100%; max-width: 450px; }}
            .result-container h3 {{ margin: 0; font-size: 22px; color: {title_color}; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); }}
            .result-container h1 {{ margin: 15px 0; font-size: 32px; font-weight: 900; line-height: 1.3; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); padding: 0 10px; }}
        </style>
    </head>
    <body>
        <div class="result-container">
            <h3>{title}</h3>
            <h1>{target_category} ({target_number})</h1>
        </div>
    </body>
    </html>
    """

# ==========================================
# 4. สร้าง UI ของแอป
# ==========================================
# --- Sidebar สำหรับโชว์เคส / บังคับเอฟเฟกต์ ---
with st.sidebar:
    st.title("🛠️ ตั้งค่าการสุ่ม (Host)")
    st.write("เลือกเอฟเฟกต์วงล้อในรอบถัดไป:")
    
    effect_options = {
        "🎲 สุ่มอัตโนมัติ (ตามเรทกาชา)": -1,
        "0. ปกติเนียนๆ": 0,
        "1. สายสปีด (เร็วปรื๊ด)": 1,
        "2. เลยแล้วถอย (Bounce)": 2,
        "3. เบรกหัวทิ่ม (Slide)": 3,
        "4. แกล้งจะหลุด (Tease)": 4,
        "5. บั๊กกระตุก (Glitch)": 5,
        "6. ร่วงหล่น 1 ช่อง (Fake out)": 6,
        "7. ลูกศรขโมยซีนเกี่ยวลงมา": 7,
        "8. ลูกศรหนีไปชี้ช่องอื่น": 8,
        "9. ลูกศรหนี แต่ล้อตามไปง้อ": 9
    }
    
    selected_effect_name = st.selectbox("บังคับเอฟเฟกต์ (Showcase Mode)", list(effect_options.keys()))
    forced_effect_id = effect_options[selected_effect_name]
    
    st.markdown("---")
    st.markdown("💡 **Tip:** สามารถกด `Spacebar` แทนการใช้เมาส์คลิกปุ่มสุ่ม/ปุ่มปิดได้เลย")

st.title("🏆 Bingo 5x5: Mega Trolly Wheel Edition")
tab_play, tab_setup = st.tabs(["🎮 โหมดเล่นเกม", "⚙️ ตั้งค่ากระดาน (Host)"])

# ----------------- จัดเตรียมกระดาน -----------------
with tab_setup:
    st.header("1. ระบบจับคู่หมวดหมู่กับตัวเลข")
    
    # อัปโหลดไฟล์
    uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์หมวดหมู่ (.txt หรือ .csv คอลัมน์แรก)", type=['txt', 'csv'])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=None)
            st.session_state.raw_text_input = "\n".join(df[0].dropna().astype(str).tolist())
        else:
            st.session_state.raw_text_input = uploaded_file.getvalue().decode("utf-8")
            
    raw_cats = st.text_area("หรือพิมพ์รายชื่อหมวดหมู่ (บรรทัดละ 1 หมวด) แล้วกดปุ่มด้านล่าง", st.session_state.raw_text_input, height=150)
    
    if st.button("🔄 สุ่มจับคู่หมวดหมู่กับตัวเลข", type="primary"):
        cat_list = [c.strip() for c in raw_cats.split('\n') if c.strip()]
        if cat_list:
            random.shuffle(cat_list)
            st.session_state.categories_map = {str(i+1): cat for i, cat in enumerate(cat_list)}
            st.session_state.pool_numbers = list(st.session_state.categories_map.keys())
            st.success(f"✅ จับคู่สำเร็จทั้งหมด {len(cat_list)} หมวดหมู่! สามารถไปดูผลได้ในโหมดเล่นเกม")
            reset_game()
        else:
            st.error("กรุณาใส่ข้อมูลหมวดหมู่ก่อน!")
        
    st.markdown("---")
    st.header("2. กรอกตัวเลขลงกระดาน (เฉพาะตัวเลข)")
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        st.button("✨ สุ่มเติมเลขลงช่องว่าง", on_click=autofill_numbers, use_container_width=True)
    with col_btn2:
        st.button("🔄 ล้างกระดานใหม่ทั้งหมด", on_click=reset_game, type="secondary", use_container_width=True)

    st.write("")
    size = st.session_state.grid_size
    for r in range(size):
        cols = st.columns(size)
        for c in range(size):
            with cols[c]:
                st.text_input(f"R{r}C{c}", key=f"cell_{r}_{c}", label_visibility="collapsed", placeholder="-")

# ----------------- หน้าเล่นเกม -----------------
with tab_play:
    if not st.session_state.categories_map:
        st.warning("⚠️ กรุณาไปที่แท็บ 'ตั้งค่ากระดาน' เพื่อสุ่มจับคู่หมวดหมู่กับตัวเลขก่อนเริ่มเล่น")
        st.stop()

    if st.session_state.is_spinning:
        target = st.session_state.pending_target
        cat_name = st.session_state.categories_map.get(target, "")
        
        spin_overlay = st.empty()
        with spin_overlay:
            # ส่ง ID เอฟเฟกต์ที่เลือกจาก Sidebar เข้าไปใน HTML
            components.html(get_mega_wheel_html(target, cat_name, st.session_state.pool_numbers, forced_effect_id), height=700)
            
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔙 ข้าม / ปิดและกลับกระดาน (Spacebar)", use_container_width=True):
                st.session_state.drawn_numbers.append(st.session_state.pending_target)
                st.session_state.current_draw = st.session_state.pending_target
                st.session_state.pending_target = None
                st.session_state.is_spinning = False
                st.rerun()

    else:
        col_left, col_right = st.columns([1.5, 2.5], gap="large")
        
        with col_left:
            st.subheader("🎰 สุ่มบิงโก")
            
            valid_pool = [n for n in st.session_state.pool_numbers if n not in st.session_state.drawn_numbers]
            
            if st.button("🎯 กดเพื่อสุ่ม! (Spacebar)", use_container_width=True, type="primary"):
                if valid_pool:
                    st.session_state.pending_target = random.choice(valid_pool)
                    st.session_state.is_spinning = True
                    st.rerun() 
                else:
                    st.warning("สุ่มตัวเลขครบหมดแล้ว!")
            
            if st.session_state.current_draw:
                last_draw = st.session_state.current_draw
                cat_name = st.session_state.categories_map.get(last_draw, "")
                components.html(get_static_result_html(last_draw, cat_name, is_bingo=st.session_state.bingo_won), height=300)
            else:
                st.markdown("<div style='text-align:center; font-size: 24px; color: gray; padding: 40px; border: 3px dashed #555; border-radius: 15px; margin-top:20px;'>กดปุ่ม Spacebar เพื่อเริ่มสุ่ม</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.write(f"**ประวัติการออกหมายเลข ({len(st.session_state.drawn_numbers)}):**")
            if st.session_state.drawn_numbers:
                history_html = "".join([f"<span style='background:#333; color:#fff; border: 1px solid #555; padding:5px 10px; border-radius:15px; margin:2px; display:inline-block; font-weight:bold;'>{n}</span>" for n in st.session_state.drawn_numbers])
                st.markdown(history_html, unsafe_allow_html=True)

        with col_right:
            if check_bingo() and not st.session_state.bingo_won:
                st.session_state.bingo_won = True
                st.balloons()
                st.rerun()

            header_text = "🏆 กระดานบิงโกแตกแล้ว!" if st.session_state.bingo_won else "📋 กระดานของคุณ"
            st.subheader(header_text)
            st.markdown(generate_board_html(), unsafe_allow_html=True)

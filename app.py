import streamlit as st
import streamlit.components.v1 as components
import random
import time

st.set_page_config(page_title="Bingo Mega Wheel", layout="wide")

# ==========================================
# 0. ระบบคีย์ลัด (Keyboard Shortcuts)
# ==========================================
# ฝัง Javascript เข้าไปที่ Window หลัก เพื่อดักจับการกด Spacebar / Enter
def inject_keyboard_shortcuts():
    js = """
    <script>
    const doc = window.parent.document;
    if (!doc.getElementById('bingo-shortcuts')) {
        const script = doc.createElement('script');
        script.id = 'bingo-shortcuts';
        script.innerHTML = `
            document.addEventListener('keydown', function(e) {
                // เช็คว่ากด Spacebar หรือ Enter (และไม่ได้พิมพ์ช่อง Text อยู่)
                if ((e.code === 'Space' || e.code === 'Enter') && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    // วนหาปุ่ม Streamlit แล้วสั่งคลิก
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
# 3. โค้ด HTML วงล้อไซส์ยักษ์
# ==========================================
def get_mega_wheel_html(target_number, target_category, all_numbers):
    js_numbers = str(all_numbers) 
    
    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;700&display=swap');
            body {{ font-family: 'Kanit', sans-serif; background-color: transparent; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 95vh; margin: 0; overflow: hidden; cursor: pointer; }}
            .picker-container {{ position: relative; width: 450px; height: 400px; background: #1a1c23; border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.8); overflow: hidden; -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%); margin-bottom: 50px; }}
            .picker-overlay {{ position: absolute; top: 50%; left: 0; right: 0; height: 80px; transform: translateY(-50%); border-top: 3px solid #FF4B4B; border-bottom: 3px solid #FF4B4B; background: rgba(255, 75, 75, 0.1); pointer-events: none; z-index: 10; box-shadow: inset 0 0 15px rgba(255, 75, 75, 0.2); }}
            .picker-wheel {{ margin: 0; padding: 0; list-style: none; text-align: center; transform: translateY(160px); }}
            .picker-item {{ height: 80px; line-height: 80px; font-size: 64px; font-weight: bold; color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }}
            
            .result-container {{ display: none; opacity: 0; text-align: center; padding: 50px 30px; background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%); border-radius: 20px; box-shadow: 0 15px 30px rgba(255,75,43,0.5); transition: opacity 0.8s; width: 100%; max-width: 600px; }}
            .result-container h3 {{ margin: 0; font-size: 32px; color: #FFD700; }}
            .result-container h1 {{ margin: 20px 0; font-size: 72px; font-weight: 900; line-height: 1.1; text-shadow: 3px 3px 6px rgba(0,0,0,0.4); }}
            .result-container h2 {{ margin: 0; font-size: 36px; background: rgba(0,0,0,0.25); border-radius: 12px; padding: 15px; display: inline-block; }}
            
            .instruction {{ display: none; margin-top: 25px; font-size: 20px; color: #aaa; text-align: center; animation: pulse 1.5s infinite; }}
            @keyframes pulse {{ 0% {{ opacity: 0.5; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.5; }} }}
        </style>
    </head>
    <body>
        <audio id="spin-sound" src="https://actions.google.com/sounds/v1/foley/spinning_bicycle_wheel.ogg"></audio>
        <audio id="win-sound" src="https://actions.google.com/sounds/v1/fantasy/magic_chime.ogg"></audio>

        <div class="picker-container" id="picker">
            <div class="picker-overlay"></div>
            <ul class="picker-wheel" id="wheel"></ul>
        </div>

        <div class="result-container" id="result">
            <h3>ได้แก่หมวดหมู่...</h3>
            <h1 id="res-cat"></h1>
            <h2>( หมายเลข <span id="res-num"></span> )</h2>
            <div class="instruction" id="instruction">🖱️ คลิกหน้าจอ หรือ กด <b>Spacebar</b> เพื่อกลับไปที่กระดาน</div>
        </div>

        <script>
            const targetNumber = "{target_number}";
            const targetCategory = "{target_category}";
            const numbers = {js_numbers}; 
            const wheel = document.getElementById('wheel');
            const itemHeight = 80;
            const visibleCenterOffset = 160;

            const trackItems = [...numbers, ...numbers, ...numbers, ...numbers, ...numbers, ...numbers, ...numbers];
            const targetBaseIndex = numbers.indexOf(targetNumber);
            const finalTargetIndex = (numbers.length * 5) + targetBaseIndex;

            trackItems.forEach(num => {{
                const li = document.createElement('li');
                li.className = 'picker-item';
                li.innerText = num;
                wheel.appendChild(li);
            }});

            // ฟังก์ชันสั่ง Streamlit ให้กดปุ่มซ่อนล้อ
            function closeToBoard() {{
                const btns = window.parent.document.querySelectorAll('button');
                btns.forEach(b => {{
                    if (b.innerText.includes('กลับกระดาน')) b.click();
                }});
            }}

            window.onload = () => {{
                document.getElementById('spin-sound').play().catch(e => console.log(e));
                
                wheel.style.transition = 'none';
                wheel.style.transform = `translateY(${{visibleCenterOffset - (targetBaseIndex * itemHeight)}}px)`;
                wheel.offsetHeight; 
                
                const rand = Math.random() * 100;
                let effectType = 0;
                if (rand < 40) effectType = 0;      
                else if (rand < 55) effectType = 1; 
                else if (rand < 65) effectType = 2; 
                else if (rand < 75) effectType = 3; 
                else if (rand < 85) effectType = 4; 
                else if (rand < 90) effectType = 5; 
                else if (rand < 95) effectType = 6; 
                else effectType = 7;                
                
                const finalY = visibleCenterOffset - (finalTargetIndex * itemHeight);
                
                if (effectType === 0) {{ 
                    wheel.style.transition = 'transform 3.8s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{finalY}}px)`;
                }} 
                else if (effectType === 1) {{ 
                    wheel.style.transition = 'transform 1.8s cubic-bezier(0.2, 0.8, 0.2, 1)';
                    wheel.style.transform = `translateY(${{finalY}}px)`;
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
                    wheel.style.transition = 'transform 4.8s cubic-bezier(0.2, 0.95, 0.6, 1)';
                    wheel.style.transform = `translateY(${{finalY}}px)`;
                }}
                else if (effectType === 6) {{ 
                    const nearY = visibleCenterOffset - ((finalTargetIndex - 1) * itemHeight);
                    wheel.style.transition = 'transform 2.5s cubic-bezier(0.1, 0.8, 0.5, 1)';
                    wheel.style.transform = `translateY(${{nearY}}px)`;
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.1s linear'; wheel.style.transform = `translateY(${{visibleCenterOffset - ((finalTargetIndex + 1) * itemHeight)}}px)`; }}, 2600);
                    setTimeout(() => {{ wheel.style.transform = `translateY(${{visibleCenterOffset - ((finalTargetIndex - 2) * itemHeight)}}px)`; }}, 2750);
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.2s ease-out'; wheel.style.transform = `translateY(${{finalY}}px)`; }}, 2950);
                }}
                else if (effectType === 7) {{ 
                    const wrongY = visibleCenterOffset - ((finalTargetIndex - 1) * itemHeight);
                    wheel.style.transition = 'transform 2.8s cubic-bezier(0.1, 0.8, 0.1, 1)';
                    wheel.style.transform = `translateY(${{wrongY}}px)`;
                    setTimeout(() => {{ wheel.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)'; wheel.style.transform = `translateY(${{finalY}}px)`; }}, 4000);
                }}

                // แสดงผลลัพธ์หลังจบอนิเมชั่น (ประมาณ 5 วินาที)
                setTimeout(() => {{
                    document.getElementById('picker').style.display = 'none';
                    const res = document.getElementById('result');
                    res.style.display = 'block';
                    document.getElementById('res-cat').innerText = targetCategory;
                    document.getElementById('res-num').innerText = targetNumber;

                    setTimeout(() => {{
                        res.style.opacity = '1';
                        document.getElementById('win-sound').play().catch(e => console.log(e));
                        
                        // รออีก 1 วินาที ให้ข้อความ "คลิกเพื่อปิด" โผล่ขึ้นมา แล้วเปิดระบบรับคลิก
                        setTimeout(() => {{
                            document.getElementById('instruction').style.display = 'block';
                            window.addEventListener('click', closeToBoard);
                            window.addEventListener('keydown', (e) => {{
                                if (e.code === 'Space' || e.code === 'Enter') closeToBoard();
                            }});
                        }}, 1000);
                        
                    }}, 50);
                }}, 5200);
            }};
        </script>
    </body>
    </html>
    """

def get_static_result_html(target_number, target_category, is_bingo=False):
    bg = "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)" if is_bingo else "linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%)"
    title = "🎉 BINGO แตกแล้ว! 🎉" if is_bingo else "ได้แก่หมวดหมู่..."
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
            .result-container h1 {{ margin: 15px 0; font-size: 48px; font-weight: 900; line-height: 1.2; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
            .result-container h2 {{ margin: 0; font-size: 28px; background: rgba(0,0,0,0.2); border-radius: 10px; padding: 10px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="result-container">
            <h3>{title}</h3>
            <h1>{target_category}</h1>
            <h2>( หมายเลข <span>{target_number}</span> )</h2>
        </div>
    </body>
    </html>
    """

# ==========================================
# 4. สร้าง UI ของแอป
# ==========================================
st.title("🏆 Bingo 5x5: Mega Trolly Wheel Edition")

tab_play, tab_setup = st.tabs(["🎮 โหมดเล่นเกม", "⚙️ ตั้งค่ากระดาน (Host)"])

# ----------------- จัดเตรียมกระดาน -----------------
with tab_setup:
    st.header("1. ระบบจับคู่หมวดหมู่กับตัวเลข")
    default_cats = "\n".join([f"หมวดที่ {i}" for i in range(1, 51)])
    raw_cats = st.text_area("ป้อนรายชื่อหมวดหมู่ (บรรทัดละ 1 หมวด) แล้วกดปุ่มด้านล่าง ระบบจะสุ่มจับคู่กับเลขให้", default_cats, height=150)
    
    if st.button("🔄 สุ่มจับคู่หมวดหมู่กับตัวเลข", type="primary"):
        cat_list = [c.strip() for c in raw_cats.split('\n') if c.strip()]
        random.shuffle(cat_list)
        st.session_state.categories_map = {str(i+1): cat for i, cat in enumerate(cat_list)}
        st.session_state.pool_numbers = list(st.session_state.categories_map.keys())
        st.success(f"✅ จับคู่สำเร็จทั้งหมด {len(cat_list)} หมวดหมู่! สามารถไปดูผลได้ในโหมดเล่นเกม")
        reset_game()
        
    st.markdown("---")
    st.header("2. กรอกตัวเลขลงกระดาน (มีเฉพาะตัวเลข)")
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
        # === โหมดหมุนเต็มจอ (แบบรอกดปิดเอง) ===
        target = st.session_state.pending_target
        cat_name = st.session_state.categories_map.get(target, "")
        
        # เรนเดอร์ HTML วงล้อ (ซึ่งตัวมันเองมีระบบดักจับการคลิกอยู่ด้านใน)
        spin_overlay = st.empty()
        with spin_overlay:
            components.html(get_mega_wheel_html(target, cat_name, st.session_state.pool_numbers), height=700)
            
        # สร้างปุ่มสำหรับกดเพื่อปิดหน้าต่างนี้ (ปุ่มนี้จะถูก Javascript สั่งคลิกอัตโนมัติเมื่อกด Space/Click ที่ HTML)
        # หรือถ้ากด Spacebar รัวๆ ตอนหมุน มันจะทำงานเหมือนปุ่ม "ข้าม (Skip)" ครับ
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔙 ข้าม / ปิดและกลับกระดาน (Spacebar)", use_container_width=True):
                st.session_state.drawn_numbers.append(st.session_state.pending_target)
                st.session_state.current_draw = st.session_state.pending_target
                st.session_state.pending_target = None
                st.session_state.is_spinning = False
                st.rerun()

    else:
        # === โหมดปกติ (แสดงแผงสุ่มซ้าย กระดานขวา) ===
        col_left, col_right = st.columns([1.5, 2.5], gap="large")
        
        with col_left:
            st.subheader("🎰 สุ่มบิงโก")
            
            valid_pool = [n for n in st.session_state.pool_numbers if n not in st.session_state.drawn_numbers]
            
            # ปุ่มสุ่ม
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

import streamlit as st
import requests
import psutil
import platform
import os

# API Configuration
API_URL = "http://localhost:8000"

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Linux Lifesaver",
    page_icon="🐧",
    layout="wide"
)

# --- 2. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'specs' not in st.session_state: st.session_state.specs = {'ram': 8, 'cpu': '', 'storage': 'SSD', 'gpu': 'Intel Integrated'}
if 'recommendation' not in st.session_state: st.session_state.recommendation = None
if "chat_install" not in st.session_state: st.session_state.chat_install = []
if "chat_linux" not in st.session_state: st.session_state.chat_linux = []
if "theme" not in st.session_state: st.session_state.theme = "Dark (Neon)"
if "session_id" not in st.session_state: st.session_state.session_id = None

# --- 3. DYNAMIC THEMING + GLOBAL CSS ---
def apply_theme():
    is_light = st.session_state.theme == "Light"

    # Google Fonts import for monospace terminal font
    fonts_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
    </style>
    """
    st.markdown(fonts_css, unsafe_allow_html=True)

    if is_light:
        css = """
        <style>
            *, *::before, *::after { transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease; }
            .stApp { background-color: #f8fafc; color: #1e293b; }
            .logo-header {
                display: flex; align-items: center; justify-content: center; gap: 14px;
                padding: 20px 0 10px 0;
                border-bottom: 1px solid #e2e8f0;
                margin-bottom: 20px;
                position: relative;
            }
            .logo-header img { width: 48px; height: 48px; }
            .logo-header .logo-title {
                font-size: 28px; font-weight: 800; color: #1e293b;
                font-family: 'Inter', sans-serif; letter-spacing: -0.5px;
            }
            .logo-header .theme-toggle-area {
                position: absolute; right: 0; top: 50%; transform: translateY(-50%);
            }
            .main-card {
                background: #ffffff; border: 1px solid #e2e8f0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.06); color: #1e293b;
                border-radius: 12px; padding: 24px;
            }
            .chat-card {
                background: #ffffff; border: 1px solid #e2e8f0;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                border-radius: 12px; padding: 20px;
                max-width: 700px; margin: 20px auto;
            }
            .stButton>button { background: #3b82f6; color: white; border: none; border-radius: 8px; font-weight: 600; }
            .stButton>button:hover { background: #2563eb; }
            h1, h2, h3 { color: #0f172a; font-family: 'Inter', sans-serif; }
            p, span, label, .stMarkdown { color: #334155; }
            code, .stCode, pre { font-family: 'Fira Code', monospace !important; }
            .progress-step-active { color: #3b82f6; font-weight: 700; }
            .progress-step-inactive { color: #94a3b8; }
            section[data-testid="stSidebar"] { background: #f1f5f9; }
        </style>
        """
    else:
        css = """
        <style>
            *, *::before, *::after { transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease; }
            .stApp { background: linear-gradient(135deg, #0f172a, #020617); color: #e2e8f0; }
            .logo-header {
                display: flex; align-items: center; justify-content: center; gap: 14px;
                padding: 20px 0 10px 0;
                border-bottom: 2px solid #00ffff;
                margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(0,255,255,0.1);
                position: relative;
            }
            .logo-header img { width: 48px; height: 48px; filter: drop-shadow(0 0 6px rgba(0,255,255,0.5)); }
            .logo-header .logo-title {
                font-size: 28px; font-weight: 800; color: #00ffff;
                font-family: 'Inter', sans-serif; letter-spacing: -0.5px;
                text-shadow: 0 0 12px rgba(0,255,255,0.4);
            }
            .logo-header .theme-toggle-area {
                position: absolute; right: 0; top: 50%; transform: translateY(-50%);
            }
            .main-card {
                background: #1e293b; border: 2px solid #00ffff;
                box-shadow: 0 0 20px rgba(0,255,255,0.15); color: #e2e8f0;
                border-radius: 12px; padding: 24px;
            }
            .chat-card {
                background: #1e293b; border: 2px solid #00ffff;
                box-shadow: 0 0 20px rgba(0,255,255,0.15);
                border-radius: 12px; padding: 20px;
                max-width: 700px; margin: 20px auto;
            }
            .stButton>button { background: #00ffff; color: #0f172a; font-weight: bold; border: none; border-radius: 8px; box-shadow: 0 0 10px rgba(0,255,255,0.3); }
            .stButton>button:hover { background: #0ea5e9; color: white; }
            .stTextInput>div>div>input { color: #e2e8f0; background-color: #334155; }
            h1, h2, h3 { color: #e2e8f0; font-family: 'Inter', sans-serif; }
            code, .stCode, pre { font-family: 'Fira Code', monospace !important; }
            .progress-step-active { color: #00ffff; font-weight: 700; text-shadow: 0 0 8px rgba(0,255,255,0.4); }
            .progress-step-inactive { color: #475569; }
            section[data-testid="stSidebar"] { background: #0f172a; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

apply_theme()

# --- 4. TOP LOGO HEADER WITH THEME TOGGLE ---
def render_header():
    col_left, col_center, col_right = st.columns([1, 6, 1])
    with col_center:
        st.markdown("""
        <div class="logo-header">
            <img src="https://cdn-icons-png.flaticon.com/512/518/518713.png" alt="Linux Penguin">
            <span class="logo-title">Linux Lifesaver</span>
        </div>
        """, unsafe_allow_html=True)
    with col_right:
        toggle_text = "☀️ Light" if st.session_state.theme == "Dark (Neon)" else "🌙 Dark"
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button(toggle_text, key="theme_toggle"):
            st.session_state.theme = "Light" if st.session_state.theme == "Dark (Neon)" else "Dark (Neon)"
            st.rerun()

render_header()

# --- 6. API HELPERS ---
def get_recommendations(specs):
    try:
        response = requests.post(f"{API_URL}/recommend", json=specs)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        st.error("⚠️ Backend Offline. Run `uvicorn api:app --reload`")
        return []

def send_chat(message, context="general"):
    payload = {"message": message, "context": context, "session_id": st.session_state.session_id}
    try:
        response = requests.post(f"{API_URL}/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data["session_id"]
            return data["response"]
        return "Error from AI."
    except Exception:
        return "⚠️ Backend Offline."

# --- SYSTEM DETECTION ---
def detect_system_specs():
    """Auto-detect system specifications from Windows"""
    try:
        # Get RAM in GB
        ram_gb = int(psutil.virtual_memory().total / (1024**3))
        
        # Get CPU
        cpu = platform.processor() or "Unknown CPU"
        
        # Get Storage (primary drive)
        try:
            disk_usage = psutil.disk_usage('C:\\' if os.name == 'nt' else '/')
            storage_gb = int(disk_usage.total / (1024**3))
        except:
            storage_gb = 500  # Default fallback
        
        # Get GPU
        gpu = "Intel Integrated"  # Default
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0].name
        except:
            # Fallback: Check for NVIDIA/AMD via platform
            try:
                result = os.popen('wmic path win32_videocontroller get name').read() if os.name == 'nt' else ""
                if 'NVIDIA' in result:
                    gpu = "NVIDIA"
                elif 'AMD' in result or 'Radeon' in result:
                    gpu = "AMD"
            except:
                pass
        
        return ram_gb, cpu, storage_gb, gpu
    except Exception as e:
        st.warning(f"⚠️ Could not auto-detect specs: {e}")
        return 8, "Intel Core i5", 500, "Intel Integrated"

# --- 7. PROGRESS BAR ---
def render_progress():
    steps = ["Hardware", "Match & Details", "Installation", "Finish"]
    val = st.session_state.step / 4
    st.progress(val)
    cols = st.columns(4)
    for i, col in enumerate(cols):
        if i + 1 <= st.session_state.step:
            col.markdown(f'<div class="progress-step-active" style="text-align:center;">✅ {steps[i]}</div>', unsafe_allow_html=True)
        else:
            col.markdown(f'<div class="progress-step-inactive" style="text-align:center;">⚪ {steps[i]}</div>', unsafe_allow_html=True)

# --- 8. CENTERED CHATBOT ---
def render_chatbot():
    st.subheader("🤖 AI Assistant")
    tab_fix, tab_teach = st.tabs(["🛠 Install Fixer", "🎓 Linux Teacher"])

    with tab_fix:
        for role, msg in st.session_state.chat_install:
            with st.chat_message("user" if role == "user" else "assistant"):
                st.markdown(msg)
        if prompt := st.chat_input("Describe your install error...", key="install_chat"):
            st.session_state.chat_install.append(("user", prompt))
            reply = send_chat(prompt, "install")
            st.session_state.chat_install.append(("bot", reply))
            st.rerun()

    with tab_teach:
        for role, msg in st.session_state.chat_linux:
            with st.chat_message("user" if role == "user" else "assistant"):
                st.markdown(msg)
        if prompt2 := st.chat_input("Ask about Linux...", key="teacher_chat"):
            st.session_state.chat_linux.append(("user", prompt2))
            reply = send_chat(prompt2, "general")
            st.session_state.chat_linux.append(("bot", reply))
            st.rerun()

# --- 9. MAIN CONTENT ---
render_progress()

if st.session_state.step == 1:
    st.header("Stage 1: Hardware Specs")
    
    # Auto-detect button
    if st.button("🖥️ Configure System", key="configure_btn"):
        ram, cpu, storage_gb, gpu = detect_system_specs()
        st.session_state.specs = {'ram': ram, 'cpu': cpu, 'storage': 'SSD', 'gpu': gpu}
        st.success(f"✅ Detected: {ram}GB RAM | CPU: {cpu} | Storage: {storage_gb}GB | GPU: {gpu}")
    
    st.write("")
    
    c1, c2 = st.columns(2)
    with c1:
        ram = st.number_input("RAM (GB)", 1, 128, st.session_state.specs.get('ram', 8))
        cpu = st.text_input("CPU", st.session_state.specs.get('cpu', 'Intel Core i5'))
    with c2:
        storage = st.selectbox("Storage", ["SSD", "HDD"], index=0 if st.session_state.specs.get('storage') == 'SSD' else 1)
        gpu = st.selectbox("GPU", ["Intel Integrated", "NVIDIA", "AMD"], index=["Intel Integrated", "NVIDIA", "AMD"].index(st.session_state.specs.get('gpu', 'Intel Integrated')))

    st.write("")
    if st.button("🔍 Check Compatibility"):
        st.session_state.specs = {'ram': ram, 'cpu': cpu, 'storage': storage, 'gpu': gpu}
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header("Stage 2: Your Match")
    distros = get_recommendations(st.session_state.specs)

    if distros:
        st.success(f"We found {len(distros)} distros for your {st.session_state.specs['ram']}GB RAM system!")

        names = [d['name'] for d in distros]
        choice = st.selectbox("Select a Distro to Preview", names)
        selected_distro = next(d for d in distros if d['name'] == choice)

        st.markdown(f"""
        <div class="main-card" style="text-align: center;">
            <h2 style="margin:0;">{selected_distro['name']}</h2>
            <p>{selected_distro['desc']}</p>
            <p style="font-size: 0.85em; opacity: 0.7;">Min RAM: {selected_distro['min_ram']}GB | Optimized for: {selected_distro['gpu']}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ Proceed with this Distro"):
            st.session_state.recommendation = selected_distro
            st.session_state.step = 3
            st.rerun()
    else:
        st.error("No distros found via API. Check connection.")

elif st.session_state.step == 3:
    d = st.session_state.recommendation
    st.header(f"Stage 3: {d['name']} Details")
    t1, t2, t3 = st.tabs(["📥 Download", "💾 Flash", "🖥️ Install"])

    with t1:
        st.info("Download the official ISO.")
        st.link_button("Download ISO", d['iso_url'])
    with t2:
        st.info("Flash to USB using Etcher.")
        st.link_button("Get Etcher", "https://etcher.balena.io/")
    with t3:
        st.write("Reboot and press F12 for Boot Menu.")
        if st.button("✅ Installation Done"):
            st.session_state.step = 4
            st.rerun()

elif st.session_state.step == 4:
    st.balloons()
    st.header("🎉 Mission Accomplished!")
    st.success("You have successfully installed Linux!")
    if st.button("🔄 Start Over"):
        st.session_state.step = 1
        st.rerun()

# --- 10. CHATBOT (centered in main area, below content) ---
st.markdown("---")
render_chatbot()
import streamlit as st

def apply_enterprise_css():
    custom_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #E2E8F0;
        }

        /* --- 1. THE LIVING BACKGROUND --- */
        .stApp {
            background: linear-gradient(-45deg, #0B0F19, #111827, #0B0F19, #0f172a);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }
        
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        footer {visibility: hidden;}

        /* --- 2. ADVANCED BUTTONS --- */
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #00E5FF 0%, #0072FF 100%);
            color: white !important;
            border: none;
            border-radius: 12px;
            padding: 12px 28px;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3);
        }
        button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 10px 25px rgba(0, 229, 255, 0.6);
        }

        /* --- 3. ANIMATED NEON TEXT --- */
        .shimmer-text {
            background: linear-gradient(to right, #00C6FF, #b829ea, #00C6FF);
            background-size: 200% auto;
            color: #000;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shine 4s linear infinite;
            font-weight: 800;
            font-size: 3.5rem;
            margin-bottom: 0px;
        }
        @keyframes shine { to { background-position: 200% center; } }

        /* --- 4. SECTION HEADERS --- */
        .section-header {
            color: #94A3B8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            margin-top: 45px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 8px;
        }

        /* --- 5. LIVE TELEMETRY ROW --- */
        .telemetry-row {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .tel-card {
            flex: 1;
            min-width: 150px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        .tel-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.2rem;
            font-weight: 700;
            color: #00E5FF;
            margin-bottom: 5px;
            text-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
        }
        .tel-label {
            font-size: 0.85rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* --- 6. DEFECT TYPOLOGY GRID --- */
        .typology-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }
        .typ-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        .typ-card:hover {
            transform: translateY(-6px);
            background: rgba(255, 255, 255, 0.05);
            border-color: #00E5FF;
            box-shadow: 0 10px 30px rgba(0, 229, 255, 0.15);
        }
        .typ-icon { font-size: 2.2rem; margin-bottom: 12px; }
        .typ-title { color: #E2E8F0; font-weight: 600; font-size: 1.1rem; margin-bottom: 8px; }
        .typ-desc { color: #64748B; font-size: 0.9rem; line-height: 1.5; }
        
        /* Status Dot */
        .status-dot {
            height: 12px; width: 12px; background-color: #10B981; border-radius: 50%;
            display: inline-block; box-shadow: 0 0 10px #10B981; animation: pulse-green 2s infinite; margin-right: 8px;
        }
        @keyframes pulse-green {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        /* --- 7. IMAGE COMPARISON SECTION --- */
        .comparison-container {
            display: flex;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .img-box {
            flex: 1;
            min-width: 300px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 15px;
            transition: all 0.3s ease;
        }
        .img-box:hover {
            border-color: #00E5FF;
            box-shadow: 0 10px 30px rgba(0, 229, 255, 0.1);
        }
        .img-label {
            color: #00E5FF;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            margin-bottom: 12px;
            text-align: center;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .demo-img {
            width: 100%;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1);
            background-color: #1E232F; /* Fallback if image fails to load */
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
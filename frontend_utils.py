import streamlit as st

def apply_enterprise_css():
    custom_css = """
    <style>
        /* IMPORT PREMIUM FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #E2E8F0;
        }

        /* --- 1. THE LIVING BACKGROUND --- */
        /* Creates a slow-moving, multi-color gradient background */
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

        /* Hide the bottom watermark only */
        footer {visibility: hidden;}

        /* --- 2. ADVANCED STREAMLIT BUTTON OVERRIDES --- */
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
        @keyframes shine {
            to { background-position: 200% center; }
        }

        /* --- 4. GLASSMORPHISM CARDS (RAW HTML STYLING) --- */
        /* Frosted glass effect for our custom HTML cards */
        .glass-container {
            display: flex;
            gap: 20px;
            margin-top: 30px;
            flex-wrap: wrap;
        }
        .glass-card {
            flex: 1;
            min-width: 250px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 25px;
            transition: all 0.4s ease;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        .glass-card:hover {
            transform: translateY(-10px);
            border: 1px solid #00E5FF;
            box-shadow: 0 10px 30px rgba(0, 229, 255, 0.2);
            background: rgba(255, 255, 255, 0.05);
        }
        .glass-card h3 {
            color: #00E5FF;
            margin-top: 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.2rem;
        }
        .glass-card p {
            color: #94A3B8;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        /* --- 5. PULSING STATUS INDICATOR --- */
        .status-dot {
            height: 12px;
            width: 12px;
            background-color: #10B981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 10px #10B981;
            animation: pulse-green 2s infinite;
            margin-right: 8px;
        }
        @keyframes pulse-green {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
"""
streamlit_config.py
Configurações de tema e estilo para o dashboard Streamlit
"""

import streamlit as st


def apply_motorsport_theme():
    """
    Aplica tema 'Motorsport Pro' ao dashboard.
    Cores neon, fundo dark carbon, tipografia agressiva.
    """
    st.markdown("""
    <style>
    /* ─────────────────────────────────────────────────────────────────── */
    /* PALETA MOTORSPORT                                                   */
    /* ─────────────────────────────────────────────────────────────────── */
    :root {
        --color-primary: #00D9FF;
        --color-accent: #FF0080;
        --color-success: #00FF41;
        --color-warning: #FFB300;
        --color-danger: #FF0000;
        --color-bg-dark: #0A0E27;
        --color-bg-card: #1A1F3A;
        --color-text-primary: #E0E0E0;
        --color-text-secondary: #888888;
    }

    body {
        background-color: var(--color-bg-dark);
        color: var(--color-text-primary);
        font-family: 'Monaco', 'Courier New', monospace;
    }

    .stApp {
        background-color: var(--color-bg-dark);
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--color-bg-dark);
    }

    h1 {
        color: var(--color-primary);
        font-size: 2.8em;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
        margin-bottom: 5px;
    }

    h2 {
        color: var(--color-primary);
        font-size: 1.6em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 2px solid var(--color-accent);
        padding-bottom: 10px;
    }

    h3 {
        color: var(--color-warning);
        font-size: 1.2em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="metric-container"] {
        background-color: var(--color-bg-card);
        border-left: 4px solid var(--color-primary);
        border-radius: 0;
        padding: 15px;
        box-shadow: inset 0 0 20px rgba(0, 217, 255, 0.05),
                    0 0 15px rgba(0, 217, 255, 0.1);
        animation: slide-in 0.5s ease-out;
    }

    [data-testid="metric-container"]:hover {
        box-shadow: inset 0 0 20px rgba(0, 217, 255, 0.1),
                    0 0 25px rgba(0, 217, 255, 0.2);
    }

    [data-testid="stMetricLabel"] {
        color: var(--color-text-secondary) !important;
        font-size: 0.85em;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: var(--color-primary) !important;
        font-size: 2.2em;
        font-weight: 900;
        text-shadow: 0 0 10px rgba(0, 217, 255, 0.3);
    }

    .plotly-graph-div {
        border: 1px solid rgba(0, 217, 255, 0.2);
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.05);
    }

    .streamlit-expanderHeader {
        background-color: var(--color-bg-card);
        border-left: 4px solid var(--color-warning);
        color: var(--color-primary);
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .streamlit-expanderHeader:hover {
        background-color: rgba(0, 217, 255, 0.05);
        border-left-color: var(--color-accent);
    }

    [data-testid="stSidebar"] {
        background-color: var(--color-bg-card);
        border-right: 2px solid var(--color-primary);
    }

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg,
            rgba(0, 217, 255, 0) 0%,
            rgba(0, 217, 255, 0.4) 50%,
            rgba(0, 217, 255, 0) 100%);
        margin: 20px 0;
    }

    .stButton > button {
        background-color: var(--color-accent);
        color: white;
        border: none;
        border-radius: 0;
        padding: 10px 20px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
        box-shadow: 0 0 15px rgba(255, 0, 128, 0.2);
    }

    .stButton > button:hover {
        background-color: var(--color-primary);
        box-shadow: 0 0 25px rgba(0, 217, 255, 0.4);
        transform: scale(1.02);
    }

    .stSuccess {
        background-color: rgba(0, 255, 65, 0.1) !important;
        border-left: 4px solid var(--color-success) !important;
    }

    .stWarning {
        background-color: rgba(255, 179, 0, 0.1) !important;
        border-left: 4px solid var(--color-warning) !important;
    }

    .stError {
        background-color: rgba(255, 0, 0, 0.1) !important;
        border-left: 4px solid var(--color-danger) !important;
    }

    .stInfo {
        background-color: rgba(0, 217, 255, 0.08) !important;
        border-left: 4px solid var(--color-primary) !important;
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--color-bg-dark); }
    ::-webkit-scrollbar-thumb { background: var(--color-primary); border-radius: 0; }
    ::-webkit-scrollbar-thumb:hover { background: var(--color-accent); }

    @keyframes glow-pulse {
        0%, 100% { text-shadow: 0 0 10px rgba(0, 217, 255, 0.5); }
        50%       { text-shadow: 0 0 20px rgba(0, 217, 255, 1.0); }
    }

    @keyframes slide-in {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .glow { animation: glow-pulse 2s infinite; }
    </style>
    """, unsafe_allow_html=True)


def create_metric_card(label: str, value: str, icon: str = "") -> None:
    """
    Renderiza um card de métrica com estilo Motorsport via HTML.

    Args:
        label: Texto do label
        value: Valor a exibir
        icon: Emoji ou ícone
    """
    st.markdown(f"""
    <div style="
        background-color: #1A1F3A;
        border-left: 4px solid #00D9FF;
        padding: 15px 20px;
        margin: 8px 0;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.1);
    ">
        <div style="color: #888888; font-size: 0.8em; text-transform: uppercase;
                    letter-spacing: 1px; font-weight: 600;">{icon} {label}</div>
        <div style="color: #00D9FF; font-size: 2em; font-weight: 900;
                    text-shadow: 0 0 10px rgba(0,217,255,0.3); margin-top: 4px;">
            {value}
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_section_header(title: str, subtitle: str = "") -> None:
    """
    Renderiza um header de seção com estilo Motorsport.

    Args:
        title: Título principal
        subtitle: Subtítulo opcional
    """
    sub_html = f'<p style="color:#888888; margin:5px 0 0 0; font-size:0.9em;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="border-bottom: 2px solid #FF0080; padding-bottom: 10px; margin-bottom: 20px;">
        <h2 style="color:#00D9FF; margin:0; text-transform:uppercase;
                   letter-spacing:1px; font-size:1.4em;">{title}</h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

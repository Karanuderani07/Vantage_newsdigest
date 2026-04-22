import os
import time
import threading
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# ── 1. Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="Vantage | Editorial AI",
    page_icon="⚖️",
    layout="wide",
)

# ── 2. Load Environment ───────────────────────────────────────
load_dotenv()

# ── 3. Imports ───────────────────────────────────────────────
from main import run, build_graph
from state import AgentState
from utils import get_client

# ── 4. Elegant Editorial UI ───────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;1,600&family=Inter:wght@300;400;600&display=swap');

    /* Global Aesthetic: Quiet Luxury */
    .stApp { 
        background-color: #0f1011; 
        color: #d1d1d1; 
        font-family: 'Inter', sans-serif; 
    }

    /* Elegant Serif Titles */
    .main-title {
        font-family: 'Crimson Pro', serif;
        font-weight: 400;
        font-size: 4.5rem;
        letter-spacing: -1px;
        margin-bottom: 0px;
        color: #f5f5f5;
        text-align: center;
    }
    
    .subtitle {
        text-align: center;
        color: #8a8a8a;
        font-size: 0.9rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 50px;
    }

    /* Minimalist Search Bar */
    .stTextInput input {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #333 !important;
        color: #ffffff !important;
        border-radius: 0px !important;
        padding: 15px 0px !important;
        font-size: 1.2rem !important;
        transition: border-color 0.4s ease;
    }
    .stTextInput input:focus {
        border-bottom: 1px solid #c5a059 !important; /* Champagne Gold */
        box-shadow: none !important;
    }

    /* The 'Execute' Button: Subtle & Refined */
    .stButton>button[kind="primary"] {
        background: #c5a059 !important;
        color: #0f1011 !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        height: 50px !important;
        width: 100%;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton>button[kind="primary"]:hover {
        background: #e2c285 !important;
        transform: translateY(-1px);
    }

    /* Sample Tags: Editorial Style */
    .stButton>button[kind="secondary"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #8a8a8a !important;
        border-radius: 2px !important;
        font-size: 0.75rem !important;
        padding: 5px 15px !important;
    }

    /* Content Containers: Soft Glass */
    .digest-box, .stTabs, div[data-testid="stExpander"] {
        background: #161719 !important;
        border: 1px solid #242528 !important;
        border-radius: 8px !important;
        padding: 30px !important;
    }

    /* Metrics: Classy Serif */
    div[data-testid="stMetricValue"] {
        color: #f5f5f5 !important;
        font-family: 'Crimson Pro', serif;
        font-size: 2.2rem !important;
    }

    /* Typography for Digest */
    .digest-text {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        line-height: 1.9;
        color: #bcbcbc;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ── 5. Header ─────────────────────────────────────────────────
st.markdown("<h1 class='main-title'>Vantage</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>The Intelligent Briefing Engine</p>", unsafe_allow_html=True)

# ── 6. Control Center ───────────────────────────────────
with st.container():
    col_empty_left, col_input, col_btn, col_empty_right = st.columns([1, 4, 1.2, 1])
    with col_input:
        topic = st.text_input(
            "Research Topic",
            value="", 
            label_visibility="collapsed",
            placeholder="Enter topic for research...",
        )
    with col_btn:
        generate = st.button("GENERATE", use_container_width=True, type="primary")

# Sample Popular Topics Section
st.markdown("<p style='text-align:center; color:#555; font-size:0.7rem; letter-spacing:2px; margin-top:20px;'>SUGGESTED CHANNELS</p>", unsafe_allow_html=True)
_, q_col, _ = st.columns([1, 6, 1])
with q_col:
    quick_topics = ["Global AI Regulation", "The Semiconductor Race", "Space Economy 2026", "Climate Tech"]
    quick_cols = st.columns(len(quick_topics))
    for i, qt in enumerate(quick_topics):
        if quick_cols[i].button(qt, key=f"qt_{i}", use_container_width=True):
            topic = qt
            generate = True

st.markdown("<br><br>", unsafe_allow_html=True)

# ── 7. Detailed Pipeline Execution ────────────────────────────
if generate and topic.strip():
    if "state" in st.session_state: del st.session_state["state"]

    GROQ_KEY = os.getenv("GROQ_API_KEY")
    NEWS_KEY = os.getenv("NEWS_API_KEY")

    if not GROQ_KEY or not NEWS_KEY:
        st.error("Protocol Error: Access Keys Missing.")
        st.stop()

    with st.status("🖋️ Planning Executive Briefing...", expanded=True) as status:
        try:
            st.write("Initializing generative planning agents...")
            get_client(GROQ_KEY)
            
            st.write("Compiling multi-agent graph architecture...")
            fresh_graph = build_graph(NEWS_KEY)
            
            initial_reset = {
                "topic": topic, "plan": [], "raw_articles": [],
                "filtered_articles": [], "clusters": [], "cluster_labels": [],
                "cluster_summaries": [], "digest": "", "sources": [], 
                "quality_score": 0, "quality_passed": True, 
                "quality_issues": [], "logs": [],
            }
            
            st.write(f"Agent is researching current vectors for: **{topic}**")
            start = time.time()
            
            # Agent Task
            final_output = fresh_graph.invoke(initial_reset)
            
            st.write("Finalizing editorial structure and source verification...")
            elapsed_time = time.time() - start
            
            st.session_state["state"] = final_output
            st.session_state["elapsed"] = elapsed_time
            status.update(label="✔ Briefing Complete", state="complete", expanded=False)
            
        except Exception as e:
            st.error(f"Execution Error: {str(e)}")
            st.stop()

# ── 8. Results Dashboard ──────────────────────────────────────
if "state" in st.session_state:
    state = st.session_state["state"]
    elapsed = st.session_state["elapsed"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Verified Nodes", len(state.get("sources", [])))
    m2.metric("Intel Integrity", f"{state.get('quality_score', 0)}/10")
    m3.metric("Key Clusters", len(state.get("clusters", [])))
    m4.metric("Latency", f"{elapsed:.1f}s")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_digest, tab_intel, tab_audit = st.tabs(["EXECUTIVE BRIEFING", "SOURCE ANALYTICS", "AGENT MANIFEST"])

    with tab_digest:
        if state.get("digest"):
            st.markdown(f'<div class="digest-box digest-text">{state["digest"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        else:
            st.info("The agent was unable to synthesize a digest for this query.")

    with tab_intel:
        clusters = state.get("clusters", [])
        labels = state.get("cluster_labels", [])
        for i, (cluster, label) in enumerate(zip(clusters, labels), 1):
            with st.expander(f"0{i} — {label.upper()}", expanded=(i == 1)):
                for art in cluster:
                    st.markdown(f"<span style='color:#c5a059;'>◈</span> **{art['title']}**", unsafe_allow_html=True)
                    st.caption(f"{art['source']} | {art['published'][:10]}")
                    if art.get("url"): st.markdown(f"[Official Source]({art['url']})")
                    st.divider()

    with tab_audit:
        for log in state.get("logs", []):
            st.text(f"log.std_out >> {log}")

# ── 9. Footer ─────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; color: #333; font-size: 0.7rem; border-top: 1px solid #222; padding-top: 30px; letter-spacing: 2px;">
        VANTAGE EDITORIAL ENGINE // DEVELOPED BY KARAN UDERANI & VARUN SHIVANIKAR
    </div>
""", unsafe_allow_html=True)
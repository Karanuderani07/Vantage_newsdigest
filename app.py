import os
import time
import threading
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

# ── 1. Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="Vantage | Editorial AI",
    page_icon="⚖️",
    layout="wide",
)

# ── 2. Load Environment & Keys ─────────────────────────────────
load_dotenv()

def get_key(name):
    try:
        return st.secrets[name]   # Streamlit Cloud
    except Exception:
        return os.getenv(name)    # Local fallback

GROQ_KEY = get_key("GROQ_API_KEY")
NEWS_KEY = get_key("NEWS_API_KEY")

# ── 3. Imports ───────────────────────────────────────────────
from main import run, build_graph
from state import AgentState
from utils import get_client

# ── 4. Modern Vibrant Blue UI ────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');

    /* Global Aesthetic: Modern Vibrant */
    .stApp { 
        background: linear-gradient(135deg, #0a0e27 0%, #0f1626 50%, #0a1f3b 100%) !important;
        color: #e0e0ff; 
        font-family: 'Poppins', sans-serif; 
    }

    /* Modern Title */
    .main-title {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 4.2rem;
        letter-spacing: -2px;
        margin-bottom: 0px;
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 50%, #6b5fff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.3));
    }
    
    .subtitle {
        text-align: center;
        background: linear-gradient(90deg, #00d4ff, #00f7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 50px;
        font-weight: 600;
    }

    /* Modern Search Bar */
    .stTextInput input {
        background: rgba(30, 80, 130, 0.2) !important;
        border: 2px solid rgba(0, 212, 255, 0.3) !important;
        color: #e0e0ff !important;
        border-radius: 12px !important;
        padding: 14px 16px !important;
        font-size: 1.1rem !important;
        transition: all 0.4s ease !important;
        backdrop-filter: blur(10px) !important;
    }
    .stTextInput input::placeholder {
        color: #6b7c9f !important;
    }
    .stTextInput input:focus {
        border: 2px solid #00d4ff !important;
        background: rgba(0, 212, 255, 0.1) !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important;
    }

    /* Glowing Primary Button */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%) !important;
        color: #0a0e27 !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 50px !important;
        width: 100% !important;
        letter-spacing: 1.5px;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important;
        font-family: 'Poppins', sans-serif !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, #00f7ff 0%, #00ccff 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 30px rgba(0, 212, 255, 0.6) !important;
    }

    /* Quick Topic Buttons */
    .stButton>button[kind="secondary"] {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(107, 95, 255, 0.1)) !important;
        border: 2px solid rgba(0, 212, 255, 0.3) !important;
        color: #00d4ff !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button[kind="secondary"]:hover {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(107, 95, 255, 0.2)) !important;
        border: 2px solid #00d4ff !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
    }

    /* Content Containers */
    .stTabs, div[data-testid="stExpander"] {
        background: linear-gradient(135deg, rgba(30, 80, 130, 0.15), rgba(75, 40, 150, 0.1)) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 25px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Section Cards */
    .section-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(107, 95, 255, 0.08)) !important;
        border: 2px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px;
        padding: 25px;
        margin: 15px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
    }

    .section-title {
        font-family: 'Poppins', sans-serif;
        font-size: 1.9rem;
        background: linear-gradient(135deg, #00d4ff, #0099ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 15px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .section-subtitle {
        color: #00d4ff;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 15px;
        font-weight: 600;
    }

    .insight-box {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(107, 95, 255, 0.05)) !important;
        border: 2px solid rgba(0, 212, 255, 0.4) !important;
        border-radius: 10px;
        padding: 16px;
        margin: 12px 0;
        border-left: 5px solid #00d4ff;
        backdrop-filter: blur(5px);
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(107, 95, 255, 0.1)) !important;
        border: 2px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border: 2px solid rgba(0, 212, 255, 0.6) !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        transform: translateY(-5px);
    }

    .metric-value {
        font-family: 'Poppins', sans-serif;
        font-size: 2.5rem;
        background: linear-gradient(135deg, #00d4ff, #0099ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }

    .metric-label {
        color: #00d4ff;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 8px;
        font-weight: 600;
    }

    /* Typography for Digest */
    .digest-text {
        font-family: 'Poppins', sans-serif;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #d0d0e0;
    }

    .article-item {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(107, 95, 255, 0.05)) !important;
        border-left: 4px solid #00d4ff;
        padding: 16px;
        margin: 12px 0;
        border-radius: 8px;
        border: 1px solid rgba(0, 212, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .article-item:hover {
        border-left: 4px solid #00f7ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
        transform: translateX(5px);
    }

    .cluster-badge {
        display: inline-block;
        background: linear-gradient(135deg, #00d4ff, #0099ff);
        color: #0a0e27;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 8px;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }

    .tab-divider {
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
        height: 1px;
        margin: 20px 0;
    }

    div[data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
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
st.markdown("<p style='text-align:center; color:#00d4ff; font-size:0.75rem; letter-spacing:3px; margin-top:30px; font-weight: 600; text-transform: uppercase;'>✨ EXPLORE TRENDING TOPICS</p>", unsafe_allow_html=True)
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
    if "state" in st.session_state: 
        del st.session_state["state"]

    if not GROQ_KEY or not NEWS_KEY:
        st.error("Protocol Error: Access Keys Missing.")
        st.stop()

    if not GROQ_KEY or not NEWS_KEY:
        st.error("Protocol Error: Access Keys Missing.")
        st.stop()

    with st.status("🖋️ Planning Executive Briefing...", expanded=True) as status:
        try:
            st.write("🌐 Initializing generative planning agents...")
            get_client(GROQ_KEY)
            
            st.write("🔗 Compiling multi-agent graph architecture...")
            fresh_graph = build_graph(NEWS_KEY)
            
            initial_reset = {
                "topic": topic, "plan": [], "raw_articles": [],
                "filtered_articles": [], "clusters": [], "cluster_labels": [],
                "cluster_summaries": [], "digest": "", "sources": [], 
                "quality_score": 0, "quality_passed": True, 
                "quality_issues": [], "logs": [],
            }
            
            st.write(f"✨ Agent is researching current vectors for: **{topic}**")
            start = time.time()
            
            # Agent Task
            final_output = fresh_graph.invoke(initial_reset)
            
            st.write("📋 Finalizing editorial structure and source verification...")
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

    # Enhanced Metrics Row with Glow Effect
    st.markdown("""
    <div style='text-align:center; margin: 40px 0 30px 0;'>
        <h2 style='background: linear-gradient(135deg, #00d4ff, #0099ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 2.2rem; letter-spacing: 2px;'>📊 INTELLIGENCE SUMMARY</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        sources_count = len(state.get("sources", []))
        st.markdown(f"""
        <div class="metric-card">
            <div style='font-size: 2.8rem; margin-bottom: 8px;'>🌐</div>
            <div class="metric-value">{sources_count}</div>
            <div class="metric-label">Verified Sources</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        quality_score = state.get('quality_score', 0)
        quality_bar = "█" * quality_score + "░" * (10 - quality_score)
        st.markdown(f"""
        <div class="metric-card">
            <div style='font-size: 2.8rem; margin-bottom: 8px;'>⭐</div>
            <div class="metric-value">{quality_score}/10</div>
            <div class="metric-label">Insight Quality</div>
            <div style='font-size: 0.75rem; margin-top: 8px; color: #00d4ff;'>{quality_bar}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        clusters_count = len(state.get("clusters", []))
        st.markdown(f"""
        <div class="metric-card">
            <div style='font-size: 2.8rem; margin-bottom: 8px;'>🔗</div>
            <div class="metric-value">{clusters_count}</div>
            <div class="metric-label">Key Clusters</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style='font-size: 2.8rem; margin-bottom: 8px;'>⚡</div>
            <div class="metric-value">{elapsed:.1f}s</div>
            <div class="metric-label">Generation Time</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='tab-divider'></div>", unsafe_allow_html=True)

    # Main Tabs with Better Organization
    tab_overview, tab_briefing, tab_analysis, tab_sources, tab_audit = st.tabs([
        "📈 OVERVIEW",
        "📋 BRIEFING", 
        "🔬 ANALYSIS", 
        "📰 SOURCES", 
        "⚙️ LOGS"
    ])

    with tab_overview:
        st.markdown("### 📊 Research Overview")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("#### Topic Details")
            st.markdown(f"""
            <div class="insight-box">
                <strong>Research Topic:</strong><br>{state.get('topic', 'N/A')}<br><br>
                <strong>Generation Time:</strong><br>{elapsed:.2f} seconds<br><br>
                <strong>Status:</strong><br>✅ Complete
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            st.markdown("#### Data Collected")
            st.markdown(f"""
            <div class="insight-box">
                <strong>Total Articles:</strong><br>{len(state.get('raw_articles', []))} raw articles<br><br>
                <strong>Clusters Found:</strong><br>{clusters_count} thematic groups<br><br>
                <strong>Sources:</strong><br>{sources_count} verified sources
            </div>
            """, unsafe_allow_html=True)
        
        # Quick stats
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📈 Cluster Distribution")
        
        clusters = state.get("clusters", [])
        if clusters:
            cluster_sizes = [len(c) for c in clusters]
            labels = state.get("cluster_labels", [])
            
            # Create a nice chart
            df = pd.DataFrame({
                'Cluster': [f"{i+1}. {label[:20]}..." for i, label in enumerate(labels)],
                'Articles': cluster_sizes
            })
            st.bar_chart(df.set_index('Cluster')['Articles'], use_container_width=True)
        else:
            st.info("No cluster data available")

    with tab_briefing:
        st.markdown("### 📋 Executive Briefing")
        
        if state.get("digest"):
            digest_text = state["digest"]
            st.markdown(f'<div class="digest-text">{digest_text}</div>', unsafe_allow_html=True)
            
            col_exp_left, col_exp_right = st.columns([3, 1])
            with col_exp_right:
                if st.button("📥 Export Text", use_container_width=True, key="export_btn"):
                    st.info("✅ Copy the text below:")
                    st.text_area("Briefing Text", value=digest_text, height=200, disabled=True)
        else:
            st.info("The agent was unable to synthesize a digest for this query.")

    with tab_analysis:
        st.markdown("### 🔬 Cluster Analysis")
        
        clusters = state.get("clusters", [])
        labels = state.get("cluster_labels", [])
        
        if not clusters:
            st.info("No cluster data available.")
        else:
            # Cluster Distribution Visualization
            cluster_sizes = [len(c) for c in clusters]
            
            col_chart, col_stats = st.columns([2, 1])
            
            with col_chart:
                st.markdown("#### 📊 Article Distribution")
                import pandas as pd
                df = pd.DataFrame({
                    'Cluster': [f"{i+1}. {label[:18]}..." for i, label in enumerate(labels)],
                    'Count': cluster_sizes
                })
                st.bar_chart(df.set_index('Cluster')['Count'], use_container_width=True)
            
            with col_stats:
                st.markdown("#### 📈 Statistics")
                st.markdown(f"""
                <div class="insight-box">
                    <strong>📊 Total:</strong><br>{sum(cluster_sizes)} articles<br><br>
                    <strong>📌 Largest:</strong><br>{max(cluster_sizes) if cluster_sizes else 0} articles<br><br>
                    <strong>📐 Average:</strong><br>{sum(cluster_sizes)//len(cluster_sizes) if cluster_sizes else 0} per cluster
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div class='tab-divider'></div>", unsafe_allow_html=True)
            
            # Detailed Cluster Views
            st.markdown("#### 🏷️ Thematic Breakdown")
            for i, (cluster, label) in enumerate(zip(clusters, labels), 1):
                with st.expander(f"🏷️ **Cluster {i}: {label}** ({len(cluster)} articles)", expanded=(i == 1)):
                    st.markdown(f"<span style='color:#00d4ff; font-weight: 600;'>📌 Theme: {label}</span>", unsafe_allow_html=True)
                    
                    for j, art in enumerate(cluster, 1):
                        st.markdown(f"""
                        <div class="article-item">
                            <strong style='color:#00d4ff;'>{j}. {art['title']}</strong><br>
                            <span style='color:#00f7ff; font-size:0.85rem;'>📰 {art['source']}</span> | <span style='color:#6b7c9f; font-size:0.85rem;'>{art['published'][:10]}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if art.get("url"): 
                            st.markdown(f"🔗 [Open Article]({art['url']})", help=art.get('description', ''))

    with tab_sources:
        st.markdown("### 📰 Source Materials")
        
        articles = state.get("filtered_articles", [])
        
        if not articles:
            st.info("No source materials available.")
        else:
            # Filter and search
            col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])
            
            with col_filter2:
                articles_per_page = st.selectbox("Per page", [5, 10, 20], index=1, label_visibility="collapsed")
            
            # Paginate
            total_pages = (len(articles) + articles_per_page - 1) // articles_per_page
            
            with col_filter3:
                page = st.selectbox("Page", range(1, total_pages + 1), label_visibility="collapsed", key="page_select") if total_pages > 1 else 1
            
            start_idx = (page - 1) * articles_per_page
            end_idx = min(start_idx + articles_per_page, len(articles))
            
            st.markdown(f"<p style='color:#00d4ff; text-align:center;'>Showing {start_idx + 1}-{end_idx} of {len(articles)} articles</p>", unsafe_allow_html=True)
            
            for art in articles[start_idx:end_idx]:
                st.markdown(f"""
                <div class="article-item">
                    <strong style='color:#00d4ff; font-size: 1.1rem;'>{art['title']}</strong><br>
                    <span style='color:#00f7ff;'>📰</span> <span style='color:#00d4ff;'>{art['source']}</span> • <span style='color:#6b7c9f;'>{art['published'][:10]}</span><br>
                    <span style='color:#9ca3af; font-size: 0.95rem; line-height: 1.5;'>{art.get('description', 'No description available')[:150]}...</span>
                </div>
                """, unsafe_allow_html=True)
                
                if art.get("url"):
                    st.markdown(f"🔗 [Read Full Article →]({art['url']})")

    with tab_audit:
        st.markdown("### ⚙️ Execution Trace")
        
        logs = state.get("logs", [])
        
        if not logs:
            st.info("No logs available.")
        else:
            st.markdown("#### 📋 Pipeline Steps")
            for idx, log in enumerate(logs, 1):
                # Color-code different log types
                if "fetch" in log.lower():
                    emoji = "🌐"
                    color = "#00d4ff"
                elif "cluster" in log.lower():
                    emoji = "🔗"
                    color = "#00f7ff"
                elif "summariz" in log.lower():
                    emoji = "✍️"
                    color = "#00d4ff"
                elif "assembl" in log.lower():
                    emoji = "📋"
                    color = "#00f7ff"
                elif "qc" in log.lower():
                    emoji = "✅"
                    color = "#00d4ff"
                else:
                    emoji = "ℹ️"
                    color = "#6b7c9f"
                
                st.markdown(f"<div style='padding: 12px; background: rgba(0, 212, 255, 0.05); border-left: 3px solid {color}; border-radius: 6px; margin: 8px 0;'>{emoji} <span style='color: {color};'><strong>{log}</strong></span></div>", unsafe_allow_html=True)
                
            if state.get("quality_issues"):
                st.markdown("<div class='tab-divider'></div>", unsafe_allow_html=True)
                st.warning("⚠️ Quality Assessment:")
                for issue in state.get("quality_issues", []):
                    st.markdown(f"• {issue}")

# ── 9. Footer ─────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.2), transparent); padding-top: 30px; padding-bottom: 20px; border-top: 1px solid rgba(0, 212, 255, 0.2); letter-spacing: 2px;">
        <span style='color: #00d4ff;'>✨ VANTAGE EDITORIAL ENGINE ✨</span><br>
        <span style='color: #6b7c9f; font-size: 0.75rem; margin-top: 10px; display: block;'>Built with AI • Powered by Groq & LangGraph</span>
    </div>
""", unsafe_allow_html=True)

"""Main Streamlit application entry point."""
import streamlit as st

st.set_page_config(
    page_title="AETHERA - Environmental Impact Assessment",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Main page content
st.markdown('<div class="main-header">🌍 AETHERA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Environmental Impact Assessment Copilot</div>', unsafe_allow_html=True)

st.markdown("""
    ### Welcome to AETHERA
    
    AETHERA is an AI-assisted Environmental Impact Assessment (EIA) platform that helps you:
    
    - 🗺️ **Define Areas of Interest** - Upload or draw project boundaries
    - 🔍 **Automated Analysis** - AI-powered geospatial screening and impact assessment
    - 📊 **Comprehensive Results** - Environmental KPIs, legal compliance, and biodiversity analysis
    - 📄 **Report Generation** - Export-ready analysis packages
    
    ### Get Started
    
    1. **Create a Project** - Start by creating a new project
    2. **Define AOI** - Upload a GeoJSON file or enter coordinates for your area of interest
    3. **Run Analysis** - Configure your analysis and start the assessment
    4. **View Results** - Explore KPIs, legal compliance, and map visualizations
    """)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 View Projects", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🏠_Home.py")

with col2:
    if st.button("➕ New Project", use_container_width=True):
        st.switch_page("pages/2_➕_New_Project.py")

with col3:
    st.info("💡 Make sure the backend API is running at http://localhost:8000")

# Sidebar
with st.sidebar:
    st.header("About AETHERA")
    st.markdown("""
    AETHERA automates the data–analysis–reporting chain for Environmental Impact Assessments.
    
    ### Features
    - Geospatial processing engine
    - AI/ML-powered analysis
    - Legal rules engine
    - Emissions & indicators
    - Biodiversity assessment
    """)
    
    st.divider()
    st.markdown("**Version:** 2.0 (Python-only)")


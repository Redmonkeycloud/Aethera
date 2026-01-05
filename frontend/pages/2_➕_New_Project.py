"""New Project page - Create a new project."""
import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from src.api_client import projects_api, APIError


st.set_page_config(
    page_title="AETHERA - New Project",
    page_icon="➕",
    layout="centered"
)

st.title("➕ Create New Project")

# Form
with st.form("new_project_form"):
    name = st.text_input("Project Name *", placeholder="Enter project name")
    
    country = st.selectbox(
        "Country",
        ["", "DEU", "FRA", "ITA", "GRC"],
        format_func=lambda x: {
            "": "Select country...",
            "DEU": "Germany",
            "FRA": "France",
            "ITA": "Italy",
            "GRC": "Greece"
        }.get(x, x)
    )
    
    sector = st.selectbox(
        "Sector",
        ["", "renewable-energy", "infrastructure", "mining", "agriculture", "other"],
        format_func=lambda x: {
            "": "Select sector...",
            "renewable-energy": "Renewable Energy",
            "infrastructure": "Infrastructure",
            "mining": "Mining",
            "agriculture": "Agriculture",
            "other": "Other"
        }.get(x, x)
    )
    
    col1, col2 = st.columns(2)
    with col1:
        cancel_button = st.form_submit_button("Cancel", use_container_width=True)
    with col2:
        submit_button = st.form_submit_button("Create Project", use_container_width=True, type="primary")
    
    if cancel_button:
        st.switch_page("pages/1_🏠_Home.py")
    
    if submit_button:
        if not name.strip():
            st.error("Project name is required")
        else:
            try:
                with st.spinner("Creating project..."):
                    project = projects_api.create(
                        name=name.strip(),
                        country=country if country else None,
                        sector=sector if sector else None
                    )
                    st.success(f"Project '{project.name}' created successfully!")
                    st.session_state.selected_project_id = project.id
                    st.switch_page("pages/3_📊_Project.py")
            except APIError as e:
                st.error(f"Failed to create project: {str(e)}")


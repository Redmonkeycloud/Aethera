"""Home page - List all projects."""
import streamlit as st
from datetime import datetime
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from src.api_client import projects_api, APIError


st.set_page_config(
    page_title="AETHERA - Projects",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 AETHERA Projects")
st.markdown("Environmental Impact Assessment Copilot")

# Initialize session state
if "projects" not in st.session_state:
    st.session_state.projects = None
if "error" not in st.session_state:
    st.session_state.error = None

# Sidebar with new project button
with st.sidebar:
    if st.button("➕ New Project", use_container_width=True, type="primary"):
        st.switch_page("pages/2_➕_New_Project.py")

# Load projects
if st.session_state.projects is None:
    try:
        with st.spinner("Loading projects..."):
            st.session_state.projects = projects_api.list()
            st.session_state.error = None
    except APIError as e:
        st.session_state.error = str(e)
        st.session_state.projects = []

# Display error if any
if st.session_state.error:
    st.error(f"❌ Error: {st.session_state.error}")
    st.info("💡 Make sure the backend API is running at http://localhost:8000")
    if st.button("🔄 Retry"):
        st.session_state.projects = None
        st.rerun()

# Display projects
if st.session_state.projects is not None:
    if len(st.session_state.projects) == 0:
        st.info("📝 No projects yet. Create your first project to get started!")
        if st.button("Create Your First Project", type="primary"):
            st.switch_page("pages/2_➕_New_Project.py")
    else:
        # Show delete confirmation if a project is marked for deletion
        if st.session_state.get("delete_project_id"):
            delete_id = st.session_state.delete_project_id
            delete_name = st.session_state.delete_project_name
            st.warning(f"⚠️ Are you sure you want to delete '{delete_name}'?")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("✅ Confirm Delete", key="confirm_delete", use_container_width=True):
                    try:
                        projects_api.delete(delete_id)
                        st.success(f"✅ Project '{delete_name}' deleted successfully")
                        # Clear session state and reload projects
                        st.session_state.delete_project_id = None
                        st.session_state.delete_project_name = None
                        st.session_state.projects = None
                        st.rerun()
                    except APIError as e:
                        st.error(f"❌ Failed to delete project: {str(e)}")
                        st.session_state.delete_project_id = None
                        st.session_state.delete_project_name = None
            with confirm_col2:
                if st.button("❌ Cancel", key="cancel_delete", use_container_width=True):
                    st.session_state.delete_project_id = None
                    st.session_state.delete_project_name = None
                    st.rerun()
            st.divider()
        
        # Display projects in a grid
        cols = st.columns(3)
        for idx, project in enumerate(st.session_state.projects):
            col = cols[idx % 3]
            with col:
                with st.container():
                    st.markdown(f"### {project.name}")
                    if project.country:
                        st.caption(f"🌍 Country: {project.country}")
                    if project.sector:
                        st.caption(f"🏭 Sector: {project.sector}")
                    
                    try:
                        created_date = datetime.fromisoformat(project.created_at.replace("Z", "+00:00"))
                        st.caption(f"📅 Created: {created_date.strftime('%B %d, %Y at %I:%M %p')}")
                    except (ValueError, AttributeError):
                        st.caption(f"📅 Created: {project.created_at}")
                    
                    col_view, col_delete = st.columns([3, 1])
                    with col_view:
                        if st.button(f"View Project", key=f"view_{project.id}", use_container_width=True):
                            st.session_state.selected_project_id = project.id
                            st.switch_page("pages/3_📊_Project.py")
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{project.id}", help=f"Delete {project.name}", use_container_width=True):
                            st.session_state.delete_project_id = project.id
                            st.session_state.delete_project_name = project.name
                            st.rerun()


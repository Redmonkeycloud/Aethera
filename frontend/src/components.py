"""Reusable Streamlit components."""
import streamlit as st
import json
from typing import Dict, Any, Optional
from datetime import datetime


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except (ValueError, AttributeError):
        return date_str


def display_error(error: str):
    """Display an error message."""
    st.error(f"❌ {error}")


def display_success(message: str):
    """Display a success message."""
    st.success(f"✅ {message}")


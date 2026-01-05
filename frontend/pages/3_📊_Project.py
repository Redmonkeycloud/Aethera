"""Project page - View and manage a project."""
import streamlit as st
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from src.api_client import projects_api, runs_api, tasks_api, layers_api, APIError


st.set_page_config(
    page_title="AETHERA - Project",
    page_icon="📊",
    layout="wide"
)

# Get project ID from session state or query params
project_id = st.session_state.get("selected_project_id")
if not project_id:
    st.error("No project selected")
    st.info("Please select a project from the home page")
    if st.button("Go to Home"):
        st.switch_page("pages/1_🏠_Home.py")
    st.stop()

# Load project
if "project_data" not in st.session_state or st.session_state.get("project_id") != project_id:
    try:
        with st.spinner("Loading project..."):
            st.session_state.project_data = projects_api.get(project_id)
            st.session_state.project_id = project_id
    except APIError as e:
        st.error(f"Failed to load project: {str(e)}")
        st.stop()

project = st.session_state.project_data

# Page header
st.title(f"📊 {project.name}")
col1, col2, col3 = st.columns(3)
with col1:
    if project.country:
        st.metric("Country", project.country)
with col2:
    if project.sector:
        st.metric("Sector", project.sector.replace("-", " ").title())
with col3:
    st.metric("Status", "Active")

# Initialize session state for AOI
if "aoi_geojson" not in st.session_state:
    st.session_state.aoi_geojson = None

# Sidebar for project actions
with st.sidebar:
    st.header("Project Actions")
    
    # AOI Upload
    st.subheader("Area of Interest (AOI)")
    uploaded_file = st.file_uploader("Upload GeoJSON", type=["geojson", "json"])
    if uploaded_file:
        try:
            geojson_data = json.load(uploaded_file)
            st.session_state.aoi_geojson = geojson_data
            st.success("AOI loaded successfully!")
        except json.JSONDecodeError:
            st.error("Invalid JSON file")
    
    # Manual coordinate input
    st.subheader("Or Enter Coordinates")
    
    coord_method = st.radio(
        "Input Method",
        ["Bounding Box", "GeoJSON"],
        horizontal=True,
        help="Choose how to input coordinates"
    )
    
    if coord_method == "Bounding Box":
        # Realistic defaults for a small field in central Italy (~10 hectares)
        # Location: Near Florence, Tuscany (43.77°N, 11.26°E)
        # 10 hectares = 0.1 km² = ~316m x 316m square
        # At this latitude: ~0.003° latitude ≈ 316m, ~0.004° longitude ≈ 316m
        default_center_lat = 43.77
        default_center_lon = 11.26
        default_size_deg = 0.003  # ~316 meters
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.caption("Enter coordinates (example: small field in Italy, ~10 hectares)")
        with col2:
            if st.button("📍 Use Italy Example", help="Load example coordinates for a 10-hectare field in central Italy"):
                st.session_state.quick_start_coords = True
                st.rerun()
        with col3:
            if st.button("🗑️ Clear", help="Clear current coordinates"):
                st.session_state.aoi_geojson = None
                st.session_state.quick_start_coords = False
                st.rerun()
        
        # Check if quick start was clicked
        if st.session_state.get("quick_start_coords", False):
            min_lon = default_center_lon - default_size_deg / 2
            max_lon = default_center_lon + default_size_deg / 2
            min_lat = default_center_lat - default_size_deg / 2
            max_lat = default_center_lat + default_size_deg / 2
            st.session_state.quick_start_coords = False
        else:
            # Default to Italy bounds with small area
            min_lon = st.session_state.get("bbox_min_lon", default_center_lon - default_size_deg / 2)
            max_lon = st.session_state.get("bbox_max_lon", default_center_lon + default_size_deg / 2)
            min_lat = st.session_state.get("bbox_min_lat", default_center_lat - default_size_deg / 2)
            max_lat = st.session_state.get("bbox_max_lat", default_center_lat + default_size_deg / 2)
        
        col1, col2 = st.columns(2)
        with col1:
            min_lon = st.number_input(
                "Min Longitude", 
                value=float(min_lon), 
                min_value=6.0, 
                max_value=19.0, 
                step=0.0001, 
                format="%.6f",
                help="Western boundary (Italy: 6.6° to 18.5°)"
            )
            min_lat = st.number_input(
                "Min Latitude", 
                value=float(min_lat), 
                min_value=35.0, 
                max_value=47.0, 
                step=0.0001, 
                format="%.6f",
                help="Southern boundary (Italy: 35.5° to 47.1°)"
            )
        with col2:
            max_lon = st.number_input(
                "Max Longitude", 
                value=float(max_lon), 
                min_value=6.0, 
                max_value=19.0, 
                step=0.0001, 
                format="%.6f",
                help="Eastern boundary"
            )
            max_lat = st.number_input(
                "Max Latitude", 
                value=float(max_lat), 
                min_value=35.0, 
                max_value=47.0, 
                step=0.0001, 
                format="%.6f",
                help="Northern boundary"
            )
        
        # Calculate area estimate (rough approximation)
        lat_span = max_lat - min_lat
        lon_span = max_lon - min_lon
        # At Italy's latitude (~43°), 1° lat ≈ 111 km, 1° lon ≈ 79 km
        area_km2 = lat_span * 111 * lon_span * 79
        area_ha = area_km2 * 100
        
        if area_ha > 0:
            if area_ha < 0.01:
                area_display = f"{area_ha * 10000:.1f} m²"
            elif area_ha < 1:
                area_display = f"{area_ha * 10000:.0f} m²"
            else:
                area_display = f"{area_ha:.2f} hectares"
            st.info(f"📍 Estimated area: {area_display} ({area_km2:.6f} km²)")
        
        if st.button("Create Bounding Box", type="primary", use_container_width=True):
            if min_lon >= max_lon or min_lat >= max_lat:
                st.error("❌ Invalid bounding box: min values must be less than max values")
            elif min_lon < 6.0 or max_lon > 19.0 or min_lat < 35.0 or max_lat > 47.0:
                st.warning("⚠️ Coordinates are outside Italy's bounds. Continue anyway?")
            else:
                # Create GeoJSON polygon from bounding box
                bbox_geojson = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [min_lon, min_lat],
                            [max_lon, min_lat],
                            [max_lon, max_lat],
                            [min_lon, max_lat],
                            [min_lon, min_lat]
                        ]]
                    },
                    "properties": {
                        "area_hectares": round(area_ha, 2),
                        "area_km2": round(area_km2, 6)
                    }
                }
                st.session_state.aoi_geojson = bbox_geojson
                st.session_state.bbox_min_lon = min_lon
                st.session_state.bbox_max_lon = max_lon
                st.session_state.bbox_min_lat = min_lat
                st.session_state.bbox_max_lat = max_lat
                st.success(f"✓ Bounding box created! Area: {area_display}")
                st.rerun()
    
    else:  # GeoJSON
        coord_input = st.text_area(
            "GeoJSON (Feature or FeatureCollection)",
            height=150,
            help="Paste GeoJSON Feature or FeatureCollection"
        )
        if st.button("Load GeoJSON", type="primary", use_container_width=True):
            if coord_input:
                try:
                    geojson_data = json.loads(coord_input)
                    # Handle FeatureCollection - extract first feature
                    if geojson_data.get("type") == "FeatureCollection":
                        features = geojson_data.get("features", [])
                        if features:
                            st.session_state.aoi_geojson = features[0]
                            st.success(f"✓ Loaded {len(features)} feature(s), using first feature")
                        else:
                            st.error("FeatureCollection is empty")
                    elif geojson_data.get("type") == "Feature":
                        st.session_state.aoi_geojson = geojson_data
                        st.success("✓ GeoJSON loaded!")
                    else:
                        st.error("Invalid GeoJSON: must be Feature or FeatureCollection")
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {str(e)}")
            else:
                st.warning("Please enter GeoJSON")
    
    # Display current AOI status
    if st.session_state.aoi_geojson:
        st.info("✓ AOI defined")
    else:
        st.warning("⚠ Please define an AOI")
    
    st.divider()
    
    # Create Analysis Run
    st.subheader("Create Analysis Run")
    
    with st.form("scenario_form"):
        project_type = st.selectbox(
            "Project Type",
            ["solar", "wind", "hydro", "other"],
            format_func=lambda x: x.title()
        )
        
        country = st.selectbox(
            "Country (Optional)",
            ["", "DEU", "FRA", "ITA", "GRC"],
            format_func=lambda x: {
                "": "Select country...",
                "DEU": "Germany",
                "FRA": "France",
                "ITA": "Italy",
                "GRC": "Greece"
            }.get(x, x)
        )
        
        submit_run = st.form_submit_button("🚀 Start Analysis", type="primary", use_container_width=True)
        
        if submit_run:
            if not st.session_state.aoi_geojson:
                st.error("❌ Please define an AOI first (upload file or enter coordinates)")
            else:
                try:
                    with st.spinner("Creating analysis run... This may take a moment."):
                        response = runs_api.create(
                            project_id=project_id,
                            aoi_geojson=st.session_state.aoi_geojson,
                            project_type=project_type,
                            country=country if country else None
                        )
                        task_id = response.get("task_id")
                        run_id = response.get("run_id")
                        
                        if task_id:
                            st.session_state.active_task_id = task_id
                            st.session_state.active_run_id = run_id
                            st.success(f"✅ Analysis run started! Task ID: {task_id[:8]}...")
                            st.info("📊 Check the 'Runs' tab to monitor progress")
                            st.rerun()
                        else:
                            st.error("Failed to get task ID from response")
                except APIError as e:
                    error_msg = str(e)
                    if "timeout" in error_msg.lower():
                        st.error(f"❌ Request timeout: {error_msg}")
                        st.info("💡 The backend may be processing. Try again in a moment.")
                    else:
                        st.error(f"❌ Failed to create run: {error_msg}")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    import traceback
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())

# Main content area
tab1, tab2 = st.tabs(["Map View", "Runs"])

with tab1:
    st.subheader("Map View")
    
    # Layer visibility toggles
    col1, col2, col3 = st.columns(3)
    with col1:
        show_natura = st.checkbox("Show Natura 2000", value=True)
    with col2:
        show_corine = st.checkbox("Show CORINE", value=False, help="⚠️ CORINE dataset is very large. Vector tiles are available via API but require a JavaScript-based map. GeoJSON mode will be used (may be slow).")
    with col3:
        show_aoi = st.checkbox("Show AOI", value=True) if st.session_state.aoi_geojson else st.checkbox("Show AOI", value=False, disabled=True)
    
    if st.session_state.aoi_geojson or show_natura or show_corine:
        # Display map using streamlit-folium
        try:
            import folium
            from streamlit_folium import st_folium
            import geopandas as gpd
            from shapely.geometry import shape
            import json
            
            # Determine map center from AOI or default location
            center_lat, center_lon = 39.5, 22.0  # Default: Greece center
            zoom = 6
            
            if st.session_state.aoi_geojson:
                try:
                    geom = st.session_state.aoi_geojson
                    if "features" in geom:
                        gdf = gpd.GeoDataFrame.from_features(geom["features"])
                    elif "geometry" in geom:
                        gdf = gpd.GeoDataFrame([1], geometry=[shape(geom["geometry"])])
                    else:
                        gdf = gpd.GeoDataFrame.from_features([{"type": "Feature", "geometry": geom}])
                    
                    bounds = gdf.total_bounds
                    center_lat = (bounds[1] + bounds[3]) / 2
                    center_lon = (bounds[0] + bounds[2]) / 2
                    zoom = 10
                except Exception as e:
                    st.warning(f"Could not parse AOI for centering: {e}")
            
            # Create Folium map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles='OpenStreetMap')
            
            # Get country code for filtering
            country_code = project.country if hasattr(project, 'country') and project.country else None
            
            # Add base layers
            if show_natura:
                try:
                    spinner_msg = f"Loading Natura 2000 layer{'' if not country_code else f' for {country_code}'}..."
                    with st.spinner(spinner_msg):
                        natura_data = layers_api.get_natura2000(country=country_code)
                        if natura_data and len(natura_data.get('features', [])) > 0:
                            folium.GeoJson(
                                natura_data,
                                style_function=lambda x: {
                                    'fillColor': '#ff0000',
                                    'color': '#8b0000',
                                    'weight': 1,
                                    'fillOpacity': 0.3
                                },
                                tooltip=folium.GeoJsonTooltip(fields=[], aliases=[], labels=False)
                            ).add_to(m)
                            st.success("✓ Natura 2000 layer loaded")
                        else:
                            st.info("Natura 2000 layer is empty")
                except APIError as e:
                    error_msg = str(e)
                    if "not found" in error_msg.lower() or "404" in error_msg:
                        st.info("ℹ️ Natura 2000 dataset not available. Dataset needs to be added to the data directory.")
                    elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                        st.warning("⚠️ Natura 2000 dataset is too large to load. The full dataset contains thousands of features. Consider using a smaller clipped version or disable this layer for now.")
                    else:
                        st.warning(f"Could not load Natura 2000: {error_msg}")
                except Exception as e:
                    st.warning(f"Error loading Natura 2000: {str(e)}")
            
            if show_corine:
                try:
                    # Check if vector tiles are available
                    try:
                        tiles_metadata = layers_api.get_corine_tiles_metadata(country=country_code)
                        st.info(f"ℹ️ Vector tiles are available for CORINE! Tile endpoint: /tiles/corine/{{z}}/{{x}}/{{y}}.mvt")
                        st.info(f"Note: Folium doesn't support vector tiles. For better performance, use a JavaScript-based map (MapLibre/Leaflet).")
                    except APIError:
                        pass  # Vector tiles not available, continue with GeoJSON
                    
                    spinner_msg = f"Loading CORINE layer (GeoJSON mode - may be slow){'' if not country_code else f' for {country_code}'}..."
                    with st.spinner(spinner_msg):
                        corine_data = layers_api.get_corine(country=country_code)
                        if corine_data and len(corine_data.get('features', [])) > 0:
                            folium.GeoJson(
                                corine_data,
                                style_function=lambda x: {
                                    'fillColor': '#00ff00',
                                    'color': '#006400',
                                    'weight': 1,
                                    'fillOpacity': 0.2
                                },
                                tooltip=folium.GeoJsonTooltip(fields=[], aliases=[], labels=False)
                            ).add_to(m)
                            st.success("✓ CORINE layer loaded (GeoJSON mode)")
                        else:
                            st.info("CORINE layer is empty")
                except APIError as e:
                    error_msg = str(e)
                    if "not found" in error_msg.lower() or "404" in error_msg:
                        st.info("ℹ️ CORINE dataset not available. Dataset needs to be added to the data directory.")
                    elif "corrupt" in error_msg.lower() or "malformed" in error_msg.lower():
                        st.error("❌ CORINE database file is corrupted. Please check the file integrity in your data directory or replace it with a valid copy.")
                    elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                        st.warning("⚠️ CORINE dataset is too large to load. The full dataset is very large. Consider using a smaller clipped version or disable this layer for now.")
                    else:
                        st.warning(f"Could not load CORINE: {error_msg}")
                except Exception as e:
                    st.warning(f"Error loading CORINE: {str(e)}")
            
            # Add AOI
            if st.session_state.aoi_geojson and show_aoi:
                try:
                    folium.GeoJson(
                        st.session_state.aoi_geojson,
                        style_function=lambda x: {
                            'fillColor': '#0066cc',
                            'color': '#003366',
                            'weight': 3,
                            'fillOpacity': 0.5
                        },
                        tooltip=folium.GeoJsonTooltip(fields=[], aliases=[], labels=False)
                    ).add_to(m)
                except Exception as e:
                    st.warning(f"Could not add AOI to map: {str(e)}")
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Display map (full width, larger height)
            st_folium(m, width=None, height=700, returned_objects=[])
            
            # Show GeoJSON data in expander
            if st.session_state.aoi_geojson:
                with st.expander("View AOI GeoJSON Data"):
                    st.json(st.session_state.aoi_geojson)
                
        except ImportError as e:
            st.error("Map libraries not installed. Please install: pip install geopandas shapely streamlit-folium folium")
            if st.session_state.aoi_geojson:
                st.json(st.session_state.aoi_geojson)
        except Exception as e:
            st.error(f"Error displaying map: {str(e)}")
            import traceback
            with st.expander("Error details"):
                st.code(traceback.format_exc())
            if st.session_state.aoi_geojson:
                st.json(st.session_state.aoi_geojson)
    else:
        st.info("Upload or define an AOI, or enable base layers to see the map")
    
    # Task status polling
    if st.session_state.get("active_task_id"):
        st.divider()
        st.subheader("Analysis Status")
        task_id = st.session_state.active_task_id
        
        try:
            task_status = tasks_api.get_status(task_id)
            status = task_status.get("status", "unknown")
            
            if status == "PENDING":
                st.info("⏳ Analysis pending...")
            elif status == "PROGRESS":
                st.info("🔄 Analysis in progress...")
                if "progress" in task_status:
                    st.json(task_status["progress"])
            elif status == "SUCCESS":
                run_id = task_status.get("run_id")
                if run_id:
                    st.success("✅ Analysis completed!")
                    if st.button("View Results"):
                        st.session_state.selected_run_id = run_id
                        st.switch_page("pages/4_📈_Run.py")
                else:
                    st.warning("Analysis completed but no run ID returned")
            elif status == "FAILURE":
                error = task_status.get("error", "Unknown error")
                st.error(f"❌ Analysis failed: {error}")
            
            if status in ["PENDING", "PROGRESS"]:
                st.rerun()
        except APIError as e:
            st.error(f"Failed to get task status: {str(e)}")

with tab2:
    st.subheader("Analysis Runs")
    try:
        all_runs = runs_api.list()
        project_runs = [r for r in all_runs if r.get("project_id") == project_id]
        
        if project_runs:
            for run in project_runs:
                with st.expander(f"Run {run.get('run_id', 'N/A')} - {run.get('status', 'unknown')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Type:** {run.get('project_type', 'N/A')}")
                        st.write(f"**Status:** {run.get('status', 'N/A')}")
                    with col2:
                        st.write(f"**Created:** {run.get('created_at', 'N/A')}")
                        if st.button("View Details", key=f"view_{run.get('run_id')}"):
                            st.session_state.selected_run_id = run.get('run_id')
                            st.switch_page("pages/4_📈_Run.py")
        else:
            st.info("No runs yet. Create an analysis run to get started.")
    except APIError as e:
        st.error(f"Failed to load runs: {str(e)}")


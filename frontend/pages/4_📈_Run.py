"""Run page - View analysis results with visualizations and report generation."""
import streamlit as st
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from src.api_client import runs_api, reports_api, APIError, API_BASE_URL

st.set_page_config(
    page_title="AETHERA - Run Results",
    page_icon="📈",
    layout="wide"
)

# Get run ID from session state
run_id = st.session_state.get("selected_run_id")
if not run_id:
    st.error("No run selected")
    if st.button("Go to Home"):
        st.switch_page("pages/1_🏠_Home.py")
    st.stop()

# Load run data
if "run_data" not in st.session_state or st.session_state.get("run_id") != run_id:
    try:
        with st.spinner("Loading run data..."):
            st.session_state.run_data = runs_api.get(run_id)
            st.session_state.run_id = run_id
    except APIError as e:
        st.error(f"Failed to load run: {str(e)}")
        st.stop()

run = st.session_state.run_data

# Page header
st.title(f"📈 Analysis Run: {run.get('run_id', 'N/A')}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Status", run.get("status", "unknown"))
with col2:
    st.metric("Project Type", run.get("project_type", "N/A"))
with col3:
    st.metric("Created", run.get("created_at", "N/A")[:10] if run.get("created_at") else "N/A")

# Load results and legal data
results = None
legal = None

try:
    with st.spinner("Loading results..."):
        results = runs_api.get_results(run_id)
except APIError as e:
    st.warning(f"Could not load results: {str(e)}")

try:
    legal = runs_api.get_legal(run_id)
except APIError:
    pass  # Legal data is optional

# Tabs for different views
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Results", "Visualizations", "Legal Compliance", "Map", "Report", "Model Explainability"])

with tab1:
    st.subheader("Analysis Results")
    if results:
        # Display KPIs and indicators
        if "kpis" in results:
            st.write("### Key Performance Indicators")
            kpis = results["kpis"]
            cols = st.columns(min(len(kpis), 4))
            for idx, (key, value) in enumerate(kpis.items()):
                with cols[idx % 4]:
                    st.metric(key.replace("_", " ").title(), value)
        
        # Display AI Model Scores with explanations
        st.write("### AI/ML Model Predictions")
        
        ai_scores = {}
        if "resm" in results and results["resm"].get("score") is not None:
            ai_scores["RESM (Suitability)"] = results["resm"]["score"]
        if "ahsm" in results and results["ahsm"].get("score") is not None:
            ai_scores["AHSM (Hazard Risk)"] = results["ahsm"]["score"]
        if "cim" in results and results["cim"].get("score") is not None:
            ai_scores["CIM (Cumulative Impact)"] = results["cim"]["score"]
        
        if ai_scores:
            cols = st.columns(len(ai_scores))
            for idx, (name, score) in enumerate(ai_scores.items()):
                with cols[idx]:
                    # Color based on score
                    if score >= 70:
                        delta_color = "inverse"
                    elif score >= 40:
                        delta_color = "normal"
                    else:
                        delta_color = "normal"
                    st.metric(name, f"{score:.1f}", delta=f"/ 100", delta_color=delta_color)
        
        # Biodiversity Score
        biodiversity_data = results.get("biodiversity")
        if biodiversity_data:
            # Handle case where biodiversity is a list (from save_summary)
            if isinstance(biodiversity_data, list) and len(biodiversity_data) > 0:
                biodiversity_data = biodiversity_data[0]
            if isinstance(biodiversity_data, dict) and biodiversity_data.get("score") is not None:
                st.write("### Biodiversity Assessment")
                bio_score = biodiversity_data["score"]
                st.metric("Biodiversity Sensitivity Score", f"{bio_score:.1f}", delta=f"/ 100")
                if "explanation" in biodiversity_data:
                    st.info(biodiversity_data["explanation"])
                else:
                    st.info(f"Score: {bio_score:.1f}/100. Higher values indicate greater biodiversity sensitivity and potential impact on protected species and habitats.")
        
        # RESM Assessment
        if "resm" in results and results["resm"].get("score") is not None:
            st.write("### RESM (Renewable Energy Suitability Model) Assessment")
            resm_data = results["resm"]
            if isinstance(resm_data, list) and len(resm_data) > 0:
                resm_data = resm_data[0]
            resm_score = resm_data.get("score") if isinstance(resm_data, dict) else results["resm"]["score"]
            st.metric("RESM Suitability Score", f"{resm_score:.1f}", delta=f"/ 100")
            caption_text = "Higher scores indicate better suitability for renewable energy development."
            if isinstance(resm_data, dict):
                if "category" in resm_data:
                    caption_text += f" Category: {resm_data['category']}."
                if "explanation" in resm_data:
                    st.info(resm_data["explanation"])
                else:
                    st.info(caption_text)
            else:
                st.info(caption_text)
        
        # AHSM Assessment
        if "ahsm" in results and results["ahsm"].get("score") is not None:
            st.write("### AHSM (Asset Hazard Susceptibility Model) Assessment")
            ahsm_data = results["ahsm"]
            if isinstance(ahsm_data, list) and len(ahsm_data) > 0:
                ahsm_data = ahsm_data[0]
            ahsm_score = ahsm_data.get("score") if isinstance(ahsm_data, dict) else results["ahsm"]["score"]
            st.metric("AHSM Hazard Risk Score", f"{ahsm_score:.1f}", delta=f"/ 100")
            caption_text = "Lower scores (green) indicate lower hazard risk. Higher scores (red) indicate higher hazard risk."
            if isinstance(ahsm_data, dict):
                if "category" in ahsm_data:
                    caption_text += f" Category: {ahsm_data['category']}."
                if "explanation" in ahsm_data:
                    st.info(ahsm_data["explanation"])
                else:
                    st.info(caption_text)
            else:
                st.info(caption_text)
        
        # CIM Assessment
        if "cim" in results and results["cim"].get("score") is not None:
            st.write("### CIM (Cumulative Impact Model) Assessment")
            cim_data = results["cim"]
            if isinstance(cim_data, list) and len(cim_data) > 0:
                cim_data = cim_data[0]
            cim_score = cim_data.get("score") if isinstance(cim_data, dict) else results["cim"]["score"]
            st.metric("CIM Cumulative Impact Score", f"{cim_score:.1f}", delta=f"/ 100")
            caption_text = "Integrates all model scores to provide overall cumulative impact assessment. Lower scores indicate lower cumulative impact."
            if isinstance(cim_data, dict):
                if "category" in cim_data:
                    caption_text += f" Category: {cim_data['category']}."
                if "explanation" in cim_data:
                    st.info(cim_data["explanation"])
                else:
                    st.info(caption_text)
            else:
                st.info(caption_text)
        
        # Emissions
        if "emissions" in results:
            st.write("### Carbon Emissions")
            emissions = results["emissions"]
            cols = st.columns(4)
            with cols[0]:
                st.metric("Baseline", f"{emissions.get('baseline_tco2e', 0):.2f}", delta="tCO₂e")
            with cols[1]:
                st.metric("Construction", f"{emissions.get('project_construction_tco2e', 0):.2f}", delta="tCO₂e")
            with cols[2]:
                st.metric("Annual Operation", f"{emissions.get('project_operation_tco2e_per_year', 0):.2f}", delta="tCO₂e/year")
            with cols[3]:
                net_diff = emissions.get('net_difference_tco2e', 0)
                delta_color = "inverse" if net_diff > 0 else "normal"
                st.metric("Net Difference", f"{net_diff:.2f}", delta="tCO₂e", delta_color=delta_color)
            
            if "explanation" in emissions:
                st.info(emissions["explanation"])
        
        # Display other results
        st.write("### Detailed Results")
        with st.expander("View Full Results JSON"):
            st.json(results)
    else:
        st.info("No results available yet")

with tab2:
    st.subheader("Visualizations")
    
    if results:
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            
            # AI Model Scores Bar Chart
            if any(key in results for key in ["resm", "ahsm", "cim"]):
                st.write("### AI Model Assessment Scores")
                ai_data = {}
                if "resm" in results and results["resm"].get("score") is not None:
                    ai_data["RESM\n(Suitability)"] = results["resm"]["score"]
                if "ahsm" in results and results["ahsm"].get("score") is not None:
                    ai_data["AHSM\n(Hazard Risk)"] = results["ahsm"]["score"]
                if "cim" in results and results["cim"].get("score") is not None:
                    ai_data["CIM\n(Cumulative Impact)"] = results["cim"]["score"]
                
                if ai_data:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=list(ai_data.keys()),
                            y=list(ai_data.values()),
                            marker=dict(
                                color=list(ai_data.values()),
                                colorscale='RdYlGn_r',
                                showscale=True,
                                cmin=0,
                                cmax=100
                            ),
                            text=[f"{v:.1f}" for v in ai_data.values()],
                            textposition='outside',
                        )
                    ])
                    fig.update_layout(
                        title="AI Model Assessment Scores (0-100 scale)",
                        yaxis=dict(range=[0, 100], title="Score"),
                        xaxis=dict(title="Model"),
                        height=400
                    )
                    st.plotly_chart(fig, width='stretch')  # width='stretch' in newer versions
                    
                    st.caption("**Score Interpretation:** Lower scores (green) indicate lower impact/risk. Higher scores (red) indicate higher impact/risk.")
            
            # Emissions Comparison
            if "emissions" in results:
                st.write("### Carbon Emissions Comparison")
                emissions = results["emissions"]
                emissions_data = {
                    "Baseline": emissions.get("baseline_tco2e", 0),
                    "Construction": emissions.get("project_construction_tco2e", 0),
                    "Annual Operation": emissions.get("project_operation_tco2e_per_year", 0),
                }
                
                fig = px.bar(
                    x=list(emissions_data.keys()),
                    y=list(emissions_data.values()),
                    labels={"x": "Category", "y": "tCO₂e"},
                    title="Carbon Emissions by Category"
                )
                fig.update_traces(marker_color='steelblue', text=list(emissions_data.values()), texttemplate='%{text:.2f}', textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
                
                st.caption("**Explanation:** Comparison of baseline carbon emissions versus projected project emissions.")
            
            # Biodiversity Score Gauge
            biodiversity_data = results.get("biodiversity")
            if biodiversity_data:
                # Handle case where biodiversity is a list (from save_summary)
                if isinstance(biodiversity_data, list) and len(biodiversity_data) > 0:
                    biodiversity_data = biodiversity_data[0]
                if isinstance(biodiversity_data, dict) and biodiversity_data.get("score") is not None:
                    st.write("### Biodiversity Sensitivity Score")
                    bio_score = biodiversity_data["score"]
                    
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = bio_score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Biodiversity Sensitivity"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 40], 'color': "lightgreen"},
                                {'range': [40, 70], 'color': "yellow"},
                                {'range': [70, 100], 'color': "lightcoral"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, width='stretch')  # width='stretch' in newer versions
                    
                    st.caption("**Interpretation:** Green (0-40): Low sensitivity. Yellow (40-70): Moderate sensitivity. Red (70-100): High sensitivity.")
            
            # RESM Score Gauge
            if "resm" in results and results["resm"].get("score") is not None:
                st.write("### RESM (Renewable Energy Suitability Model) Score")
                resm_data = results["resm"]
                if isinstance(resm_data, list) and len(resm_data) > 0:
                    resm_data = resm_data[0]
                resm_score = resm_data.get("score") if isinstance(resm_data, dict) else results["resm"]["score"]
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = resm_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "RESM Suitability Score"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 40], 'color': "lightgreen"},
                            {'range': [40, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "lightcoral"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, width='stretch')
                
                caption_text = "**Interpretation:** Higher scores indicate better suitability for renewable energy development."
                if isinstance(resm_data, dict) and "category" in resm_data:
                    caption_text += f" Category: {resm_data['category']}."
                st.caption(caption_text)
            
            # AHSM Score Gauge
            if "ahsm" in results and results["ahsm"].get("score") is not None:
                st.write("### AHSM (Asset Hazard Susceptibility Model) Score")
                ahsm_data = results["ahsm"]
                if isinstance(ahsm_data, list) and len(ahsm_data) > 0:
                    ahsm_data = ahsm_data[0]
                ahsm_score = ahsm_data.get("score") if isinstance(ahsm_data, dict) else results["ahsm"]["score"]
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = ahsm_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "AHSM Hazard Risk Score"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkred"},
                        'steps': [
                            {'range': [0, 40], 'color': "lightgreen"},
                            {'range': [40, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "lightcoral"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, width='stretch')
                
                caption_text = "**Interpretation:** Lower scores (green) indicate lower hazard risk. Higher scores (red) indicate higher hazard risk."
                if isinstance(ahsm_data, dict) and "category" in ahsm_data:
                    caption_text += f" Category: {ahsm_data['category']}."
                st.caption(caption_text)
            
            # CIM Score Gauge
            if "cim" in results and results["cim"].get("score") is not None:
                st.write("### CIM (Cumulative Impact Model) Score")
                cim_data = results["cim"]
                if isinstance(cim_data, list) and len(cim_data) > 0:
                    cim_data = cim_data[0]
                cim_score = cim_data.get("score") if isinstance(cim_data, dict) else results["cim"]["score"]
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = cim_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "CIM Cumulative Impact Score"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkorange"},
                        'steps': [
                            {'range': [0, 40], 'color': "lightgreen"},
                            {'range': [40, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "lightcoral"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, width='stretch')
                
                caption_text = "**Interpretation:** Integrates all model scores to provide overall cumulative impact assessment. Lower scores indicate lower cumulative impact."
                if isinstance(cim_data, dict) and "category" in cim_data:
                    caption_text += f" Category: {cim_data['category']}."
                st.caption(caption_text)
        
        except ImportError:
            st.warning("⚠️ Plotly not installed. Install with: `pip install plotly` to see visualizations.")
            st.info("Charts and graphs will still be included in generated reports.")
    else:
        st.info("No results available for visualization")

with tab3:
    st.subheader("Legal Compliance")
    if legal:
        if "overall_compliant" in legal:
            if legal["overall_compliant"]:
                st.success("✅ **Overall Compliance: COMPLIANT**")
            else:
                st.error("❌ **Overall Compliance: NON-COMPLIANT**")
        
        if "summary" in legal:
            st.write(legal["summary"])
        
        if "critical_violations" in legal and legal["critical_violations"]:
            st.write("### Critical Violations")
            for violation in legal["critical_violations"]:
                st.error(f"**{violation.get('rule_name', 'Unknown Rule')}:** {violation.get('message', 'N/A')}")
        
        if "warnings" in legal and legal["warnings"]:
            st.write("### Warnings")
            for warning in legal["warnings"]:
                st.warning(f"**{warning.get('rule_name', 'Unknown Rule')}:** {warning.get('message', 'N/A')}")
        
        with st.expander("View Full Legal Evaluation"):
            st.json(legal)
    else:
        st.info("No legal compliance data available")

with tab4:
    st.subheader("Map View")
    
    # Try to load biodiversity layers
    biodiversity_layers = run.get("outputs", {}).get("biodiversity_layers", {})
    if biodiversity_layers:
        st.write("### Available Biodiversity Layers")
        
        # Layer visibility checkboxes
        layer_visibility = {}
        cols = st.columns(min(len(biodiversity_layers), 4))
        for idx, layer_name in enumerate(biodiversity_layers.keys()):
            with cols[idx % len(cols)]:
                layer_visibility[layer_name] = st.checkbox(f"Show {layer_name}", key=f"layer_{layer_name}", value=True)
        
        # Display map if at least one layer is selected
        if any(layer_visibility.values()):
            try:
                import folium
                from streamlit_folium import st_folium
                import geopandas as gpd
                from shapely.geometry import shape
                
                # Determine map center from first available layer
                center_lat, center_lon = 39.5, 22.0  # Default: Greece center
                zoom = 6
                map_bounds = None
                
                # Load first visible layer to determine map center
                first_layer = next((name for name, visible in layer_visibility.items() if visible), None)
                if first_layer:
                    try:
                        layer_data = runs_api.get_biodiversity_layer(run_id, first_layer)
                        if layer_data and layer_data.get("features"):
                            gdf = gpd.GeoDataFrame.from_features(layer_data["features"])
                            if not gdf.empty:
                                bounds = gdf.total_bounds
                                center_lat = (bounds[1] + bounds[3]) / 2
                                center_lon = (bounds[0] + bounds[2]) / 2
                                map_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]
                                zoom = 10
                    except Exception as e:
                        st.warning(f"Could not determine map center from {first_layer}: {e}")
                
                # Create Folium map
                m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles='OpenStreetMap')
                
                # Add layers
                for layer_name, visible in layer_visibility.items():
                    if visible:
                        try:
                            layer_data = runs_api.get_biodiversity_layer(run_id, layer_name)
                            if layer_data and layer_data.get("features"):
                                # Determine color based on layer type
                                if "sensitivity" in layer_name.lower():
                                    fill_color = '#ef4444'  # Red for sensitivity
                                    line_color = '#dc2626'
                                else:
                                    fill_color = '#3b82f6'  # Blue for other layers
                                    line_color = '#2563eb'
                                
                                folium.GeoJson(
                                    layer_data,
                                    style_function=lambda x, fc=fill_color, lc=line_color: {
                                        'fillColor': fc,
                                        'color': lc,
                                        'weight': 2,
                                        'fillOpacity': 0.5
                                    },
                                    tooltip=folium.GeoJsonTooltip(
                                        fields=['biodiversity_score', 'biodiversity_sensitivity', 'area_hectares'],
                                        aliases=['Score:', 'Sensitivity:', 'Area (ha):'],
                                        labels=True
                                    ) if layer_data.get("features") and layer_data["features"][0].get("properties") else None
                                ).add_to(m)
                        except APIError as e:
                            st.warning(f"Failed to load layer {layer_name}: {str(e)}")
                        except Exception as e:
                            st.warning(f"Error displaying layer {layer_name}: {str(e)}")
                
                # Fit bounds if available
                if map_bounds:
                    m.fit_bounds(map_bounds)
                
                # Add layer control
                folium.LayerControl().add_to(m)
                
                # Display map
                st_folium(m, width=None, height=600, returned_objects=[])
                
            except ImportError:
                st.error("Map libraries not installed. Please install: pip install folium streamlit-folium geopandas")
                # Fallback: show JSON data
                st.write("### Layer Data (JSON)")
                for layer_name, visible in layer_visibility.items():
                    if visible:
                        try:
                            layer_data = runs_api.get_biodiversity_layer(run_id, layer_name)
                            with st.expander(f"{layer_name} GeoJSON"):
                                st.json(layer_data)
                        except APIError as e:
                            st.error(f"Failed to load layer: {str(e)}")
            except Exception as e:
                st.error(f"Error displaying map: {str(e)}")
                import traceback
                with st.expander("Error details"):
                    st.code(traceback.format_exc())
    else:
        st.info("No biodiversity layers available for this run")

with tab5:
    st.subheader("Generate & Download Report")
    st.write("Create a comprehensive PDF or DOCX report with visualizations and explanatory text.")
    
    col1, col2 = st.columns(2)
    with col1:
        report_format = st.selectbox("Report Format", ["markdown", "pdf", "docx"], index=2)
    with col2:
        use_rag = st.checkbox("Use RAG (Retrieval-Augmented Generation)", value=True, help="Augment report with insights from similar past reports")
    
    if st.button("📄 Generate Report", type="primary", use_container_width=True):  # TODO: Update to width='stretch' when Streamlit version supports it
        try:
            with st.spinner("Generating report with visualizations and explanations... This may take a moment."):
                report_response = reports_api.generate(
                    run_id=run_id,
                    template_name="enhanced_report.md.jinja",
                    format=report_format,
                    enable_rag=use_rag
                )
                
                report_id = report_response.get("report_id")
                st.success(f"✅ Report generated successfully! Report ID: {report_id}")
                
                # Download button
                if report_format in ["pdf", "docx"]:
                    try:
                        with st.spinner("Preparing download..."):
                            report_data = reports_api.export(report_id, format=report_format)
                            file_ext = "pdf" if report_format == "pdf" else "docx"
                            st.download_button(
                                label=f"📥 Download {report_format.upper()} Report",
                                data=report_data,
                                file_name=f"aethera_report_{run_id}.{file_ext}",
                                mime=f"application/{file_ext}" if file_ext == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                width='stretch'
                            )
                    except APIError as e:
                        st.error(f"Failed to prepare download: {str(e)}")
                        st.info("You can still access the report via the API or download it manually from the reports directory.")
                else:
                    st.info("Markdown reports can be viewed via the API. Use PDF or DOCX format for direct download.")
        
        except APIError as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                st.error(f"❌ Report generation timeout: {error_msg}")
                st.info("💡 Report generation may take longer when using ChatGPT for explanations. Please try again or disable RAG.")
            else:
                st.error(f"❌ Failed to generate report: {error_msg}")
    
    # Show existing reports for this run
    st.divider()
    st.write("### Existing Reports")
    try:
        all_reports = reports_api.list()
        run_reports = [r for r in all_reports if r.get("run_id") == run_id]
        
        if run_reports:
            for report in run_reports:
                with st.expander(f"Report {report.get('report_id', 'N/A')[:8]}... - {report.get('status', 'draft')}"):
                    st.write(f"**Created:** {report.get('created_at', 'N/A')}")
                    if report.get("summary"):
                        st.write(f"**Summary:** {report['summary'][:200]}...")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📥 Download PDF", key=f"pdf_{report.get('report_id')}"):
                            try:
                                report_data = reports_api.export(report.get("report_id"), format="pdf")
                                st.download_button(
                                    label="Download",
                                    data=report_data,
                                    file_name=f"report_{report.get('report_id')}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_pdf_{report.get('report_id')}"
                                )
                            except APIError as e:
                                st.error(str(e))
                    with col2:
                        if st.button("📥 Download DOCX", key=f"docx_{report.get('report_id')}"):
                            try:
                                report_data = reports_api.export(report.get("report_id"), format="docx")
                                st.download_button(
                                    label="Download",
                                    data=report_data,
                                    file_name=f"report_{report.get('report_id')}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"dl_docx_{report.get('report_id')}"
                                )
                            except APIError as e:
                                st.error(str(e))
        else:
            st.info("No reports generated yet. Use the button above to create one.")
    except APIError as e:
        st.warning(f"Could not load existing reports: {str(e)}")

with tab6:
    st.subheader("Model Explainability")
    st.write("View model performance metrics, feature importance, and SHAP explanations for each ML model.")
    
    # Model selection
    model_names = ["biodiversity", "resm", "ahsm", "cim"]
    selected_model = st.selectbox("Select Model", model_names, key="explainability_model")
    
    explainability_data = None
    
    # Try to load existing explainability data
    try:
        explainability_data = runs_api.get_explainability(run_id, selected_model)
        st.success(f"✅ Explainability data loaded for {selected_model}")
    except APIError as e:
        if "404" in str(e) or "not found" in str(e).lower():
            st.info(f"🤖 Explainability artifacts not yet generated for {selected_model}. Click the button below to generate them.")
        else:
            st.warning(f"⚠️ Could not load explainability data: {str(e)}")
    
    # Generate button
    if explainability_data is None:
        if st.button(f"🔬 Generate Explainability for {selected_model.upper()}", type="primary", use_container_width=True):  # TODO: Update to width='stretch'
            try:
                with st.spinner(f"Generating explainability artifacts for {selected_model}... This may take a minute."):
                    generation_result = runs_api.generate_explainability(run_id, selected_model)
                    st.success("✅ Explainability artifacts generated successfully!")
                    st.info("🔄 Please refresh the page to view the visualizations.")
                    st.rerun()
            except APIError as e:
                st.error(f"❌ Failed to generate explainability: {str(e)}")
                st.info("💡 Make sure the backend has yellowbrick and shap installed: `pip install yellowbrick shap`")
    
    # Display explainability data
    if explainability_data:
        # SHAP Feature Importance
        if "shap_values" in explainability_data and explainability_data["shap_values"]:
            st.write("### Feature Importance (SHAP)")
            
            # Aggregate feature importance across all models in ensemble
            all_importance = {}
            for model_name, shap_data in explainability_data["shap_values"].items():
                if "feature_importance" in shap_data:
                    for feature, importance in shap_data["feature_importance"].items():
                        if feature not in all_importance:
                            all_importance[feature] = []
                        all_importance[feature].append(importance)
            
            # Average importance across models
            avg_importance = {feature: sum(imps) / len(imps) for feature, imps in all_importance.items()}
            
            if avg_importance:
                # Sort by importance
                sorted_features = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)
                
                try:
                    import plotly.graph_objects as go
                    
                    features = [f[0] for f in sorted_features]
                    importances = [f[1] for f in sorted_features]
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=importances,
                            y=features,
                            orientation='h',
                            marker=dict(color=importances, colorscale='Viridis', showscale=True),
                            text=[f"{imp:.4f}" for imp in importances],
                            textposition='outside',
                        )
                    ])
                    fig.update_layout(
                        title=f"{selected_model.upper()} Feature Importance (SHAP Values)",
                        xaxis_title="Mean |SHAP Value|",
                        yaxis_title="Feature",
                        height=max(400, len(features) * 30),
                    )
                    st.plotly_chart(fig, width='stretch')  # width='stretch' in newer versions
                    
                    st.caption("**Interpretation:** Higher values indicate features that have greater influence on model predictions.")
                    
                except ImportError:
                    # Fallback to simple display
                    st.write("**Top Features by Importance:**")
                    for feature, importance in sorted_features[:10]:
                        st.write(f"- **{feature}**: {importance:.4f}")
        
        # Performance Plots (Yellowbrick and SHAP)
        if "plots" in explainability_data and explainability_data["plots"]:
            st.write("### Model Performance Visualizations")
            
            # Handle nested structure (plots organized by model in ensemble)
            all_plots = {}
            if isinstance(explainability_data["plots"], dict):
                # Check if it's nested by model name
                first_key = list(explainability_data["plots"].keys())[0] if explainability_data["plots"] else None
                if first_key and isinstance(explainability_data["plots"][first_key], dict):
                    # Nested structure: {model_name: {plot_name: path}}
                    for model_name, model_plots in explainability_data["plots"].items():
                        if isinstance(model_plots, dict):
                            st.write(f"#### {model_name.replace('_', ' ').title()} Model")
                            cols = st.columns(min(2, len(model_plots)))
                            for idx, (plot_name, plot_path) in enumerate(model_plots.items()):
                                with cols[idx % 2]:
                                    try:
                                        # Handle different path formats
                                        if isinstance(plot_path, str):
                                            if plot_path.startswith("/"):
                                                # Absolute path from API
                                                plot_url = f"{API_BASE_URL}{plot_path}"
                                            else:
                                                # Relative path or just plot name
                                                # Use the path from the API response directly
                                                plot_url = f"{API_BASE_URL}{plot_path}" if plot_path.startswith("/") else f"{API_BASE_URL}/runs/{run_id}/explainability/{selected_model}/plots/{plot_path}"
                                        else:
                                            # Fallback: use plot name
                                            plot_url = runs_api.get_explainability_plot_url(run_id, selected_model, plot_name)
                                        
                                        st.write(f"**{plot_name.replace('_', ' ').title()}**")
                                        st.image(plot_url, width='stretch')
                                    except Exception as e:
                                        st.warning(f"Could not load plot {plot_name}: {e}")
                else:
                    # Flat structure: {plot_name: path}
                    plot_names = list(explainability_data["plots"].keys())
                    cols = st.columns(min(2, len(plot_names)))
                    for idx, plot_name in enumerate(plot_names):
                        with cols[idx % 2]:
                            try:
                                plot_url = runs_api.get_explainability_plot_url(run_id, selected_model, plot_name)
                                st.write(f"**{plot_name.replace('_', ' ').title()}**")
                                st.image(plot_url, width='stretch')
                            except Exception as e:
                                st.warning(f"Could not load plot {plot_name}: {e}")
        
        # Model Details
        if "shap_values" in explainability_data:
            with st.expander("View Detailed SHAP Values"):
                st.json(explainability_data["shap_values"])
        
        # Metadata
        if "metadata" in explainability_data:
            with st.expander("View Metadata"):
                st.json(explainability_data["metadata"])
    
    # Export button
    if explainability_data:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export Explainability Report (PDF)", use_container_width=True):  # TODO: Update to width='stretch'
                try:
                    with st.spinner("Generating PDF report..."):
                        report_data = runs_api.export_explainability(run_id, selected_model)
                        st.download_button(
                            label="Download PDF Report",
                            data=report_data,
                            file_name=f"{selected_model}_explainability_{run_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                except APIError as e:
                    st.error(f"Failed to export report: {str(e)}")
        
        with col2:
            st.info("💡 The PDF report includes all visualizations and SHAP feature importance data.")
    
    # Information about explainability
    st.divider()
    st.write("### About Model Explainability")
    st.info("""
    **SHAP (SHapley Additive exPlanations)** values explain the contribution of each feature to individual predictions.
    - **Feature Importance**: Shows which features most influence model predictions
    - **Waterfall Plots**: Visualize how each feature contributes to a specific prediction
    - **Dependence Plots**: Show how model output changes with feature values
    
    **Yellowbrick** provides visual diagnostic tools for machine learning models, including:
    - Confusion matrices (classification)
    - ROC curves (classification)
    - Prediction error plots (regression)
    - Residual plots (regression)
    - Feature importance (tree-based models)
    
    These visualizations help understand model behavior and build trust in AI predictions.
    **Note:** Explainability artifacts are automatically generated during analysis and cached for faster access.
    """)

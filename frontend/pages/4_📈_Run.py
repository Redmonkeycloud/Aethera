"""Run page - View analysis results with visualizations and report generation."""
import streamlit as st
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from src.api_client import runs_api, reports_api, APIError

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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Results", "Visualizations", "Legal Compliance", "Map", "Report"])

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
        if "biodiversity" in results and results["biodiversity"].get("score") is not None:
            st.write("### Biodiversity Assessment")
            bio_score = results["biodiversity"]["score"]
            st.metric("Biodiversity Sensitivity Score", f"{bio_score:.1f}", delta=f"/ 100")
            if "explanation" in results["biodiversity"]:
                st.info(results["biodiversity"]["explanation"])
            else:
                st.info(f"Score: {bio_score:.1f}/100. Higher values indicate greater biodiversity sensitivity and potential impact on protected species and habitats.")
        
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
                    st.plotly_chart(fig, use_container_width=True)
                    
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
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption("**Explanation:** Comparison of baseline carbon emissions versus projected project emissions.")
            
            # Biodiversity Score Gauge
            if "biodiversity" in results and results["biodiversity"].get("score") is not None:
                st.write("### Biodiversity Sensitivity Score")
                bio_score = results["biodiversity"]["score"]
                
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
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption("**Interpretation:** Green (0-40): Low sensitivity. Yellow (40-70): Moderate sensitivity. Red (70-100): High sensitivity.")
        
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
    st.info("Map visualization with biodiversity layers would go here")
    
    # Try to load biodiversity layers
    biodiversity_layers = run.get("outputs", {}).get("biodiversity_layers", {})
    if biodiversity_layers:
        st.write("### Available Biodiversity Layers")
        for layer_name in biodiversity_layers.keys():
            if st.checkbox(f"Show {layer_name}", key=f"layer_{layer_name}"):
                try:
                    layer_data = runs_api.get_biodiversity_layer(run_id, layer_name)
                    st.json(layer_data)
                except APIError as e:
                    st.error(f"Failed to load layer: {str(e)}")

with tab5:
    st.subheader("Generate & Download Report")
    st.write("Create a comprehensive PDF or DOCX report with visualizations and explanatory text.")
    
    col1, col2 = st.columns(2)
    with col1:
        report_format = st.selectbox("Report Format", ["markdown", "pdf", "docx"], index=2)
    with col2:
        use_rag = st.checkbox("Use RAG (Retrieval-Augmented Generation)", value=True, help="Augment report with insights from similar past reports")
    
    if st.button("📄 Generate Report", type="primary", use_container_width=True):
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
                                use_container_width=True
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

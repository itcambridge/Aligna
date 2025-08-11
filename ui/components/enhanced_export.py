"""
Enhanced export functionality with citation preservation.
"""

import streamlit as st
import os
import json
from typing import Dict, List, Any, Optional
import tempfile
from export.cv_exporter import CVExporter
import logging

logger = logging.getLogger(__name__)

def create_export_section(cv_data: Dict[str, Any], evidence_validation: Dict[str, Any]):
    """
    Create an enhanced export section with citation preservation.
    
    Args:
        cv_data: CV data with sections and evidence
        evidence_validation: Evidence validation results
    """
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(20px); border-radius: 24px; 
         padding: 32px; margin: 32px 0; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);">
        <h3 style="text-align: center; margin-bottom: 24px; font-weight: 300; color: #111827;">
            Export Options
        </h3>
    """, unsafe_allow_html=True)
    
    # Create tabs for different export options
    tab1, tab2, tab3 = st.tabs(["📄 Document Export", "🔍 Evidence Export", "⚙️ Advanced Options"])
    
    with tab1:
        create_document_export_tab(cv_data)
    
    with tab2:
        create_evidence_export_tab(cv_data, evidence_validation)
    
    with tab3:
        create_advanced_export_tab(cv_data)
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_document_export_tab(cv_data: Dict[str, Any]):
    """Create document export tab."""
    st.markdown("""
    <p style="margin-bottom: 16px;">Export your CV in different formats with citations preserved.</p>
    """, unsafe_allow_html=True)
    
    # Template selection
    st.subheader("Select Template")
    
    # Get available templates
    exporter = CVExporter()
    templates = exporter.get_available_templates()
    
    # Create template selection
    template_options = {t["id"]: f"{t['name']} - {t['description']}" for t in templates}
    selected_template = st.selectbox(
        "CV Template",
        options=list(template_options.keys()),
        format_func=lambda x: template_options[x],
        index=0
    )
    
    # Format selection
    st.subheader("Select Format")
    
    format_col1, format_col2, format_col3, format_col4 = st.columns(4)
    
    with format_col1:
        if st.button("📝 Text", use_container_width=True):
            export_cv(cv_data, selected_template, "text")
    
    with format_col2:
        if st.button("📄 DOCX", use_container_width=True):
            export_cv(cv_data, selected_template, "docx")
    
    with format_col3:
        if st.button("📊 PDF", use_container_width=True):
            export_cv(cv_data, selected_template, "pdf")
    
    with format_col4:
        if st.button("🔄 JSON", use_container_width=True):
            export_cv(cv_data, selected_template, "json")
    
    # Citation style
    st.subheader("Citation Style")
    citation_style = st.radio(
        "Select citation style",
        options=["Footnotes", "Endnotes", "Inline"],
        horizontal=True
    )
    
    # Preview
    st.markdown("""
    <div style="background: #f8fafc; border-radius: 12px; padding: 16px; margin-top: 24px;">
        <h4 style="margin-bottom: 12px;">Preview</h4>
        <p style="color: #6b7280; font-size: 14px;">
            A preview of your CV with the selected template and citation style will appear here.
        </p>
    </div>
    """, unsafe_allow_html=True)

def create_evidence_export_tab(cv_data: Dict[str, Any], evidence_validation: Dict[str, Any]):
    """Create evidence export tab."""
    st.markdown("""
    <p style="margin-bottom: 16px;">Export detailed evidence reports and coverage analysis.</p>
    """, unsafe_allow_html=True)
    
    # Evidence report
    st.subheader("Evidence Report")
    
    report_col1, report_col2 = st.columns(2)
    
    with report_col1:
        if st.button("📊 Evidence Report", use_container_width=True):
            # Create evidence report
            evidence_report = cv_data.get("evidence_report", "No evidence report available")
            
            # Download
            st.download_button(
                "📥 Download Evidence Report",
                evidence_report,
                file_name="evidence_report.txt",
                mime="text/plain"
            )
    
    with report_col2:
        if st.button("📈 Coverage Matrix", use_container_width=True):
            # Create coverage matrix report
            coverage_matrix = evidence_validation.get("coverage_matrix", {})
            coverage_report = json.dumps(coverage_matrix, indent=2)
            
            # Download
            st.download_button(
                "📥 Download Coverage Matrix",
                coverage_report,
                file_name="coverage_matrix.json",
                mime="application/json"
            )
    
    # Source attribution
    st.subheader("Source Attribution")
    
    source_attribution = cv_data.get("source_attribution", {})
    
    # Create source attribution report
    source_report = "Source Attribution Report\n\n"
    
    for source, attribution in source_attribution.items():
        source_report += f"Source: {source}\n"
        source_report += f"Contributions: {attribution.get('matches_contributed', 0)}\n"
        source_report += f"Sections: {', '.join(attribution.get('sections_used', []))}\n"
        source_report += f"Average Score: {attribution.get('avg_relevance_score', 0.0):.2f}\n\n"
        
        source_report += "Sample Contributions:\n"
        for contrib in attribution.get("sample_contributions", []):
            source_report += f"- {contrib.get('text', '')}\n"
        
        source_report += "\n---\n\n"
    
    # Download button
    st.download_button(
        "📥 Download Source Attribution",
        source_report,
        file_name="source_attribution.txt",
        mime="text/plain"
    )

def create_advanced_export_tab(cv_data: Dict[str, Any]):
    """Create advanced export tab."""
    st.markdown("""
    <p style="margin-bottom: 16px;">Configure advanced export options and formats.</p>
    """, unsafe_allow_html=True)
    
    # Citation depth
    st.subheader("Citation Depth")
    citation_depth = st.slider(
        "Select citation detail level",
        min_value=1,
        max_value=5,
        value=3,
        help="Higher values include more detailed citations"
    )
    
    # Evidence threshold
    st.subheader("Evidence Threshold")
    evidence_threshold = st.slider(
        "Minimum evidence confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        format="%.1f",
        help="Only include evidence above this confidence threshold"
    )
    
    # Custom export
    st.subheader("Custom Export")
    
    custom_col1, custom_col2 = st.columns(2)
    
    with custom_col1:
        if st.button("🔄 Export All Data", use_container_width=True):
            # Export all data as JSON
            all_data = {
                "cv_data": cv_data,
                "export_settings": {
                    "citation_depth": citation_depth,
                    "evidence_threshold": evidence_threshold
                }
            }
            
            # Download
            st.download_button(
                "📥 Download All Data",
                json.dumps(all_data, indent=2),
                file_name="cv_complete_data.json",
                mime="application/json"
            )
    
    with custom_col2:
        if st.button("📊 Export for ATS", use_container_width=True):
            # Create ATS-friendly version
            ats_text = create_ats_friendly_cv(cv_data)
            
            # Download
            st.download_button(
                "📥 Download ATS Version",
                ats_text,
                file_name="cv_ats_version.txt",
                mime="text/plain"
            )

def export_cv(cv_data: Dict[str, Any], template_id: str, output_format: str):
    """
    Export CV using the CV exporter.
    
    Args:
        cv_data: CV data
        template_id: Template ID
        output_format: Output format (text, docx, pdf, json)
    """
    try:
        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create output path
            output_path = os.path.join(temp_dir, f"cv.{output_format}")
            
            # Export CV
            exporter = CVExporter()
            result = exporter.export_cv(
                cv_data=cv_data,
                template_id=template_id,
                output_format=output_format,
                output_path=output_path
            )
            
            if result["status"] == "success":
                # Read the exported file
                if output_format == "text":
                    with open(output_path, "r") as f:
                        content = f.read()
                    
                    # Download button
                    st.download_button(
                        "📥 Download Text CV",
                        content,
                        file_name=f"cv_{template_id}.txt",
                        mime="text/plain"
                    )
                
                elif output_format == "json":
                    with open(output_path, "r") as f:
                        content = f.read()
                    
                    # Download button
                    st.download_button(
                        "📥 Download JSON CV",
                        content,
                        file_name=f"cv_{template_id}.json",
                        mime="application/json"
                    )
                
                elif output_format == "docx":
                    with open(output_path, "rb") as f:
                        content = f.read()
                    
                    # Download button
                    st.download_button(
                        "📥 Download DOCX CV",
                        content,
                        file_name=f"cv_{template_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                elif output_format == "pdf":
                    with open(output_path, "rb") as f:
                        content = f.read()
                    
                    # Download button
                    st.download_button(
                        "📥 Download PDF CV",
                        content,
                        file_name=f"cv_{template_id}.pdf",
                        mime="application/pdf"
                    )
                
                st.success(f"✅ CV exported successfully in {output_format.upper()} format!")
            else:
                st.error(f"❌ Export failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        logger.error(f"Error exporting CV: {e}")
        st.error(f"❌ Export error: {str(e)}")

def create_ats_friendly_cv(cv_data: Dict[str, Any]) -> str:
    """
    Create an ATS-friendly version of the CV.
    
    Args:
        cv_data: CV data
        
    Returns:
        ATS-friendly CV text
    """
    # Contact information
    contact_info = cv_data.get("contact_info", {})
    ats_text = f"{contact_info.get('name', '')}\n"
    ats_text += f"{contact_info.get('email', '')} | {contact_info.get('phone', '')} | {contact_info.get('location', '')}\n\n"
    
    # Summary
    summary = cv_data.get("summary", {})
    ats_text += "PROFESSIONAL SUMMARY\n"
    ats_text += "===================\n"
    ats_text += f"{summary.get('content', '')}\n\n"
    
    # Experience
    experience = cv_data.get("experience", {})
    ats_text += "WORK EXPERIENCE\n"
    ats_text += "===============\n"
    ats_text += f"{experience.get('content', '')}\n\n"
    
    # Skills
    skills = cv_data.get("skills", {})
    ats_text += "SKILLS\n"
    ats_text += "======\n"
    ats_text += f"{skills.get('content', '')}\n\n"
    
    # Education
    education = cv_data.get("education", {})
    ats_text += "EDUCATION\n"
    ats_text += "=========\n"
    ats_text += f"{education.get('content', '')}\n\n"
    
    return ats_text

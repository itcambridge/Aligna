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
import sys

# Configure logging to write to both console and file
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler('export_debug.log')
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def create_export_section(cv_data: Dict[str, Any], evidence_validation: Dict[str, Any]):
    """
    Create an enhanced export section with citation preservation.
    
    Args:
        cv_data: CV data with sections and evidence
        evidence_validation: Evidence validation results
    """
    # Log the structure of the input data
    logger.info(f"Creating export section with cv_data keys: {list(cv_data.keys())}")
    logger.info(f"Evidence validation keys: {list(evidence_validation.keys()) if evidence_validation else 'None'}")
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
    # Initialize session state for export content if it doesn't exist
    if 'export_content' not in st.session_state:
        logger.info("Initializing export session state")
        st.session_state.export_content = None
        st.session_state.export_filename = None
        st.session_state.export_mime = None
        st.session_state.export_format = None
        logger.info("Export session state initialized")
    
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
    
    # Initialize export format state if it doesn't exist
    if 'export_format_clicked' not in st.session_state:
        st.session_state.export_format_clicked = None
    
    # Format selection
    st.subheader("Select Format")
    
    format_col1, format_col2, format_col3, format_col4 = st.columns(4)
    
    # Define callback functions for each button
    def on_text_click():
        logger.info("Text button clicked")
        st.session_state.export_format_clicked = "text"
    
    def on_docx_click():
        logger.info("DOCX button clicked")
        st.session_state.export_format_clicked = "docx"
    
    def on_pdf_click():
        logger.info("PDF button clicked")
        st.session_state.export_format_clicked = "pdf"
    
    def on_json_click():
        logger.info("JSON button clicked")
        st.session_state.export_format_clicked = "json"
    
    # Create buttons with callbacks
    with format_col1:
        st.button("📝 Text", on_click=on_text_click, use_container_width=True)
    
    with format_col2:
        st.button("📄 DOCX", on_click=on_docx_click, use_container_width=True)
    
    with format_col3:
        st.button("📊 PDF", on_click=on_pdf_click, use_container_width=True)
    
    with format_col4:
        st.button("🔄 JSON", on_click=on_json_click, use_container_width=True)
    
    # Process the export if a format was clicked
    if st.session_state.export_format_clicked:
        logger.info(f"Processing export for format: {st.session_state.export_format_clicked}")
        export_format = st.session_state.export_format_clicked
        export_cv(cv_data, selected_template, export_format)
        # Reset the clicked state to prevent repeated exports
        st.session_state.export_format_clicked = None
    
    # Display download button if content is available
    if st.session_state.export_content is not None:
        st.download_button(
            f"📥 Download CV ({st.session_state.export_format.upper()})",
            st.session_state.export_content,
            file_name=st.session_state.export_filename,
            mime=st.session_state.export_mime,
            key="download_cv_button"
        )
        
        st.success(f"✅ CV exported successfully in {st.session_state.export_format.upper()} format! Click the download button above.")
    
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
    # Initialize session state for evidence exports if they don't exist
    if 'evidence_report_content' not in st.session_state:
        st.session_state.evidence_report_content = None
        st.session_state.evidence_report_filename = None
        st.session_state.evidence_report_mime = None
    
    if 'coverage_matrix_content' not in st.session_state:
        st.session_state.coverage_matrix_content = None
        st.session_state.coverage_matrix_filename = None
        st.session_state.coverage_matrix_mime = None
    
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
            
            # Store in session state
            st.session_state.evidence_report_content = evidence_report
            st.session_state.evidence_report_filename = "evidence_report.txt"
            st.session_state.evidence_report_mime = "text/plain"
    
    with report_col2:
        if st.button("📈 Coverage Matrix", use_container_width=True):
            # Create coverage matrix report
            coverage_matrix = evidence_validation.get("coverage_matrix", {})
            coverage_report = json.dumps(coverage_matrix, indent=2)
            
            # Store in session state
            st.session_state.coverage_matrix_content = coverage_report
            st.session_state.coverage_matrix_filename = "coverage_matrix.json"
            st.session_state.coverage_matrix_mime = "application/json"
    
    # Display download buttons if content is available
    if st.session_state.evidence_report_content is not None:
        st.download_button(
            "📥 Download Evidence Report",
            st.session_state.evidence_report_content,
            file_name=st.session_state.evidence_report_filename,
            mime=st.session_state.evidence_report_mime,
            key="download_evidence_report_button"
        )
        
        st.success("✅ Evidence report generated successfully! Click the download button above.")
    
    if st.session_state.coverage_matrix_content is not None:
        st.download_button(
            "📥 Download Coverage Matrix",
            st.session_state.coverage_matrix_content,
            file_name=st.session_state.coverage_matrix_filename,
            mime=st.session_state.coverage_matrix_mime,
            key="download_coverage_matrix_button"
        )
        
        st.success("✅ Coverage matrix generated successfully! Click the download button above.")
    
    # Source attribution
    st.subheader("Source Attribution")
    
    # Initialize session state for source attribution if it doesn't exist
    if 'source_attribution_content' not in st.session_state:
        st.session_state.source_attribution_content = None
        st.session_state.source_attribution_filename = None
        st.session_state.source_attribution_mime = None
    
    if st.button("📋 Generate Source Attribution", use_container_width=True):
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
        
        # Store in session state
        st.session_state.source_attribution_content = source_report
        st.session_state.source_attribution_filename = "source_attribution.txt"
        st.session_state.source_attribution_mime = "text/plain"
    
    # Display download button if content is available
    if st.session_state.source_attribution_content is not None:
        st.download_button(
            "📥 Download Source Attribution",
            st.session_state.source_attribution_content,
            file_name=st.session_state.source_attribution_filename,
            mime=st.session_state.source_attribution_mime,
            key="download_source_attribution_button"
        )
        
        st.success("✅ Source attribution report generated successfully! Click the download button above.")

def create_advanced_export_tab(cv_data: Dict[str, Any]):
    """Create advanced export tab."""
    # Initialize session state for advanced exports if they don't exist
    if 'all_data_content' not in st.session_state:
        st.session_state.all_data_content = None
        st.session_state.all_data_filename = None
        st.session_state.all_data_mime = None
    
    if 'ats_content' not in st.session_state:
        st.session_state.ats_content = None
        st.session_state.ats_filename = None
        st.session_state.ats_mime = None
    
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
            
            # Store in session state
            st.session_state.all_data_content = json.dumps(all_data, indent=2)
            st.session_state.all_data_filename = "cv_complete_data.json"
            st.session_state.all_data_mime = "application/json"
    
    with custom_col2:
        if st.button("📊 Export for ATS", use_container_width=True):
            # Create ATS-friendly version
            ats_text = create_ats_friendly_cv(cv_data)
            
            # Store in session state
            st.session_state.ats_content = ats_text
            st.session_state.ats_filename = "cv_ats_version.txt"
            st.session_state.ats_mime = "text/plain"
    
    # Display download buttons if content is available
    if st.session_state.all_data_content is not None:
        st.download_button(
            "📥 Download All Data",
            st.session_state.all_data_content,
            file_name=st.session_state.all_data_filename,
            mime=st.session_state.all_data_mime,
            key="download_all_data_button"
        )
        
        st.success("✅ Complete data export generated successfully! Click the download button above.")
    
    if st.session_state.ats_content is not None:
        st.download_button(
            "📥 Download ATS Version",
            st.session_state.ats_content,
            file_name=st.session_state.ats_filename,
            mime=st.session_state.ats_mime,
            key="download_ats_button"
        )
        
        st.success("✅ ATS-friendly version generated successfully! Click the download button above.")

def export_cv(cv_data: Dict[str, Any], template_id: str, output_format: str):
    """
    Export CV using the CV exporter.
    
    Args:
        cv_data: CV data
        template_id: Template ID
        output_format: Output format (text, docx, pdf, json)
    """
    # Store the CV data in session state to preserve it
    if 'cv_data_backup' not in st.session_state:
        st.session_state.cv_data_backup = cv_data
        logger.info("CV data backed up to session state")
    try:
        # Log the export attempt
        logger.info(f"Attempting to export CV in {output_format} format using {template_id} template")
        
        # Create exports directory if it doesn't exist
        exports_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(exports_dir, exist_ok=True)
        logger.info(f"Using exports directory: {exports_dir}")
        
        # Create a CV exporter instance
        exporter = CVExporter()
        
        # Generate output file path in the exports directory
        if output_format == "text":
            output_file = os.path.join(exports_dir, f"cv_{template_id}.txt")
            mime_type = "text/plain"
        elif output_format == "docx":
            output_file = os.path.join(exports_dir, f"cv_{template_id}.docx")
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif output_format == "pdf":
            output_file = os.path.join(exports_dir, f"cv_{template_id}.pdf")
            mime_type = "application/pdf"
        elif output_format == "json":
            output_file = os.path.join(exports_dir, f"cv_{template_id}.json")
            mime_type = "application/json"
        else:
            raise ValueError(f"Unsupported format: {output_format}")
        
        # Log the output file path
        logger.info(f"Output file path: {output_file}")
        
        # Check if the directory is writable
        if not os.access(os.path.dirname(output_file), os.W_OK):
            logger.error(f"Directory {os.path.dirname(output_file)} is not writable")
            raise PermissionError(f"Directory {os.path.dirname(output_file)} is not writable")
        
        # Export the CV
        result = exporter.export_cv(
            cv_data=cv_data,
            template_id=template_id,
            output_format=output_format,
            output_path=output_file
        )
        
        # Log the export result
        logger.info(f"Export result: {result}")
        
        # Check if export was successful
        if result["status"] != "success":
            logger.error(f"Export failed: {result.get('error', 'Unknown error')}")
            raise ValueError(f"Export failed: {result.get('error', 'Unknown error')}")
        
        # Read the file content
        if output_format in ["docx", "pdf"]:
            # Binary content
            logger.info(f"Reading binary content from {output_file}")
            with open(output_file, 'rb') as f:
                content = f.read()
            logger.info(f"Read {len(content)} bytes of binary content")
        else:
            # Text content
            if "content" in result:
                # Use content from result if available
                logger.info("Using content from result")
                content = result["content"]
                if output_format == "json" and isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                    logger.info("Converted JSON dict to string")
            else:
                # Read from file
                logger.info(f"Reading text content from {output_file}")
                with open(output_file, 'r') as f:
                    content = f.read()
                logger.info(f"Read {len(content)} characters of text content")
        
        # Store in session state for download
        logger.info("Storing content in session state")
        st.session_state.export_content = content
        st.session_state.export_filename = os.path.basename(output_file)
        st.session_state.export_mime = mime_type
        st.session_state.export_format = output_format
        logger.info(f"Session state updated: format={output_format}, mime={mime_type}, filename={os.path.basename(output_file)}")
    
    except Exception as e:
        logger.error(f"Error exporting CV: {e}")
        st.error(f"❌ Export error: {str(e)}")
        
        # Log the exception traceback
        import traceback
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        
        # Log the CV data structure (without sensitive content)
        logger.info(f"CV data keys: {list(cv_data.keys())}")
        
        # Fallback to text format if export fails
        if output_format in ["docx", "pdf"]:
            logger.info(f"Falling back to text format for {output_format}")
            content = create_text_cv(cv_data)
            content += f"\n\nNote: {output_format.upper()} export failed. This is a text version instead."
            
            # Store fallback in session state
            logger.info("Storing fallback content in session state")
            st.session_state.export_content = content
            st.session_state.export_filename = f"cv_{template_id}.txt"
            st.session_state.export_mime = "text/plain"
            st.session_state.export_format = "text (fallback)"
            logger.info(f"Session state updated with fallback: format=text (fallback)")

def create_text_cv(cv_data: Dict[str, Any]) -> str:
    """
    Create a simple text version of the CV.
    
    Args:
        cv_data: CV data
        
    Returns:
        Text CV
    """
    # Contact information
    contact_info = cv_data.get("contact_info", {})
    text_cv = f"{contact_info.get('name', '')}\n"
    text_cv += f"{contact_info.get('email', '')} | {contact_info.get('phone', '')} | {contact_info.get('location', '')}\n\n"
    
    # Summary
    summary = cv_data.get("summary", {})
    if summary and summary.get("content"):
        text_cv += "PROFESSIONAL SUMMARY\n"
        text_cv += "===================\n"
        text_cv += f"{summary.get('content', '')}\n\n"
    
    # Check if we have the generated CV structure
    if "generated_cv" in cv_data:
        generated_cv = cv_data.get("generated_cv", {})
        
        # Sections
        sections = generated_cv.get("sections", [])
        for section in sections:
            section_title = section.get("title", "")
            bullets = section.get("bullets", [])
            
            if section_title and bullets:
                text_cv += f"{section_title.upper()}\n"
                text_cv += "=" * len(section_title) + "\n"
                
                for bullet in bullets:
                    text_cv += f"• {bullet.get('text', '')}\n"
                
                text_cv += "\n"
    else:
        # Experience
        experience = cv_data.get("experience", {})
        if experience and experience.get("content"):
            text_cv += "WORK EXPERIENCE\n"
            text_cv += "===============\n"
            text_cv += f"{experience.get('content', '')}\n\n"
        
        # Skills
        skills = cv_data.get("skills", {})
        if skills and skills.get("content"):
            text_cv += "SKILLS\n"
            text_cv += "======\n"
            text_cv += f"{skills.get('content', '')}\n\n"
        
        # Education
        education = cv_data.get("education", {})
        if education and education.get("content"):
            text_cv += "EDUCATION\n"
            text_cv += "=========\n"
            text_cv += f"{education.get('content', '')}\n\n"
    
    # Evidence summary
    text_cv += "EVIDENCE SUMMARY\n"
    text_cv += "===============\n"
    
    # Get all citations
    all_citations = []
    if "match_evidence" in cv_data and "matches" in cv_data["match_evidence"]:
        all_citations = cv_data["match_evidence"]["matches"]
    elif "cv_matching" in cv_data and "matches" in cv_data["cv_matching"]:
        all_citations = cv_data["cv_matching"]["matches"]
    elif "matches" in cv_data:
        all_citations = cv_data["matches"]
    
    # Add citations
    for i, citation in enumerate(all_citations):
        text_cv += f"{i+1}. {citation.get('text', '')}\n"
        text_cv += f"   Source: {citation.get('cv_id', 'Unknown')} | Section: {citation.get('section', 'Unknown')} | Score: {citation.get('score', 0.0):.2f}\n\n"
    
    return text_cv

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

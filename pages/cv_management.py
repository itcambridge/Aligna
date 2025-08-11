"""
CV Management Dashboard - Manage your CV knowledge base
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from main import GroundedCVGenerator
from auth.supabase_auth import StreamlitAuth
import logging
import json
from datetime import datetime

# Import UI components
from ui.components.evidence_display import render_interactive_cv_section
from ui.components.enhanced_export import create_export_section

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="CV Management - Grounded CV Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS matching the landing page Apple-style design
st.markdown("""
<style>
    /* Hide Streamlit elements */
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main {
        padding: 0;
        margin: 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 50%, #f1f5f9 100%);
        min-height: 100vh;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Back to Generate link */
    .back-link {
        position: fixed;
        top: 24px;
        left: 24px;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(229, 231, 235, 0.8);
        border-radius: 24px;
        padding: 8px 20px;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
        text-decoration: none;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
        z-index: 1000;
    }
    
    .back-link:hover {
        background: rgba(255, 255, 255, 1);
        border-color: #d1d5db;
        text-decoration: none;
        color: #111827;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Main sections */
    .section {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border: 0;
        border-radius: 24px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
        padding: 48px;
        margin: 24px auto;
        max-width: 1200px;
    }
    
    .section-title {
        font-size: 36px;
        font-weight: 300;
        color: #111827;
        text-align: center;
        margin-bottom: 32px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(229, 231, 235, 0.8);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    }
    
    .metric-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 16px auto;
        font-size: 24px;
    }
    
    .metric-number {
        font-size: 36px;
        font-weight: 300;
        color: #111827;
        margin-bottom: 8px;
    }
    
    .metric-label {
        font-size: 14px;
        color: #6b7280;
    }
    
    /* Upload Area */
    .upload-area {
        background: #ffffff;
        border: 2px dashed #e5e7eb;
        border-radius: 16px;
        padding: 48px;
        text-align: center;
        transition: all 0.2s ease;
        margin: 32px 0;
    }
    
    .upload-area:hover {
        border-color: #3b82f6;
        background: #f8fafc;
    }
    
    .upload-title {
        font-size: 24px;
        font-weight: 300;
        color: #111827;
        margin-bottom: 16px;
    }
    
    .upload-subtitle {
        font-size: 16px;
        color: #6b7280;
        margin-bottom: 32px;
    }
    
    /* Buttons matching landing page */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 16px 48px !important;
        font-size: 18px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3) !important;
        height: auto !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 20px 40px rgba(59, 130, 246, 0.4) !important;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
    }
    
    /* Quick Actions Grid */
    .quick-actions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-top: 32px;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .section {
            padding: 32px 24px;
            margin: 16px;
        }
        
        .section-title {
            font-size: 28px;
        }
        
        .back-link {
            left: 16px;
            top: 16px;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize authentication
    auth = StreamlitAuth()
    
    # Check authentication
    user_id = auth.require_authentication()
    
    if not user_id:
        # User is not authenticated, login page is shown
        return
    
    # Back to Generate link
    st.markdown("""
    <a href="/" target="_self" class="back-link">
        ← Generate CV
    </a>
    """, unsafe_allow_html=True)
    
    # Initialize user-specific generator
    generator = GroundedCVGenerator(user_id=user_id)
    
    # Get user's CV collection
    cv_stats = generator.get_user_cv_collection(user_id)
    
    # Main content with padding for the back link
    st.markdown('<div style="padding-top: 80px;"></div>', unsafe_allow_html=True)
    
    # CV Collection Overview - Display CV collection stats
    if cv_stats["total_cvs"] > 0:
        col1_stats, col2_stats, col3_stats, col4_stats = st.columns(4)
        
        with col1_stats:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon" style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white;">👥</div>
                <div class="metric-number">{cv_stats['total_cvs']}</div>
                <div class="metric-label">Total CVs</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2_stats:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon" style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); color: white;">📄</div>
                <div class="metric-number">{cv_stats['total_chunks']}</div>
                <div class="metric-label">Total Sections</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3_stats:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white;">🎯</div>
                <div class="metric-number">{cv_stats['unique_sections']}</div>
                <div class="metric-label">Unique Skills</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4_stats:
            avg_sections = cv_stats['total_chunks'] / cv_stats['total_cvs'] if cv_stats['total_cvs'] > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white;">📊</div>
                <div class="metric-number">{avg_sections:.1f}</div>
                <div class="metric-label">Avg Sections/CV</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #6b7280; max-width: 600px; margin: 0 auto;">
            <h3 style="color: #111827; font-weight: 300;">No CVs in your knowledge base yet</h3>
            <p>Upload your first CV below to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        
    # CV Upload Section
    st.markdown("""
    <div style="max-width: 800px; margin: 48px auto;">
        <div class="upload-area">
            <h3 class="upload-title">📄 Add CV to Knowledge Base</h3>
            <p class="upload-subtitle">Upload PDF or DOCX files to expand your CV knowledge base</p>
    """, unsafe_allow_html=True)
        
    uploaded_file = st.file_uploader(
        "Choose a CV file",
        type=['pdf', 'docx'],
        label_visibility="collapsed",
        key="cv_upload"
    )
    
    if uploaded_file:
        col1_upload, col2_upload, col3_upload = st.columns([1, 2, 1])
        with col2_upload:
            if st.button("🚀 Process CV", use_container_width=True):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    with st.spinner("📄 Processing CV file..."):
                        # Process the CV upload
                        cv_result = generator.process_cv_upload(tmp_file_path, user_id)
                        
                        if cv_result["status"] == "success":
                            st.success(f"✅ CV processed successfully! Added {cv_result['total_chunks']} sections to your knowledge base")
                            st.rerun()  # Refresh the page to show updated stats
                        else:
                            st.error(f"❌ CV processing failed: {cv_result.get('error')}")
                    
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    st.error(f"❌ Error processing CV: {str(e)}")
                    logger.error(f"Error processing CV upload: {e}")
                    if 'tmp_file_path' in locals():
                        try:
                            os.unlink(tmp_file_path)
                        except:
                            pass
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Quick Actions Section
    st.markdown("""
    <div style="max-width: 800px; margin: 48px auto;">
        <div class="quick-actions-grid">
    """, unsafe_allow_html=True)
    
    col1_quick, col2_quick, col3_quick = st.columns(3)
    
    with col1_quick:
        if st.button("🚀 Generate CV Now", use_container_width=True, type="primary"):
            st.switch_page("web_app.py")
    
    with col2_quick:
        if st.button("📊 Export CV Data", use_container_width=True):
            # Show export options using our enhanced export component
            if "export_view" not in st.session_state:
                st.session_state.export_view = True
            else:
                st.session_state.export_view = not st.session_state.export_view
    
    with col3_quick:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Show export section if export view is active
    if st.session_state.get("export_view", False) and cv_stats["total_cvs"] > 0:
        st.markdown("""
        <div style="max-width: 1000px; margin: 48px auto;">
            <h2 style="text-align: center; font-weight: 300; color: #111827; margin-bottom: 24px;">
                Export Options
            </h2>
        """, unsafe_allow_html=True)
        
        # Get the most recent CV data
        recent_cv_data = generator.get_most_recent_cv(user_id)
        
        if recent_cv_data:
            # Create sample evidence validation data
            evidence_validation = {
                "status": "success",
                "coverage_matrix": {
                    "summary": {
                        "total_requirements": 10,
                        "covered_requirements": 7,
                        "overall_coverage_rate": 0.7,
                        "average_confidence": 0.8,
                        "critical_gaps": ["Cloud deployment experience", "Team leadership"]
                    },
                    "detailed_matrix": [
                        {
                            "text": "Python programming",
                            "category": "required_skill",
                            "covered": True,
                            "confidence": 0.92,
                            "evidence_count": 3
                        },
                        {
                            "text": "Machine learning",
                            "category": "required_skill",
                            "covered": True,
                            "confidence": 0.87,
                            "evidence_count": 2
                        },
                        {
                            "text": "Cloud deployment",
                            "category": "required_skill",
                            "covered": False,
                            "confidence": 0.2,
                            "evidence_count": 0
                        }
                    ],
                    "gaps": [
                        {
                            "requirement": "Cloud deployment experience",
                            "recommendations": ["Consider adding cloud deployment experience to your CV"]
                        },
                        {
                            "requirement": "Team leadership",
                            "recommendations": ["Add specific examples of team leadership"]
                        }
                    ]
                }
            }
            
            # Use our enhanced export component
            create_export_section(recent_cv_data, evidence_validation)
        else:
            st.info("No CV data available for export. Generate a CV first.")
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

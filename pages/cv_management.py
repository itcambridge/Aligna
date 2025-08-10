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

# Custom CSS for Apple-style design (shared with main page)
st.markdown("""
<style>
    .main {
        padding: 0;
        margin: 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    .header {
        text-align: center;
        padding: 60px 20px 30px 20px;
        background: rgba(255, 255, 255, 0.9);
        margin-bottom: 40px;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .nav-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 40px;
        background: rgba(255, 255, 255, 0.95);
        margin-bottom: 40px;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .management-section {
        background: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 20px auto;
        max-width: 1200px;
        backdrop-filter: blur(10px);
    }
    
    .cv-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .cv-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 10px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
        margin: 20px 0;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: rgba(102, 126, 234, 0.1);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    .nav-button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 25px;
        font-size: 14px;
        font-weight: 500;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.6);
        text-decoration: none;
        color: white;
    }
    
    .danger-button {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 20px;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
    }
    
    .danger-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(220, 53, 69, 0.6);
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
    
    # Navigation header
    st.markdown("""
    <div class="nav-header">
        <div>
            <h2 style="margin: 0; color: #2c3e50;">📚 CV Management Dashboard</h2>
            <p style="margin: 5px 0 0 0; color: #7f8c8d;">Manage your CV knowledge base</p>
        </div>
        <div>
            <a href="/" target="_self" class="nav-button">🚀 Generate CV</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # User info in sidebar
    with st.sidebar:
        auth.show_user_info()
        st.markdown("---")
        st.markdown("### Navigation")
        if st.button("🚀 Generate CV", use_container_width=True):
            st.switch_page("web_app.py")
    
    # Initialize user-specific generator
    generator = GroundedCVGenerator(user_id=user_id)
    
    # Get user's CV collection
    cv_stats = generator.get_user_cv_collection(user_id)
    
    # Main content
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        # CV Collection Overview
        st.markdown("""
        <div class="management-section">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2c3e50;">
                📊 Your CV Knowledge Base Overview
            </h2>
        """, unsafe_allow_html=True)
        
        # Display CV collection stats
        if cv_stats["total_cvs"] > 0:
            col1_stats, col2_stats, col3_stats, col4_stats = st.columns(4)
            
            with col1_stats:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 1.1rem;">Total CVs</h3>
                    <h1 style="margin: 10px 0; font-size: 2.5rem;">{cv_stats['total_cvs']}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col2_stats:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 1.1rem;">Total Sections</h3>
                    <h1 style="margin: 10px 0; font-size: 2.5rem;">{cv_stats['total_chunks']}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col3_stats:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 1.1rem;">Unique Skills</h3>
                    <h1 style="margin: 10px 0; font-size: 2.5rem;">{cv_stats['unique_sections']}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col4_stats:
                avg_sections = cv_stats['total_chunks'] / cv_stats['total_cvs'] if cv_stats['total_cvs'] > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 1.1rem;">Avg Sections/CV</h3>
                    <h1 style="margin: 10px 0; font-size: 2.5rem;">{avg_sections:.1f}</h1>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; color: #7f8c8d;">
                <h3>No CVs in your knowledge base yet</h3>
                <p>Upload your first CV below to get started!</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # CV Upload Section
        st.markdown("""
        <div class="management-section">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2c3e50;">
                📤 Upload New CV
            </h2>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="upload-area">
            <h3 style="color: #667eea; margin-bottom: 20px;">📄 Add CV to Knowledge Base</h3>
            <p style="color: #7f8c8d; margin-bottom: 20px;">Upload PDF or DOCX files to expand your CV knowledge base</p>
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
        
        # CV Library Section
        if cv_stats["total_cvs"] > 0:
            st.markdown("""
            <div class="management-section">
                <h2 style="text-align: center; margin-bottom: 30px; color: #2c3e50;">
                    📚 Your CV Library
                </h2>
            """, unsafe_allow_html=True)
            
            # Search and filter options
            col1_search, col2_search = st.columns([3, 1])
            with col1_search:
                search_term = st.text_input("🔍 Search CVs", placeholder="Search by name, skills, or content...")
            with col2_search:
                sort_option = st.selectbox("Sort by", ["Most Recent", "Name", "Sections Count"])
            
            # Display CVs
            cv_list = cv_stats["cv_list"]
            
            # Apply search filter
            if search_term:
                cv_list = [cv for cv in cv_list if search_term.lower() in cv['name'].lower() or 
                          search_term.lower() in cv['preview_text'].lower() or
                          any(search_term.lower() in section.lower() for section in cv['sections'])]
            
            # Apply sorting
            if sort_option == "Name":
                cv_list = sorted(cv_list, key=lambda x: x['name'])
            elif sort_option == "Sections Count":
                cv_list = sorted(cv_list, key=lambda x: x['total_chunks'], reverse=True)
            # Most Recent is default order
            
            if cv_list:
                for i, cv in enumerate(cv_list):
                    st.markdown(f"""
                    <div class="cv-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0 0 10px 0; color: #2c3e50;">📄 {cv['name']}</h3>
                                <p style="margin: 5px 0; color: #7f8c8d;"><strong>Sections:</strong> {cv['total_chunks']} | <strong>Skills:</strong> {', '.join(cv['sections'][:3])}{'...' if len(cv['sections']) > 3 else ''}</p>
                                <p style="margin: 10px 0 0 0; color: #6c757d; font-size: 0.9rem;"><strong>Preview:</strong> {cv['preview_text'][:150]}...</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons for each CV
                    col1_actions, col2_actions, col3_actions, col4_actions = st.columns([1, 1, 1, 3])
                    
                    with col1_actions:
                        if st.button("👁️ View", key=f"view_{i}"):
                            st.session_state[f"show_cv_{i}"] = not st.session_state.get(f"show_cv_{i}", False)
                    
                    with col2_actions:
                        if st.button("📊 Stats", key=f"stats_{i}"):
                            st.session_state[f"show_stats_{i}"] = not st.session_state.get(f"show_stats_{i}", False)
                    
                    with col3_actions:
                        if st.button("🗑️ Delete", key=f"delete_{i}", type="secondary"):
                            st.session_state[f"confirm_delete_{i}"] = True
                    
                    # Show CV details if requested
                    if st.session_state.get(f"show_cv_{i}", False):
                        with st.expander(f"📄 {cv['name']} - Full Details", expanded=True):
                            st.write(f"**Total Sections:** {cv['total_chunks']}")
                            st.write(f"**All Sections:** {', '.join(cv['sections'])}")
                            st.write(f"**Preview Text:**")
                            st.text_area("Content Preview", cv['preview_text'], height=200, disabled=True, key=f"preview_{i}")
                    
                    # Show stats if requested
                    if st.session_state.get(f"show_stats_{i}", False):
                        with st.expander(f"📊 {cv['name']} - Statistics", expanded=True):
                            col1_stat, col2_stat, col3_stat = st.columns(3)
                            with col1_stat:
                                st.metric("Total Sections", cv['total_chunks'])
                            with col2_stat:
                                st.metric("Unique Skills", len(cv['sections']))
                            with col3_stat:
                                st.metric("Content Length", f"{len(cv['preview_text'])} chars")
                            
                            st.write("**Section Breakdown:**")
                            for section in cv['sections']:
                                st.write(f"• {section}")
                    
                    # Confirm delete dialog
                    if st.session_state.get(f"confirm_delete_{i}", False):
                        st.warning(f"⚠️ Are you sure you want to delete '{cv['name']}'? This action cannot be undone.")
                        col1_confirm, col2_confirm, col3_confirm = st.columns([1, 1, 2])
                        with col1_confirm:
                            if st.button("✅ Yes, Delete", key=f"confirm_yes_{i}", type="primary"):
                                # TODO: Implement CV deletion
                                st.error("🚧 CV deletion feature coming soon!")
                                st.session_state[f"confirm_delete_{i}"] = False
                        with col2_confirm:
                            if st.button("❌ Cancel", key=f"confirm_no_{i}"):
                                st.session_state[f"confirm_delete_{i}"] = False
                    
                    st.markdown("---")
            else:
                st.info("🔍 No CVs found matching your search criteria.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Quick Actions Section
        st.markdown("""
        <div class="management-section">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2c3e50;">
                ⚡ Quick Actions
            </h2>
        """, unsafe_allow_html=True)
        
        col1_quick, col2_quick, col3_quick = st.columns(3)
        
        with col1_quick:
            if st.button("🚀 Generate CV Now", use_container_width=True, type="primary"):
                st.switch_page("web_app.py")
        
        with col2_quick:
            if st.button("📊 Export CV Data", use_container_width=True):
                # TODO: Implement export functionality
                st.info("🚧 Export feature coming soon!")
        
        with col3_quick:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

import streamlit as st
import os
import tempfile
from pathlib import Path
from main import GroundedCVGenerator
from auth.supabase_auth import StreamlitAuth
import logging
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Grounded CV Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Apple-style design
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
        padding: 80px 20px 40px 20px;
        background: rgba(255, 255, 255, 0.9);
        margin-bottom: 60px;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .upload-section {
        background: rgba(255, 255, 255, 0.95);
        padding: 60px 40px;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 40px auto;
        max-width: 800px;
        backdrop-filter: blur(10px);
    }
    
    .result-section {
        background: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 40px auto;
        max-width: 800px;
        backdrop-filter: blur(10px);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 15px 40px;
        font-size: 18px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
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
    
    .progress-container {
        background: rgba(255, 255, 255, 0.9);
        padding: 30px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px;
    }
    
    .download-button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
    }
    
    .download-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.6);
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
    
    # User is authenticated, show main interface
    # Navigation header
    st.markdown("""
    <div class="nav-header">
        <div>
            <h1 style="margin: 0; color: #2c3e50; font-size: 2.5rem;">🚀 Grounded CV Generator</h1>
            <p style="margin: 5px 0 0 0; color: #7f8c8d;">AI-powered CV generation from your knowledge base</p>
        </div>
        <div>
            <a href="/cv_management" target="_self" class="nav-button">📚 Manage CVs</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # User info in sidebar
    with st.sidebar:
        auth.show_user_info()
        st.markdown("---")
        st.markdown("### Navigation")
        if st.button("📚 Manage CVs", use_container_width=True):
            st.switch_page("pages/cv_management.py")
    
    # Initialize user-specific generator
    generator = GroundedCVGenerator(user_id=user_id)
    
    # Get user's CV collection
    cv_stats = generator.get_user_cv_collection(user_id)
    
    # Check if user has CVs in knowledge base
    if cv_stats["total_cvs"] == 0:
        # No CVs - redirect to CV management
        st.markdown("""
        <div class="upload-section">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2c3e50; font-weight: 300;">
                📚 Welcome to Grounded CV Generator
            </h2>
            <div style="text-align: center; padding: 40px; color: #7f8c8d;">
                <h3>No CVs in your knowledge base yet</h3>
                <p>You need to upload at least one CV before you can generate tailored CVs.</p>
                <br>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📚 Go to CV Management", use_container_width=True, type="primary"):
                st.switch_page("pages/cv_management.py")
        
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Main content - Pure generation interface
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Simple generation section
        st.markdown("""
        <div class="upload-section">
            <h2 style="text-align: center; margin-bottom: 40px; color: #2c3e50; font-weight: 300;">
                💼 Job Description
            </h2>
        """, unsafe_allow_html=True)
        
        job_description = st.text_area(
            "Enter the job description, requirements, and qualifications...",
            height=300,
            placeholder="Paste the job description here...",
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Process button
        col1_btn, col2_btn, col3_btn = st.columns([1, 2, 1])
        with col2_btn:
            process_button = st.button(
                "🚀 Generate Grounded CV",
                use_container_width=True,
                type="primary"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Processing section - Pure generation from knowledge base
        if process_button and job_description:
            # Generate from knowledge base (we know user has CVs since we checked above)
            st.markdown("""
            <div class="progress-container">
                <h3 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
                    🧠 Generating CV from Your Knowledge Base
                </h3>
            """, unsafe_allow_html=True)
            
            try:
                with st.spinner("🔍 Searching across all your CVs..."):
                    result = generator.generate_cv_from_knowledge_base(user_id, job_description)
                    
                    if result["status"] == "success":
                        st.success(f"✅ Found relevant experience from {len(result['matches_summary']['cv_sources_used'])} CVs")
                    else:
                        raise Exception(f"Knowledge base generation failed: {result.get('error')}")
                
                with st.spinner("📋 Analyzing job requirements..."):
                    st.success("✅ Analyzed job requirements and matched against your experience")
                
                with st.spinner("✍️ Generating comprehensive CV..."):
                    st.success("✅ Generated grounded CV with evidence from multiple CVs")
                
                st.success("✅ Knowledge base processing complete!")
                
                # Results section for knowledge base generation
                st.markdown("""
                <div class="result-section">
                    <h2 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
                        🧠 Knowledge Base Results
                    </h2>
                """, unsafe_allow_html=True)
                
                # Knowledge base specific metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    cv_sources_used = result.get('matches_summary', {}).get('cv_sources_used', [])
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>CVs Used</h3>
                        <h2>{len(cv_sources_used)}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    total_matches = result.get('matches_summary', {}).get('total_matches', 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Matches Found</h3>
                        <h2>{total_matches}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    match_rate = result.get('matches_summary', {}).get('match_rate', 0) * 100
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Match Rate</h3>
                        <h2>{match_rate:.0f}%</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    total_chunks = result.get('cv_stats', {}).get('total_chunks', 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Total Experience</h3>
                        <h2>{total_chunks}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Source attribution
                st.markdown("### 📊 Experience Sources")
                for cv_id, attribution in result['source_attribution'].items():
                    with st.expander(f"📄 {attribution['cv_name']} - {attribution['matches_contributed']} contributions"):
                        st.write(f"**Sections used:** {', '.join(attribution['sections_used'])}")
                        st.write(f"**Average relevance:** {attribution['avg_relevance_score']:.2f}")
                        st.write("**Sample contributions:**")
                        for contrib in attribution['sample_contributions']:
                            st.write(f"- {contrib['text']} (Score: {contrib['score']:.2f})")
                
                # Download section
                st.markdown("""
                <div style="text-align: center; margin: 40px 0;">
                    <h3 style="color: #2c3e50; margin-bottom: 20px;">Download Your Results</h3>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    st.download_button(
                        "📄 Generated CV",
                        result['cv_text'],
                        file_name="knowledge_base_cv.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col2:
                    st.download_button(
                        "📊 Evidence Report",
                        result['evidence_report'],
                        file_name="evidence_report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col3:
                    source_report = f"""Source Attribution Report

Generated from {len(result['source_attribution'])} CVs
Total matches: {result['matches_summary']['total_matches']}
Match rate: {result['matches_summary']['match_rate']:.2%}

CV Sources:
"""
                    for cv_id, attr in result['source_attribution'].items():
                        source_report += f"""
{attr['cv_name']}:
- Contributions: {attr['matches_contributed']}
- Sections: {', '.join(attr['sections_used'])}
- Avg Score: {attr['avg_relevance_score']:.2f}
"""
                    
                    st.download_button(
                        "📋 Source Attribution",
                        source_report,
                        file_name="source_attribution.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                # Show CV preview
                st.markdown("""
                <div style="margin: 40px 0;">
                    <h3 style="color: #2c3e50; margin-bottom: 20px;">Generated CV Preview</h3>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea;">
                """, unsafe_allow_html=True)
                
                preview_text = result['cv_text'][:800] + "..." if len(result['cv_text']) > 800 else result['cv_text']
                st.text(preview_text)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                logger.error(f"Error generating from knowledge base: {e}")
        
        elif process_button:
            if not job_description:
                st.warning("⚠️ Please enter a job description")

if __name__ == "__main__":
    main()

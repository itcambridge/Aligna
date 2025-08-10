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
    
    /* Apple-style Navigation */
    .apple-nav {
        position: sticky;
        top: 0;
        z-index: 50;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(229, 231, 235, 0.8);
        padding: 16px 0;
    }
    
    .nav-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .nav-logo {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .nav-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    .nav-text h1 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        color: #111827;
    }
    
    .nav-text p {
        margin: 0;
        font-size: 14px;
        color: #6b7280;
    }
    
    .nav-button {
        background: transparent;
        border: 1px solid #e5e7eb;
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
    }
    
    .nav-button:hover {
        background: #f9fafb;
        border-color: #d1d5db;
        text-decoration: none;
        color: #111827;
    }
    
    /* Hero Section */
    .hero-section {
        padding: 80px 24px 128px 24px;
        text-align: center;
        max-width: 1000px;
        margin: 0 auto;
    }
    
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #dbeafe;
        color: #1d4ed8;
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 32px;
    }
    
    .hero-title {
        font-size: 72px;
        font-weight: 300;
        color: #111827;
        line-height: 1.1;
        margin-bottom: 24px;
        letter-spacing: -0.02em;
    }
    
    .hero-gradient-text {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 500;
    }
    
    .hero-subtitle {
        font-size: 20px;
        color: #6b7280;
        line-height: 1.6;
        margin-bottom: 48px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Stats Section */
    .stats-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 48px;
        margin-bottom: 64px;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-number {
        font-size: 36px;
        font-weight: 300;
        color: #111827;
        margin-bottom: 4px;
    }
    
    .stat-label {
        font-size: 14px;
        color: #6b7280;
    }
    
    .stat-divider {
        width: 1px;
        height: 48px;
        background: #e5e7eb;
    }
    
    /* Main Interface Card */
    .main-card {
        max-width: 768px;
        margin: 0 auto;
        padding: 0 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
    }
    
    .interface-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border: 0;
        border-radius: 24px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
        padding: 48px;
        width: 100%;
    }
    
    /* CV Management Link */
    .cv-management-link {
        position: fixed;
        top: 24px;
        right: 24px;
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
    
    .cv-management-link:hover {
        background: rgba(255, 255, 255, 1);
        border-color: #d1d5db;
        text-decoration: none;
        color: #111827;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .card-header {
        text-align: center;
        margin-bottom: 48px;
    }
    
    .card-icon {
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 24px auto;
        font-size: 32px;
    }
    
    .card-title {
        font-size: 36px;
        font-weight: 300;
        color: #111827;
        margin-bottom: 16px;
    }
    
    .card-subtitle {
        font-size: 16px;
        color: #6b7280;
    }
    
    /* Custom Textarea */
    .stTextArea > div > div > textarea {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 20px;
        font-size: 16px;
        line-height: 1.5;
        min-height: 200px;
        resize: none;
        transition: all 0.2s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        outline: none;
    }
    
    /* Generate Button */
    .generate-button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 24px;
        padding: 16px 48px;
        font-size: 18px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 32px auto 0 auto;
    }
    
    .generate-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(59, 130, 246, 0.4);
    }
    
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
    
    /* Results Section */
    .results-section {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 24px 128px 24px;
    }
    
    .results-header {
        text-align: center;
        margin-bottom: 64px;
    }
    
    .success-badge {
        background: #dcfce7;
        color: #166534;
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 24px;
        display: inline-block;
    }
    
    .results-title {
        font-size: 48px;
        font-weight: 300;
        color: #111827;
        margin-bottom: 16px;
    }
    
    .results-subtitle {
        font-size: 20px;
        color: #6b7280;
    }
    
    /* Metric Cards */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 24px;
        margin-bottom: 64px;
    }
    
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
    
    /* Download Section */
    .download-section {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 48px;
        text-align: center;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
    }
    
    .download-title {
        font-size: 24px;
        font-weight: 300;
        color: #111827;
        margin-bottom: 32px;
    }
    
    .download-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 48px;
    }
    
    .download-button {
        background: transparent;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 20px;
        font-size: 16px;
        font-weight: 500;
        color: #374151;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        height: 64px;
    }
    
    .download-button:hover {
        background: #f9fafb;
        border-color: #d1d5db;
        transform: translateY(-2px);
    }
    
    /* CV Preview */
    .cv-preview {
        background: #f8fafc;
        border-radius: 16px;
        padding: 32px;
        text-align: left;
        margin-top: 48px;
    }
    
    .preview-title {
        font-size: 18px;
        font-weight: 500;
        color: #111827;
        margin-bottom: 16px;
    }
    
    .preview-content {
        color: #374151;
        line-height: 1.6;
        font-size: 14px;
        font-family: 'SF Mono', Monaco, monospace;
    }
    
    /* Welcome Section */
    .welcome-section {
        max-width: 600px;
        margin: 0 auto;
        padding: 80px 24px;
        text-align: center;
    }
    
    .welcome-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 48px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
    }
    
    .welcome-title {
        font-size: 36px;
        font-weight: 300;
        color: #111827;
        margin-bottom: 16px;
    }
    
    .welcome-subtitle {
        font-size: 18px;
        color: #6b7280;
        margin-bottom: 32px;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 48px;
        }
        
        .stats-container {
            flex-direction: column;
            gap: 24px;
        }
        
        .stat-divider {
            display: none;
        }
        
        .interface-card {
            padding: 32px 24px;
        }
        
        .nav-container {
            padding: 0 16px;
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
    
    # Initialize user-specific generator
    generator = GroundedCVGenerator(user_id=user_id)
    
    # Get user's CV collection
    cv_stats = generator.get_user_cv_collection(user_id)
    
    # Check if user has CVs in knowledge base
    if cv_stats["total_cvs"] == 0:
        # No CVs - redirect to CV management
        st.switch_page("pages/cv_management.py")
        return
    
    # Add CV Management link (moved to bottom right, smaller)
    st.markdown("""
    <a href="/cv_management" target="_self" class="cv-management-link" style="top: auto; bottom: 24px; font-size: 12px; padding: 6px 16px;">
        📄 Manage CVs
    </a>
    """, unsafe_allow_html=True)
    
    # Ultra-minimal interface - textarea at very top
    st.markdown("""
    <div style="padding: 24px; max-width: 768px; margin: 0 auto;">
    """, unsafe_allow_html=True)
    
    # Job description input
    job_description = st.text_area(
        "Enter the job description, requirements, and qualifications...",
        height=200,
        placeholder="Paste the job description here...",
        label_visibility="collapsed"
    )
    
    # Generate button
    col1_btn, col2_btn, col3_btn = st.columns([1, 2, 1])
    with col2_btn:
        process_button = st.button(
            "✨ Generate Grounded CV →",
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
            
            # Apple-style Results Section
            st.markdown("""
            <section class="results-section">
                <div class="results-header">
                    <div class="success-badge">✅ Generation Complete</div>
                    <h2 class="results-title">Your CV is ready</h2>
                    <p class="results-subtitle">Generated from your knowledge base with high relevance matching</p>
                </div>
                
                <div class="metrics-grid">
            """, unsafe_allow_html=True)
            
            # Apple-style metric cards
            cv_sources_used = result.get('matches_summary', {}).get('cv_sources_used', [])
            total_matches = result.get('matches_summary', {}).get('total_matches', 0)
            match_rate = result.get('matches_summary', {}).get('match_rate', 0) * 100
            total_chunks = result.get('cv_stats', {}).get('total_chunks', 0)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white;">👥</div>
                    <div class="metric-number">{len(cv_sources_used)}</div>
                    <div class="metric-label">CVs Used</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); color: white;">🎯</div>
                    <div class="metric-number">{total_matches}</div>
                    <div class="metric-label">Matches Found</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white;">📊</div>
                    <div class="metric-number">{match_rate:.0f}%</div>
                    <div class="metric-label">Match Rate</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white;">📄</div>
                    <div class="metric-number">{total_chunks}</div>
                    <div class="metric-label">Experience Points</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Source attribution
            st.markdown("### 📊 Experience Sources")
            for cv_id, attribution in result['source_attribution'].items():
                with st.expander(f"📄 {attribution['cv_name']} - {attribution['matches_contributed']} contributions"):
                    st.write(f"**Sections used:** {', '.join(attribution['sections_used'])}")
                    st.write(f"**Average relevance:** {attribution['avg_relevance_score']:.2f}")
                    st.write("**Sample contributions:**")
                    for contrib in attribution['sample_contributions']:
                        st.write(f"- {contrib['text']} (Score: {contrib['score']:.2f})")
            
            # Apple-style Download Section
            st.markdown("""
                <div class="download-section">
                    <h3 class="download-title">Download Your Results</h3>
                    <div class="download-grid">
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
            
            # Apple-style CV Preview
            st.markdown("""
                    </div>
                    <div class="cv-preview">
                        <h4 class="preview-title">CV Preview</h4>
                        <div class="preview-content">
            """, unsafe_allow_html=True)
            
            preview_text = result['cv_text'][:800] + "..." if len(result['cv_text']) > 800 else result['cv_text']
            st.text(preview_text)
            
            st.markdown("""
                        </div>
                    </div>
                </div>
            </section>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            logger.error(f"Error generating from knowledge base: {e}")
    
    elif process_button:
        if not job_description:
            st.warning("⚠️ Please enter a job description")

if __name__ == "__main__":
    main()

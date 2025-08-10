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
    # Header with user info
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown("""
        <div class="header">
            <h1 style="font-size: 3.5rem; font-weight: 300; margin-bottom: 20px; color: #2c3e50;">
                Grounded CV Generator
            </h1>
            <p style="font-size: 1.2rem; color: #7f8c8d; margin-bottom: 0;">
                AI-powered CV generation with evidence-based matching from your CV knowledge base
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        auth.show_user_info()
    
    # Initialize user-specific generator
    generator = GroundedCVGenerator(user_id=user_id)
    
    # Get user's CV collection
    cv_stats = generator.get_user_cv_collection(user_id)
    
    # Main content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # CV Knowledge Base Section
        if cv_stats["total_cvs"] > 0:
            st.markdown("""
            <div class="upload-section">
                <h2 style="text-align: center; margin-bottom: 30px; color: #2c3e50; font-weight: 300;">
                    📚 Your CV Knowledge Base
                </h2>
            """, unsafe_allow_html=True)
            
            # Display CV collection stats
            col1_stats, col2_stats, col3_stats = st.columns(3)
            with col1_stats:
                st.markdown(f"""
                <div class="metric-card" style="margin: 0;">
                    <h3 style="margin: 0; font-size: 1.2rem;">CVs</h3>
                    <h2 style="margin: 5px 0;">{cv_stats['total_cvs']}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2_stats:
                st.markdown(f"""
                <div class="metric-card" style="margin: 0;">
                    <h3 style="margin: 0; font-size: 1.2rem;">Sections</h3>
                    <h2 style="margin: 5px 0;">{cv_stats['total_chunks']}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3_stats:
                st.markdown(f"""
                <div class="metric-card" style="margin: 0;">
                    <h3 style="margin: 0; font-size: 1.2rem;">Skills</h3>
                    <h2 style="margin: 5px 0;">{cv_stats['unique_sections']}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Show CV list
            with st.expander("📋 View Your CV Collection", expanded=False):
                for cv in cv_stats["cv_list"]:
                    st.markdown(f"""
                    **{cv['name']}** - {cv['total_chunks']} sections  
                    *Sections: {', '.join(cv['sections'][:3])}{'...' if len(cv['sections']) > 3 else ''}*  
                    Preview: {cv['preview_text'][:100]}...
                    """)
                    st.markdown("---")
            
            st.markdown("""
            <div style="text-align: center; margin: 20px 0;">
                <p style="color: #667eea; font-weight: 500;">
                    💡 Smart Generation: We'll search across your entire CV history to find the best experience for any job
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # CV Upload Section (for adding new CVs or first-time users)
        st.markdown("""
        <div class="upload-section">
            <h2 style="text-align: center; margin-bottom: 40px; color: #2c3e50; font-weight: 300;">
                {} Your CV Collection
            </h2>
        """.format("Add to" if cv_stats["total_cvs"] > 0 else "Start"), unsafe_allow_html=True)
        
        if cv_stats["total_cvs"] > 0:
            # Show option to add new CV
            add_new_cv = st.checkbox("➕ Add a new CV to your knowledge base")
            
            if add_new_cv:
                st.markdown("""
                <div class="upload-area">
                    <h3 style="color: #667eea; margin-bottom: 20px;">📄 Upload Additional CV</h3>
                """, unsafe_allow_html=True)
                
                cv_file = st.file_uploader(
                    "Choose a CV file to add to your collection",
                    type=['pdf', 'docx'],
                    label_visibility="collapsed"
                )
                
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                cv_file = None
        else:
            # First-time user - show upload
            st.markdown("""
            <div class="upload-area">
                <h3 style="color: #667eea; margin-bottom: 20px;">📄 Upload Your First CV</h3>
            """, unsafe_allow_html=True)
            
            cv_file = st.file_uploader(
                "Choose a CV file",
                type=['pdf', 'docx'],
                label_visibility="collapsed"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Job description input
        st.markdown("""
        <div style="margin: 40px 0;">
            <h3 style="color: #667eea; margin-bottom: 20px;">💼 Job Description</h3>
        """, unsafe_allow_html=True)
        
        job_description = st.text_area(
            "Paste the job description here...",
            height=200,
            placeholder="Enter the job description, requirements, and qualifications...",
            label_visibility="collapsed"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            process_button = st.button(
                "🚀 Generate Grounded CV",
                use_container_width=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Processing section - Handle both new CV upload and knowledge base generation
        if process_button and job_description:
            # First, handle CV upload if there's a file
            if cv_file:
                st.markdown("""
                <div class="progress-container">
                    <h3 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
                        📄 Processing Your CV
                    </h3>
                """, unsafe_allow_html=True)
                
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{cv_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(cv_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    with st.spinner("📄 Processing CV file..."):
                        # Process the CV upload
                        cv_result = generator.process_cv_upload(tmp_file_path, user_id)
                        
                        if cv_result["status"] == "success":
                            st.success(f"✅ CV processed successfully! Added {cv_result['total_chunks']} sections to your knowledge base")
                            # Update CV stats after successful upload
                            cv_stats = generator.get_user_cv_collection(user_id)
                        else:
                            raise Exception(f"CV processing failed: {cv_result.get('error')}")
                    
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
                    return
            
            # Check if we should use knowledge base or need CV upload
            use_knowledge_base = cv_stats["total_cvs"] > 0
            
            if use_knowledge_base:
                # Generate from knowledge base
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
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>CVs Used</h3>
                            <h2>{len(result['matches_summary']['cv_sources_used'])}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Matches Found</h3>
                            <h2>{result['matches_summary']['total_matches']}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        match_rate = result['matches_summary']['match_rate'] * 100
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Match Rate</h3>
                            <h2>{match_rate:.0f}%</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Total Experience</h3>
                            <h2>{result['cv_stats']['total_chunks']}</h2>
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
            
            else:
                # Show warning if no CV file and no existing CVs
                if not cv_file:
                    st.warning("⚠️ Please upload a CV file or ensure you have existing CVs in your knowledge base")
        
        elif process_button:
            if not job_description:
                st.warning("⚠️ Please enter a job description")

if __name__ == "__main__":
    main()

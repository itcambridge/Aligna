import streamlit as st
import os
import tempfile
from pathlib import Path
from main import GroundedCVGenerator
from auth.supabase_auth import StreamlitAuth
import logging
import json
import uuid

# Import UI components
from ui.components.evidence_display import render_interactive_cv_section, render_cv_with_evidence
from ui.components.enhanced_export import create_export_section

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
    
    /* Evidence Validation Section */
    .evidence-section {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 32px;
        margin: 32px 0;
        border: 1px solid rgba(229, 231, 235, 0.8);
    }
    
    .evidence-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
    }
    
    .evidence-icon {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    
    .evidence-title {
        font-size: 20px;
        font-weight: 500;
        color: #111827;
    }
    
    .coverage-matrix {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 24px 0;
    }
    
    .coverage-item {
        background: #f8fafc;
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid #3b82f6;
    }
    
    .coverage-item.covered {
        border-left-color: #10b981;
    }
    
    .coverage-item.partial {
        border-left-color: #f59e0b;
    }
    
    .coverage-item.uncovered {
        border-left-color: #ef4444;
    }
    
    .coverage-status {
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .coverage-status.covered {
        color: #10b981;
    }
    
    .coverage-status.partial {
        color: #f59e0b;
    }
    
    .coverage-status.uncovered {
        color: #ef4444;
    }
    
    .coverage-text {
        font-size: 14px;
        color: #374151;
        margin-bottom: 8px;
    }
    
    .coverage-confidence {
        font-size: 12px;
        color: #6b7280;
    }
    
    /* Gap Analysis */
    .gap-analysis {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 20px;
        margin: 24px 0;
    }
    
    .gap-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
        color: #dc2626;
        font-weight: 500;
    }
    
    .gap-item {
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 3px solid #dc2626;
    }
    
    .gap-requirement {
        font-weight: 500;
        color: #111827;
        margin-bottom: 4px;
    }
    
    .gap-recommendation {
        font-size: 14px;
        color: #6b7280;
    }
    
    /* Risk Assessment */
    .risk-assessment {
        background: #fffbeb;
        border: 1px solid #fed7aa;
        border-radius: 12px;
        padding: 20px;
        margin: 24px 0;
    }
    
    .risk-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
        color: #d97706;
        font-weight: 500;
    }
    
    .risk-level {
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
    }
    
    .risk-level.low {
        background: #dcfce7;
        color: #166534;
    }
    
    .risk-level.medium {
        background: #fef3c7;
        color: #d97706;
    }
    
    .risk-level.high {
        background: #fee2e2;
        color: #dc2626;
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
    
    /* Welcome Page Styles */
    .welcome-section {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px 24px;
    }
    
    .welcome-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 48px;
        max-width: 800px;
        width: 100%;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(229, 231, 235, 0.8);
    }
    
    /* Gap Analysis Styles */
    .gap-analysis {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 20px;
        margin: 24px 0;
    }
    
    .gap-header {
        font-weight: 600;
        color: #dc2626;
        margin-bottom: 16px;
        font-size: 16px;
    }
    
    .gap-item {
        background: white;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #f87171;
    }
    
    .gap-requirement {
        font-weight: 600;
        color: #111827;
        margin-bottom: 8px;
    }
    
    .gap-recommendation {
        color: #6b7280;
        font-size: 14px;
    }
    
    /* Risk Assessment Styles */
    .risk-assessment {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 12px;
        padding: 20px;
        margin: 24px 0;
    }
    
    .risk-level {
        font-weight: 700;
        font-size: 14px;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 8px;
    }
    
    .risk-level.low {
        background: #dcfce7;
        color: #166534;
    }
    
    .risk-level.medium {
        background: #fef3c7;
        color: #92400e;
    }
    
    .risk-level.high {
        background: #fee2e2;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)

def show_welcome_page(user_id: str, cv_stats: dict):
    """Show welcome page for users with no CVs."""
    st.markdown("""
    <div class="welcome-section">
        <div class="welcome-card">
            <div class="card-header">
                <div class="card-icon">🚀</div>
                <h1 class="card-title">Welcome to Aligna</h1>
                <p class="card-subtitle">Your AI-powered CV generator with evidence validation</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <h2 style="color: #111827; font-weight: 300; margin-bottom: 16px;">
                    Get Started with Grounded CV Generation
                </h2>
                <p style="color: #6b7280; font-size: 16px; line-height: 1.6; margin-bottom: 32px;">
                    Upload your CVs to create a knowledge base, then generate tailored CVs with zero hallucinations.
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 40px 0;">
                <div style="background: #f8fafc; border-radius: 16px; padding: 24px; text-align: center;">
                    <div style="font-size: 32px; margin-bottom: 16px;">📄</div>
                    <h3 style="color: #111827; margin-bottom: 12px;">Upload Your CVs</h3>
                    <p style="color: #6b7280; margin-bottom: 20px;">Start by uploading your existing CVs to build your knowledge base</p>
                    <a href="/cv_management" target="_self" class="nav-button" style="display: inline-block;">
                        Manage CVs →
                    </a>
                </div>
                
                <div style="background: #f8fafc; border-radius: 16px; padding: 24px; text-align: center;">
                    <div style="font-size: 32px; margin-bottom: 16px;">🧪</div>
                    <h3 style="color: #111827; margin-bottom: 12px;">Try Demo Mode</h3>
                    <p style="color: #6b7280; margin-bottom: 20px;">Experience the system with sample data and see how it works</p>
                    <button onclick="showDemo()" class="nav-button" style="display: inline-block; cursor: pointer;">
                        Start Demo →
                    </button>
                </div>
            </div>
            
            <div style="background: #dbeafe; border-radius: 12px; padding: 20px; margin: 32px 0;">
                <h4 style="color: #1d4ed8; margin-bottom: 12px;">✨ What's New in Phase 1</h4>
                <ul style="color: #374151; margin: 0; padding-left: 20px;">
                    <li><strong>Evidence Validation:</strong> Every generated bullet has citations</li>
                    <li><strong>Coverage Matrix:</strong> See which job requirements are covered vs gaps</li>
                    <li><strong>Zero Hallucinations:</strong> Guaranteed evidence-based generation</li>
                    <li><strong>Risk Assessment:</strong> Hallucination risk levels and recommendations</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo functionality
    if st.button("🧪 Try Demo Mode", use_container_width=True, type="secondary"):
        st.session_state.demo_mode = True
        st.rerun()

def show_demo_interface(user_id: str, generator: GroundedCVGenerator):
    """Show demo interface with sample data."""
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
            <h3 style="color: #d97706; margin: 0;">🧪 Demo Mode</h3>
            <p style="color: #92400e; margin: 8px 0 0 0;">Using sample CV data to demonstrate the system</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add exit demo button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Exit Demo Mode", use_container_width=True, type="secondary"):
            st.session_state.demo_mode = False
            st.rerun()
    
    # Show the main interface (same as normal mode but with demo data)
    show_main_interface(user_id, generator, demo_mode=True)

def show_main_interface(user_id: str, generator: GroundedCVGenerator, demo_mode: bool = False):
    """Show the main CV generation interface."""
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
        placeholder="Paste the job description here..." + (" (Demo: Try 'Software Engineer with Python and Machine Learning experience')" if demo_mode else ""),
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
    
    # Processing section
    if process_button and job_description:
        if demo_mode:
            show_demo_results(job_description)
        else:
            show_generation_results(user_id, generator, job_description)

def show_demo_results(job_description: str):
    """Show demo results with sample data."""
    st.markdown("""
    <div class="progress-container">
        <h3 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
            🧪 Demo: Generating CV from Sample Knowledge Base
        </h3>
    """, unsafe_allow_html=True)
    
    # Simulate processing steps
    with st.spinner("🔍 Validating evidence coverage..."):
        import time
        time.sleep(1)
        st.success("✅ Evidence validation complete - 85.2% coverage")
    
    with st.spinner("📋 Analyzing job requirements..."):
        time.sleep(1)
        st.success("✅ Analyzed job requirements and matched against sample experience")
    
    with st.spinner("✍️ Generating grounded CV..."):
        time.sleep(1)
        st.success("✅ Generated grounded CV with evidence validation")
    
    st.success("✅ Demo processing complete!")
    
    # Show demo results
    st.markdown("""
    <section class="results-section">
        <div class="results-header">
            <div class="success-badge">✅ Demo Complete</div>
            <h2 class="results-title">Sample CV Generated</h2>
            <p class="results-subtitle">This is a demonstration of the evidence validation system</p>
        </div>
        
        <div class="metrics-grid">
    """, unsafe_allow_html=True)
    
    # Demo metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white;">👥</div>
            <div class="metric-number">3</div>
            <div class="metric-label">Sample CVs Used</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); color: white;">🎯</div>
            <div class="metric-number">24</div>
            <div class="metric-label">Matches Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white;">📊</div>
            <div class="metric-number">85%</div>
            <div class="metric-label">Match Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white;">📄</div>
            <div class="metric-number">156</div>
            <div class="metric-label">Experience Points</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Demo evidence validation section
    st.markdown("""
    <div class="evidence-section">
        <div class="evidence-header">
            <div class="evidence-icon" style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white;">🔍</div>
            <h3 class="evidence-title">Demo Evidence Validation Results</h3>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Coverage", "85.2%", "12/14 requirements")
    
    with col2:
        st.metric("Average Confidence", "78.5%", "Evidence quality score")
    
    with col3:
        st.metric("Critical Gaps", "2", "Required skills missing")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Demo download section
    st.markdown("""
    <div class="download-section">
        <h3 class="download-title">Demo Downloads</h3>
        <div class="download-grid">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.download_button(
            "📄 Sample CV",
            "This is a demo CV generated with evidence validation...",
            file_name="demo_cv.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        st.download_button(
            "📊 Evidence Report",
            "Demo evidence report showing citations and coverage...",
            file_name="demo_evidence_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        st.download_button(
            "📋 Coverage Matrix",
            "Demo coverage matrix showing requirement analysis...",
            file_name="demo_coverage_matrix.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("""
        </div>
    </div>
    </section>
    """, unsafe_allow_html=True)

def show_generation_results(user_id: str, generator: GroundedCVGenerator, job_description: str):
    """Show actual generation results."""
    # Generate from knowledge base (we know user has CVs since we checked above)
    st.markdown("""
    <div class="progress-container">
        <h3 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
            🧠 Generating CV from Your Knowledge Base
        </h3>
    """, unsafe_allow_html=True)
    
    try:
        with st.spinner("🔍 Validating evidence coverage..."):
            result = generator.generate_cv_from_knowledge_base(user_id, job_description)
            
            if result["status"] == "success":
                st.success(f"✅ Evidence validation complete - {result['evidence_validation']['coverage_matrix']['summary']['overall_coverage_rate']:.1%} coverage")
            else:
                raise Exception(f"Knowledge base generation failed: {result.get('error')}")
        
        with st.spinner("📋 Analyzing job requirements..."):
            st.success("✅ Analyzed job requirements and matched against your experience")
        
        with st.spinner("✍️ Generating grounded CV..."):
            st.success("✅ Generated grounded CV with evidence validation")
        
        st.success("✅ Knowledge base processing complete!")
        
        # Show results (existing code)
        show_results_section(result)
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        logger.error(f"Error generating from knowledge base: {e}")

def show_results_section(result: dict):
    """Show the results section."""
    # Apple-style Results Section
    st.markdown("""
    <section class="results-section">
        <div class="results-header">
            <div class="success-badge">✅ Generation Complete</div>
            <h2 class="results-title">Your CV is ready</h2>
            <p class="results-subtitle">Generated from your knowledge base with evidence validation</p>
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
    
    # Evidence Validation Section
    evidence_validation = result.get('evidence_validation', {})
    if evidence_validation:
        show_evidence_validation_section(evidence_validation)
    
    # Interactive CV with Evidence
    st.header("📄 Generated CV with Interactive Evidence")
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(20px); border-radius: 24px; 
         padding: 32px; margin: 32px 0; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);">
    """, unsafe_allow_html=True)
    
    # Use the new interactive CV renderer
    render_cv_with_evidence(result)
    
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
    
    # Enhanced Export Section
    create_export_section(result, evidence_validation)

def show_evidence_validation_section(evidence_validation: dict):
    """Show evidence validation section."""
    st.markdown("""
    <div class="evidence-section">
        <div class="evidence-header">
            <div class="evidence-icon" style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white;">🔍</div>
            <h3 class="evidence-title">Evidence Validation Results</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Coverage Matrix
    coverage_matrix = evidence_validation.get('coverage_matrix', {})
    summary = coverage_matrix.get('summary', {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Overall Coverage",
            f"{summary.get('overall_coverage_rate', 0):.1%}",
            f"{summary.get('covered_requirements', 0)}/{summary.get('total_requirements', 0)} requirements"
        )
    
    with col2:
        st.metric(
            "Average Confidence",
            f"{summary.get('average_confidence', 0):.1%}",
            "Evidence quality score"
        )
    
    with col3:
        st.metric(
            "Critical Gaps",
            len(summary.get('critical_gaps', [])),
            "Required skills missing"
        )
    
    # Detailed Coverage Matrix
    st.subheader("📋 Requirement Coverage Matrix")
    detailed_matrix = coverage_matrix.get('detailed_matrix', [])
    
    for req in detailed_matrix:
        status_class = "covered" if req.get('covered') else "partial" if req.get('confidence', 0) > 0.3 else "uncovered"
        status_text = "Covered" if req.get('covered') else "Partial" if req.get('confidence', 0) > 0.3 else "Uncovered"
        
        with st.expander(f"{status_text}: {req.get('text', '')[:50]}..."):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Category:** {req.get('category', '').replace('_', ' ').title()}")
                st.write(f"**Confidence:** {req.get('confidence', 0):.1%}")
                st.write(f"**Evidence Count:** {req.get('evidence_count', 0)}")
            
            with col2:
                if req.get('evidence'):
                    st.write("**Sample Evidence:**")
                    for i, evidence in enumerate(req.get('evidence', [])[:2]):
                        st.write(f"{i+1}. {evidence.get('snippet', '')[:100]}...")
    
    # Gap Analysis
    gaps = coverage_matrix.get('gaps', [])
    if gaps:
        st.markdown("""
        <div class="gap-analysis">
            <div class="gap-header">
                ⚠️ Gaps Identified
            </div>
        """, unsafe_allow_html=True)
        
        for gap in gaps[:5]:  # Show top 5 gaps
            st.markdown(f"""
            <div class="gap-item">
                <div class="gap-requirement">{gap.get('requirement', '')}</div>
                <div class="gap-recommendation">{gap.get('recommendations', [''])[0] if gap.get('recommendations') else 'No specific recommendation available'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Risk Assessment
    hallucination_risk = evidence_validation.get('hallucination_risk', {})
    if hallucination_risk:
        risk_level = hallucination_risk.get('risk_level', 'low')
        risk_color = {
            'low': '#10b981',
            'medium': '#f59e0b', 
            'high': '#ef4444'
        }.get(risk_level, '#6b7280')
        
        st.markdown(f"""
        <div class="risk-assessment">
            <div class="gap-header" style="color: {risk_color};">
                🛡️ Hallucination Risk Assessment
            </div>
            <div class="risk-level {risk_level}">{risk_level.upper()} RISK</div>
            <p style="margin-top: 12px; color: #6b7280;">
                {hallucination_risk.get('recommendations', [''])[0] if hallucination_risk.get('recommendations') else 'Risk assessment complete'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_download_section(result: dict):
    """Show download section."""
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

def main():
    # Initialize authentication
    auth = StreamlitAuth()
    
    # Check authentication
    user_id = auth.require_authentication()
    
    if not user_id:
        # User is not authenticated, login page is shown
        return
    
    # Check for demo mode
    demo_mode = st.session_state.get('demo_mode', False)
    
    # Initialize user-specific generator
    generator = GroundedCVGenerator(user_id=user_id)
    
    # Get user's CV collection
    cv_stats = generator.get_user_cv_collection(user_id)
    
    # If in demo mode, show demo interface
    if demo_mode:
        show_demo_interface(user_id, generator)
        return
    
    # Check if user has CVs in knowledge base
    if cv_stats["total_cvs"] == 0:
        # No CVs - show welcome page with options
        show_welcome_page(user_id, cv_stats)
        return
    
    # Show the main interface
    show_main_interface(user_id, generator, demo_mode=False)

if __name__ == "__main__":
    main()

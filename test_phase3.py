"""
Test script for Phase 3 implementation: UI/UX Evidence Experience.
"""

import streamlit as st
import json
import os
from ui.components.evidence_display import render_interactive_cv_section, render_cv_with_evidence
from ui.components.enhanced_export import create_export_section

def test_interactive_evidence_display():
    """Test the interactive evidence display components."""
    st.title("Phase 3 Test: Interactive Evidence Experience")
    
    st.markdown("""
    This test demonstrates the interactive evidence display components implemented in Phase 3.
    These components allow users to click on bullet points to see the source evidence.
    """)
    
    # Create sample bullets with evidence
    bullets = [
        {
            "text": "Developed machine learning models using Python and scikit-learn for customer churn prediction.",
            "citations": [
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "snippet": "Developed machine learning models using Python and scikit-learn for customer churn prediction, achieving 85% accuracy.",
                    "score": 0.92
                }
            ],
            "confidence": 0.92,
            "risk_flags": []
        },
        {
            "text": "Implemented deep learning solutions with TensorFlow for image classification tasks.",
            "citations": [
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "snippet": "Implemented deep learning solutions with TensorFlow for image classification tasks, improving accuracy by 30%.",
                    "score": 0.87
                }
            ],
            "confidence": 0.87,
            "risk_flags": ["metric_inferred"]
        },
        {
            "text": "Optimized Python code for 30% performance improvement in data processing pipeline.",
            "citations": [
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "snippet": "Optimized Python code for significant performance improvement in data processing pipeline.",
                    "score": 0.75
                }
            ],
            "confidence": 0.75,
            "risk_flags": ["metric_inferred", "scope_inferred"]
        },
        {
            "text": "Led a team of 5 developers to deliver a machine learning project on time and under budget.",
            "citations": [],
            "confidence": 0.3,
            "risk_flags": ["no_direct_evidence", "role_inferred", "scope_inferred"]
        }
    ]
    
    # Test interactive CV section
    st.header("Interactive CV Section Test")
    render_interactive_cv_section("Work Experience", bullets)
    
    st.markdown("""
    ### Instructions
    - Click on the 📝 icon to see the evidence for each bullet point
    - Notice how bullets are color-coded based on confidence
    - Bullets with ⚠️ icons have risk flags (hover to see details)
    """)
    
    # Create sample CV data
    cv_data = {
        "contact_info": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": "San Francisco, CA"
        },
        "summary": {
            "content": "Experienced software engineer with expertise in Python, machine learning, and cloud technologies."
        },
        "experience": {
            "content": "• Developed machine learning models using Python and scikit-learn for customer churn prediction.\n• Implemented deep learning solutions with TensorFlow for image classification tasks.\n• Optimized Python code for 30% performance improvement in data processing pipeline.\n• Led a team of 5 developers to deliver a machine learning project on time and under budget."
        },
        "skills": {
            "content": "• Python\n• Machine Learning\n• TensorFlow\n• AWS\n• Docker\n• Kubernetes"
        },
        "education": {
            "content": "• M.S. Computer Science, Stanford University\n• B.S. Computer Engineering, MIT"
        },
        "match_evidence": {
            "matches": [
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "text": "Developed machine learning models using Python and scikit-learn for customer churn prediction, achieving 85% accuracy.",
                    "score": 0.92
                },
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "text": "Implemented deep learning solutions with TensorFlow for image classification tasks, improving accuracy by 30%.",
                    "score": 0.87
                },
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "text": "Optimized Python code for significant performance improvement in data processing pipeline.",
                    "score": 0.75
                }
            ]
        }
    }
    
    # Test complete CV with evidence
    st.header("Complete CV with Evidence Test")
    render_cv_with_evidence(cv_data)
    
    # Test enhanced export functionality
    st.header("Enhanced Export Test")
    
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
    
    create_export_section(cv_data, evidence_validation)

def main():
    """Run the Phase 3 test."""
    test_interactive_evidence_display()

if __name__ == "__main__":
    main()

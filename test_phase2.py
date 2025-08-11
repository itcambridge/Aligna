"""
Test script for Phase 2 implementation: Generation Contracts & Templates.
"""

import os
import json
from agents.cv_writer.bullet_generator import BulletGenerator, BulletInput
from export.cv_exporter import CVExporter

def test_bullet_generator():
    """Test the bullet generator with sample data."""
    print("Testing Bullet Generator...")
    
    # Create a bullet generator
    generator = BulletGenerator()
    
    # Sample requirement and evidence
    requirement = "Experience with Python and machine learning"
    evidence_snippets = [
        "Developed machine learning models using Python and scikit-learn for customer churn prediction.",
        "Implemented deep learning solutions with TensorFlow for image classification tasks.",
        "Optimized Python code for 30% performance improvement in data processing pipeline."
    ]
    
    # Generate a bullet
    bullet_input = BulletInput(
        requirement=requirement,
        evidence_snippets=evidence_snippets,
        allowed_claims_only=True,
        style_preference="action"
    )
    
    bullet_output = generator.generate_bullet(bullet_input)
    
    # Print results
    print("\nGenerated Bullet:")
    print(f"- {bullet_output.bullet}")
    
    print("\nCitations:")
    for citation in bullet_output.citations:
        print(f"- {citation.cv_id}: {citation.snippet[:50]}...")
    
    print("\nRisk Flags:")
    for flag in bullet_output.risk_flags:
        print(f"- {flag}")
    
    print(f"\nConfidence: {bullet_output.confidence:.2f}")
    print(f"Evidence Coverage: {bullet_output.evidence_coverage:.2f}")
    
    return bullet_output

def test_cv_exporter():
    """Test the CV exporter with sample data."""
    print("\nTesting CV Exporter...")
    
    # Create a CV exporter
    exporter = CVExporter()
    
    # Print available templates
    templates = exporter.get_available_templates()
    print("\nAvailable Templates:")
    for template in templates:
        print(f"- {template['id']}: {template['name']} - {template['description']}")
    
    # Sample CV data
    cv_data = {
        "contact_info": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/johndoe"
        },
        "summary": {
            "content": "Experienced software engineer with expertise in Python, machine learning, and cloud technologies."
        },
        "skills": {
            "content": "• Python\n• Machine Learning\n• TensorFlow\n• AWS\n• Docker\n• Kubernetes"
        },
        "experience": {
            "content": "• Developed machine learning models using Python and scikit-learn for customer churn prediction.\n• Implemented deep learning solutions with TensorFlow for image classification tasks.\n• Optimized Python code for 30% performance improvement in data processing pipeline."
        },
        "education": {
            "content": "• M.S. Computer Science, Stanford University\n• B.S. Computer Engineering, MIT"
        },
        "match_evidence": {
            "matches": [
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "text": "Developed machine learning models using Python and scikit-learn for customer churn prediction.",
                    "score": 0.92
                },
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "text": "Implemented deep learning solutions with TensorFlow for image classification tasks.",
                    "score": 0.87
                },
                {
                    "cv_id": "cv_123",
                    "section": "Experience",
                    "text": "Optimized Python code for 30% performance improvement in data processing pipeline.",
                    "score": 0.85
                }
            ]
        }
    }
    
    # Export CV in different formats
    for template_id in ["classic", "concise", "impact"]:
        # Export as text
        output_path = f"export/output/{template_id}_cv.txt"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        result = exporter.export_cv(
            cv_data=cv_data,
            template_id=template_id,
            output_format="text",
            output_path=output_path
        )
        
        print(f"\nExported {template_id} CV to {output_path}")
        
        # Print a sample of the content
        content = result.get("content", "")
        print(f"\nSample content ({len(content)} chars):")
        print(content[:300] + "..." if len(content) > 300 else content)
    
    return result

def main():
    """Run all tests."""
    bullet_output = test_bullet_generator()
    export_result = test_cv_exporter()
    
    print("\nAll tests completed successfully!")
    
    # Return results for inspection
    return {
        "bullet_output": bullet_output,
        "export_result": export_result
    }

if __name__ == "__main__":
    main()

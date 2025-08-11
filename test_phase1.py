#!/usr/bin/env python3
"""
Test script for Phase 1 - Evidence Validation System
Tests the requirement scoring, coverage matrix, and evidence validation.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.evidence_validator import EvidenceValidator
from agents.job_breakdown.job_analyzer import JobRequirements
from main import GroundedCVGenerator

def test_evidence_validation():
    """Test the evidence validation system."""
    print("🧪 Testing Phase 1 - Evidence Validation System")
    print("=" * 60)
    
    # Initialize the evidence validator
    validator = EvidenceValidator()
    
    # Create sample job requirements
    job_requirements = JobRequirements(
        skills_required=["Python", "Machine Learning", "SQL"],
        skills_preferred=["Docker", "AWS"],
        experience=["3+ years software development"],
        qualifications=["Bachelor's in Computer Science"],
        industry="Technology",
        level="Mid-level"
    )
    
    # Test with a sample user ID
    user_id = "test_user_123"
    
    print(f"📋 Job Requirements:")
    print(f"   Required Skills: {job_requirements.skills_required}")
    print(f"   Preferred Skills: {job_requirements.skills_preferred}")
    print(f"   Experience: {job_requirements.experience}")
    print(f"   Qualifications: {job_requirements.qualifications}")
    print()
    
    try:
        # Test evidence validation
        print("🔍 Validating evidence coverage...")
        validation_result = validator.validate_evidence(
            job_requirements=job_requirements,
            user_id=user_id,
            top_k=5
        )
        
        if validation_result["status"] == "success":
            print("✅ Evidence validation completed successfully!")
            
            # Display results
            coverage_matrix = validation_result["coverage_matrix"]
            summary = coverage_matrix["summary"]
            
            print(f"\n📊 Coverage Summary:")
            print(f"   Total Requirements: {summary['total_requirements']}")
            print(f"   Covered Requirements: {summary['covered_requirements']}")
            print(f"   Partial Requirements: {summary['partial_requirements']}")
            print(f"   Uncovered Requirements: {summary['uncovered_requirements']}")
            print(f"   Overall Coverage Rate: {summary['overall_coverage_rate']:.1%}")
            print(f"   Average Confidence: {summary['average_confidence']:.1%}")
            
            # Display gaps
            gaps = coverage_matrix["gaps"]
            if gaps:
                print(f"\n⚠️  Gaps Found ({len(gaps)}):")
                for gap in gaps[:3]:  # Show first 3 gaps
                    print(f"   • {gap['requirement']} ({gap['gap_type']})")
            
            # Display risk assessment
            risk = validation_result["hallucination_risk"]
            print(f"\n🛡️  Hallucination Risk: {risk['risk_level'].upper()}")
            for rec in risk['recommendations'][:2]:
                print(f"   • {rec}")
            
            return True
            
        else:
            print(f"❌ Evidence validation failed: {validation_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during evidence validation: {e}")
        return False

def test_grounded_cv_generator():
    """Test the integrated grounded CV generator with evidence validation."""
    print("\n🚀 Testing Integrated Grounded CV Generator")
    print("=" * 60)
    
    # Initialize the generator
    generator = GroundedCVGenerator()
    
    # Sample job description
    job_description = """
    Software Engineer - Machine Learning
    
    We are looking for a Software Engineer with expertise in machine learning and Python development.
    
    Required Skills:
    - Python programming
    - Machine learning algorithms
    - SQL database experience
    - 3+ years of software development experience
    
    Preferred Skills:
    - Docker containerization
    - AWS cloud services
    - Deep learning frameworks
    
    Qualifications:
    - Bachelor's degree in Computer Science or related field
    """
    
    user_id = "test_user_123"
    
    try:
        print("🔍 Testing evidence validation integration...")
        
        # Test evidence validation
        validation_result = generator.validate_evidence_coverage(
            job_requirements={
                "skills_required": ["Python", "Machine Learning", "SQL"],
                "skills_preferred": ["Docker", "AWS"],
                "experience": ["3+ years software development"],
                "qualifications": ["Bachelor's in Computer Science"],
                "industry": "Technology",
                "level": "Mid-level"
            },
            user_id=user_id
        )
        
        if validation_result["status"] == "success":
            print("✅ Evidence validation integration working!")
            
            # Display key metrics
            coverage_matrix = validation_result["coverage_matrix"]
            summary = coverage_matrix["summary"]
            
            print(f"   Coverage Rate: {summary['overall_coverage_rate']:.1%}")
            print(f"   Requirements Covered: {summary['covered_requirements']}/{summary['total_requirements']}")
            print(f"   Critical Gaps: {len(summary['critical_gaps'])}")
            
            return True
        else:
            print(f"❌ Evidence validation integration failed: {validation_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during integration test: {e}")
        return False

def main():
    """Run all Phase 1 tests."""
    print("🎯 Phase 1 - Evidence Validation System Tests")
    print("=" * 60)
    
    # Test 1: Evidence Validation System
    test1_passed = test_evidence_validation()
    
    # Test 2: Integrated Generator
    test2_passed = test_grounded_cv_generator()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    print(f"Evidence Validation System: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Integrated Generator: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All Phase 1 tests passed! Evidence validation system is working correctly.")
        print("\n✅ Key Features Implemented:")
        print("   • Requirement scoring with evidence coverage")
        print("   • Coverage matrix with gap analysis")
        print("   • Hallucination risk assessment")
        print("   • Evidence integrity validation")
        print("   • Integration with main workflow")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    
    return test1_passed and test2_passed

if __name__ == "__main__":
    main()

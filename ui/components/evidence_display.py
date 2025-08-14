"""
Interactive evidence display components for Streamlit.
"""

import streamlit as st
import re
from typing import Dict, List, Any, Optional
import json
import uuid

def add_citation_markers(text: str, citations: List[Dict[str, Any]], citation_style: str = "superscript") -> str:
    """
    Add citation markers to text.
    
    Args:
        text: Text to add citations to
        citations: List of citation objects
        citation_style: Style of citation markers (superscript, bracket, footnote)
        
    Returns:
        Text with citation markers
    """
    if not citations:
        return text
    
    # Create a unique ID for this set of citations
    citation_id = str(uuid.uuid4())[:8]
    
    # Add citation marker at the end of the text
    if citation_style == "superscript":
        marker = f'<sup class="citation-marker" data-citations="{citation_id}">📝</sup>'
    elif citation_style == "bracket":
        marker = f'<span class="citation-marker" data-citations="{citation_id}">[📝]</span>'
    elif citation_style == "footnote":
        marker = f'<sup class="citation-marker" data-citations="{citation_id}">[{len(citations)}]</sup>'
    else:
        marker = f'<span class="citation-marker" data-citations="{citation_id}">📝</span>'
    
    # Store citations in session state for retrieval by JavaScript
    if "citations" not in st.session_state:
        st.session_state.citations = {}
    
    st.session_state.citations[citation_id] = citations
    
    # Add marker to the end of the text
    return f'{text} {marker}'

def create_interactive_bullet(
    bullet_text: str,
    citations: List[Dict[str, Any]],
    confidence: float,
    risk_flags: List[str],
    bullet_id: Optional[str] = None
) -> str:
    """
    Create an interactive bullet point with citation markers and risk indicators.
    
    Args:
        bullet_text: The bullet point text
        citations: List of citation objects
        confidence: Confidence score (0-1)
        risk_flags: List of risk flag strings
        bullet_id: Optional bullet ID
        
    Returns:
        HTML for the interactive bullet
    """
    # Generate ID if not provided
    if not bullet_id:
        bullet_id = f"bullet_{str(uuid.uuid4())[:8]}"
    
    # Determine confidence class
    if confidence >= 0.8:
        confidence_class = "high-confidence"
    elif confidence >= 0.5:
        confidence_class = "medium-confidence"
    else:
        confidence_class = "low-confidence"
    
    # Add citation markers
    text_with_citations = add_citation_markers(bullet_text, citations)
    
    # Add risk indicators if any
    risk_indicators = ""
    if risk_flags:
        risk_tooltip = ", ".join(risk_flags)
        risk_indicators = f'<span class="risk-indicator" title="{risk_tooltip}">⚠️</span>'
    
    # Create the interactive bullet HTML
    bullet_html = f"""
    <div class="interactive-bullet {confidence_class}" id="{bullet_id}">
        <div class="bullet-content">
            <span class="bullet-text">{text_with_citations}</span>
            {risk_indicators}
        </div>
        <div class="bullet-confidence" title="Confidence: {confidence:.0%}">
            <div class="confidence-bar" style="width: {confidence * 100}%;"></div>
        </div>
    </div>
    """
    
    return bullet_html

def create_evidence_panel(
    bullet_id: str,
    citations: List[Dict[str, Any]],
    panel_id: Optional[str] = None
) -> str:
    """
    Create an evidence panel for a bullet point.
    
    Args:
        bullet_id: ID of the bullet point
        citations: List of citation objects
        panel_id: Optional panel ID
        
    Returns:
        HTML for the evidence panel
    """
    # Generate ID if not provided
    if not panel_id:
        panel_id = f"panel_{str(uuid.uuid4())[:8]}"
    
    # Create the evidence panel HTML
    panel_html = f"""
    <div class="evidence-panel" id="{panel_id}" data-bullet="{bullet_id}">
        <div class="evidence-panel-header">
            <h4>Evidence Sources</h4>
            <button class="close-panel">×</button>
        </div>
        <div class="evidence-panel-content">
    """
    
    # Add each citation
    for i, citation in enumerate(citations):
        source = citation.get("cv_id", "Unknown Source")
        section = citation.get("section", "Unknown Section")
        snippet = citation.get("snippet", "")
        score = citation.get("score", 0.0)
        
        # Determine score class
        if score >= 0.8:
            score_class = "high-score"
        elif score >= 0.5:
            score_class = "medium-score"
        else:
            score_class = "low-score"
        
        panel_html += f"""
        <div class="evidence-item">
            <div class="evidence-header">
                <span class="evidence-source">{source}</span>
                <span class="evidence-section">{section}</span>
                <span class="evidence-score {score_class}">{score:.0%}</span>
            </div>
            <div class="evidence-snippet">{snippet}</div>
        </div>
        """
    
    panel_html += """
        </div>
    </div>
    """
    
    return panel_html

def add_interactive_evidence_css():
    """Add CSS for interactive evidence components."""
    st.markdown("""
    <style>
        /* Interactive Bullet Styles */
        .interactive-bullet {
            position: relative;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 8px;
            background: #ffffff;
            border-left: 4px solid #d1d5db;
            transition: all 0.2s ease;
        }
        
        .interactive-bullet:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        .interactive-bullet.high-confidence {
            border-left-color: #10b981;
        }
        
        .interactive-bullet.medium-confidence {
            border-left-color: #f59e0b;
        }
        
        .interactive-bullet.low-confidence {
            border-left-color: #ef4444;
        }
        
        .bullet-content {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        
        .bullet-text {
            flex: 1;
            color: #111827;
        }
        
        .risk-indicator {
            margin-left: 8px;
            color: #f59e0b;
            cursor: help;
        }
        
        .bullet-confidence {
            height: 4px;
            width: 100%;
            background: #e5e7eb;
            border-radius: 2px;
            overflow: hidden;
        }
        
        .confidence-bar {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #3b82f6);
            border-radius: 2px;
        }
        
        /* Citation Marker Styles */
        .citation-marker {
            cursor: pointer;
            color: #3b82f6;
            font-size: 0.8em;
            margin-left: 2px;
        }
        
        /* Evidence Panel Styles */
        .evidence-panel {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            display: none;
            overflow: hidden;
        }
        
        .evidence-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .evidence-panel-header h4 {
            margin: 0;
            color: #111827;
            font-weight: 500;
        }
        
        .close-panel {
            background: none;
            border: none;
            font-size: 24px;
            color: #6b7280;
            cursor: pointer;
        }
        
        .evidence-panel-content {
            padding: 16px 24px;
            max-height: calc(80vh - 60px);
            overflow-y: auto;
        }
        
        .evidence-item {
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 8px;
            background: #f8fafc;
            border-left: 3px solid #3b82f6;
        }
        
        .evidence-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .evidence-source {
            font-weight: 500;
            color: #111827;
        }
        
        .evidence-section {
            color: #6b7280;
            font-size: 0.9em;
        }
        
        .evidence-score {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        .evidence-score.high-score {
            background: #dcfce7;
            color: #166534;
        }
        
        .evidence-score.medium-score {
            background: #fef3c7;
            color: #92400e;
        }
        
        .evidence-score.low-score {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .evidence-snippet {
            color: #374151;
            font-size: 0.95em;
            line-height: 1.5;
            white-space: pre-wrap;
        }
        
        /* Overlay */
        .evidence-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

def add_interactive_evidence_js():
    """Add JavaScript for interactive evidence components."""
    st.markdown("""
    <script>
        // Function to initialize evidence components
        function initEvidenceComponents() {
            console.log("Initializing evidence components");
            
            // Create overlay if it doesn't exist
            let overlay = document.querySelector('.evidence-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'evidence-overlay';
                document.body.appendChild(overlay);
            }
            
            // Handle citation marker clicks
            document.querySelectorAll('.citation-marker').forEach(marker => {
                marker.onclick = function(event) {
                    const citationId = this.getAttribute('data-citations');
                    console.log("Citation clicked:", citationId);
                    showEvidencePanel(citationId);
                    event.stopPropagation();
                };
            });
            
            // Handle close panel button clicks
            document.querySelectorAll('.close-panel').forEach(button => {
                button.onclick = function() {
                    hideEvidencePanel();
                };
            });
            
            // Handle overlay clicks
            overlay.onclick = function() {
                hideEvidencePanel();
            };
        }
        
        // Show evidence panel
        function showEvidencePanel(citationId) {
            // Get the panel
            const panel = document.querySelector(`.evidence-panel[data-citation="${citationId}"]`);
            if (panel) {
                console.log("Showing panel:", panel);
                panel.style.display = 'block';
                document.querySelector('.evidence-overlay').style.display = 'block';
            } else {
                console.log("Panel not found for citation:", citationId);
                // Create a simple alert if panel not found
                alert("Evidence details: " + citationId);
            }
        }
        
        // Hide evidence panel
        function hideEvidencePanel() {
            document.querySelectorAll('.evidence-panel').forEach(panel => {
                panel.style.display = 'none';
            });
            document.querySelector('.evidence-overlay').style.display = 'none';
        }
        
        // Initialize on load and also when Streamlit reloads
        document.addEventListener('DOMContentLoaded', initEvidenceComponents);
        
        // For Streamlit - need to reinitialize when the DOM updates
        const observer = new MutationObserver(function(mutations) {
            initEvidenceComponents();
        });
        
        // Start observing the document body for DOM changes
        observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)

def render_interactive_cv_section(
    section_title: str,
    bullets: List[Dict[str, Any]],
    section_id: Optional[str] = None
):
    """
    Render an interactive CV section with evidence-linked bullets.
    
    Args:
        section_title: Title of the section
        bullets: List of bullet objects with text, citations, confidence, and risk_flags
        section_id: Optional section ID
    """
    # Generate ID if not provided
    if not section_id:
        section_id = f"section_{str(uuid.uuid4())[:8]}"
    
    # Create section container
    st.markdown(f"### {section_title}")
    
    # Add CSS and JavaScript
    add_interactive_evidence_css()
    add_interactive_evidence_js()
    
    # Create bullets and evidence panels
    bullets_html = ""
    panels_html = ""
    
    for i, bullet in enumerate(bullets):
        bullet_id = f"{section_id}_bullet_{i}"
        panel_id = f"{section_id}_panel_{i}"
        
        # Create bullet HTML
        bullet_html = create_interactive_bullet(
            bullet_text=bullet.get("text", ""),
            citations=bullet.get("citations", []),
            confidence=bullet.get("confidence", 0.0),
            risk_flags=bullet.get("risk_flags", []),
            bullet_id=bullet_id
        )
        bullets_html += bullet_html
        
        # Create evidence panel HTML
        panel_html = create_evidence_panel(
            bullet_id=bullet_id,
            citations=bullet.get("citations", []),
            panel_id=panel_id
        )
        panels_html += panel_html
    
    # Render bullets and panels - wrap in a container to ensure proper rendering
    section_html = f"""
    <div class="interactive-section" id="{section_id}">
        <div class="interactive-bullets">
            {bullets_html}
        </div>
        {panels_html}
    </div>
    """
    st.markdown(section_html, unsafe_allow_html=True)

def render_cv_with_evidence(cv_data: Dict[str, Any], debug_mode: bool = False):
    """
    Render a complete CV with interactive evidence components.
    
    Args:
        cv_data: CV data with sections and evidence
        debug_mode: Whether to show debug information
    """
    # Add CSS and JavaScript for interactive components
    add_interactive_evidence_css()
    add_interactive_evidence_js()
    
    # Debug: Log the structure of cv_data
    if debug_mode:
        st.write("Debug: CV Data Keys", list(cv_data.keys()))
        
        # Debug: Log the CV text
        st.write("Debug: CV Text (first 100 chars):", cv_data.get("cv_text", "")[:100] if cv_data.get("cv_text") else "No CV text")
    
    # Check if we have the generated CV data
    if "generated_cv" in cv_data:
        # Use the generated CV structure
        generated_cv = cv_data.get("generated_cv", {})
        
        if debug_mode:
            # Debug: Log the structure of generated_cv
            st.write("Debug: Generated CV Keys", list(generated_cv.keys()))
            
            # Debug: Log the contact info
            contact_info = generated_cv.get("contact_info", {})
            st.write("Debug: Contact Info:", contact_info)
            
            # Debug: Log the summary
            summary = generated_cv.get("summary", {})
            st.write("Debug: Summary:", summary)
        
        # Check for individual section objects (experience, skills, education)
        # This is the structure from CVWriter.generate_cv
        experience = generated_cv.get("experience", {})
        skills = generated_cv.get("skills", {})
        education = generated_cv.get("education", {})
        additional_sections = generated_cv.get("additional_sections", [])
        
        if debug_mode:
            st.write("Debug: Experience section:", experience.get("title", "No title") if experience else "No experience section")
            st.write("Debug: Skills section:", skills.get("title", "No title") if skills else "No skills section")
            st.write("Debug: Education section:", education.get("title", "No title") if education else "No education section")
            st.write("Debug: Additional sections count:", len(additional_sections))
        
        # Create a sections array from the individual section objects
        sections = []
        if experience:
            sections.append(experience)
        if skills:
            sections.append(skills)
        if education:
            sections.append(education)
        sections.extend(additional_sections)
        
        if debug_mode:
            st.write(f"Debug: Created {len(sections)} sections from individual section objects")
        
        # If sections exist in the original structure, use that instead
        if "sections" in generated_cv:
            original_sections = generated_cv.get("sections", [])
            if debug_mode:
                st.write(f"Debug: Found {len(original_sections)} sections in original structure")
            if original_sections:
                sections = original_sections
                if debug_mode:
                    st.write("Debug: Using original sections")
                    
                    if len(sections) > 0:
                        st.write(f"Debug: First section keys: {list(sections[0].keys())}")
                        st.write(f"Debug: First section title: {sections[0].get('title', 'No title')}")
                        bullets = sections[0].get("bullets", [])
                        st.write(f"Debug: First section bullet count: {len(bullets)}")
                        if len(bullets) > 0:
                            st.write(f"Debug: First bullet keys: {list(bullets[0].keys())}")
                            st.write(f"Debug: First bullet text: {bullets[0].get('text', 'No text')}")
        
        # Contact information
        contact_info = generated_cv.get("contact_info", {})
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 32px;">
            <h2 style="margin-bottom: 8px;">{contact_info.get("name", "")}</h2>
            <p style="color: #6b7280;">
                {contact_info.get("email", "")} | {contact_info.get("phone", "")} | {contact_info.get("location", "")}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Summary section
        summary = generated_cv.get("summary", {})
        if summary and summary.get("content"):
            st.markdown("### Professional Summary")
            st.markdown(summary.get("content", ""))
        
        # Create a sections array from the individual section objects if not already present
        sections = []
        if "sections" in generated_cv:
            sections = generated_cv.get("sections", [])
        else:
            # Add experience section
            experience = generated_cv.get("experience", {})
            if experience and experience.get("content"):
                # Create bullets from content
                experience_content = experience.get("content", "")
                bullet_pattern = r'•\s*(.*?)(?=\n•|\n\n|$)'
                experience_texts = re.findall(bullet_pattern, experience_content, re.DOTALL)
                
                # If no bullets found, treat the whole content as one bullet
                if not experience_texts and experience_content.strip():
                    experience_texts = [experience_content.strip()]
                
                # Create bullets
                bullets = []
                for text in experience_texts:
                    bullet = {
                        "text": text.strip(),
                        "citations": [],
                        "confidence": 0.7,
                        "risk_flags": []
                    }
                    bullets.append(bullet)
                
                # Add to sections
                sections.append({
                    "title": experience.get("title", "Work Experience"),
                    "bullets": bullets
                })
            
            # Add skills section
            skills = generated_cv.get("skills", {})
            if skills and skills.get("content"):
                # Create bullets from content
                skills_content = skills.get("content", "")
                bullet_pattern = r'•\s*(.*?)(?=\n•|\n\n|$)'
                skills_texts = re.findall(bullet_pattern, skills_content, re.DOTALL)
                
                # If no bullets found, treat the whole content as one bullet
                if not skills_texts and skills_content.strip():
                    skills_texts = [skills_content.strip()]
                
                # Create bullets
                bullets = []
                for text in skills_texts:
                    bullet = {
                        "text": text.strip(),
                        "citations": [],
                        "confidence": 0.7,
                        "risk_flags": []
                    }
                    bullets.append(bullet)
                
                # Add to sections
                sections.append({
                    "title": skills.get("title", "Skills"),
                    "bullets": bullets
                })
            
            # Add education section
            education = generated_cv.get("education", {})
            if education and education.get("content"):
                # Create bullets from content
                education_content = education.get("content", "")
                bullet_pattern = r'•\s*(.*?)(?=\n•|\n\n|$)'
                education_texts = re.findall(bullet_pattern, education_content, re.DOTALL)
                
                # If no bullets found, treat the whole content as one bullet
                if not education_texts and education_content.strip():
                    education_texts = [education_content.strip()]
                
                # Create bullets
                bullets = []
                for text in education_texts:
                    bullet = {
                        "text": text.strip(),
                        "citations": [],
                        "confidence": 0.7,
                        "risk_flags": []
                    }
                    bullets.append(bullet)
                
                # Add to sections
                sections.append({
                    "title": education.get("title", "Education"),
                    "bullets": bullets
                })
            
            # Add additional sections
            additional_sections = generated_cv.get("additional_sections", [])
            for section in additional_sections:
                if section and section.get("content"):
                    # Create bullets from content
                    section_content = section.get("content", "")
                    bullet_pattern = r'•\s*(.*?)(?=\n•|\n\n|$)'
                    section_texts = re.findall(bullet_pattern, section_content, re.DOTALL)
                    
                    # If no bullets found, treat the whole content as one bullet
                    if not section_texts and section_content.strip():
                        section_texts = [section_content.strip()]
                    
                    # Create bullets
                    bullets = []
                    for text in section_texts:
                        bullet = {
                            "text": text.strip(),
                            "citations": [],
                            "confidence": 0.7,
                            "risk_flags": []
                        }
                        bullets.append(bullet)
                    
                    # Add to sections
                    sections.append({
                        "title": section.get("title", "Additional Section"),
                        "bullets": bullets
                    })
        
        # Render each section
        for section in sections:
            section_title = section.get("title", "")
            bullets = section.get("bullets", [])
            
            if section_title and bullets:
                # Convert to the format expected by render_interactive_cv_section
                interactive_bullets = []
                for bullet in bullets:
                    interactive_bullet = {
                        "text": bullet.get("text", ""),
                        "citations": bullet.get("citations", []),
                        "confidence": bullet.get("confidence", 0.7),
                        "risk_flags": bullet.get("risk_flags", [])
                    }
                    interactive_bullets.append(interactive_bullet)
                
                # Render the section
                render_interactive_cv_section(section_title, interactive_bullets)
    else:
        # Fallback to the simple CV structure
        # Contact information
        contact_info = cv_data.get("contact_info", {})
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 32px;">
            <h2 style="margin-bottom: 8px;">{contact_info.get("name", "")}</h2>
            <p style="color: #6b7280;">
                {contact_info.get("email", "")} | {contact_info.get("phone", "")} | {contact_info.get("location", "")}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Summary section
        summary = cv_data.get("summary", {})
        if summary and summary.get("content"):
            st.markdown("### Professional Summary")
            st.markdown(summary.get("content", ""))
        
        # Experience section with interactive bullets
        experience = cv_data.get("experience", {})
        if experience and experience.get("content"):
            experience_bullets = []
            
            # Extract bullets from experience content
            experience_content = experience.get("content", "")
            bullet_pattern = r'•\s*(.*?)(?=\n•|\n\n|$)'
            experience_texts = re.findall(bullet_pattern, experience_content, re.DOTALL)
            
            # Get all available matches
            all_matches = []
            if "match_evidence" in cv_data and "matches" in cv_data["match_evidence"]:
                all_matches = cv_data["match_evidence"]["matches"]
            
            # Create bullet objects
            for i, text in enumerate(experience_texts):
                # Find the best matching citation for this bullet
                best_match = None
                best_score = 0
                
                for match in all_matches:
                    match_text = match.get("text", "")
                    if text.strip() in match_text or match_text in text.strip():
                        score = match.get("score", 0)
                        if score > best_score:
                            best_match = match
                            best_score = score
                
                # Create bullet object
                citations = [best_match] if best_match else []
                confidence = best_score if best_match else 0.3
                risk_flags = ["no_direct_evidence"] if not best_match else []
                
                bullet = {
                    "text": text.strip(),
                    "citations": citations,
                    "confidence": confidence,
                    "risk_flags": risk_flags
                }
                experience_bullets.append(bullet)
            
            # Render interactive experience section
            render_interactive_cv_section("Work Experience", experience_bullets)
        
        # Skills section
        skills = cv_data.get("skills", {})
        if skills and skills.get("content"):
            st.markdown("### Skills")
            st.markdown(skills.get("content", ""))
        
        # Education section
        education = cv_data.get("education", {})
        if education and education.get("content"):
            st.markdown("### Education")
            st.markdown(education.get("content", ""))
    
    # If no sections were rendered but we have matches, create sections from matches
    if "matches" in cv_data:
        if debug_mode:
            st.write("Debug: Matches found, creating sections from matches")
        # Get all matches
        matches = cv_data.get("matches", [])
        if debug_mode:
            st.write(f"Debug: Creating sections from {len(matches)} matches")
            
            # Debug: Log the first few matches
            if len(matches) > 0:
                st.write(f"Debug: First match keys: {list(matches[0].keys())}")
                st.write(f"Debug: First match text: {matches[0].get('text', 'No text')}")
                st.write(f"Debug: First match category: {matches[0].get('category', 'No category')}")
        
        # Group matches by category
        matches_by_category = {}
        for match in matches:
            category = match.get("category", "Experience")
            if category not in matches_by_category:
                matches_by_category[category] = []
            matches_by_category[category].append(match)
        
        # Create a section for each category
        for category, category_matches in matches_by_category.items():
            # Skip if no matches
            if not category_matches:
                continue
                
            # Create bullets for this category
            bullets = []
            for match in category_matches:
                bullet = {
                    "text": match.get("text", ""),
                    "citations": [match],
                    "confidence": match.get("score", 0.5),
                    "risk_flags": []
                }
                bullets.append(bullet)
            
            # Render the section
            section_title = category.replace("_", " ").title()
            render_interactive_cv_section(section_title, bullets)
    
    # Evidence summary
    st.markdown("### Evidence Summary")
    
    # Get all citations
    all_citations = []
    if "match_evidence" in cv_data and "matches" in cv_data["match_evidence"]:
        all_citations = cv_data["match_evidence"]["matches"]
    elif "cv_matching" in cv_data and "matches" in cv_data["cv_matching"]:
        all_citations = cv_data["cv_matching"]["matches"]
    elif "matches" in cv_data:
        all_citations = cv_data["matches"]
    
    # Group citations by source
    citations_by_source = {}
    for citation in all_citations:
        source = citation.get("cv_id", "Unknown")
        if source not in citations_by_source:
            citations_by_source[source] = []
        citations_by_source[source].append(citation)
    
    # Display citation summary
    if citations_by_source:
        for source, citations in citations_by_source.items():
            with st.expander(f"📄 {source} ({len(citations)} citations)"):
                for i, citation in enumerate(citations):
                    st.markdown(f"**{i+1}.** {citation.get('text', '')}")
                    st.markdown(f"*Section: {citation.get('section', 'Unknown')} | Score: {citation.get('score', 0.0):.2f}*")
                    st.markdown("---")
    else:
        st.info("No evidence citations available for this CV.")

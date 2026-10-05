"""
pdf_generator.py
----------------
Renders a structured resume (sections dict) into a professionally
formatted PDF for download.

Pipeline position: Step 9 of the workflow
    9. The user downloads the updated resume as a PDF
"""

import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

SECTION_ORDER = [
    "summary", "skills", "experience", "education",
    "projects", "certifications", "achievements",
]

SECTION_TITLES = {
    "summary": "Professional Summary",
    "skills": "Skills",
    "experience": "Experience",
    "education": "Education",
    "projects": "Projects",
    "certifications": "Certifications",
    "achievements": "Achievements",
}


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ResumeName", fontSize=20, leading=24, spaceAfter=4,
        textColor=colors.HexColor("#1a1a1a"), fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=12, leading=14, spaceBefore=12, spaceAfter=6,
        textColor=colors.HexColor("#2b4c7e"), fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="BodyTextResume", fontSize=10, leading=14,
        textColor=colors.HexColor("#333333"), fontName="Helvetica",
    ))
    return styles


def generate_resume_pdf(
    output_path: str,
    full_name: str,
    contact_line: str,
    sections: dict,
) -> str:
    """
    Build a PDF resume from a sections dict, e.g.:
        {"summary": "...", "skills": "...", "experience": "...", ...}

    Returns the output_path for convenience (so callers can chain it into
    a FileResponse).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = _build_styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )

    story = [
        Paragraph(full_name, styles["ResumeName"]),
        Paragraph(contact_line, styles["BodyTextResume"]),
        Spacer(1, 8),
        HRFlowable(width="100%", color=colors.HexColor("#2b4c7e"), thickness=1),
    ]

    for key in SECTION_ORDER:
        content = sections.get(key)
        if not content:
            continue
        story.append(Paragraph(SECTION_TITLES[key], styles["SectionHeading"]))
        # Preserve line breaks within a section as separate paragraphs/bullets
        for line in content.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["BodyTextResume"]))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    demo_sections = {
        "summary": "Backend engineer with 3 years of experience building scalable APIs.",
        "skills": "Python, FastAPI, PostgreSQL, Docker, Machine Learning",
        "experience": "Backend Developer at TechCorp (2022-2024)\nImproved API latency by 35%.",
        "education": "B.Tech in Computer Science, 2022",
    }
    path = generate_resume_pdf(
        "/tmp/demo_resume.pdf", "Jane Doe", "jane.doe@email.com | +1 555-0100", demo_sections
    )
    print("Generated:", path)

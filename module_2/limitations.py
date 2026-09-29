from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_limitations_pdf():
    pdf_filename = "limitations.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles matching clean executive documentation standards
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=14
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12
    )

    story = []

    # Document Header
    story.append(Paragraph("Data Limitations & Analysis Reflection", title_style))
    story.append(Spacer(1, 10))

    # Paragraph 1: Selection Bias, Self-Reporting, and Representativeness
    para1_text = (
        "Analyzing self-submitted data from platforms like Grad Café introduces significant selection and voluntary response bias "
        "that must be factored into any downstream interpretation. Because participation is completely unmoderated and optional, "
        "the resulting dataset represents a non-random sample heavily skewed toward applicants with extreme outcomes—primarily "
        "those with top-tier metrics receiving early acceptances or those voicing early rejections. Consequently, the sample lacks "
        "statistical representativeness across the broader applicant pool. This bias is clearly visible in our analysis results: "
        "for instance, Question 4 yielded an average GPA of 3.82 for Fall 2026 American applicants. In practice, this metric is "
        "artificially high and reflects a self-reporting tendency where high-performing candidates are far more inclined to share "
        "their scores publicly, leading to an overestimation of actual admission baselines."
    )
    story.append(Paragraph(para1_text, body_style))
    story.append(Spacer(1, 10))

    # Paragraph 2: Data Missingness, Noise, and Standardization (LLM Comparison)
    para2_text = (
        "Beyond sampling bias, the anonymous and unverified nature of the inputs creates issues with data missingness, consistency, "
        "and overall reliability. Optional fields such as GRE scores, sub-scores, and exact decision dates are frequently left blank, "
        "limiting the viability of deeper multi-variable regressions. Furthermore, raw user entries lack standardized data validation, "
        "resulting in duplicate submissions, typos, and fragmented naming conventions. This challenge directly surfaces when comparing "
        "the raw string queries to the normalized LLM fields in Question 9. Querying raw program text for Computer Science PhD acceptances "
        "undercounted total admissions compared to the LLM-classified field simply because applicants entered variations like 'CS', "
        "'CompSci', or 'Ph.D. in Computer Science'. Without programmatic normalization or LLM entity extraction, reliance on unvalidated, "
        "self-reported text strings introduces structural noise that distorts baseline counts and decision timelines."
    )
    story.append(Paragraph(para2_text, body_style))

    doc.build(story)
    print(f"Successfully generated '{pdf_filename}'.")

if __name__ == "__main__":
    create_limitations_pdf()
import os
from fpdf import FPDF, XPos, YPos

class PDF(FPDF):
    def header(self):
        # Header formatting
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'SQL Query Analysis Results', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 8, 'Module 3 Assignment', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

    def footer(self):
        # Footer formatting
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')


# Updated text input content
content = """
--- Question 1 ---
Question: How many entries in your database are from applicants who applied for Fall 2026?
Fall 2026 applicant count: 49,996

--- Question 2 ---
Question: Among entries that provide a nationality classification, what percentage are international students?
Percent international: 44.85%

--- Question 3 ---
Question: What are the average GPA, GRE Quantitative, GRE Verbal, and GRE Analytical Writing scores of applicants who provide each metric?
Average GPA: 3.75
Average GRE Quantitative: 381.64
Average GRE Verbal: 322.14
Average GRE Analytical Writing: 6.30

--- Question 4 ---
Question: What is the average GPA of American applicants who applied for Fall 2026?
Average GPA of American applicants (Fall 2026): 3.79

--- Question 5 ---
Question: What percentage of Fall 2025 entries are acceptances?
Fall 2025 acceptance percentage: 41.20%

--- Question 6 ---
Question: What is the average GPA of accepted applicants who applied for Fall 2026?
Average GPA of accepted applicants (Fall 2026): 3.78

--- Question 7 ---
Question: How many entries are from applicants who applied to Johns Hopkins University for a master's degree in Computer Science?
JHU Master's CS applicant count: 18

--- Question 8 ---
Question: How many Fall 2026 entries are acceptances from applicants applying for a PhD in Computer Science at Georgetown, MIT, Stanford, or Carnegie Mellon (using original fields)?
Original-field count: 30

--- Question 9 ---
Question: Repeat Question 8 using the LLM-generated university and program fields, and compare the results.
Original-field count: 30
LLM-field count: 30
Difference: 0

--- Custom Question 1 ---
Question: What is the average GPA of Fall 2026 PhD applicants, grouped by their admission status?
Status: Waitlisted | Average GPA: 3.84 | Count: 1,534
Status: Accepted   | Average GPA: 3.83 | Count: 5,614
Status: Rejected   | Average GPA: 3.80 | Count: 10,993

--- Custom Question 2 ---
Question: Which 5 universities received the most Fall 2026 applications, and what is their average GRE Quant score?
1. University of British Columbia | Applications: 5,682 | Average GRE Quant: 258.51
2. University of California, Berkeley | Applications: 5,193 | Average GRE Quant: 276.68
3. University of California, Los Angeles | Applications: 1,918 | Average GRE Quant: 275.12
4. Unknown | Applications: 1,086 | Average GRE Quant: 259.37
5. University of Toronto | Applications: 830 | Average GRE Quant: 262.63
"""

# Initialize PDF document
pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# Clean special characters and format tabs
clean_content = content.replace('\u2019', "'").replace('\u2013', "-").replace('\t', '    ')

lines = clean_content.split('\n')

for line in lines:
    line_str = line.rstrip('\r\n')
    
    # Empty lines: add spacing using pdf.ln()
    if not line_str.strip():
        pdf.ln(3)
        continue

    # Format section headers
    if line_str.startswith("---"):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 51, 102)  # Dark Blue
        pdf.multi_cell(0, 6, line_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)      # Reset to black
        pdf.ln(1)
        
    # Format key-value lines with bold prefix (e.g. "Question:", "Average GPA:")
    elif ":" in line_str and not line_str.startswith("1.") and not line_str.startswith("2.") and not line_str.startswith("3.") and not line_str.startswith("4.") and not line_str.startswith("5."):
        parts = line_str.split(":", 1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.write(5, parts[0] + ":")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, parts[1], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
    # Standard body text and numbered lists
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, line_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Save output
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_results.pdf")
pdf.output(output_path)
print(f"Success! Updated PDF generated at: {output_path}")
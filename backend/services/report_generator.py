from fpdf import FPDF
import os

def create_pdf_report(scan_id, final_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 10, txt="NEXORA FORENSIC ANALYSIS REPORT", ln=True, align='C')
    pdf.ln(10)
    
    # Scan Info
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Scan ID: {scan_id}", ln=True)
    pdf.cell(200, 10, txt=f"Verdict: {final_data['verdict']}", ln=True)
    pdf.cell(200, 10, txt=f"Confidence: {final_data['confidence']}%", ln=True)
    pdf.ln(10)
    
    # Technical Breakdown
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Mathematical Evidence", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"The FFT Engine detected a high-frequency noise score of {final_data['fft_score']}. "
                             "This indicates non-biological pixel patterns typical of GAN-based face swaps.")
    
    report_path = f"storage/results/{scan_id}.pdf"
    pdf.output(report_path)
    return report_path
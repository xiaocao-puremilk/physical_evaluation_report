
import sys
import os
import numpy as np
from PyQt5.QtWidgets import QApplication
from report_ui import MentalReportPage
from report_ui_pro import ProfessionalReportPage

def setup_page_data(page):
    # 1. Person Info
    page.set_person_info(name="测试用户", age="28岁", date_str="2026-02-04")
    
    # 2. Mock Data
    # Scores (High risk to show alert)
    page.set_scores(s1=68, t1="中度风险", s2=55, t2="轻度风险")
    
    # ERP (Mock)
    t = np.linspace(0, 6, 250*6)
    neutral = (np.sin(2*np.pi*t) * 5).tolist()
    pos = (np.sin(2*np.pi*t + 1) * 6).tolist()
    neg = (np.sin(2*np.pi*t + 2) * 8).tolist()
    page.set_erp_data(neutral, pos, neg)
    
    # Bands (Mock)
    page.set_emotion_wave_data(
        [10, 20, 40, 20, 10], # Neutral
        [5, 15, 30, 30, 20],  # Negative
        [15, 25, 40, 15, 5]   # Positive
    )
    
    # Features (Mock)
    page.set_feature_data(0.75, 0.42, 0.65)
    
    # Conclusion
    conclusion = page.generate_auto_conclusion()
    page.set_conclusion(conclusion)

def main():
    app = QApplication(sys.argv)
    
    # --- 1. Customer Version ---
    print("Generating Customer Report...")
    customer_page = MentalReportPage()
    setup_page_data(customer_page)
    
    out1 = os.path.abspath("pdf_customer.pdf")
    customer_page.export_pdf(out1)
    print(f"Customer PDF saved to: {out1}")
    
    # --- 2. Professional Version ---
    print("Generating Professional Report...")
    pro_page = ProfessionalReportPage()
    setup_page_data(pro_page)
    
    out2 = os.path.abspath("pdf_professional.pdf")
    pro_page.export_pdf(out2)
    print(f"Professional PDF saved to: {out2}")
    
    print("Verification finished.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        sys.exit(1)

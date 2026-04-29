from fpdf import FPDF
from datetime import date
import os
import sys


def _find_font(filename):
    """Find a font file across common locations on Linux and macOS."""
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/{filename}",
        f"/usr/share/fonts/dejavu/{filename}",
        f"/Library/Fonts/{filename}",
        os.path.join(os.path.dirname(__file__), filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def generate_client_report(client, workouts, progress, metrics):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    regular = _find_font("DejaVuSans.ttf")
    bold = _find_font("DejaVuSans-Bold.ttf")

    if regular and bold:
        pdf.add_font("DejaVu", "", regular, uni=True)
        pdf.add_font("DejaVu", "B", bold, uni=True)
        font_name = "DejaVu"
    else:
        font_name = "Helvetica"

    # Header
    pdf.set_fill_color(212, 175, 55)
    pdf.rect(0, 0, 210, 25, "F")
    pdf.set_font(font_name, "B", 18)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 7)
    pdf.cell(0, 10, "ACEest Fitness & Gym - Client Report", ln=True)

    pdf.set_text_color(50, 50, 50)
    pdf.ln(10)

    # Client details
    pdf.set_font(font_name, "B", 13)
    pdf.cell(0, 8, "Client Profile", ln=True)
    pdf.set_font(font_name, "", 11)
    pdf.cell(0, 6, f"Name:   {client['name']}", ln=True)
    pdf.cell(0, 6, f"Age:    {client['age'] or 'N/A'}", ln=True)
    pdf.cell(0, 6, f"Weight: {client['weight'] or 'N/A'} kg", ln=True)
    pdf.cell(0, 6, f"Program: {client['program'] or 'Not assigned'}", ln=True)
    pdf.cell(0, 6, f"Membership: {client['membership_status']}", ln=True)
    pdf.cell(0, 6, f"Report date: {date.today()}", ln=True)
    pdf.ln(5)

    # Workouts
    pdf.set_font(font_name, "B", 13)
    pdf.cell(0, 8, "Workout History", ln=True)
    pdf.set_font(font_name, "", 11)
    if workouts:
        for w in workouts:
            pdf.cell(0, 6, f"  {w['date']} - {w['workout_type']} ({w['duration_min']} min)", ln=True)
    else:
        pdf.cell(0, 6, "  No workouts logged.", ln=True)
    pdf.ln(5)

    # Progress
    pdf.set_font(font_name, "B", 13)
    pdf.cell(0, 8, "Progress / Adherence", ln=True)
    pdf.set_font(font_name, "", 11)
    if progress:
        for p in progress:
            pdf.cell(0, 6, f"  {p['week'] or 'Week'}: {p['adherence']}%", ln=True)
    else:
        pdf.cell(0, 6, "  No progress entries.", ln=True)
    pdf.ln(5)

    # Metrics
    pdf.set_font(font_name, "B", 13)
    pdf.cell(0, 8, "Body Metrics", ln=True)
    pdf.set_font(font_name, "", 11)
    if metrics:
        for m in metrics:
            line = f"  {m['date']} - Weight: {m['weight_kg'] or 'N/A'} kg"
            if m["body_fat_pct"] is not None:
                line += f", Body Fat: {m['body_fat_pct']}%"
            if m["notes"]:
                line += f" ({m['notes']})"
            pdf.cell(0, 6, line, ln=True)
    else:
        pdf.cell(0, 6, "  No metrics recorded.", ln=True)

    return pdf.output()

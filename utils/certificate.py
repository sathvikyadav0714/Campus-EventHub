from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from datetime import datetime

def generate_certificate(student_name, event_title, output_path):
    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Background
    c.setFillColorRGB(1, 1, 1)  # white
    c.rect(0, 0, width, height, fill=1)

    # ALWAYS reset text color
    c.setFillColor(black)

    # Title
    c.setFont("Helvetica-Bold", 36)
    c.drawString(60, height - 90, "CERTIFICATE")
    c.drawString(60, height - 135, "OF PARTICIPATION")

    # Divider line
    c.setLineWidth(2)
    c.line(60, height - 155, width - 60, height - 155)

    # Intro
    c.setFont("Helvetica", 16)
    c.drawString(60, height - 220, "This certificate is proudly presented to")

    # Student Name
    c.setFont("Helvetica-Bold", 30)
    c.drawString(60, height - 270, student_name)

    # Name divider
    c.setLineWidth(1.5)
    c.line(60, height - 290, width - 60, height - 290)

    # Description
    c.setFont("Helvetica", 16)
    c.drawString(60, height - 340, "For active participation in the event")

    # Event Name
    c.setFont("Helvetica-Bold", 20)
    c.drawString(60, height - 380, f"“{event_title}”")

    # Organizer
    c.setFont("Helvetica", 14)
    c.drawString(60, height - 420, "Conducted by Campus EventHub")

    # Signature
    c.setLineWidth(1)
    c.line(60, 110, 240, 110)
    c.setFont("Helvetica", 12)
    c.drawString(60, 90, "Authorized Signature")

    # Date
    date_str = datetime.now().strftime("%B %d, %Y")
    c.drawRightString(width - 60, 90, date_str)

    c.save()

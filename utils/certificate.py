from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

def generate_certificate(student_name, event_title, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 150, "CERTIFICATE OF PARTICIPATION")

    # Body text
    c.setFont("Helvetica", 16)
    c.drawCentredString(
        width / 2,
        height - 250,
        f"This is to certify that"
    )

    # Student name
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(
        width / 2,
        height - 300,
        student_name
    )

    # Event text
    c.setFont("Helvetica", 16)
    c.drawCentredString(
        width / 2,
        height - 360,
        f"has successfully participated in the event"
    )

    # Event title
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(
        width / 2,
        height - 410,
        event_title
    )

    # Footer
    c.setFont("Helvetica", 12)
    c.drawString(50, 100, "Campus EventHub")
    c.drawRightString(width - 50, 100, "Authorized Signature")

    c.showPage()
    c.save()

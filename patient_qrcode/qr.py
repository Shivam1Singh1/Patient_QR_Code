import qrcode, base64, frappe
from io import BytesIO

def generate_qr_code(doc, method=None):

    if doc.custom_base64data:
        return

    url = f"{frappe.utils.get_url()}/app/patient/{doc.name}"

    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")

    doc.custom_base64data = (
        "data:image/png;base64," +
        base64.b64encode(buf.getvalue()).decode()
    )

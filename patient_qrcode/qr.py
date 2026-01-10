import qrcode
import frappe
from io import BytesIO
import base64
import urllib.parse


@frappe.whitelist()
def generate_qr_code(doc, method=None):

    # 🚨 Do not generate QR until document is saved
    if not doc.name:
        return

    if doc.custom_base64data:
        return

    base_url = frappe.utils.get_url()

    values = [
        doc.name, 
        doc.custom_trial_id or "NA",
        doc.custom_patient_initials or "NA",
        doc.dob or "NA",
        doc.sex or "NA",
        doc.blood_group or "NA",
        doc.custom_weight_on_the_day_of_leukapheresis or "NA",
        doc.custom_hospital_id_uhid or "NA"
    ]

    encoded_values = [
        urllib.parse.quote(str(v), safe="")
        for v in values
    ]

    qr_url = f"{base_url}/patient/{'/'.join(encoded_values)}"

    print("QR URL:", qr_url)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=4
    )

    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    doc.db_set(
        "custom_base64data",
        "data:image/png;base64," +
        base64.b64encode(buffer.getvalue()).decode()
    )

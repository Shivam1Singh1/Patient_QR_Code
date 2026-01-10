import qrcode
import frappe
from io import BytesIO
import base64
import urllib.parse


@frappe.whitelist()
def generate_qr_code(doc, method=None):

    if doc.custom_base64data:
        return

    base_url = frappe.utils.get_url()

    asset_url = f"patient/{doc.name}"

    
    values = [
        doc.name,                                     
        doc.custom_trial_id,
        doc.custom_patient_initials,
        doc.dob,
        doc.sex,
        doc.blood_group,
        doc.custom_weight_on_the_day_of_leukapheresis,
        doc.custom_hospital_id_uhid,
        asset_url
    ]

    encoded_values = [
        urllib.parse.quote(str(v), safe="") if v else ""
        for v in values
    ]

    qr_url = f"{base_url}/patient/test/" + "/".join(encoded_values)

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

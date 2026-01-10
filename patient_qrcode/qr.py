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

    asset_url = f"{base_url}/app/patient/{doc.name}"

    params = {
        "pid": doc.name,
        "trial_id": doc.custom_trial_id,
        "initials": doc.custom_patient_initials,
        "dob": doc.dob,
        "gender": doc.sex,
        "blood_group": doc.blood_group,
        "weight": doc.custom_weight_on_the_day_of_leukapheresis,
        "uhid": doc.custom_hospital_id_uhid,
        "asset_url": asset_url
    }

    params = {k: v for k, v in params.items() if v}

    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    qr_url = f"{base_url}/patient/test?{query_string}"

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

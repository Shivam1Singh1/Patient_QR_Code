import qrcode
import frappe
from io import BytesIO
import base64
import urllib.parse


def generate_qr_code(doc, method=None):
    try:
        if method != "after_insert":
            return

        if doc.custom_base64data:
            return

        base_url = frappe.utils.get_url()

        params = {
            "pid": doc.name,

            "trial_id": doc.get("custom_trial_id"),
            "initials": doc.get("custom_patient_initials"),
            "dob": doc.get("dob"),
            "gender": doc.get("sex"),
            "blood_group": doc.get("blood_group"),
            "weight": doc.get("custom_weight_on_the_day_of_leukapheresis"),
            "uhid": doc.get("custom_hospital_id_uhid"),
            "user_id": doc.get("user_id"),

            "redirect_to": f"/app/patient/{urllib.parse.quote(doc.name)}"
        }

        params = {k: v for k, v in params.items() if v}

        query_string = urllib.parse.urlencode(
            params, quote_via=urllib.parse.quote
        )

        qr_url = f"{base_url}/patient-summary?{query_string}"

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

        base64_data = (
            "data:image/png;base64," +
            base64.b64encode(buffer.getvalue()).decode()
        )

        doc.db_set(
            "custom_base64data",
            base64_data,
            update_modified=False
        )

        frappe.db.commit()

        frappe.logger().info(
            f"QR Code generated successfully for Patient {doc.name}"
        )

    except Exception as e:
        frappe.log_error(
            title="QR Code Generation Error",
            message=f"Patient: {doc.name}\nError: {str(e)}"
        )
        frappe.throw("Failed to generate QR Code")

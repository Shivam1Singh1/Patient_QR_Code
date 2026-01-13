import qrcode
import frappe
from io import BytesIO
import base64
import urllib.parse

@frappe.whitelist()
def generate_qr_code(doc, method=None):
    try:
        # QR already generated
        # if doc.custom_base64data:
        #     return
        base_url = frappe.utils.get_url()
        params = {
            "pid": doc.name,
            "trial_id": doc.get("custom_trial_id"),
            "initials": doc.get("custom_patient_initials"),
            "dob": doc.get("dob"),
            "gender": doc.get("sex"),
            "blood_group": doc.get("blood_group"),
            "weight": doc.get("custom_weight_on_the_day_of_leukapheresis"),
            "uid": doc.get("custom_hospital_id_uhid"),
            "redirect_to": f"/app/patient/{urllib.parse.quote(doc.name)}"
        }
        # remove empty values
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
            "data:image/png;base64,"
            + base64.b64encode(buffer.getvalue()).decode()
        )
        doc.db_set(
            "custom_base64data",
            base64_data,
            update_modified=False
        )
        frappe.logger().info(
            f"QR Code generated successfully for Patient {doc.name}"
        )
    except Exception as e:
        frappe.log_error(
            title="QR Code Generation Error",
            message=f"Patient: {doc.name}\nError: {str(e)}"
        )
        frappe.throw("Failed to generate QR Code")


@frappe.whitelist()
def generate_cart_qr_codes(patient_id, cart_name):
    """
    Generate three different QR codes for CarT Manufacturing:
    1. Patient QR Code - Contains patient information
    2. BMR QR Code - Contains patient info + Type: BMR + Batch
    3. G-Rex QR Code - Contains patient info + Type: G-Rex + Batch
    """
    try:
        # Get patient and cart details
        patient = frappe.get_doc('Patient', patient_id)
        cart = frappe.get_doc("CarT Manufacturing", cart_name)
        
        base_url = frappe.utils.get_url()
        
        # Base patient params
        base_params = {
            "pid": patient_id,
            "trial_id": patient.get("custom_trial_id"),
            "initials": patient.get("custom_patient_initials"),
            "dob": patient.get("dob"),
            "gender": patient.get("sex"),
            "blood_group": patient.get("blood_group"),
            "uid": patient.get("custom_hospital_id_uhid"),
            "redirect_to": f"/app/patient/{urllib.parse.quote(patient_id)}"
        }
        # Remove empty values
        base_params = {k: v for k, v in base_params.items() if v}
        
        # Generate Patient QR Code
        patient_params = base_params.copy()
        patient_query = urllib.parse.urlencode(patient_params, quote_via=urllib.parse.quote)
        patient_qr_url = f"{base_url}/patient-summary?{patient_query}"
        patient_qr_base64 = _generate_qr_code_base64(patient_qr_url)
        
        # Generate BMR QR Code
        bmr_params = base_params.copy()
        bmr_params.update({
            "batch": cart.get("batch") or "N/A",
            "type": "BMR",
            "cart_id": cart_name
        })
        bmr_params = {k: v for k, v in bmr_params.items() if v}
        bmr_query = urllib.parse.urlencode(bmr_params, quote_via=urllib.parse.quote)
        bmr_qr_url = f"{base_url}/patient-summary?{bmr_query}"
        bmr_qr_base64 = _generate_qr_code_base64(bmr_qr_url)
        
        # Generate G-Rex QR Code
        grex_params = base_params.copy()
        grex_params.update({
            "batch": cart.get("batch") or "N/A",
            "type": "G-Rex",
            "cart_id": cart_name
        })
        grex_params = {k: v for k, v in grex_params.items() if v}
        grex_query = urllib.parse.urlencode(grex_params, quote_via=urllib.parse.quote)
        grex_qr_url = f"{base_url}/patient-summary?{grex_query}"
        grex_qr_base64 = _generate_qr_code_base64(grex_qr_url)
        
        frappe.logger().info(
            f"CarT QR Codes generated successfully for Patient {patient_id}, CarT {cart_name}"
        )
        
        return {
            'patient_qr': patient_qr_base64,
            'bmr_qr': bmr_qr_base64,
            'grex_qr': grex_qr_base64,
            'patient_name': patient.patient_name or patient_id
        }
        
    except Exception as e:
        frappe.log_error(
            title="CarT QR Code Generation Error",
            message=f"Patient: {patient_id}, CarT: {cart_name}\nError: {str(e)}"
        )
        frappe.throw(f"Failed to generate CarT QR codes: {str(e)}")


@frappe.whitelist()
def get_item_qr_codes_for_table(cart_manufacturing_name):
    """
    Generate QR codes for each item in CarT Manufacturing table
    """
    try:
        doc = frappe.get_doc("CarT Manufacturing", cart_manufacturing_name)
        
        if not doc.patient or not doc.batch:
            return {}

        patient = frappe.get_doc("Patient", doc.patient)
        base_url = frappe.utils.get_url()

        qr_data = {}

        for item in doc.items:
            # Build params for each item
            item_params = {
                "cart_id": doc.name,
                "batch": doc.batch,
                "pid": doc.patient,
                "patient_name": patient.patient_name or doc.patient,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "dose": item.get("dose"),
                "redirect_to": f"/app/cart-manufacturing/{urllib.parse.quote(doc.name)}"
            }
            # Remove empty values
            item_params = {k: v for k, v in item_params.items() if v}
            
            item_query = urllib.parse.urlencode(item_params, quote_via=urllib.parse.quote)
            item_qr_url = f"{base_url}/cart-item-summary?{item_query}"
            
            qr_base64 = _generate_qr_code_base64(item_qr_url)

            qr_data[item.name] = {
                "qr_code": qr_base64,
                "dose": item.get("dose") or "N/A",
                "qty": item.qty
            }

        frappe.logger().info(
            f"Item QR Codes generated successfully for CarT Manufacturing {cart_manufacturing_name}"
        )
        
        return qr_data
        
    except Exception as e:
        frappe.log_error(
            title="Item QR Code Generation Error",
            message=f"CarT Manufacturing: {cart_manufacturing_name}\nError: {str(e)}"
        )
        frappe.throw(f"Failed to generate item QR codes: {str(e)}")


def _generate_qr_code_base64(qr_url):
    """
    Internal helper function to generate QR code from URL and return base64 string
    """
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
    
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

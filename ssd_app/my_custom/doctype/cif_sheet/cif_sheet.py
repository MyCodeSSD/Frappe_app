# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CIFSheet(Document):
      
	pass


@frappe.whitelist()
def render_cif_sheet_pdf(inv_name):
    doc = frappe.get_doc("CIF Sheet", inv_name)
    context = {
        "doc": doc,
        "custom_message": "Generated from Python",
        "formatted_date": frappe.format_value(doc.inv_date, {"fieldtype": "Date"})
    }
    html = frappe.render_template("ssd_app/templates/includes/cif_sheet_pdf.html", context)
    return html
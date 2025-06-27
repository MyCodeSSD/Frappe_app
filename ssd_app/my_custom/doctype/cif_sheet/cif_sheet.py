# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf


class CIFSheet(Document):   
	pass


@frappe.whitelist()
def render_cif_sheet_pdf(inv_name, pdf=0):
    doc = frappe.get_doc("CIF Sheet", inv_name)
    doc.customer_name=frappe.db.get_value("Customer", doc.customer, "customer")
    doc.notify_name=frappe.db.get_value("Notify", doc.notify, "notify")
    doc.acc_com_name = frappe.db.get_value("Company", doc.accounting_company, "company_code")
    doc.category_name=frappe.db.get_value("Product Category", doc.category, "product_category")
    doc.bank_name=frappe.db.get_value("Bank", doc.bank, "bank")
    doc.load_port_name=frappe.db.get_value("Port", doc.load_port, "port")
    doc.f_country_name=frappe.db.get_value("Port", doc.load_port, "country")
    doc.notify_city=frappe.db.get_value("Notify", doc.notify, "city")
    doc.t_country_name=frappe.db.get_value("City", doc.notify_city, "country")
    doc.destination_port_name=frappe.db.get_value("Port", doc.destination_port, "port")
    product =  frappe.db.sql("""
        SELECT p.parent, pg.product_group, pro.product, p.sc_no, p.qty, u.unit, p.rate, p.currency, p.ex_rate, 
            p.charges, p.charges_amount, p.gross, p.gross_usd 
        FROM `tabProduct CIF` p 
        LEFT JOIN `tabUnit` u ON p.unit = u.name 
        LEFT JOIN `tabProduct` pro ON p.product = pro.name 
        LEFT JOIN `tabProduct Group` pg ON pro.product_group = pg.name 
        WHERE p.parent = %s""", inv_name, as_dict=1)
    product = sorted(product, key=lambda x: x['product_group'])
    exp = frappe.db.sql("""
        SELECT 
            parent, 
            expenses,
            SUM(amount_usd) AS total_amount 
        FROM `tabExpenses CIF`
        WHERE parent = %s
        GROUP BY expenses, parent
    """, (inv_name,), as_dict=1)
    exp_dict = {i.expenses: i.total_amount for i in exp}
    expenses = {e: exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others"]}

    context = {
        "doc": doc,
        "product":product,
        "expenses":expenses,
        "generated_date": frappe.utils.nowdate(),
        "custom_message": "Generated from Python",
        "formatted_date": frappe.format_value(doc.inv_date, {"fieldtype": "Date"})
    }
    html = frappe.render_template("ssd_app/templates/includes/cif_sheet_pdf.html", context)
    if (pdf):
        frappe.local.response.filename = f"CIF_{inv_name}.pdf"
        frappe.local.response.filecontent = get_pdf(html)
        frappe.local.response.type = "pdf"

    else:
        return html
    
@frappe.whitelist()
def check_related_docs(inv_id):
    has_received = frappe.db.exists("Doc Received", {"inv_no": inv_id})
    has_nego = frappe.db.exists("Doc Nego", {"inv_no": inv_id})
    return bool(has_received or has_nego)

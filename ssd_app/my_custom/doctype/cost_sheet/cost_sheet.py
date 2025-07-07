# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf
from frappe.utils import now_datetime
from frappe import _

@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.get_doc("CIF Sheet", inv_no)
    data = {
        "inv_no": cif.inv_no,
        "inv_date": cif.inv_date,
        "customer": cif.customer,
        "category": cif.category,
        "notify": cif.notify,
        "accounting_company": cif.accounting_company,
        "shipping_company": cif.shipping_company,
        "handling_charges":cif.handling_charges,
        "sales":cif.sales,
        "multiple_sc":cif.multiple_sc if cif.multiple_sc else 0,
        "sc_no":cif.sc_no,
        "product_details": [
            {
                "name": d.name,
                "product": d.product,
                "qty": d.qty,
                "unit": d.unit,
                "sc_no": d.sc_no if d.sc_no else "",
                "rate":d.rate,
                "currency":d.currency,
                "ex_rate":d.ex_rate,
                "charges":d.charges,
                "charges_amount":d.charges_amount,
                "round_off_usd":d.round_off_usd
            }
            for d in cif.product_details
        ],
        "expenses": [
            {
                "name": e.name,
                "expenses": e.expenses,
                "amount":e.amount,
                "currency":e.currency,
                "ex_rate":e.ex_rate
            }
            for e in cif.expenses
        ] if cif.expenses else []
    }
    # frappe.msgprint('expenses')
    return data

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    used_inv = frappe.get_all("Cost Sheet", pluck="inv_no")

    if used_inv:
        placeholders = ', '.join(['%s'] * len(used_inv))
        condition = f"WHERE name NOT IN ({placeholders}) AND inv_no LIKE %s"
        values = used_inv + [f"%{txt}%"]
    else:
        condition = "WHERE inv_no LIKE %s"
        values = [f"%{txt}%"]

    values += [page_len, start]

    return frappe.db.sql(f"""
        SELECT name, inv_no
        FROM `tabCIF Sheet`
        {condition}
        ORDER BY inv_no ASC
        LIMIT %s OFFSET %s
    """, tuple(values))

def validate_unique_expenses(doc):
        seen = set()
        for row in doc.expenses:
            if row.expenses in seen:
                frappe.throw(_('Expenses must be unique: {0}').format(row.expenses))
            seen.add(row.expenses)


class CostSheet(Document):
    def validate(self):
        validate_unique_expenses(self)


# To Prepare Cost Sheet PDF
@frappe.whitelist()
def render_cost_sheet_pdf(cost_id, pdf=0):
    inv_name=cost_id
    doc = frappe.get_doc("Cost Sheet", cost_id)
    cif_doc= frappe.get_doc("CIF Sheet", doc.inv_no, "load_port")
    doc.customer_name=frappe.db.get_value("Customer", doc.customer, "customer")
    doc.notify_name=frappe.db.get_value("Notify", doc.notify, "notify")
    doc.acc_com_name = frappe.db.get_value("Company", doc.accounting_company, "company_code")
    doc.category_name=frappe.db.get_value("Product Category", doc.category, "product_category")
    doc.load_port_name=frappe.db.get_value("Port", cif_doc.load_port, "port")
    doc.f_country_name=frappe.db.get_value("Port", cif_doc.load_port, "country")
    doc.notify_city=frappe.db.get_value("Notify", doc.notify, "city")
    doc.t_country_name=frappe.db.get_value("City", doc.notify_city, "country")
    doc.destination_port_name=frappe.db.get_value("Port", cif_doc.destination_port, "port")
    doc.agent_name=frappe.db.get_value("Comm Agent", doc.agent, "agent_name")

    product =  frappe.db.sql("""
        SELECT p.parent, pg.product_group, pro.product, p.po_no, p.qty, u.unit, p.rate, p.currency, p.ex_rate, 
            p.charges, p.charges_amount, p.gross, p.gross_usd 
        FROM `tabProduct Cost` p 
        LEFT JOIN `tabUnit` u ON p.unit = u.name 
        LEFT JOIN `tabProduct` pro ON p.product = pro.name 
        LEFT JOIN `tabProduct Group` pg ON pro.product_group = pg.name 
        WHERE p.parent = %s""", cost_id, as_dict=1)
    product = sorted(product, key=lambda x: x['product_group'])
    exp = frappe.db.sql("""
        SELECT 
            parent,
            amount,
            currency,
            expenses,
            amount_usd AS total_amount 
        FROM `tabExpenses Cost`
        WHERE parent = %s
    """, (inv_name,), as_dict=1)
    # exp_dict = {i.expenses: i.total_amount for i in exp}
    # expenses = {e: exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others", "Insurance"]}

    exp_dict = {
        i.expenses: {
            "amount": i.amount,
            "currency": i.currency,
            "total_amount": i.total_amount
        }
        for i in exp
    }
    expenses = {e: exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others"]}

    context = {
        "doc": doc,
        "product":product,
        "expenses":expenses,
        "generated_date": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "custom_message": "Generated from Python",
        "formatted_date": frappe.format_value(doc.inv_date, {"fieldtype": "Date"})
    }
    html = frappe.render_template("ssd_app/templates/includes/cost_sheet_pdf.html", context)
    if (pdf):
        frappe.local.response.filename = f"CIF_{inv_name}.pdf"
        frappe.local.response.filecontent = get_pdf(html)
        frappe.local.response.type = "pdf"

    else:
        return html
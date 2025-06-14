# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

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
        "insurance":cif.insurance,
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


class CostSheet(Document):
    pass

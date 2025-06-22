# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta


def final_validation(doc):
    if not doc.inv_no:
        return

    # Fetch CIF document value
    cif_document = frappe.db.get_value("CIF Sheet", doc.inv_no, "document") or 0

    # Total received from other Doc Received entries (excluding current one)
    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s 
    """, (doc.inv_no))[0][0] or 0

    # Total nego from other Doc Nego entries (excluding current one)
    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s AND name != %s 
    """, (doc.inv_no, doc.name))[0][0] or 0

    # Can Nego calculation
    can_nego = round((cif_document - total_nego) + min(total_nego - total_received, 0), 2)
    nego = doc.nego_amount or 0

    if nego > can_nego:
        frappe.throw(_(f"""
            ❌ <b>Nego amount exceeds the Document Amount.</b><br>
            <b>CIF Document Amount:</b> {cif_document:,.2f}<br>
            <b>Total Already Received:</b> {total_received:,.2f}<br>
            <b>Total Already Nego:</b> {total_nego:,.2f}<br>
            <b>Can Nego:</b> {can_nego:,.2f}<br>
            <b>This Entry:</b> {doc.nego_amount:,.2f}
        """))
        doc.nego_amount= None

    # Validate Nego Date
    inv_date = frappe.db.get_value("CIF Sheet", doc.inv_no, "inv_date") or ""

    # convert strings to date if needed
    if isinstance(doc.nego_date, str):
        nego_date = datetime.strptime(doc.nego_date, "%Y-%m-%d").date()

    if isinstance(inv_date, str):
        inv_date = datetime.strptime(inv_date, "%Y-%m-%d").date()

    if nego_date and inv_date and nego_date < inv_date:
        frappe.msgprint(
            _("🛑 <b>Nego Date</b> cannot be before the <b>Invoice Date</b>. Please correct the dates."),
            title=_("Date Validation Error")
        )
        doc.nego_date = None


class DocNego(Document): 
    def validate(self):
        final_validation(self)


@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.db.get_value(
        "CIF Sheet", inv_no,
        ["inv_date", "category", "notify", "customer",
         "bank", "payment_term", "term_days", "due_date", "document"],
        as_dict=True
    ) or {}

    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0

    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0
    doc= cif.get("document")
    cif["can_nego"]=(doc- total_nego) + min(total_nego-total_received,0)

    return cif

@frappe.whitelist()
def update_cif_bank_if_missing(inv_no, bank_value):
    if not inv_no or not bank_value:
        return

    # Only update bank if it's missing
    bank = frappe.db.get_value("CIF Sheet", inv_no, "bank")
    if not bank:
        frappe.db.set_value("CIF Sheet", inv_no, "bank", bank_value)
        frappe.db.commit()

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    query = """
    SELECT cif.name, cif.inv_no
    FROM `tabCIF Sheet` AS cif
    LEFT JOIN (
        SELECT inv_no, SUM(received) AS total_received
        FROM `tabDoc Received`
        GROUP BY inv_no
    ) AS dr ON dr.inv_no = cif.name
    LEFT JOIN (
        SELECT inv_no, SUM(nego_amount) AS total_nego
        FROM `tabDoc Nego`
        GROUP BY inv_no
    ) AS dn ON dn.inv_no = cif.name
    WHERE cif.document > 0
        AND cif.payment_term != 'TT'
        AND cif.inv_no LIKE %s
        AND ROUND(
            (cif.document - IFNULL(dn.total_nego, 0)) 
            + LEAST(IFNULL(dn.total_nego, 0) - IFNULL(dr.total_received, 0), 0),
            2
        ) > 0
    ORDER BY cif.inv_no ASC
    LIMIT %s, %s
    """
    return frappe.db.sql(query, (f"%{txt}%", start, page_len))
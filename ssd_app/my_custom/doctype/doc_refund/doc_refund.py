# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def final_validation(doc):
    # Get total received for this invoice
    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s
    """, (doc.inv_no,))[0][0]

    # Get total negotiated amount
    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s
    """, (doc.inv_no,))[0][0]

    # Get total refunded already
    total_ref = frappe.db.sql("""
        SELECT IFNULL(SUM(refund_amount), 0)
        FROM `tabDoc Refund`
        WHERE inv_no = %s
        AND name != %s  
    """, (doc.inv_no, doc.name))[0][0]

    # Compute pending Nego balance
    pending_nego = max(total_nego - total_received - total_ref, 0)

    # Validation 1: For new docs only
    if doc.is_new() and pending_nego < doc.refund_amount:
        frappe.throw(f"""
            ❌ <b>Refund amount exceeds the Nego Amount.</b><br>
            <b>Total Nego Amount:</b> {total_nego:,.2f}<br>
            <b>Total Refund:</b> {total_ref:,.2f}<br>
            <b>Total Already Received:</b> {total_received:,.2f}<br>
            <b>Balance in Nego:</b> {pending_nego:,.2f}<br>
            <b>This Entry:</b> {doc.refund_amount:,.2f}
        """)

    # Validation 2: Total Refund + current refund > Nego
    if (total_ref + doc.refund_amount) > total_nego:
        frappe.throw(f"""
            ❌ <b>Total Refund amount exceeds the Nego Amount.</b><br>
            <b>Total Nego Amount:</b> {total_nego:,.2f}<br>
            <b>Total Refund (including this):</b> {(total_ref + doc.refund_amount):,.2f}
        """)

class DocRefund(Document):
    def validate(self):
        final_validation(self)



# @frappe.whitelist()
# def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
# 	return frappe.db.sql(f"""
#         SELECT cif.name, cif.inv_no FROM 
#         (SELECT inv_no, SUM(nego_amount) AS total_nego 
#         FROM `tabDoc Nego` GROUP BY inv_no) 
#         AS nego 
#         LEFT JOIN `tabCIF Sheet` AS cif ON cif.name = nego.inv_no 
#         LEFT JOIN 
#         (SELECT inv_no, SUM(received) AS total_rec FROM `tabDoc Received`
#         GROUP BY inv_no) AS rec 
#         ON rec.inv_no = nego.inv_no
# 		(SELECT inv_no, SUM(ref_amount) AS total_ref FROM `tabDoc Refund`
#         GROUP BY inv_no) AS ref 
#         ON ref.inv_no = nego.inv_no
#         WHERE COALESCE((nego.total_nego, 0) - COALESCE(rec.total_ref, 0)- COALESCE(rec.total_rec, 0)) > 0;
#         """,)

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(f"""
        SELECT cif.name, cif.inv_no
        FROM (
            SELECT inv_no, SUM(nego_amount) AS total_nego
            FROM `tabDoc Nego`
            GROUP BY inv_no
        ) AS nego
        LEFT JOIN `tabCIF Sheet` AS cif ON cif.name = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(received) AS total_rec
            FROM `tabDoc Received`
            GROUP BY inv_no
        ) AS rec ON rec.inv_no = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(refund_amount) AS total_ref
            FROM `tabDoc Refund`
            GROUP BY inv_no
        ) AS ref ON ref.inv_no = nego.inv_no
        WHERE (COALESCE(nego.total_nego, 0) - COALESCE(ref.total_ref, 0)) > COALESCE(rec.total_rec, 0) 
        AND (cif.name LIKE %(txt)s OR cif.inv_no LIKE %(txt)s)
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })


@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.db.get_value(
        "CIF Sheet", inv_no,
        ["inv_date", "category", "notify", "customer",
         "bank", "payment_term", "term_days", "document"],
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
	
    total_ref = frappe.db.sql("""
        SELECT IFNULL(SUM(refund_amount), 0)
        FROM `tabDoc Refund`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0

    # cif["total_received"] = round(total_received, 2)
    cif["nego_amount"]= total_nego-total_received-total_ref
    # cif["receivable"] = round(cif["document"] - total_received, 2)

    return cif
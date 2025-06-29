# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# ----------------------------
# 🔁 Utility: Aggregate sums by inv_no
# ----------------------------
def get_total(table, field, inv_no, exclude_name=None):
    condition = "AND name != %(exclude_name)s" if exclude_name else ""
    params = {"inv_no": inv_no}
    if exclude_name:
        params["exclude_name"] = exclude_name

    return frappe.db.sql(f"""
        SELECT IFNULL(SUM({field}), 0)
        FROM `tab{table}`
        WHERE inv_no = %(inv_no)s {condition}
    """, params)[0][0]

# ----------------------------
# 🔎 Validate refund entry
# ----------------------------
def final_validation(doc):
    total_received = get_total("Doc Received", "received", doc.inv_no)
    total_nego     = get_total("Doc Nego", "nego_amount", doc.inv_no)
    total_ref      = get_total("Doc Refund", "refund_amount", doc.inv_no, exclude_name=doc.name)

    pending_nego = max(total_nego - total_received - total_ref, 0)

    if doc.is_new() and pending_nego < doc.refund_amount:
        frappe.throw(f"""
            ❌ <b>Refund amount exceeds the Nego Amount.</b><br>
            <b>Total Nego Amount:</b> {total_nego:,.2f}<br>
            <b>Total Refund:</b> {total_ref:,.2f}<br>
            <b>Total Already Received:</b> {total_received:,.2f}<br>
            <b>Balance in Nego:</b> {pending_nego:,.2f}<br>
            <b>This Entry:</b> {doc.refund_amount:,.2f}
        """)

    if (total_ref + doc.refund_amount) > total_nego:
        frappe.throw(f"""
            ❌ <b>Total Refund amount exceeds the Nego Amount.</b><br>
            <b>Total Nego Amount:</b> {total_nego:,.2f}<br>
            <b>Total Refund (including this):</b> {(total_ref + doc.refund_amount):,.2f}
        """)


def protect_delete(doc):
    if frappe.db.exists("Doc Received", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Received part or full")


def put_value_from_cif(doc):
    if doc.is_new():
        fields = ["customer", "bank", "notify", "payment_term"]
        data = frappe.db.get_value("CIF Sheet", doc.inv_no, fields, as_dict=True)

        if data:
            for field in fields:
                if not getattr(doc, field):  # only set if value is missing
                    setattr(doc, field, data.get(field))

    

# ----------------------------
# 📄 DocType Class
# ----------------------------
class DocRefund(Document):
    def validate(self):
        final_validation(self)

    def before_save(self):
        put_value_from_cif(self)

    def on_trash(self):
        protect_delete(self)

# ----------------------------
# 🔍 For Link Field Filtering
# ----------------------------
@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT cif.name, cif.inv_no
        FROM (
            SELECT inv_no, SUM(nego_amount) AS total_nego
            FROM `tabDoc Nego` GROUP BY inv_no
        ) AS nego
        LEFT JOIN `tabCIF Sheet` AS cif ON cif.name = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(received) AS total_rec
            FROM `tabDoc Received` GROUP BY inv_no
        ) AS rec ON rec.inv_no = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(refund_amount) AS total_ref
            FROM `tabDoc Refund` GROUP BY inv_no
        ) AS ref ON ref.inv_no = nego.inv_no
        WHERE (COALESCE(nego.total_nego, 0) - COALESCE(ref.total_ref, 0)) > COALESCE(rec.total_rec, 0)
          AND (cif.name LIKE %(txt)s OR cif.inv_no LIKE %(txt)s)
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

# ----------------------------
# 🧠 Get CIF data with computed nego amount
# ----------------------------
@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.db.get_value(
        "CIF Sheet", inv_no,
        ["inv_date", "category", "notify", "customer", "bank", "payment_term", "term_days", "document"],
        as_dict=True
    ) or {}

    total_received = get_total("Doc Received", "received", inv_no)
    total_nego     = get_total("Doc Nego", "nego_amount", inv_no)
    total_ref      = get_total("Doc Refund", "refund_amount", inv_no)

    cif["nego_amount"] = total_nego - total_received - total_ref

    return cif

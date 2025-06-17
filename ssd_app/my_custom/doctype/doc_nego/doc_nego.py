# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class DocNego(Document):
	def validate(self):
		if not self.inv_no:
			return

		# Fetch CIF document value
		cif_document = frappe.db.get_value("CIF Sheet", self.inv_no, "document") or 0

		# Total received from other Doc Received entries (excluding current one)
		total_received = frappe.db.sql("""
			SELECT IFNULL(SUM(received), 0)
			FROM `tabDoc Received`
			WHERE inv_no = %s AND name != %s
		""", (self.inv_no, self.name))[0][0] or 0

		total_nego = frappe.db.sql("""
			SELECT IFNULL(SUM(nego_amount), 0)
			FROM `tabDoc Nego`
			WHERE inv_no = %s AND name != %s
		""", (self.inv_no, self.name))[0][0] or 0

		# Add current form's value
		# total_with_current = round(total_received + (self.received or 0), 2)
		receivable = round(cif_document - total_received, 2)
		can_nego = round(cif_document - total_received- total_nego, 2)

		if self.nego_amount > round(can_nego, 2):
			frappe.throw(_(f"""
				❌ <b>Nego amount exceeds the Document Amount.</b>
				<br><b>CIF Document Amount:</b> {cif_document:,.2f}
				<br><b>Total Already Received:</b> {total_received:,.2f}
				<br><b>Total Already Nego:</b> {total_nego:,.2f}
				<br><b>Can Nego:</b> {can_nego:,.2f}
				<br><b>This Entry :</b> {self.nego_amount:,.2f}
			"""))



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

    total_ref = frappe.db.sql("""
        SELECT IFNULL(SUM(refund_amount), 0)
        FROM `tabDoc Refund`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0
    doc= cif.get("document")
    cif["can_nego"]=(doc- total_nego) + min(total_ref-total_received,0)

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
    return frappe.db.sql(f"""
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
        AND ROUND(cif.document - IFNULL(dr.total_received, 0)-IFNULL(dn.total_nego, 0), 2) > 0
        ORDER BY cif.inv_no ASC
        LIMIT %s, %s
    """, (f"%{txt}%", start, page_len))

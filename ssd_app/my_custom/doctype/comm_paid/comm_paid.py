# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _

class CommPaid(Document):
    def validate(self):
        validate_comm_breakup(self)
        validate_unique_inv_no(self)

def validate_comm_breakup(doc):
    """
    Validate the comm Breakup child table:
    - sum of amounts == amount_usd
    - no blank/zero/negative amounts
    """
    total_amount = doc.amount_usd or 0
    breakup_sum = sum(flt(d.amount) for d in doc.comm_breakup)

    if total_amount <= 0:
        frappe.throw(_("Amount USD should not be zero"))

    if breakup_sum != total_amount:
        frappe.throw(
            _("Total of Comm Breakup amounts ({0}) must equal Amount USD ({1})")
            .format(breakup_sum, total_amount)
        )

    for row in doc.comm_breakup:
        if row.amount is None or row.amount <= 0:
            frappe.throw(_("Each Comm Breakup row must have a positive amount and cannot be zero"))


def validate_unique_inv_no(doc):
    inv_no_set = set()
    for idx, row in enumerate(doc.comm_breakup, start=1):
        row.inv_no = (row.inv_no or "").strip()
        if not row.inv_no:
            frappe.throw(f"⚠️ Row {idx}: Inv No cannot be empty.")
        if row.inv_no in inv_no_set:
            frappe.throw(f"⚠️ Row {idx}: Inv No '{row.inv_no}' is duplicated in Comm Breakup.")
        inv_no_set.add(row.inv_no)


@frappe.whitelist()
def inv_no_filter(doc):
	pass

@frappe.whitelist()
def get_filter_inv_no(doctype, txt, searchfield, start, page_len, filters=None):
    filters = filters or {}
    agent = filters.get('agent')

    query = """
        SELECT
            cost.name,
            cost.custom_title,
            cost.commission,
			(cost.commission- IFNULL(cb.total_paid, 0)) AS Balance,
            IFNULL(cb.total_paid, 0) AS total_paid
        FROM `tabCost Sheet` AS cost
        LEFT JOIN (
            SELECT inv_no, SUM(amount) AS total_paid
            FROM `tabComm Breakup`
            GROUP BY inv_no
        ) cb ON cost.name = cb.inv_no
        WHERE (%s IS NULL OR cost.agent = %s)
		AND (cost.commission- IFNULL(cb.total_paid, 0)) != 0
        ORDER BY cost.name ASC
        LIMIT %s OFFSET %s
    """

    params = (
        agent, agent,
        page_len, start
    )

    return frappe.db.sql(query, params)

@frappe.whitelist()
def get_inv_no_balance(inv_no):
    balance = frappe.db.sql("""
        SELECT 
            (cost.commission - IFNULL(cb.total_paid, 0)) AS balance
        FROM `tabCost Sheet` AS cost
        LEFT JOIN (
            SELECT inv_no, SUM(amount) AS total_paid
            FROM `tabComm Breakup`
            GROUP BY inv_no
        ) cb ON cost.name = cb.inv_no
        WHERE cost.name = %s
    """, (inv_no,), as_dict=1)

    if balance:
        return balance[0].balance
    return 0

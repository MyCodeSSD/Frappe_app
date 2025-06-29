# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CommPaid(Document):
	pass


@frappe.whitelist()
def inv_no_filter(doc):
	pass

@frappe.whitelist()
def get_filter_inv_no(doctype, txt, searchfield, start, page_len, filters=None):

    filters = filters or {}
    agent = filters.get('agent')
	
    query = """
        SELECT cost.name, cost.custom_title
        FROM `tabCost Sheet` AS cost
        WHERE (%s IS NULL OR cost.agent = %s)
        ORDER BY cost.inv_no ASC
    """

    params = (
        agent, agent,
    )

	
    return frappe.db.sql(query, params)


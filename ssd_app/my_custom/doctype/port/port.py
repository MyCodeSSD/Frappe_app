# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def set_custom_title(doc):
	if (not doc.port or not doc.country):
		return
	country= frappe.db.get_value("Country",doc.country, "country_name")
	doc.custom_title = f"{country.strip()} :: {doc.port.strip()}".strip()

class Port(Document):
	def before_save(self):
		set_custom_title(self)

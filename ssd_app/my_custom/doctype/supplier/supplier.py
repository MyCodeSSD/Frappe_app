# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def fill_country(doc):
    if not doc.supplier:
        return
    
    country = frappe.db.get_value("City", doc.supplier, "country")
    if country:
        doc.country = country

class Supplier(Document):
	def before_save(self):
		fill_country(self)

# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def set_default(doc):
    if not doc.notify:
        return
    
    country = frappe.db.get_value("City", doc.city, "country")
    if country:
        doc.country = country

    if not doc.customer_group:
        doc.customer_group = doc.notify

class Notify(Document):
    def before_save(self):
        set_default(self)


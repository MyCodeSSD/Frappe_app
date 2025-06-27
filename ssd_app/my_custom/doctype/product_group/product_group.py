# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# Create Custom Title 
def set_custom_title(doc):
    if not doc.product_category:
        return
    
    p_category = frappe.db.get_value("Product Category", doc.product_category, "product_category") or ""

    product_group = doc.product_group or ""
    doc.custom_title = f"{(p_category or '').strip()} :: {product_group.strip()}".strip()

class ProductGroup(Document):
	def before_save(self):
		set_custom_title(self)

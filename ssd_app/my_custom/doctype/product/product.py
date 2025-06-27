# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# Create Custom Title 
def set_custom_title(doc):
    if not doc.product_group:
        return

    p_group, p_category_id = frappe.db.get_value("Product Group", doc.product_group, ["product_group", "product_category"],
        as_dict=False
    ) or ("", "")

    product = doc.product or ""
    doc.custom_title = f"{(p_group or '').strip()} :: {product.strip()}".strip()
    doc.category = p_category_id
    
class Product(Document):
	def before_save(self):
		set_custom_title(self)

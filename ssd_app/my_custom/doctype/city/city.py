# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

# Create Custom Title 
def set_custom_title(doc):
	city = doc.city
	country = doc.country
	
	# Strip and combine
	doc.custom_title = f"{country.strip()} :: {city.strip()}".strip()
	# doc.title = doc.custom_title

class City(Document):
	def before_save(self):
		set_custom_title(self)
	

import frappe
from frappe import _
from frappe.model.document import Document

@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.get_doc("CIF Sheet", inv_no)
    data = {
        "inv_date": cif.inv_date,
        "category": cif.category,
        "notify": cif.notify,
        "customer": cif.customer,
        "bank": cif.bank,
        "payment_term": cif.payment_term,
        "term_days":cif.term_days,
        "document":cif.document
    }
    return data

@frappe.whitelist()
def update_cif_bank_if_missing(inv_no, bank_value):
    if not inv_no or not bank_value:
        return

    doc = frappe.get_doc("CIF Sheet", inv_no)
    if not doc.bank:
        doc.bank = bank_value
        doc.save(ignore_permissions=True)  
        # frappe.msgprint("Bank updated successfully")      
        return
    
    return



class DocReceived(Document):
    frappe.frappe.msgprint('Message')
    
	# pass

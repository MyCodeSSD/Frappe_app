from frappe.model.document import Document
import frappe
from frappe import _
from frappe.utils import flt

def validate_amount_sum(doc):
    total_child_amount = sum(flt(row.amount) for row in doc.cc_breakup)
    if flt(doc.amount_usd) != total_child_amount:
        frappe.throw(
            f"⚠️ Amount (USD) {doc.amount_usd} must equal the total of child amounts {total_child_amount}."
        )

def validate_child_amount_nonzero(doc):
        for idx, row in enumerate(doc.cc_breakup, start=1):
            if flt(row.amount) == 0:
                frappe.throw(
                    f"⚠️ Row {idx}: Amount cannot be zero in CC Breakup."
                )

def validate_unique_ref_no(doc):
    ref_no_set = set()
    for idx, row in enumerate(doc.cc_breakup, start=1):
        row.ref_no = (row.ref_no or "").strip()
        if not row.ref_no:
            frappe.throw(f"⚠️ Row {idx}: Ref No cannot be empty.")
        if row.ref_no in ref_no_set:
            frappe.throw(f"⚠️ Row {idx}: Ref No '{row.ref_no}' is duplicated in CC Breakup.")
        ref_no_set.add(row.ref_no)


class CCReceived(Document):
    def validate(self):
        validate_amount_sum(self)
        validate_child_amount_nonzero(self)
        validate_unique_ref_no(self)


   

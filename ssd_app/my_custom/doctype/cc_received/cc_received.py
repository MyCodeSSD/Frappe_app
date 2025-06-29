from frappe.model.document import Document
import frappe
from frappe import _
from frappe.utils import flt


class CCReceived(Document):
    def validate(self):
        validate_cc_breakup(self)  # delegate validation to helper

def validate_cc_breakup(doc):
    """
    Validate the CC Breakup child table:
    - sum of amounts == amount_usd
    - no blank/zero/negative amounts
    - optional: first row ref_no must be 'On Account'
    """
    total_amount = doc.amount_usd or 0
    breakup_sum = sum(flt(d.amount) for d in doc.cc_breakup)

    if total_amount <= 0:
        frappe.throw(_("Amount USD must be greater than zero"))

    if breakup_sum != total_amount:
        frappe.throw(
            _("Total of CC Breakup amounts ({0}) must equal Amount USD ({1})")
            .format(breakup_sum, total_amount)
        )

    for row in doc.cc_breakup:
        if row.amount is None or row.amount <= 0:
            frappe.throw(_("Each CC Breakup row must have a positive amount and cannot be zero"))

    # Optional: enforce first row ref_no rule
    if doc.cc_breakup:
        first = doc.cc_breakup[0]
        if first.ref_no != 'On Account':
            frappe.throw(_("First CC Breakup row must have Ref No 'On Account'"))


import frappe
from frappe.model.document import Document
from frappe import _


def update_cif_bank_if_missing(doc):
    # Only update bank if it's missing
    bank = frappe.db.get_value("CIF Sheet", doc.inv_no, "bank")
    if bank:
        doc.bank=bank
    else:
        if(doc.bank):
            frappe.db.set_value("CIF Sheet", doc.inv_no, "bank", doc.bank)
        else:
            frappe.throw('Bank name not put in CIF Sheet, Please insert Bank name')



def final_validation(doc):
    if not doc.inv_no:
            return

    # Fetch CIF document value
    cif_document = frappe.db.get_value("CIF Sheet", doc.inv_no, "document") or 0

    # Total received from other Doc Received entries (excluding current one)
    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s AND name != %s
    """, (doc.inv_no, doc.name))[0][0] or 0

    # Add current form's value
    total_with_current = round(total_received + (doc.received or 0), 2)
    receivable = round(cif_document - total_received, 2)

    if total_with_current > round(cif_document, 2):
        frappe.throw(_(f"""
            ❌ <b>Received amount exceeds the receivable limit.</b>
            <br><b>CIF Document Amount:</b> {cif_document:,.2f}
            <br><b>Total Already Received:</b> {total_received:,.2f}
            <br><b>Receivable:</b> {receivable:,.2f}
            <br><b>This Entry:</b> {doc.received:,.2f}
        """))

def put_value_from_cif(doc):
    if doc.is_new():
        fields = ["inv_date", "category", "customer", "bank", "notify", "payment_term", "term_days", "document"]
        data = frappe.db.get_value("CIF Sheet", doc.inv_no, fields, as_dict=True)

        if data:
            for field in fields:
                if not getattr(doc, field):  # only set if value is missing
                    setattr(doc, field, data.get(field))


class DocReceived(Document):
    def validate(self):
        final_validation(self)
        update_cif_bank_if_missing(self)
    
    def before_save(self):
        put_value_from_cif(self)


@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.db.get_value(
        "CIF Sheet", inv_no,
        ["inv_date", "category", "notify", "customer",
         "bank", "payment_term", "term_days", "document"],
        as_dict=True
    ) or {}

    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0

    cif["total_received"] = round(total_received, 2)
    cif["receivable"] = round(cif["document"] - total_received, 2)

    return cif



@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(f"""
        SELECT cif.name, cif.inv_no
        FROM `tabCIF Sheet` AS cif
        LEFT JOIN (
            SELECT inv_no, SUM(received) AS total_received
            FROM `tabDoc Received`
            GROUP BY inv_no
        ) AS dr ON dr.inv_no = cif.name
        WHERE cif.document > 0 
        AND cif.payment_term != 'TT'
        AND cif.inv_no LIKE %s
        AND ROUND(cif.document - IFNULL(dr.total_received, 0), 2) > 0
        ORDER BY cif.inv_no ASC
        LIMIT %s, %s
    """, (f"%{txt}%", start, page_len))


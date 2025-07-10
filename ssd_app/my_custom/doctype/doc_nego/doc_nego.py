# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
# from datetime import datetime, timedelta
from frappe.utils import getdate, add_days
import json
import pandas as pd


def calculate_term_days(doc):
    if doc.bank_due_date and doc.nego_date:
        due_date = getdate(doc.bank_due_date)
        nego_date = getdate(doc.nego_date)

        if due_date > nego_date:
            doc.term_days = (due_date - nego_date).days
        else:
            frappe.throw(
                title="Invalid Date",
                msg="Bank Due Date must be after Negotiation Date."
            )

def calculate_due_date(doc):
    if doc.term_days and doc.nego_date and not doc.bank_due_date:
        if doc.term_days > 0:
            nego_date = getdate(doc.nego_date)
            doc.bank_due_date = add_days(nego_date, doc.term_days)
        else:
            frappe.throw(
                title="Invalid Term Days",
                msg="Term Days must be a positive integer."
            )


def final_validation(doc):
    if not doc.inv_no:
        return

    # Fetch CIF document value
    cif_data = frappe.db.get_value("CIF Sheet", doc.inv_no, ["document", "inv_date"], as_dict=True)
    cif_document = cif_data.document or 0
    inv_date = cif_data.inv_date or ""

    # Total received from other Doc Received entries (excluding current one)
    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s 
    """, (doc.inv_no))[0][0] or 0

    # Total nego from other Doc Nego entries (excluding current one)
    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s AND name != %s 
    """, (doc.inv_no, doc.name))[0][0] or 0

    # Can Nego calculation
    can_nego = round((cif_document - total_nego) + min(total_nego - total_received, 0), 2)
    nego = doc.nego_amount or 0

    if doc.is_new() and nego > can_nego:
        frappe.throw(_(f"""
            ❌ <b>Nego amount exceeds the Document Amount.</b><br>
            <b>CIF Document Amount:</b> {cif_document:,.2f}<br>
            <b>Total Already Received:</b> {total_received:,.2f}<br>
            <b>Total Already Nego:</b> {total_nego:,.2f}<br>
            <b>Can Nego:</b> {can_nego:,.2f}<br>
            <b>This Entry:</b> {doc.nego_amount:,.2f}
        """))
        

    if (total_nego + doc.nego_amount)>cif_document:
        frappe.throw(_(f"""
            ❌ <b> Total Nego amount exceeds the Document Amount.</b><br>
            <b>CIF Document Amount:</b> {cif_document:,.2f}<br>
            <b>Total Already Nego:</b> {total_nego:,.2f}<br>
            <b>This Entry:</b> {doc.nego_amount:,.2f}
        """))


    nego_date = getdate(doc.nego_date) if doc.nego_date else None
    inv_date = getdate(cif_data.inv_date) if cif_data.inv_date else None

    if not inv_date:
        frappe.throw(_("🛑 Please set the <b>Invoice Date</b> before saving."))

    if not nego_date:
        frappe.throw(_("🛑 Please set the <b>Nego Date</b> before saving."))

    if nego_date < inv_date:
        frappe.throw(
            _("🛑 <b>Nego Date</b> cannot be before the <b>Invoice Date</b>. Please correct the dates."),
            title=_("Date Validation Error")
        )

def update_cif_bank_if_missing(doc):
    # Only update bank if it's missing
    bank = frappe.db.get_value("CIF Sheet", doc.inv_no, "bank")

    if bank:
        doc.bank=bank
        frappe.get_meta(doc.doctype).get_field("bank").read_only = 1

    else:
        if(doc.bank):
            frappe.db.set_value("CIF Sheet", doc.inv_no, "bank", doc.bank)
            # frappe.db.commit()
        else:
            frappe.throw('Bank name not put in CIF Sheet, Please input Bank name')
            

def protect_delete(doc):

    if frappe.db.exists("Doc Received", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Received part or full")
    if frappe.db.exists("Doc Refund", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Refunded")



def put_value_from_cif(doc):
    if doc.is_new():
        fields = ["inv_date", "category", "notify", "customer", "bank", "payment_term", "due_date"]
        data = frappe.db.get_value("CIF Sheet", doc.inv_no, fields, as_dict=True)

        if data:
            for field in fields:
                if not getattr(doc, field):  # only set if value is missing
                    setattr(doc, field, data.get(field))


class DocNego(Document): 
    def validate(self):
        final_validation(self)
        update_cif_bank_if_missing(self)
        calculate_term_days(self)
        calculate_due_date

    
    def before_save(self):
        put_value_from_cif(self)
    
    def on_trash(self):
        protect_delete(self)

@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.db.get_value(
        "CIF Sheet", inv_no,
        ["inv_date", "category", "notify", "customer",
         "bank", "payment_term", "term_days", "due_date", "document"],
        as_dict=True
    ) or {}

    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0

    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0
    doc= cif.get("document")
    cif["can_nego"]=(doc- total_nego) + min(total_nego-total_received,0)

    return cif

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    query = """
    SELECT cif.name, cif.inv_no
    FROM `tabCIF Sheet` AS cif
    LEFT JOIN (
        SELECT inv_no, SUM(received) AS total_received
        FROM `tabDoc Received`
        GROUP BY inv_no
    ) AS dr ON dr.inv_no = cif.name
    LEFT JOIN (
        SELECT inv_no, SUM(nego_amount) AS total_nego
        FROM `tabDoc Nego`
        GROUP BY inv_no
    ) AS dn ON dn.inv_no = cif.name
    WHERE cif.document > 0
        AND cif.payment_term != 'TT'
        AND cif.inv_no LIKE %s
        AND ROUND(
            (cif.document - IFNULL(dn.total_nego, 0)) 
            + LEAST(IFNULL(dn.total_nego, 0) - IFNULL(dr.total_received, 0), 0),
            2
        ) > 0
    ORDER BY cif.inv_no ASC
    LIMIT %s, %s
    """
    return frappe.db.sql(query, (f"%{txt}%", start, page_len))





@frappe.whitelist()
def banking_line(as_on):
    query = """
    SELECT
        cif.name,
        cif.inv_no,
        com.company_code AS com,
        bank.bank,
        CASE 
            WHEN cif.payment_term IN ('DA', 'DP') THEN 'DA+DP'
            ELSE cif.payment_term
        END AS p_term,
        ROUND(cif.document, 0) * 1.0 AS document,
        GREATEST(
            IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0),
            0
        ) * 1.0 AS nego
    FROM `tabCIF Sheet` cif
    LEFT JOIN (
        SELECT inv_no, SUM(nego_amount) * 1.0 AS total_nego
        FROM `tabDoc Nego`
        WHERE nego_date <= %(as_on)s
        GROUP BY inv_no
    ) nego ON cif.name = nego.inv_no
    LEFT JOIN (
        SELECT inv_no, SUM(refund_amount) * 1.0 AS total_ref
        FROM `tabDoc Refund`
        WHERE refund_date <= %(as_on)s
        GROUP BY inv_no
    ) ref ON cif.name = ref.inv_no
    LEFT JOIN (
        SELECT inv_no, SUM(received) * 1.0 AS total_rec
        FROM `tabDoc Received`
        WHERE received_date <= %(as_on)s
        GROUP BY inv_no
    ) rec ON cif.name = rec.inv_no
    LEFT JOIN `tabBank` bank ON cif.bank = bank.name
    LEFT JOIN `tabCompany` com ON cif.shipping_company= com.name
    WHERE cif.payment_term != 'TT'
      AND GREATEST(
          IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0),
          0
      ) != 0
      AND cif.inv_date <= %(as_on)s
    ORDER BY cif.name ASC
    """

    rows = frappe.db.sql(query, {"as_on": as_on}, as_dict=True)
    # Force to list of pure dicts
    data = [dict(row) for row in rows]

    if not data:
        return "<p>No data found</p>"

    df = pd.DataFrame(data)

    # Get full list of banks across all data
    all_banks = sorted(df['bank'].dropna().unique())

    total_columns = 1 + len(all_banks) + 1
    col_width = 100 / total_columns

    html = """
    <style>
        .babking_line-table-container {
            max-height: 80vh;
            overflow: auto;
            width: 100%;
        }
        table.babking_line-table {
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
        }
        table.babking_line-table th, table.babking_line-table td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: right;
            white-space: nowrap;
        }
        table.babking_line-table th {
            background-color: #f5f5f5;
            position: sticky;
            top: 0;
            z-index: 1;
            text-align: center;
        }
        td#left { text-align: left; }
        .total-column { font-weight: bold; }
        .total-row td { font-weight: bold; }
    </style>
    """

    col_width = 15  # percent for Payment Term column
    num_numeric_cols = len(all_banks) + 1  # +1 for Total column
    numeric_col_width = (100 - col_width) / num_numeric_cols

    # Process per company
    com_list = df['com'].dropna().unique()
    for com in com_list:
        df_com = df[df['com'] == com]
        pivot = pd.pivot_table(
            df_com, values='nego', index='p_term', columns='bank',
            aggfunc='sum', fill_value=0
        )
        pivot = pivot.reindex(columns=all_banks, fill_value=0)
        pivot['Total'] = pivot.sum(axis=1)
        total_row = pd.DataFrame(pivot.sum(axis=0)).T
        total_row.index = ['Total']
        pivot = pd.concat([pivot, total_row])
        pivot = pivot.round(2)

        html += f"<h3>{com}</h3>"
        html += "<div class='babking_line-table-container'>"
        html += "<table class='babking_line-table'>"
        html += "<thead><tr>"
        html += f"<th id='left' style='width:{col_width:.2f}%;'>Payment Term</th>"
        for bank in all_banks:
            html += f"<th style='width:{numeric_col_width:.2f}%;'>{bank}</th>"
        html += f"<th style='width:{numeric_col_width:.2f}%;'>Total</th></tr></thead>"
        html += "<tbody>"

        for idx, row in pivot.iterrows():
            total_row_class = "total-row" if idx == 'Total' else ""
            html += f"<tr class='{total_row_class}'><td id='left'>{idx}</td>"
            for bank in all_banks:
                html += f"<td>{'{:,.2f}'.format(row[bank])}</td>"
            html += f"<td class='total-column'>{'{:,.2f}'.format(row['Total'])}</td></tr>"
        html += "</tbody></table></div>"

    # Grand total
    grand_pivot = pd.pivot_table(
        df, values='nego', index='p_term', columns='bank',
        aggfunc='sum', fill_value=0
    )
    grand_pivot = grand_pivot.reindex(columns=all_banks, fill_value=0)
    grand_pivot['Total'] = grand_pivot.sum(axis=1)
    total_row = pd.DataFrame(grand_pivot.sum(axis=0)).T
    total_row.index = ['Total']
    grand_pivot = pd.concat([grand_pivot, total_row])
    grand_pivot = grand_pivot.round(2)

    html += "<h3>All Companies</h3>"
    html += "<div class='babking_line-table-container'>"
    html += "<table class='babking_line-table'>"
    html += "<thead><tr>"
    html += f"<th id='left' style='width:{col_width:.2f}%;'>Payment Term</th>"
    for bank in all_banks:
        html += f"<th style='width:{numeric_col_width:.2f}%;'>{bank}</th>"
    html += f"<th style='width:{numeric_col_width:.2f}%;'>Total</th></tr></thead>"
    html += "<tbody>"

    for idx, row in grand_pivot.iterrows():
        total_row_class = "total-row" if idx == 'Total' else ""
        html += f"<tr class='{total_row_class}'><td id='left'>{idx}</td>"
        for bank in all_banks:
            html += f"<td>{'{:,.2f}'.format(row[bank])}</td>"
        html += f"<td class='total-column'>{'{:,.2f}'.format(row['Total'])}</td></tr>"

    html += "</tbody></table></div>"

    return html
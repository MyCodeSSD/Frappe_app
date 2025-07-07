from frappe.model.document import Document
import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils import now_datetime
import pandas as pd
import json


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


   

@frappe.whitelist()
def cc_balance_breakup(cus_id, as_on):
    query = """
        SELECT 
            cif.inv_no AS ref_no,
            cif.cc AS amount
        FROM 
            `tabCIF Sheet` cif
        WHERE
            cif.customer = %(customer)s AND
            cif.inv_date <= %(date)s AND
            cif.cc !=0  
    """

    params = {
        "customer": cus_id,
        "date": as_on
    }

    raw_data = frappe.db.sql(query, params, as_dict=True)
    data = json.loads(frappe.as_json(raw_data))
    if data:
        df= pd.DataFrame(data)
        inv_data= df.copy()
    else:
        inv_data = pd.DataFrame(columns=["ref_no", "amount"])
# -------------------------------
    query = """
        SELECT 
            ccb.ref_no, 
            SUM(ccb.amount) AS amount
        FROM 
            `tabCC Breakup` ccb
        LEFT JOIN 
            `tabCC Received` ccr ON ccb.parent = ccr.name
        WHERE
            ccr.customer = %(customer)s AND
            ccr.date <= %(date)s
        GROUP BY
            ccb.ref_no
    """

    params = {
        "customer": cus_id,
        "date": as_on
    }

    raw_data = frappe.db.sql(query, params, as_dict=True)
    data = json.loads(frappe.as_json(raw_data))
    if data:
        df= pd.DataFrame(data)
        df["amount"]= df["amount"]*-1
        rec_data= df.copy()
    else:
        rec_data = pd.DataFrame(columns=["ref_no", "amount"])
# ---------------------------------------------------------

    final_df = pd.concat([inv_data, rec_data], ignore_index=True)
    final_df = final_df.groupby("ref_no")["amount"].sum().reset_index()
    # Build HTML table
    html = """
    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <thead style="background-color: #f0f0f0;">
            <tr>
                <th style="text-align: center;">Ref No</th>
                <th style="text-align: center;">Amount</th>
            </tr>
        </thead>
        <tbody>
    """
    total=0
    for _, row in final_df.iterrows():
        total+=row['amount']
        html += f"""
            <tr>
                <td>{row['ref_no']}</td>
                <td style="text-align: right;">{row['amount']:,.2f}</td>
            </tr>
        """
    html += f"""
        </tbody>
        <tfoot>
            <tr style="font-weight: bold; background-color: #f9f9f9;">
                <td style="text-align: center;">Total</td>
                <td style="text-align: right;">{total:,.2f}</td>
            </tr>
        </tfoot>
    </table>
    """

    return html

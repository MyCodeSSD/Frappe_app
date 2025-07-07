import frappe
import pandas as pd
import json

def execute(filters=None):
    conditions = ""
    if filters.get("customer"):
        conditions += " AND cif.customer = %(customer)s"

    if filters.get("as_on"):
        conditions += " AND cif.inv_date <= %(as_on)s"
    query = f"""
        SELECT 
            cif.inv_date AS date, 
            cif.inv_no, 
            cus.customer,
            noti.notify, 
            cif.sales, 
            cif.document, 
            cif.cc 
        FROM `tabCIF Sheet` cif
        LEFT JOIN `tabCustomer` cus ON cif.customer = cus.name
        LEFT JOIN `tabNotify` noti ON cif.notify = noti.name
        WHERE cif.cc!=0 {conditions}
    """
    raw_data = frappe.db.sql(query, filters, as_dict=True)
    data = json.loads(frappe.as_json(raw_data))
    if data:
        df = pd.DataFrame(data)
        df["note"] = ""
        cif_df = df[["date", "inv_no", "customer", "notify", "sales", "document", "cc", "note"]].copy()
    else:
        cif_df = pd.DataFrame(columns=["date", "inv_no", "customer", "notify", "sales", "document", "cc", "note"])

    # -----------------------------
    conditions = ""
    if filters.get("customer"):
        conditions += " AND rec.customer = %(customer)s"
    if filters.get("as_on"):
        conditions += " AND rec.date <= %(as_on)s"
    query = f"""
        SELECT rec.date, cus.customer, rec.amount_usd AS cc, rec.note 
        FROM `tabCC Received` rec
        LEFT JOIN `tabCustomer` cus ON rec.customer = cus.name
        WHERE 1=1 {conditions} 
    """
    raw_data = frappe.db.sql(query, filters, as_dict=True)
    data = json.loads(frappe.as_json(raw_data))
    if data:
        df = pd.DataFrame(data)
        df["inv_no"] = ""
        df["notify"] = ""
        df["sales"] = 0
        df["cc"] = df["cc"]*-1
        df["document"] = 0
        rec_df = df[["date", "inv_no", "customer", "notify", "sales", "document", "cc", "note"]]
    else:
        rec_df = pd.DataFrame(columns=["date", "inv_no", "customer", "notify", "sales", "document", "cc", "note"])

    # -----------------------------
    final_df = pd.concat([cif_df, rec_df], ignore_index=True)
    final_df["date"] = pd.to_datetime(final_df["date"], errors="coerce")
    final_df = final_df.sort_values(by="date").reset_index(drop=True)
    final_df["balance"] = final_df["cc"].cumsum()

    result = final_df.to_dict(orient='records')

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
        # {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 150},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 150},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 120},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 120},
        {"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Float", "width": 120},
        {"label": "Narration", "fieldname": "note", "fieldtype": "Data", "width": 250},
    ]
    if not filters.get("customer"):
        customer_col = {"label": "Customer","fieldname": "customer","fieldtype": "Data","width": 150}
        # insert at position 1 (second column)
        columns.insert(2, customer_col)
    return columns, result
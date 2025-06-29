# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import formatdate, flt
from frappe.utils.jinja import render_template
from frappe import _
from datetime import date, timedelta


today_str = date.today().strftime("%Y-%m-%d")

def execute(filters=None):    
	# columns, data = [], []
	conditional_filter= ""
	if(filters.based_on=="Receivable"):
		conditional_filter= "AND (cif.document - IFNULL(rec.total_rec, 0)) > 0"
	elif(filters.based_on=="Coll"):
		conditional_filter= """AND IFNULL( ROUND(
			(cif.document - IFNULL(nego.total_nego, 0)) 
			+ LEAST(IFNULL(nego.total_nego, 0) - IFNULL(rec.total_rec, 0), 0),
			2
		), 0)>0"""
	elif(filters.based_on=="Nego"):
		conditional_filter="""AND IFNULL( ROUND(
			(nego.total_nego - IFNULL(ref.total_ref, 0)) 
			+ LEAST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0),
			2
		), 0)>0"""
	elif(filters.based_on=="Refund"):
		conditional_filter= """ AND GREATEST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0)>0"""
	as_on= filters.as_on
	columns= [
	
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 120},
		{"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 130},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
		{"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 80},
		{"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 105},
		{"label": "Received", "fieldname": "total_rec", "fieldtype": "Float", "width": 105},
		{"label": "Receivable", "fieldname": "receivable", "fieldtype": "Float", "width": 105},
		{"label": "Cus Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
		{"label": "Bank Date", "fieldname": "bank_due_date", "fieldtype": "Date", "width": 110},
		{"label": "Coll", "fieldname": "coll", "fieldtype": "Float", "width": 100},
		{"label": "Nego", "fieldname": "nego", "fieldtype": "Float", "width": 100},
		{"label": "Refund", "fieldname": "ref", "fieldtype": "Float", "width": 100},
        # {"label": "Action", "fieldname": "action", "fieldtype": "HTML", "width": 80},
	]

	data=frappe.db.sql(f"""
        SELECT 
        cif.name, 
        cif.inv_no,
        cif.inv_date, 
        cus.code AS customer, 
        noti.code AS notify, 
        bank.bank,  
        IF(cif.payment_term IN ('LC', 'DA'),
        CONCAT(cif.payment_term, '- ', cif.term_days),
        cif.payment_term) AS p_term,
        ROUND(cif.document,0) AS document, 
        cif.due_date,
        IFNULL(nego.total_nego, 0) AS total_nego,
        CASE 
        WHEN IFNULL( ROUND(
            GREATEST((nego.total_nego - IFNULL(ref.total_ref, 0)) 
            + LEAST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0),0),
            2
        ), 0) > 0
        THEN nego.bank_due_date
        ELSE NULL
    END AS bank_due_date,
        DATEDIFF(nego.bank_due_date, CURDATE()) AS days_to_due,
        nego.due_date_confirm,
        IFNULL(ref.total_ref, 0) AS total_ref,
        IFNULL(rec.total_rec, 0) AS total_rec,
        ROUND(cif.document - IFNULL(rec.total_rec, 0), 2) AS receivable,
        IFNULL( ROUND(
            (cif.document - IFNULL(nego.total_nego, 0)) 
            + LEAST(IFNULL(nego.total_nego, 0) - IFNULL(rec.total_rec, 0), 0),
            2
        ), 0) AS coll,
        IFNULL( ROUND(
            GREATEST((nego.total_nego - IFNULL(ref.total_ref, 0)) 
            + LEAST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0),0),
            2
        ), 0) AS nego,
        GREATEST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0) as ref			
        FROM 
            `tabCIF Sheet` cif
        LEFT JOIN (
            SELECT 
                inv_no, 
                SUM(nego_amount) AS total_nego,
                MIN(bank_due_date) AS bank_due_date,
                MIN(due_date_confirm) AS due_date_confirm
            FROM 
                `tabDoc Nego`
            WHERE nego_date <= %(as_on)s
            GROUP BY 
                inv_no
        ) AS nego ON cif.name = nego.inv_no
        LEFT JOIN (
            SELECT 
                inv_no, 
                SUM(refund_amount) AS total_ref
            FROM 
                `tabDoc Refund`
            WHERE refund_date <= %(as_on)s
            GROUP BY 
                inv_no
        ) AS ref ON cif.name = ref.inv_no
        LEFT JOIN (
            SELECT 
                inv_no, 
                SUM(received) AS total_rec
            FROM 
                `tabDoc Received`
            WHERE received_date <= %(as_on)s
            GROUP BY 
                inv_no
        ) AS rec ON cif.name = rec.inv_no
        LEFT JOIN `tabCustomer` cus ON cif.customer= cus.name
        LEFT JOIN `tabNotify` noti ON cif.notify= noti.name
        LEFT JOIN `tabBank` bank ON cif.bank= bank.name
        WHERE 
            cif.payment_term != 'TT'
            {conditional_filter}
            AND cif.inv_date <= %(as_on)s
        ORDER BY 
            cif.inv_no ASC;""",
        {"as_on": as_on}, as_dict=1)
     
    # print(data)
	return columns, data
    



@frappe.whitelist()
def get_doc_flow(inv_name):
    if not inv_name:
        return "Invalid Invoice Number"
    doc = frappe.get_doc("CIF Sheet", inv_name)
    customer = frappe.get_value("Customer", doc.customer, "code")
    notify = frappe.get_value("Notify", doc.notify, "code")
    bank = frappe.get_value("Bank", doc.bank, "bank")
    category = frappe.get_value("Product Category", doc.category, "product_category")

    doc_amount = doc.document or 0

    inv = [{"name":doc.name,"Type": "Sales", "Date": doc.inv_date, "Amount": doc_amount, "Note":""}]
    
    nego = frappe.db.sql("""
        SELECT name, 'Nego' AS Type, nego_date AS Date, nego_amount AS Amount , note as Note
        FROM `tabDoc Nego` WHERE inv_no = %s
    """, (inv_name,), as_dict=1)
    
    ref = frappe.db.sql("""
        SELECT name, 'Refund' AS Type, refund_date AS Date, refund_amount AS Amount ,note as Note
        FROM `tabDoc Refund` WHERE inv_no = %s
    """, (inv_name,), as_dict=1)
    
    rec = frappe.db.sql("""
        SELECT name,'Received' AS Type, received_date AS Date, received AS Amount , note as Note
        FROM `tabDoc Received` WHERE inv_no = %s
    """, (inv_name,), as_dict=1)

    # Combine and sort by date
    combined = inv + nego + ref + rec
    combined.sort(key=lambda x: x["Date"] or frappe.utils.nowdate())

    # Running totals
    coll = 0
    nego_amt = 0
    refund = 0
    received = 0

    rows = ""
    for entry in combined:
        typ = entry['Type']
        amt = entry['Amount'] or 0
        nte= entry['Note'] or ""
        name= entry['name']

        if typ == "Sales":
            coll += amt

        elif typ == "Nego":
            coll -= amt
            nego_amt += amt

        elif typ == "Refund":
            nego_amt -= amt
            refund += amt

        elif typ == "Received":
            remain = amt

            # 2. Subtract from nego
            if remain > 0:
                if nego_amt >= remain:
                    nego_amt -= remain
                    remain = 0
                else:
                    remain -= nego_amt
                    nego_amt = 0

            # 1. Subtract from refund
            if refund >= remain:
                refund -= remain
                remain = 0
            else:
                remain -= refund
                refund = 0


            # 3. Subtract from coll
            if remain > 0:
                if coll >= remain:
                    coll -= remain
                    remain = 0
                else:
                    remain -= coll
                    coll = 0

            received += amt

        # Add a row to the table
        rows += f"""
        <tr>
            <td>{typ}</td>
            <td>{entry['Date']}</td>
            <td style="text-align: right;">{frappe.utils.fmt_money(amt)}</td>
            <td style="text-align: right;">{frappe.utils.fmt_money(received)}</td>
            <td style="text-align: right;">{frappe.utils.fmt_money(doc_amount - received)}</td>
            <td style="text-align: right;background-color: silver;">{frappe.utils.fmt_money(coll)}</td>
            <td style="text-align: right;background-color: silver;">{frappe.utils.fmt_money(nego_amt)}</td>
            <td style="text-align: right;background-color: silver;">{frappe.utils.fmt_money(refund)}</td>
            <td style="text-align: right;background-color: silver;">{nte}</td>
            
        """
        
    details_html = f"""
    <div style="margin-bottom: 12px;">
        <table style="width: 100%; font-size: 13px; margin-bottom: 10px;">
            <tr>
                <td style="width: 33%;"><b>Invoice Date:</b> {doc.inv_date}</td>
                <td style="width: 33%;"><b>Customer:</b> {customer}</td>
                <td style="width: 33%;"><b>Notify:</b> {notify}</td>
            </tr>
            <tr>
                <td><b>Bank:</b> {bank}</td>
                <td><b>Payment Term:</b> {doc.payment_term}{' - ' + str(doc.term_days) if doc.payment_term in ['LC', 'DA'] else ''} </td>
                <td><b>Category:</b> {category}</td>
                <td></td>
            </tr>
        </table>
    </div>
    """
    buttons_html = ""
    due_date = date.today() + timedelta(days=doc.term_days + 90)
    due_date_str = due_date.strftime("%Y-%m-%d")

    if coll > 0:
        buttons_html += f"""
        <a href="#"  onclick="frappe.new_doc('Doc Nego', {{ 
            inv_no: '{inv_name}',
            nego_date:'{today_str}', 
            term_days:'{doc.term_days}',
            nego_amount: {coll}, 
            bank_due_date:'{due_date_str}'
        }}); return false;" 
        class="btn btn-primary btn-sm" style="margin-left: 8px; background-color:blue;">Nego</a>
        """


    if nego_amt > 0:
        buttons_html += f"""
        <a href="#" onclick="frappe.new_doc('Doc Refund', {{ 
            inv_no: '{inv_name}',
            refund_date:'{today_str}',
            refund_amount: '{nego_amt}'}}); return false;" 
        class="btn btn-danger btn-sm" style="margin-left: 8px;background-color:red;">Refund</a>"""
        

    if (doc_amount - received) > 0:
        buttons_html += f"""
        <a href="#" onclick="frappe.new_doc('Doc Received', {{ 
            inv_no: '{inv_name}',
            received_date:'{today_str}',
            received:'{doc_amount - received}'
            }}); return false;" 
        class="btn btn-success btn-sm" style="margin-left: 8px; background-color:green;">Received</a>
        """

    html = f"""
    <div>
		{details_html}
        <table class="table table-bordered" style="font-size: 14px;">
            <thead>
                <tr>
                    <th style="width: 10%;">Type</th>
                    <th style="width: 15%;">Date</th>
                    <th style="width: 10%; text-align: right;">Amount</th>
                    <th style="width: 10%; text-align: right;">Received</th>
                    <th style="width: 10%; text-align: right;">Receivable</th>
                    <th style="width: 10%; text-align: right; background-color: silver;">Coll</th>
                    <th style="width: 10%; text-align: right; background-color: silver;">Nego</th>
                    <th style="width: 10%; text-align: right; background-color: silver;">Refund</th>
                    <th style="width: 15%; text-align: right; background-color: silver;">Note</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    <div>

    <div style="text-align: right; margin-top: 10px;">
        {buttons_html}
    </div>
    </div>
    """
    return html

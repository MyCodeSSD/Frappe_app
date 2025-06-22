# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import formatdate, flt
from frappe.utils.jinja import render_template
from frappe import _



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
		IFNULL(nego.bank_due_date, null) AS bank_due_date,
		IFNULL(nego.due_date_confirm, 0) AS due_date_confirm,
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
			cif.inv_no ASC;


	""",{"as_on": as_on}, as_dict=1)
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

    sales_amount = doc.document or 0

    inv = [{"Type": "Sales", "Date": doc.inv_date, "Amount": sales_amount}]
    
    nego = frappe.db.sql("""
        SELECT 'Negotiation' AS Type, nego_date AS Date, nego_amount AS Amount 
        FROM `tabDoc Nego` WHERE inv_no = %s
    """, (inv_name,), as_dict=1)
    
    ref = frappe.db.sql("""
        SELECT 'Refund' AS Type, refund_date AS Date, refund_amount AS Amount 
        FROM `tabDoc Refund` WHERE inv_no = %s
    """, (inv_name,), as_dict=1)
    
    rec = frappe.db.sql("""
        SELECT 'Received' AS Type, received_date AS Date, received AS Amount 
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

        if typ == "Sales":
            coll += amt

        elif typ == "Negotiation":
            coll -= amt
            nego_amt += amt

        elif typ == "Refund":
            nego_amt -= amt
            refund += amt

        elif typ == "Received":
            remain = amt

            # 1. Subtract from refund
            if refund >= remain:
                refund -= remain
                remain = 0
            else:
                remain -= refund
                refund = 0

            # 2. Subtract from nego
            if remain > 0:
                if nego_amt >= remain:
                    nego_amt -= remain
                    remain = 0
                else:
                    remain -= nego_amt
                    nego_amt = 0

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
            <td style="text-align: right;">{frappe.utils.fmt_money(sales_amount - received)}</td>
            <td style="text-align: right;background-color: silver;">{frappe.utils.fmt_money(coll)}</td>
            <td style="text-align: right;background-color: silver;">{frappe.utils.fmt_money(nego_amt)}</td>
            <td style="text-align: right;background-color: silver;">{frappe.utils.fmt_money(refund)}</td>
        </tr>
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

    html = f"""
    <div>
		{details_html}
        <table class="table table-bordered" style="font-size: 13px;">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Date</th>
                    <th style="text-align: right;">Amount</th>
                    <th style="text-align: right;">Received</th>
                    <th style="text-align: right;">Receivable</th>
                    <th style="text-align: right;background-color: silver;">Coll</th>
                    <th style="text-align: right;background-color: silver;">Nego</th>
                    <th style="text-align: right;background-color: silver;">Refund</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """
    return html

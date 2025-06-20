# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe


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
			(nego.total_nego - IFNULL(ref.total_ref, 0)) 
			+ LEAST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0),
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

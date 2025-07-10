# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import fmt_money
from datetime import date, timedelta

today_str = date.today().strftime("%Y-%m-%d")

def execute(filters=None):
	as_on = filters.as_on
	conditional_filter = ""

	if filters.based_on == "Receivable":
		conditional_filter = "AND (cif.document - IFNULL(rec.total_rec, 0)) > 0"
	elif filters.based_on == "Coll":
		conditional_filter = """AND IFNULL( ROUND(
			(cif.document - IFNULL(nego.total_nego, 0))
			+ LEAST(IFNULL(nego.total_nego, 0) - IFNULL(rec.total_rec, 0), 0), 2), 0) > 0"""
	elif filters.based_on == "Nego":
		conditional_filter = """AND IFNULL( ROUND(
			GREATEST((IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref, 0))
			+ LEAST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0), 0), 2), 0) > 0"""
	elif filters.based_on == "Refund":
		conditional_filter = "AND GREATEST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0) > 0"

	columns = [
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

	data = frappe.db.sql(f"""
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
			ROUND(cif.document, 0) AS document,
			cif.due_date,
			IFNULL(nego.total_nego, 0) AS total_nego,
			CASE
				WHEN GREATEST(IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref,0) - IFNULL(rec.total_rec, 0), 0) > 0
				THEN nego.bank_due_date
				ELSE NULL
			END AS bank_due_date,
			CASE WHEN nego.bank_due_date IS NOT NULL THEN DATEDIFF(nego.bank_due_date, CURDATE()) END AS days_to_due,
			nego.due_date_confirm,
			IFNULL(ref.total_ref, 0) AS total_ref,
			IFNULL(rec.total_rec, 0) AS total_rec,
			ROUND(cif.document - IFNULL(rec.total_rec, 0), 2) AS receivable,
			IFNULL(ROUND(
				(cif.document - IFNULL(nego.total_nego, 0))
				+ LEAST(IFNULL(nego.total_nego, 0) - IFNULL(rec.total_rec, 0), 0), 2), 0) AS coll,
			IFNULL(ROUND(
				GREATEST(IFNULL(ref.total_ref, 0)
				+ LEAST((IFNULL(nego.total_nego, 0)-IFNULL(ref.total_ref, 0)) - IFNULL(rec.total_rec, 0), 0), 0), 2), 0) AS ref,
			GREATEST(IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref,0) - IFNULL(rec.total_rec, 0), 0) AS nego
		FROM `tabCIF Sheet` cif
		LEFT JOIN (
			SELECT inv_no, SUM(nego_amount) AS total_nego, MIN(bank_due_date) AS bank_due_date, MIN(due_date_confirm) AS due_date_confirm
			FROM `tabDoc Nego` WHERE nego_date <= %(as_on)s GROUP BY inv_no
		) nego ON cif.name = nego.inv_no
		LEFT JOIN (
			SELECT inv_no, SUM(refund_amount) AS total_ref
			FROM `tabDoc Refund` WHERE refund_date <= %(as_on)s GROUP BY inv_no
		) ref ON cif.name = ref.inv_no
		LEFT JOIN (
			SELECT inv_no, SUM(received) AS total_rec
			FROM `tabDoc Received` WHERE received_date <= %(as_on)s GROUP BY inv_no
		) rec ON cif.name = rec.inv_no
		LEFT JOIN `tabCustomer` cus ON cif.customer = cus.name
		LEFT JOIN `tabNotify` noti ON cif.notify = noti.name
		LEFT JOIN `tabBank` bank ON cif.bank = bank.name
		WHERE cif.payment_term != 'TT'
			{conditional_filter}
			AND cif.inv_date <= %(as_on)s
		ORDER BY cif.inv_no ASC
	""", {"as_on": as_on}, as_dict=1)

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

	# One query to get all related docs
	entries = frappe.db.sql("""
		SELECT name, 'Nego' AS Type, nego_date AS Date, nego_amount AS Amount, note AS Note FROM `tabDoc Nego` WHERE inv_no=%s
		UNION ALL
		SELECT name, 'Refund', refund_date, refund_amount, note FROM `tabDoc Refund` WHERE inv_no=%s
		UNION ALL
		SELECT name, 'Received', received_date, received, note FROM `tabDoc Received` WHERE inv_no=%s
	""", (inv_name, inv_name, inv_name), as_dict=1)

	# Start with sales
	combined = [{"name": doc.name, "Type": "Sales", "Date": doc.inv_date, "Amount": doc_amount, "Note": ""}] + entries
	combined.sort(key=lambda x: x["Date"] or date.today())

	# Running totals
	coll, nego_amt, refund, received = 0, 0, 0, 0
	rows = []

	for entry in combined:
		typ, amt, note = entry["Type"], entry["Amount"] or 0, entry.get("Note") or ""

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
			for pool in [('nego_amt', nego_amt), ('refund', refund), ('coll', coll)]:
				if remain <= 0: break
				pool_name, pool_value = pool
				use = min(remain, pool_value)
				remain -= use
				if pool_name == 'nego_amt': nego_amt -= use
				elif pool_name == 'refund': refund -= use
				else: coll -= use
			received += amt

		rows.append(f"""
			<tr>
				<td>{typ}</td>
				<td>{entry['Date']}</td>
				<td style="text-align:right;">{fmt_money(amt)}</td>
				<td style="text-align:right;">{fmt_money(received)}</td>
				<td style="text-align:right;">{fmt_money(doc_amount - received)}</td>
				<td style="text-align:right;background-color:silver;">{fmt_money(coll)}</td>
				<td style="text-align:right;background-color:silver;">{fmt_money(nego_amt)}</td>
				<td style="text-align:right;background-color:silver;">{fmt_money(refund)}</td>
				<td style="text-align:right;">{note}</td>
			</tr>
		""")

	# Build buttons
 
	due_date_str = (date.today() + timedelta(days=doc.term_days)).strftime("%Y-%m-%d")
	buttons_html = ""
	if coll > 0:
		buttons_html += f"""
		<a href="#" onclick="frappe.new_doc('Doc Nego', {{ inv_no: '{inv_name}', nego_date:'{today_str}', term_days:'{doc.term_days}', nego_amount: {coll}, bank_due_date:'{due_date_str}' }}); return false;" class="btn btn-primary btn-sm" style="margin-left:8px;background-color:blue;">Nego</a>"""
	if nego_amt > 0:
		buttons_html += f"""
		<a href="#" onclick="frappe.new_doc('Doc Refund', {{ inv_no: '{inv_name}', refund_date:'{today_str}', refund_amount:'{nego_amt}' }}); return false;" class="btn btn-danger btn-sm" style="margin-left:8px;background-color:red;">Refund</a>"""
	if (doc_amount - received) > 0:
		buttons_html += f"""
		<a href="#" onclick="frappe.new_doc('Doc Received', {{ inv_no: '{inv_name}', received_date:'{today_str}', received:'{doc_amount - received}' }}); return false;" class="btn btn-success btn-sm" style="margin-left:8px;background-color:green;">Received</a>"""



	# Build final HTML
	html = f"""
	<div style="bmargin-bottom: 12px; background-color: #f9f9f9; padding: 8px 12px;  border-radius: 6px; 
	box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <table style="width:100%; font-size:13px; margin-bottom:0;">
			<tr><td><b>Invoice Date:</b> {doc.inv_date}</td><td><b>Customer:</b> {customer}</td><td><b>Notify:</b> {notify}</td></tr>
			<tr><td><b>Bank:</b> {bank}</td><td><b>Payment Term:</b> {doc.payment_term}{' - '+str(doc.term_days) if doc.payment_term in ['LC','DA'] else ''}</td><td><b>Category:</b> {category}</td></tr>
		</table>
	</div>
	<table class="table table-bordered" style="font-size:14px; border:1px solid #ddd;">
		<thead style="background-color: #f1f1f1;">
			<tr>
				<th style="width:10%; text-align:center;">Type</th>
				<th style="width:15%; text-align:center;">Date</th>
				<th style="width:10%;text-align:center;">Amount</th>
				<th style="width:10%;text-align:center;">Received</th>
				<th style="width:10%;text-align:center;">Receivable</th>
				<th style="width:10%;text-align:center;">Coll</th>
				<th style="width:10%;text-align:center;">Nego</th>
				<th style="width:10%;text-align:center;">Refund</th>
				<th style="width:15%;text-align:center;">Note</th>
			</tr>
		</thead>
		<tbody style="border-top:1px solid #ddd;">

			{''.join(rows)}
		</tbody>
	</table>
	<div style="text-align:right; margin-top:12px;padding:8px; border-top:1px solid #eee;">
	{buttons_html}
	</div>
	"""
	return html

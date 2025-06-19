import frappe
from frappe.utils import flt

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Acc Com", "fieldname": "a_com", "fieldtype": "Data", "width": 110},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 120},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 150},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 110},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 110},
        {"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 110},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 80},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
    ]

    data = frappe.db.sql(f"""
        SELECT
		cif.inv_no,
		cif.inv_date,
		com.company_code AS a_com,
		cat.product_category,
		cus.code as customer,
		noti.code as notify,
		cif.sales,
		cif.document,
		cif.cc,
        bank.bank,
		IF(cif.payment_term IN ('LC', 'DA'),
		CONCAT(cif.payment_term, '- ', cif.term_days),cif.payment_term) AS p_term,
		cif.due_date
		FROM `tabCIF Sheet` cif
		LEFT JOIN `tabCompany` com ON cif.accounting_company= com.name
		LEFT JOIN `tabCustomer` cus ON cif.customer= cus.name
		LEFT JOIN `tabProduct Category` cat ON cif.category= cat.name
		LEFT JOIN `tabNotify` noti ON cif.notify= noti.name
		LEFT JOIN `tabBank` bank ON cif.bank= bank.name
		ORDER BY cif.inv_date DESC
    """, as_dict=1)
    

    return columns, data

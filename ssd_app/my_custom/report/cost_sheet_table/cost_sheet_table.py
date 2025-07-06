import frappe
from frappe.utils import formatdate, flt
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template
from frappe import _

def get_cif_data(filters):
    user_limit = filters.get('user_limit') or 100

    data= frappe.db.sql(f"""
    SELECT
    cost.custom_title AS inv_no,
    cost.name,
    cost.inv_date,
    com.company_code AS a_com,
    cat.product_category,
    cus.code AS customer,
    noti.code AS notify,
    cost.insurance,
    cost.purchase,
    cost.sales,
    cost.cost,
    cost.profit,
    IFNULL(exp.freight, 0) AS freight,
    IFNULL(exp.local_exp, 0) AS local_exp,
    l_port.port AS load_port,
    d_port.port AS destination_port,
    l_port.country AS from_country,
    city.country AS to_country,                
    COALESCE(NULLIF(sup.supplier, ''), '**Multi Supplier**') AS supplier
    FROM `tabCost Sheet` cost
    LEFT JOIN `tabCompany` com ON cost.accounting_company = com.name
    LEFT JOIN `tabCustomer` cus ON cost.customer = cus.name
    LEFT JOIN `tabProduct Category` cat ON cost.category = cat.name
    LEFT JOIN `tabNotify` noti ON cost.notify = noti.name
    LEFT JOIN `tabPort` l_port ON cost.load_port= l_port.name
    LEFT JOIN `tabPort` d_port ON cost.destination_port= d_port.name
    LEFT JOIN `tabCity` city ON noti.city=city.name
    LEFT JOIN `tabSupplier` sup ON cost.supplier = sup.name
    LEFT JOIN (SELECT 
  parent,
  SUM(CASE WHEN expenses = 'Freight' THEN amount ELSE 0 END) AS freight,
  SUM(CASE WHEN expenses = 'Local Exp' THEN amount ELSE 0 END) AS local_exp,
  SUM(CASE WHEN expenses = 'Inland Charges' THEN amount ELSE 0 END) AS inland_charges,
  SUM(CASE WHEN expenses = 'Switch B/L Charges' THEN amount ELSE 0 END) AS switch_bl_charges,
  SUM(CASE WHEN expenses = 'Insurance' THEN amount ELSE 0 END) AS insurance,
  SUM(CASE WHEN expenses = 'Others' THEN amount ELSE 0 END) AS others
FROM `tabExpenses Cost`
GROUP BY parent) AS exp ON exp.parent= cost.name
    ORDER BY cost.creation DESC 
    LIMIT {user_limit};
    """, as_dict=1)
    return data


def execute(filters=None):
    filters = filters or {}

    columns = [
        # {"label": "Inv ID", "fieldname": "name", "fieldtype": "Data", "width": 80},
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data"},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date"},
        {"label": "Com", "fieldname": "a_com", "fieldtype": "Data"},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 120},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 150},
        {"label": "Purchase", "fieldname": "purchase", "fieldtype": "Float"},
        {"label": "Freight", "fieldname": "freight", "fieldtype": "Float"},
        {"label": "Local Exp", "fieldname": "local_exp", "fieldtype": "Float"},
        {"label": "Cost", "fieldname": "cost", "fieldtype": "Float"},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float"},
        {"label": "Profit", "fieldname": "profit", "fieldtype": "Float"},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180}
    ]
    data = get_cif_data(filters)
    return columns, data




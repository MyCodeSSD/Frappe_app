# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

# import frappe
import frappe

def get_cc_vs_rec(as_on):
    """
    Get total_cc and total_rec grouped by customer as on a given date,
    including customer_name and total amount (total_cc + total_rec).
    
    :param as_on: str, e.g. "2025-07-07"
    :return: list of dicts
    """
    return frappe.db.sql("""
        SELECT 
            combined.customer,
            cust.customer AS customer_name,
            combined.total_cc,
            combined.total_rec,
            (combined.total_cc - combined.total_rec) AS amount
        FROM (
            SELECT 
                COALESCE(cif_cc.customer, cc_rec.customer) AS customer,
                COALESCE(cif_cc.total_cc, 0) AS total_cc,
                COALESCE(cc_rec.total_rec, 0) AS total_rec
            FROM
                (SELECT customer, SUM(cc) AS total_cc
                 FROM `tabCIF Sheet`
                 WHERE cc != 0 AND inv_date <= %(as_on)s
                 GROUP BY customer) AS cif_cc
            LEFT JOIN
                (SELECT customer, SUM(amount_usd) AS total_rec
                 FROM `tabCC Received`
                 WHERE date <= %(as_on)s
                 GROUP BY customer) AS cc_rec
            ON cif_cc.customer = cc_rec.customer

            UNION

            SELECT 
                COALESCE(cif_cc.customer, cc_rec.customer) AS customer,
                COALESCE(cif_cc.total_cc, 0) AS total_cc,
                COALESCE(cc_rec.total_rec, 0) AS total_rec
            FROM
                (SELECT customer, SUM(cc) AS total_cc
                 FROM `tabCIF Sheet`
                 WHERE cc != 0 AND inv_date <= %(as_on)s
                 GROUP BY customer) AS cif_cc
            RIGHT JOIN
                (SELECT customer, SUM(amount_usd) AS total_rec
                 FROM `tabCC Received`
                 WHERE date <= %(as_on)s
                 GROUP BY customer) AS cc_rec
            ON cif_cc.customer = cc_rec.customer
        ) AS combined
        LEFT JOIN `tabCustomer` AS cust ON combined.customer = cust.name
        ORDER BY combined.customer
    """, {"as_on": as_on}, as_dict=True)





def execute(filters=None):
      as_on = filters.get("as_on") if filters and filters.get("as_on") else today()
      data=get_cc_vs_rec(as_on)
      columns= [
        {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
        {"label": "Total Sales", "fieldname": "total_cc", "fieldtype": "Float", "width": 130},
        {"label": "Total Received", "fieldname": "total_rec", "fieldtype": "Float", "width": 130},
        {"label": "CC Balance", "fieldname": "amount", "fieldtype": "Float", "width": 130},
	  ]
      return columns, data

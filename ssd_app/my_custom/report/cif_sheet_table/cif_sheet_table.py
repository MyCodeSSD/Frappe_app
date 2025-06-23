import frappe
from frappe.utils import formatdate, flt
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template
from frappe import _

def get_cif_data(inv_name=None):
    if(inv_name):
        conditional_format= f"""WHERE cif.name= '{inv_name}'"""
    else:
        conditional_format=""

    data= frappe.db.sql(f"""
        SELECT
    cif.inv_no,
    cif.name,
    cif.inv_date,
    com.company_code AS a_com,
    cat.product_category,
    cus.code AS customer,
    noti.code AS notify,
    cif.sales,
    cif.document,
    cif.cc,
    CASE
    WHEN cost.inv_no IS NULL THEN ''
    ELSE COALESCE(sup.supplier, '--Multi--')
    END AS supplier,
    bank.bank,
    IF(cif.payment_term IN ('LC', 'DA'),
       CONCAT(cif.payment_term, '- ', cif.term_days),
       cif.payment_term) AS p_term,
    cif.due_date,

    CASE
        WHEN cif.payment_term = 'TT' THEN ''
        WHEN COALESCE(t_rec.total_rec, 0) = 0 THEN 'Unpaid'
        WHEN COALESCE(t_rec.total_rec, 0) >= cif.document THEN 'Paid'
        ELSE 'Part'
    END AS status

    FROM `tabCIF Sheet` cif

    LEFT JOIN `tabCompany` com ON cif.accounting_company = com.name
    LEFT JOIN `tabCustomer` cus ON cif.customer = cus.name
    LEFT JOIN `tabProduct Category` cat ON cif.category = cat.name
    LEFT JOIN `tabNotify` noti ON cif.notify = noti.name
    LEFT JOIN `tabBank` bank ON cif.bank = bank.name

    LEFT JOIN (
        SELECT inv_no, MIN(supplier) AS supplier
        FROM `tabCost Sheet`
        GROUP BY inv_no
    ) cost ON cif.name = cost.inv_no
    LEFT JOIN `tabSupplier` sup ON cost.supplier = sup.name

    LEFT JOIN (
        SELECT inv_no, SUM(received) AS total_rec
        FROM `tabDoc Received`
        GROUP BY inv_no
    ) t_rec ON cif.name = t_rec.inv_no
    {conditional_format}
    ORDER BY cif.inv_date DESC;
    """, as_dict=1)
    return data


def get_cif_product_data(inv_name=None):
    conditional_format = ""
    values = ()

    if inv_name:
        conditional_format = "WHERE p.parent = %s"
        values = (inv_name,)

    data = frappe.db.sql("""
        SELECT 
            p.parent, 
            pg.product_group, 
            pro.product, 
            p.sc_no, 
            p.qty, 
            u.unit, 
            p.rate, 
            p.currency, 
            p.ex_rate, 
            p.charges, 
            p.charges_amount, 
            p.gross, 
            p.gross_usd 
        FROM `tabProduct CIF` p 
        LEFT JOIN `tabUnit` u ON p.unit = u.name 
        LEFT JOIN `tabProduct` pro ON p.product = pro.name 
        LEFT JOIN `tabProduct Group` pg ON pro.product_group = pg.name 
        {condition}
    """.format(condition=conditional_format), values, as_dict=1)

    return data



def execute(filters=None):
    filters = filters or {}

    columns = [
        # {"label": "Inv ID", "fieldname": "name", "fieldtype": "Data", "width": 80},
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Acc Com", "fieldname": "a_com", "fieldtype": "Data", "width": 90},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 120},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 150},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 100},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 100},
        {"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 100},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 70},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 80},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180},
    ]

    data = get_cif_data()
    return columns, data


@frappe.whitelist()
def get_cif_details(inv_name):
    if not inv_name:
        return "Invalid Invoice Number"

    doc = get_cif_data(inv_name)[0]
    products= get_cif_product_data(inv_name)
    exp = frappe.db.sql("""
        SELECT 
            parent, 
            expenses,
            SUM(amount_usd) AS total_amount 
        FROM `tabExpenses CIF`
        WHERE parent = %s
        GROUP BY expenses, parent
    """, (inv_name,), as_dict=1)
        
    # Build product table HTML
    product_table_rows = ""
    for p in products:
        product_table_rows += f"""
            <tr>
                <td>{p.product_group}</td>
                <td>{p.product}</td>
                <td>{p.sc_no}</td>
                <td>{p.unit}</td>
                <td style="text-align: right;">{p.qty}</td>
                <td style="text-align: right;">{p.rate}</td>
                <td style="text-align: right;">{p.charges_amount}</td>
                <td style="text-align: right;">{p.gross}</td>
                <td>{p.currency}</td>
                <td style="text-align: right;">{p.ex_rate}</td>
                <td style="text-align: right;">{p.gross_usd}</td>
            </tr>
        """
 
    product_table_html = f"""
    <h4>Product Details</h4>
    <table style="width: 100%; border-collapse: collapse;" border="1" cellpadding="5">
        <thead style="background-color: #f0f0f0;">
            <tr>
                <th>Product Group</th>
                <th>Product Group</th>
                <th>SC No</th>
                <th>Unit</th>
                <th>Qty</th>
                <th style="text-align: right;">Rate</th>
                <th style="text-align: right;">Chrgs</th>
                <th>Gross</th>
                <th>Curr</th>
                <th style="text-align: right;">Ex. Rate</th>
                <th style="text-align: right;">Gross (USD)</th>
            
            </tr>
        </thead>
        <tbody>
            {product_table_rows}
        </tbody>
    </table>
    """
    if (exp):
        exp_row_html=""
        for ex in exp:
          exp_row_html +=f"""<tr>
                    <td> {ex.expenses}</td>
                    <td>{ex.total_amount}</td>
                </tr>"""

    exp_html=""
    if (exp):
        exp_html +=f"""
        <table style="width: 100%; border-collapse: collapse;">
           {exp_row_html}
        </table>"""

    # Final HTML output
    html = f"""
    <div style="font-family: Arial; font-size: 12px; padding: 10px; ">
        <h3 style="text-align: center; margin-bottom: 10px;">CIF Sheet</h3>

        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td><b>Inv No.:</b> {doc.inv_no}</td>
                <td><b>Inv Date:</b> {formatdate(doc.inv_date)}</td>
                <td><b>Supplier:</b> {doc.supplier}</td>
            </tr>
            <tr>
                <td><b>Category:</b> {doc.product_category}</td>
                <td><b>Notify:</b> {doc.notify}</td>
                <td><b>Notify:</b> {doc.customer}</td>
                
            </tr>
        </table>
        <br><hr><br>

        {product_table_html}

        <br><hr><br>
        {exp_html}

        <table style="width: 100%;">
            <tr>
                
            </tr>
            <tr>
                <td><b>Payment Term:</b> {doc.payment_term}{' - ' + str(doc.term_days) + ' Days' if doc.payment_term in ['LC', 'DA'] else ''}</td>
                <td><b>Due Date:</b> {formatdate(doc.due_date)}</td>
            </tr>
         
        </table>

        <br><br>
        <p style="font-size: 11px; color: #888;">Generated on: {frappe.utils.nowdate()}</p>
    </div>
    """
    return html




@frappe.whitelist()
def download_cif_pdf(inv_name):
    if not inv_name:
        frappe.throw(_("Missing Invoice Number"))

    doc = frappe.get_doc("CIF Sheet", inv_name)
    
    customer = frappe.get_value("Customer", doc.customer, "code")
    notify = frappe.get_value("Notify", doc.notify, "code")
    bank = frappe.get_value("Bank", doc.bank, "bank")
    category = frappe.get_value("Product Category", doc.category, "product_category")
    company = frappe.get_value("Company", doc.accounting_company, "company_code")

    total_received = frappe.db.get_value("Doc Received", {"inv_no": inv_name}, "SUM(received)") or 0

    html = f"""
    <div style="width: 21cm; min-height: 29.7cm; padding: 1.5cm; font-size: 13px;">
        <h2>CIF Sheet - Invoice {doc.inv_no}</h2>
        <p><b>Date:</b> {doc.inv_date}</p>
        <p><b>Customer:</b> {customer}</p>
        <p><b>Notify:</b> {notify}</p>
        <p><b>Category:</b> {category}</p>
        <p><b>Company:</b> {company}</p>
        <p><b>Bank:</b> {bank}</p>
        <p><b>Sales:</b> {doc.sales}</p>
        <p><b>Document:</b> {doc.document}</p>
        <p><b>CC:</b> {doc.cc}</p>
        <p><b>Payment Term:</b> {doc.payment_term}</p>
        <p><b>Due Date:</b> {doc.due_date}</p>
        <p><b>Total Received:</b> {total_received}</p>
    </div>
    """

    frappe.local.response.filename = f"CIF_{inv_name}.pdf"
    frappe.local.response.filecontent = get_pdf(html)
    frappe.local.response.type = "pdf"



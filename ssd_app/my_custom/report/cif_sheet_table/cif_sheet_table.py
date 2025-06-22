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


from frappe.utils.formatters import format_value


def fmt_money(amount, currency=None):
    return format_value(amount, {"fieldtype": "Currency", "options": "USD"})
currency= "usd"



@frappe.whitelist()
def get_cif_details(inv_name):
    if not inv_name:
        return "Invalid Invoice Number"

    doc = get_cif_data(inv_name)[0]
    
    # Get product child table entries
    products = frappe.get_all(
        "Product CIF",
        filters={"parent": inv_name},
        fields=["product", "qty", 'unit', "rate", "Currency", "ex_rate", "charges", "charges_amount", "round_off"]
    )

    customer = doc.customer#frappe.get_value("Customer", doc.customer, "code")
    notify = doc.notify# frappe.get_value("Notify", doc.notify, "code")
    bank = doc.bank# frappe.get_value("Bank", doc.bank, "bank")
    category = doc.category# frappe.get_value("Product Category", doc.category, "product_category")
    company = doc.company#frappe.get_value("Company", doc.accounting_company, "company_code")

    total_received = frappe.db.get_value("Doc Received", {"inv_no": inv_name}, "SUM(received)") or 0
    total_received = flt(total_received)

    if doc.payment_term == "TT":
        status = ""
    elif total_received == 0:
        status = "Unpaid"
    elif total_received >= flt(doc.document):
        status = "Paid"
    else:
        status = "Part"

    # Build product table HTML
    product_table_rows = ""
    for p in products:
        product_table_rows += f"""
            <tr>
                <td>{p.product}</td>
                <td style="text-align: right;">{p.qty}</td>
                <td style="text-align: right;">{p.rate}</td>
                <td>{p.Currency}</td>
                <td style="text-align: right;">{p.ex_rate}</td>
                <td>{p.charges}</td>
                <td style="text-align: right;">{p.charges_amount}</td>
                <td style="text-align: right;">{p.round_off}</td>
                <td style="text-align: right;">{p.unit}</td>
            </tr>
        """

    product_table_html = f"""
    <h4>Product Details</h4>
    <table style="width: 100%; border-collapse: collapse;" border="1" cellpadding="5">
        <thead style="background-color: #f0f0f0;">
            <tr>
                <th>Product</th>
                <th style="text-align: right;">Qty</th>
                <th style="text-align: right;">Rate</th>
                <th>Currency</th>
                <th style="text-align: right;">Ex. Rate</th>
                <th>Charges</th>
                <th style="text-align: right;">Charges Amt</th>
                <th style="text-align: right;">Round Off</th>
                <th style="text-align: right;">Unit</th>
            </tr>
        </thead>
        <tbody>
            {product_table_rows}
        </tbody>
    </table>
    """

    currency = products[0]["Currency"] if products else "USD"

    # Final HTML output
    html = f"""
    <div style="font-family: Arial; font-size: 12px; padding: 10px; ">
        <h3 style="text-align: center; margin-bottom: 10px;">CIF Sheet</h3>

        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td><b>Invoice No.:</b> {doc.inv_no}</td>
                <td><b>Invoice Date:</b> {formatdate(doc.inv_date)}</td>
                <td><b>Supplier:</b> {doc.supplier}</td>
            </tr>
            <tr>
                <td><b>Category:</b> {category}</td>
                <td><b>Company:</b> {company}</td>
                <td><b>Currency:</b> {currency}</td>
            </tr>
            <tr>
                <td><b>Notify:</b> {notify}</td>
                <td><b>Bank:</b> {bank}</td>
                <td><b>Sales:</b> {doc.sales}</td>
            </tr>
        </table>
        <br><hr><br>

        {product_table_html}

        <br><hr><br>
    

        <table style="width: 100%;">
            <tr>
                <td><b>Document Amount:</b> {fmt_money(doc.document, currency=currency)}</td>
                <td><b>CC:</b> {fmt_money(doc.cc, currency=currency)}</td>
            </tr>
            <tr>
                <td><b>Payment Term:</b> {doc.payment_term}{' - ' + str(doc.term_days) + ' Days' if doc.payment_term in ['LC', 'DA'] else ''}</td>
                <td><b>Due Date:</b> {formatdate(doc.due_date)}</td>
            </tr>
            <tr>
                <td><b>Total Received:</b> {fmt_money(total_received, currency=currency)}</td>
                <td><b>Status:</b> <strong>{status}</strong></td>
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



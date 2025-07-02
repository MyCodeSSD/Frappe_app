import frappe
from datetime import datetime
from frappe.utils import fmt_money
from datetime import date, timedelta
today_str = date.today().strftime("%Y-%m-%d")


filter_data_dict = {
        "Customer": {"dc": "tabCustomer", "field": "code", "l_field": "customer"},
        "Notify": {"dc": "tabNotify", "field": "code", "l_field": "notify"},
        "Category": {"dc": "tabProduct Category", "field": "product_category", "l_field": "category"}
    }

def execute(filters=None):
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    group_by = filters.get('group_by') or "Customer"

    if not from_date or not to_date:
        frappe.throw("Please set both From Date and To Date")

    # Map group_by to database fields


    # handle invalid group_by
    if group_by not in filter_data_dict:
        frappe.throw(f"Invalid Group By value: {group_by}")

    filter_field = filter_data_dict[group_by]["field"]
    filter_dc = filter_data_dict[group_by]["dc"]
    filter_l_field = filter_data_dict[group_by]["l_field"]

    # Build month list
    months = []
    current = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")
    while current <= end:
        month_label = current.strftime('%b-%Y')
        months.append({
            'label': month_label,
            'year': current.year,
            'month': current.month
        })
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    # Build columns
    columns = [
        {"label": group_by, "fieldname": "group_value", "fieldtype": "Data", "width": 150}
    ]
    for m in months:
        columns.append({
            "label": m['label'],
            "fieldname": m['label'].lower().replace('-', '_'),
            "fieldtype": "Float",
            "width": 110
        })
    # Add total column
    columns.append({
        "label": "Total",
        "fieldname": "total",
        "fieldtype": "Float",
        "width": 120
    })

    # Query data
    data = frappe.db.sql(f"""
        SELECT 
            jdc.{filter_field} AS group_value,
            YEAR(cif.inv_date) AS year,
            MONTH(cif.inv_date) AS month,
            SUM(cif.sales) AS amount
        FROM `tabCIF Sheet` cif
        LEFT JOIN `{filter_dc}` jdc ON cif.{filter_l_field} = jdc.name
        WHERE cif.inv_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY jdc.{filter_field}, YEAR(cif.inv_date), MONTH(cif.inv_date)
        ORDER BY jdc.{filter_field} ASC
    """, {
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=1)

    # Pivot data into result_map
    result_map = {}
    for row in data:
        key = row.group_value or "(Not Set)"
        month_label = datetime(row.year, row.month, 1).strftime('%b-%Y')
        if key not in result_map:
            result_map[key] = {}
        result_map[key][month_label] = row.amount

    # Build final result rows with total
    result = []
    for key, month_values in result_map.items():
        row = {"group_value": key}
        total = 0
        for m in months:
            label = m['label']
            value = month_values.get(label, 0)
            row[label.lower().replace('-', '_')] = value
            total += value
        row["total"] = total
        result.append(row)

    # Sort by group_value
    # result.sort(key=lambda x: x["group_value"])

    return columns, result






@frappe.whitelist()
def show_inv_wise(group_by, head, month):
    mon = month.split("_")[0]
    yr= month.split("_")[1]
    month_map= {"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12}
    filter_field = filter_data_dict[group_by]["field"]
    filter_dc = filter_data_dict[group_by]["dc"]
    filter_l_field = filter_data_dict[group_by]["l_field"]


    # Build SQL query
    data = frappe.db.sql(f"""
        SELECT 
            cif.name, 
            cif.inv_no, 
            cif.inv_date, 
            pg.product_category AS Category, 
            cus.code AS Customer, 
            noti.code AS Notify, 
            cif.sales, 
            cif.document, 
            cif.cc 
        FROM `tabCIF Sheet` cif 
        JOIN `tabProduct Category` pg ON pg.name = cif.category
        JOIN `tabCustomer` cus ON cus.name = cif.customer
        JOIN `tabNotify` noti ON noti.name = cif.notify
        WHERE MONTH(cif.inv_date) = %(month)s
        AND YEAR(cif.inv_date) = %(year)s
        AND pg.{filter_field} = %(head)s
        ORDER BY cif.inv_date DESC
        LIMIT 50
    """, {
        "month": month_map[mon.lower()],
        "year": yr,
        "head": head
    }, as_dict=True)


    if not data:
        return "<p>No data found.</p>"

    # Build HTML table
    html = """
    <style>
        .cif-table-container {
            max-height: 75vh;
            overflow: auto;
        }
        table.cif-table {
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
            min-width: 1000px;
        }
        table.cif-table th, table.cif-table td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: left;
            white-space: nowrap;
        }
        table.cif-table th {
            background-color: #f5f5f5;
            position: sticky;
            top: 0;
            z-index: 1;
        }
    </style>
    <table class="cif-table">
        <thead>
            <tr>
                <th>Inv No</th>
                <th>Inv Date</th>
                <th>Category</th>
                <th>Customer</th>
                <th>Notify</th>
                <th>Sales</th>
                <th>Document</th>
                <th>CC</th>
            </tr>
        </thead>
        <tbody>
    """

    for row in data:
        html += f"""
            <tr>

                <td><a style="color:blue;" href="#" onclick="showCIFDetails('{row.name}', '{row.inv_no}');">{row.inv_no}</a></td>
                <td>{row.inv_date }</td>
                <td>{row.Category or ""}</td>
                <td>{row.Customer or ""}</td>
                <td>{row.Notify or ""}</td>
                <td style="text-align:right;">{frappe.format(row.sales, {"fieldtype": "Currency"})}</td>
                <td>{row.document or ""}</td>
                <td>{row.cc or ""}</td>
            </tr>
        """

    html += "</tbody></table>"

    return html
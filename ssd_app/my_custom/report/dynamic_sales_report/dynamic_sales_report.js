// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Dynamic Sales Report"] = {
    onload: function(report) {
        // Wait until datatable is ready
        report.datatable.then(dt => {
            dt.freezeColumn = 1;  // freeze first column
            dt.refresh();
        });
    },
    formatter: function (value, row, column, data, default_formatter) {
        // Use default_formatter first for non-numeric columns
        value = default_formatter(value, row, column, data);

        if (data) {
            const columns = frappe.query_report.columns;
            const col_index = columns.findIndex(col => col.fieldname === column.fieldname);

            // Skip first and last columns
            if (col_index > 0 && col_index < columns.length - 1) {
                const field_value = data[column.fieldname];

                if (field_value && field_value != 0) {
                    const first_column_fieldname = columns[0].label; // corrected to fieldname

                    // Apply 0 decimal comma formatting if value is a number
                    if (typeof field_value === "number") {
                        value = field_value.toLocaleString(undefined, { 
                            minimumFractionDigits: 0, 
                            maximumFractionDigits: 0 
                        });
                    }

                    return `<a href="#" onclick="showInvWise('${first_column_fieldname}', '${data.group_value}', '${column.fieldname}'); return false;">${value}</a>`;
                }
            }
        }

        return value;
    },

    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": "2025-01-01",
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "group_by",
            "label": __("Group By"),
            "fieldtype": "Select",
            "options": "\nCategory\nCustomer\nNotify\nFrom Country\nTo Country\nCompany",
            "default": "Category",
            "reqd": 1
        }
    ]
};


// 🧾 Modal Dialog to Show Document Flow
function showInvWise(group_by, head, month_year) {
    inv_name="cif-0027"
    inv_no="cif-0027"
    frappe.call({
        method: "ssd_app.my_custom.report.dynamic_sales_report.dynamic_sales_report.show_inv_wise",
        args: { inv_name, group_by, head, month_year},
        callback: function (r) {
            if (r.message) {
                const d = new frappe.ui.Dialog({
                    title: `Invoice Details of: ${group_by}: ${head}, ${month_year}`,
                    size: 'extra-large',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'details_html',
                            options: `
                                <div id="cif-details-a4" style="box-shadow: 0 0 8px rgba(0,0,0,0.2);">
                                    ${r.message}
                                </div>`
                        }
                    ]
                });

                d.show();

            }
        }
    });
}

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
        value = default_formatter(value, row, column, data);
        if (data) {
            return `<a style="color:blue;" href="#" onclick="showInvList('${column.fieldname}', '${data.group_value}'); return false;">${value}</a>`;
        }
        return value;
    },


    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -6),
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
            "options": "\nCategory\nCustomer\nNotify\nTo Country",
            "default": "Category",
            "reqd": 1
        }
    ]
};


// 🧾 Modal Dialog to Show Document Flow
function showInvList(row, column) {
    inv_name="cif-0027"
    inv_no="cif-0027"
    frappe.call({
        method: "ssd_app.my_custom.report.document_receivable.document_receivable.get_doc_flow",
        args: { inv_name },
        callback: function (r) {
            if (r.message) {
                const d = new frappe.ui.Dialog({
                    title: `Document Flow for: ${inv_no}`,
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

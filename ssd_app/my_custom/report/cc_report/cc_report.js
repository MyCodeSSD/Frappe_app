// Copyright (c) 2025, SSDolui
// For license information, please see license.txt

frappe.query_reports["CC Report"] = {
    onload: function (report) {
        report.page.add_inner_button("Balance Break", function () {
            // Fetch current filter values
            let filters = report.get_values();
            if (filters.customer && filters.as_on) {
                 ccBalanceBreakup(filters.customer, filters.as_on);
            } else {
                frappe.msgprint(__("Please select a Customer & Date first."));
            }
        });
        report.page.add_inner_button("Go to CC Balance", function () {
            frappe.set_route('query-report', 'CC Balance');
        });
    },
    "filters": [
        {
            "fieldname": "as_on",
            "label": __("As On"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 0
        }
    ]
};


function ccBalanceBreakup(cus_id, as_on) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cc_received.cc_received.cc_balance_breakup",
        args: { cus_id, as_on },
        callback: function (r) {
            if (!r.message) return;
            const htmlContent = `
                <div id="cif-details-a4" style="
                    width: 20cm;
                    max-width: 100%;
                    min-height: 5cm;
                    padding: 0.3cm;
                    background: white;
                    font-size: 13px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.2);"
                >${r.message}</div>
            `;

            const dialog = new frappe.ui.Dialog({
                title: `CC Balabce Breakup of: ${cus_id}`,
                size: 'small',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'details_html',
                        options: htmlContent
                    }
                ]
            });

            dialog.show();
        }
    });
} 
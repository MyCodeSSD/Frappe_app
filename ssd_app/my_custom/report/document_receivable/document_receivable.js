frappe.query_reports["Document Receivable"] = {
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "bank_due_date" && data?.bank_due_date) {
            let style = "font-weight: bold;";

            if (!data.due_date_confirm) {
                style += " text-decoration-line: underline;";
                style += " text-decoration-style: double;";
                style += " text-decoration-color: red;";
                if (data.days_to_due < 5) {
                    style += " color: red;";
                }
            } else {
                if (data.days_to_due < 5) {
                    style += " color: red;";
                }
            }

            return `<span style="${style}">${value}</span>`;
        }

        if (column.fieldname === "inv_no" && data?.name) {
            return `<a href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }

        return value;
    },

    onload: function (report) {
        const style = document.createElement('style');
        style.textContent = `
            .dt-scrollable .dt-cell__content:first-child,
            .dt-scrollable .dt-header__cell:first-child {
                min-width: 40px !important;
            }
        `;
        document.head.appendChild(style);
    },

    filters: [
        {
            fieldname: "based_on",
            label: "Based On",
            fieldtype: "Select",
            options: "Receivable\nColl\nNego\nRefund\nAll",
            default: "Receivable",
            reqd: 1
        },
        {
            fieldname: "as_on",
            label: "As On",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        }
    ]
};

// 🧾 Modal Dialog to Show Document Flow
function showDocFlow(inv_name, inv_no) {
    frappe.call({
        method: "ssd_app.my_custom.report.document_receivable.document_receivable.get_doc_flow",
        args: { inv_name },
        callback: function (r) {
            if (r.message) {
                new frappe.ui.Dialog({
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
                }).show();
            }
        }
    });
}

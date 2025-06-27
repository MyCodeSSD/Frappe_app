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

        if (column.fieldname === "document" && data?.name) {
            return `<a  href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        }
        if (column.fieldname === "inv_no" && data?.name) {
            return `<a  href="#" onclick="showCIFDetails('${data.name}', '${data.inv_no}'); return false;">${data.inv_no})}</a>`;
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


function showCIFDetails(inv_name, inv_no) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_cif_sheet_pdf",
        args: { inv_name },
        callback: function (r) {
            if (!r.message) return;
            const htmlContent = `
                <div id="cif-details-a4" style="
                    width: 20cm;
                    max-width: 100%;
                    min-height: 28.7cm;
                    padding: 0.3cm;
                    background: white;
                    font-size: 13px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.2);"
                >${r.message}</div>
            `;

            const dialog = new frappe.ui.Dialog({
                title: `CIF Sheet: ${inv_no}`,
                size: 'large',
                primary_action_label: 'PDF',
                primary_action() {
                    window.open(
                        `/api/method/ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_cif_sheet_pdf?inv_name=${inv_name}&pdf=1`,
                        '_blank'
                    );
                },
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
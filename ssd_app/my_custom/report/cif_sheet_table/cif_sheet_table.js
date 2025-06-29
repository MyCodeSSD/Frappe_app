// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt
// Load html2pdf only once
if (typeof html2pdf === "undefined") {
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
    script.defer = true;
    document.head.appendChild(script);
}



frappe.query_reports["CIF Sheet Table"] = {
    onload: function (report) {
        report.page.add_inner_button("Open CIF Sheet List", function () {
            frappe.set_route("List", "CIF Sheet");
        });
    },
        formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // 🎯 Highlight status column
        if (column.fieldname === "status") {
            let style = "font-weight: bold;";
            if (value === "Paid") {
                style+="color: green;";
                // return `<span style="color: green; font-weight: bold;">${value}</span>`;
            } else if (value === "Part") {
                style+="color: purple;";
                // return `<span style="color: purple; font-weight: bold;">${value}</span>`;
            } else if (value === "Unpaid") {
                style+="color: red;";
                // return `<span style="color: red; font-weight: bold;">${value}</span>`;
            }
            // return `<span style="${style}"; font-weight: bold;">${value}</span>`;
            return `<a style="${style}" href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${value}</a>`;
        }

        // 🔗 Clickable inv_no with modal
        if (column.fieldname === "inv_no" && data && data.name) {
            return `<a href="#" onclick="showCIFDetails('${data.name}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }

        return value;
    },
	filters: [        
    ],
};



// function showCIFDetails(inv_name, inv_no) {
//     frappe.call({
//         method: "ssd_app.my_custom.report.cif_sheet_table.cif_sheet_table.get_cif_details",
//         args: { inv_name },
//         callback: function (r) {
//             if (r.message) {
//                 let dialog = new frappe.ui.Dialog({
//                     title: 'CIF Sheet: ' + inv_no,
//                     size: 'large',
//                     primary_action_label: 'PDF',
//                     primary_action: () => {
//                         window.open(`/api/method/ssd_app.my_custom.report.cif_sheet_table.cif_sheet_table.get_cif_details?inv_name=${inv_name}&pdf=1`, '_blank');
//                     },
//                     fields: [
//                         {
//                             fieldtype: 'HTML',
//                             fieldname: 'details_html',
//                             options: `<div id="cif-details-a4" style="width: 20cm; max-width:100%; min-height: 28.7cm; padding: 0.5cm; background: white; font-size: 13px; box-shadow: 0 0 8px rgba(0,0,0,0.2);">${r.message}</div>`
//                         }
//                     ]
//                 });
//                 dialog.show();
//             }
//         }
//     });
// }


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


// 🧾 Modal Dialog to Show Document Flow
function showDocFlow(inv_name, inv_no) {
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

                // Add refresh button with better styling
                const $header = $(d.$wrapper).find('.modal-header');
                const refreshBtn = $(`
                    <button 
                        type="button" 
                        class="btn btn-light btn-sm" 
                        title="Refresh"
                        style="
                            margin-left: auto; 
                            margin-right: 20px; 
                            display: flex; 
                            align-items: center; 
                            gap: 8px;
                            border: 1px solid #ddd;
                            padding: 4px 8px;
                            font-size: 13px;
                        ">
                        <span style="font-size: 14px;">🔄</span> Refresh
                    </button>
                `);

                refreshBtn.on('click', function(e) {
                    e.preventDefault();
                    frappe.call({
                        method: "ssd_app.my_custom.report.document_receivable.document_receivable.get_doc_flow",
                        args: { inv_name },
                        callback: function (res) {
                            if (res.message) {
                                d.set_value('details_html', `
                                    <div id="cif-details-a4" style="box-shadow: 0 0 8px rgba(0,0,0,0.2);">
                                        ${res.message}
                                    </div>`);
                            }
                        }
                    });
                });

                // Insert before the close (X) button for better spacing
                $header.find('.modal-title').after(refreshBtn);
            }
        }
    });
}


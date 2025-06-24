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
            if (value === "Paid") {
                return `<span style="color: green; font-weight: bold;">${value}</span>`;
            } else if (value === "Part") {
                return `<span style="color: purple; font-weight: bold;">${value}</span>`;
            } else if (value === "Unpaid") {
                return `<span style="color: red; font-weight: bold;">${value}</span>`;
            }
        }

        // 🔗 Clickable inv_no with modal
        if (column.fieldname === "inv_no" && data && data.name) {
            return `<a href="#" onclick="showCIFDetails('${data.name}'); return false;">${data.inv_no}</a>`;
        }

        return value;
    },
	filters: [        
    ],
};



function showCIFDetails(inv_name) {
    frappe.call({
        method: "ssd_app.my_custom.report.cif_sheet_table.cif_sheet_table.get_cif_details",
        args: { inv_name },
        callback: function (r) {
            if (r.message) {
                let dialog = new frappe.ui.Dialog({
                    title: 'CIF Details: ' + inv_name,
                    size: 'large',
                    primary_action_label: 'PDF',
                    primary_action: () => {
                        window.open(`/api/method/ssd_app.my_custom.report.cif_sheet_table.cif_sheet_table.download_cif_pdf?inv_name=${inv_name}`, '_blank');
                    },
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'details_html',
                            options: `<div id="cif-details-a4" style="width: 20cm; min-height: 29.7cm; padding: 0.5cm; background: white; font-size: 13px; box-shadow: 0 0 8px rgba(0,0,0,0.2);">${r.message}</div>`
                        }
                    ]
                });
                dialog.show();
            }
        }
    });
}



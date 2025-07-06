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
        if (column.fieldname === "status" && data && data.status) {
            let style = "font-weight: bold;";
            if (value === "Paid") {
                style+="color: green;";
            } else if (value === "Part") {
                style+="color: purple;";
            } else if (value === "Unpaid") {
                style+="color: red;";
            }
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




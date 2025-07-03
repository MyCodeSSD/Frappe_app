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
            return `<a style="color:blue;"  href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        }
        if (column.fieldname === "inv_no" && data?.name) {
            return `<a style="color:blue;" href="#" onclick="showCIFDetails('${data.name}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
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


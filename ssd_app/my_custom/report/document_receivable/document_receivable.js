frappe.query_reports["Document Receivable"] = {
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "bank_due_date" && data) { 
            if (!data.due_date_confirm) {
                // return `<span style="color: red; font-weight: bold;">${value}</span>`;
				return `<span style="text-decoration-line: underline; text-decoration-style: double; text-decoration-color: red;">${value}</span>`;
            }
        }
        return value;
    },
	onload: function(report) {
        setTimeout(() => {
            const style = document.createElement('style');
            style.innerHTML = `
                .dt-scrollable .dt-cell__content:first-child,
                .dt-scrollable .dt-header__cell:first-child {
                    min-width: 40px !important;
                }
            `;
            document.head.appendChild(style);
        }, 50);
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
		reqd: 1 }
	]
};



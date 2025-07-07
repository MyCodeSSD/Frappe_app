// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["CC Balance"] = {
	formatter: function(value, row, column, data, default_formatter) {
        // check if this is the column you want clickable
        if (column.fieldname === "customer_name" && data && data.customer) {
            // return HTML link with onclick
            return `<a href="#" onclick="frappe.query_reports['CC Balance'].openOtherReport('${data.customer}')">${value}</a>`;
        }
        return default_formatter(value, row, column, data);
    },

    openOtherReport: function(customer) {
        frappe.set_route('query-report', 'CC Report', {
            customer: customer,
            as_on: frappe.query_report.get_filter_value('as_on')
        });
    },
	"filters": [
		{
            "fieldname": "as_on",
            "label": __("As On"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }

	]
};

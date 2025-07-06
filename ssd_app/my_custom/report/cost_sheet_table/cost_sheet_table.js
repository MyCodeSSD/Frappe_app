if (typeof Chart === "undefined") {
    const chartScript = document.createElement("script");
    chartScript.src = "https://cdn.jsdelivr.net/npm/chart.js";
    chartScript.defer = true;
    document.head.appendChild(chartScript);
}

frappe.query_reports["Cost Sheet Table"] = {
	onload: function (report) {
        report.page.add_inner_button("Open Cost Sheet List", function () {
            frappe.set_route("List", "Cost Sheet");
        });
    },
    filters: [
        {
            fieldname: "user_limit",
            label: __("User Limit"),
            fieldtype: "Select",
            options: ["20", "50", "500", "2000"],
            default: "20",
            hidden: 0   // show to user; if you still want to hide, set hidden: 1
        }
    ]
};

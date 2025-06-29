frappe.ui.form.on('Comm Paid', {
    onload(frm) {
        set_child_inv_no_query(frm);
    },
    agent(frm) {
        set_child_inv_no_query(frm);
    }
});

function set_child_inv_no_query(frm) {
    // Set query for the child table Link field "inv_no"
    frm.fields_dict['comm_breakup'].grid.get_field('inv_no').get_query = function(doc, cdt, cdn) {
        let child = frappe.get_doc(cdt, cdn);
        return {
            query: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_filter_inv_no",
            filters: {
                agent: frm.doc.agent || ''
            }
        };
    };
}

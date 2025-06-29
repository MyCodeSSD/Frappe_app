// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_nego.doc_nego.get_available_inv_no'
    }));
}

//  🧠 Function to fetch CIF data based on selected inv_no
function get_cif_data(frm) {
    if (!frm.doc.inv_no) return;

    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_cif_data",
            args: { inv_no: frm.doc.inv_no },
            callback: function (r) {
                const data = r.message;
                console.log("Received data:", r.message);
                if (!data) return;
                const fields_to_lock = ['inv_date', 'category', 'bank', 'notify', 'due_date', 'customer', 'payment_term', "document"];
                fields_to_lock.forEach(field => {
                        frm.set_df_property(field, 'read_only', 0);
                    });

                frm.set_value({
                    inv_date: data.inv_date,
                    category: data.category,
                    notify: data.notify,
                    customer: data.customer,
                    bank: data.bank,
                    payment_term: data.payment_term,
                    term_days: data.term_days,
                    due_date: data.due_date,
                    document: data.document,
                    nego_date: frappe.datetime.get_today(),
                    nego_amount: data.can_nego,
                    bank_due_date:frappe.datetime.add_days(frm.doc.nego_date, data.term_days || 0),

                });

                // Lock fields after delay to ensure they are set
                setTimeout(() => {
                    fields_to_lock.forEach(field => {
                        frm.set_df_property(field, 'read_only', 1);
                    });

                    // Unlock and require bank if it's empty
                    if (!data.bank) {
                        frm.set_df_property('bank', 'reqd', 1);
                        frm.set_df_property('bank', 'read_only', 0);
                    }

                    frm.refresh_fields();
                }, 150);
            }
        });
    }
}



frappe.ui.form.on("Doc Nego", {
	onload(frm) {
        inv_no_filter(frm);  // ✅ Register custom filter  
        get_cif_data(frm);
    },
    inv_no(frm) {
        get_cif_data(frm);   // ✅ Fetch CIF details
    }

});




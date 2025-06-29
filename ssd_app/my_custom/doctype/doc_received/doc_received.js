// 🧠 Function to apply custom query filter on inv_no field
function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_received.doc_received.get_available_inv_no'
    }));
}

// 🧠 Function to fetch CIF data based on selected inv_no
function get_cif_data(frm) {
    if (!frm.doc.inv_no) return;

    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.doc_received.doc_received.get_cif_data",
            args: { inv_no: frm.doc.inv_no },
            callback: function (r) {
                const data = r.message;
                if (!data) return;
                const fields_to_lock = ['inv_date', 'category', 'bank','notify', 'customer', 'payment_term'];
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
                    document: data.document,
                    received: data.receivable,
                    received_date: frappe.datetime.get_today()
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


// 🧩 Main Form Event Bindings
frappe.ui.form.on("Doc Received", {
    onload(frm) {
        inv_no_filter(frm);  // ✅ Register custom filter
        get_cif_data(frm);  
    },
    inv_no(frm) {
        get_cif_data(frm);   // ✅ Fetch CIF details
    }
});

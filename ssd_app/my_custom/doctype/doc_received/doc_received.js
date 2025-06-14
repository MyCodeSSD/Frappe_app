function get_cif_data(frm) {
    if (!frm.doc.inv_no) return;

    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_received.doc_received.get_cif_data",
        args: { inv_no: frm.doc.inv_no },
        callback: function (r) {
            const data = r.message;
            if (!data) return;

            frm.set_value({
                inv_date: data.inv_date,
                category: data.category,
                notify: data.notify,
                customer: data.customer,
                bank: data.bank,
                payment_term: data.payment_term,
                term_days: data.term_days,
                document: data.document,
                received:data.document
            });

            // Delay to ensure fields are set before locking
            setTimeout(() => {
                const fields_to_lock = ['inv_date', 'category', 'bank', 'notify', 'customer', 'payment_term'];

                fields_to_lock.forEach(field => {
                    frm.set_df_property(field, 'read_only', 1);
                });

                // Conditionally unlock bank if missing
                if (!data.bank) {
                    frm.set_df_property('bank', 'reqd', 1);
                    frm.set_df_property('bank', 'read_only', 0);
                }

                frm.refresh_fields();
            }, 300);
        }
    });
}

function put_bank_in_cif(frm) {
    if (!frm.doc.bank) return;

    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_received.doc_received.update_cif_bank_if_missing",
        args: {
            inv_no: frm.doc.inv_no,
            bank_value: frm.doc.bank
        }
    });
}

frappe.ui.form.on("Doc Received", {
    inv_no: get_cif_data,
    before_save: put_bank_in_cif
});

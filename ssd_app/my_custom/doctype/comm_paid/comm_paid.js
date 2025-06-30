// ------------------------
// Parent Doctype: Comm Paid
// ------------------------
frappe.ui.form.on('Comm Paid', {
    
    onload(frm) {
        set_child_inv_no_query(frm);
    },
    onload_post_render(frm) {
        frm.set_value('date', frappe.datetime.get_today());
    },
    agent(frm) {
        set_child_inv_no_query(frm);
    },
    amount_usd(frm) {
        calculate_running_balance(frm);
    },
    refresh(frm) {
        calculate_running_balance(frm);
    },
    comm_breakup_add(frm) {
        calculate_running_balance(frm);
    },
    comm_breakup_remove(frm) {
        calculate_running_balance(frm);
    },
    validate(frm) {
        // Final validation: running balance must be zero before submission
        const total = frm.doc.amount_usd || 0;
        const allocated = frm.doc.comm_breakup.reduce((sum, row) => sum + flt(row.amount), 0);
        const remaining = flt(total) - flt(allocated);

        if (remaining !== 0) {
            frappe.throw(__('Total commission must be fully allocated before submission. Remaining: {0}', [remaining]));
        }
    }
});

// ------------------------
// Child Table: Comm Breakup
// ------------------------
frappe.ui.form.on('Comm Breakup', {
    inv_no(frm, cdt, cdn) {
        toggle_agent_readonly(frm);
        const child = locals[cdt][cdn];
        if (child.inv_no) {
            fetch_and_set_balance_as_amount(child, cdt, cdn, frm);
        }
    },
    amount(frm, cdt, cdn) {
        const child = locals[cdt][cdn];
        validate_child_amount_not_exceed_balance(child, cdt, cdn, frm);
        calculate_running_balance(frm);
    },
   
});

// ------------------------
// Utility Functions
// ------------------------

function set_child_inv_no_query(frm) {
    frm.fields_dict['comm_breakup'].grid.get_field('inv_no').get_query = function(doc, cdt, cdn) {
        return {
            query: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_filter_inv_no",
            filters: {
                agent: frm.doc.agent || ''
            }
        };
    };
}

function fetch_and_set_balance_as_amount(child, cdt, cdn, frm) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_inv_no_balance",
        args: { inv_no: child.inv_no },
        callback: function(r) {
            if (r.message !== undefined) {
                const balance = flt(r.message) || 0;
                frappe.model.set_value(cdt, cdn, 'amount', balance);
                calculate_running_balance(frm);
            }
        }
    });
}

function validate_child_amount_not_exceed_balance(child, cdt, cdn, frm) {
    if (child.inv_no && child.amount) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_inv_no_balance",
            args: { inv_no: child.inv_no },
            callback: function(r) {
                if (r.message !== undefined) {
                    const balance = flt(r.message) || 0;
                    if (flt(child.amount) > balance) {
                        frappe.model.set_value(cdt, cdn, 'amount', balance);
                        frappe.msgprint({
                            title: __("Validation Error"),
                            message: __("Entered amount cannot exceed the pending receivable for this invoice (Max: {0}).", [balance]),
                            indicator: 'red'
                        });
                    }
                    calculate_running_balance(frm);
                }
            }
        });
    }
}

function calculate_running_balance(frm) {
    const total = flt(frm.doc.amount_usd) || 0;
    let running_balance = total;

    frm.doc.comm_breakup.forEach(row => {
        running_balance -= flt(row.amount);
        row.balance = running_balance;
    });

    frm.refresh_field('comm_breakup');

    // Disable adding rows if fully allocated
    frm.fields_dict.comm_breakup.grid.cannot_add_rows = running_balance <= 0;

    // Enable/Disable Save based on exact allocation
    if (running_balance !== 0) {
        frm.disable_save();
    } else {
        frm.enable_save();
    }
}


// if Data in Product in product_item then category read_only
function toggle_agent_readonly(frm) {
    const hasProduct = frm.doc.comm_breakup?.some(row => row.inv_no);
    frm.set_df_property('agent', 'read_only', !!hasProduct);
}


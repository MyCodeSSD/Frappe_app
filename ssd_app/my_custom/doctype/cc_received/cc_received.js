
// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.ui.form.on("CC Received", {
	onload_post_render(frm) {
        frm.set_value('date', frappe.datetime.get_today());
        frm.set_value('currency', "USD");
        frm.set_value('ex_rate', 1);
        // frm.fields_dict.cc_breakup.grid.cannot_open_form = true;
	},
    refresh(frm) {
        calculate_running_balance(frm);
    },
    cc_breakup_add(frm, cdt, cdn) {
        // When user adds a new row → recalculate
        calculate_running_balance(frm);
    },
    cc_breakup_remove(frm) {
        // When user deletes a row → recalculate
        calculate_running_balance(frm);
    },
    amount_usd(frm) {
        // When user deletes a row → recalculate
        add_default_cc_breakup(frm);
        calculate_running_balance(frm);
    }
});

frappe.ui.form.on('CC Breakup', {
    amount(frm, cdt, cdn) {
        calculate_running_balance(frm);
    }
});


function calculate_running_balance(frm) {
    let total = frm.doc.amount_usd || 0;
    let running_balance = total;

    // Loop through child table
    frm.doc.cc_breakup.forEach(row => {
        row.balance = flt(running_balance) - flt(row.amount);
        running_balance = row.balance;
    });

    frm.refresh_field('cc_breakup'); // refresh child table display

    // Prevent adding row if balance <= 0
    if (running_balance == 0) {
        frm.fields_dict.cc_breakup.grid.cannot_add_rows = true;
    } else {
        frm.fields_dict.cc_breakup.grid.cannot_add_rows = false;
    }

    // Disable Save if balance != 0
    if (running_balance != 0) {
        frm.disable_save();
        // frappe.msgprint(__('Remaining balance must be zero to save.'));
    } else {
        frm.enable_save();
    }
}

function add_default_cc_breakup(frm) {
    if (!frm.doc.cc_breakup || frm.doc.cc_breakup.length === 0) {
        let child = frm.add_child('cc_breakup', {
            ref_no: 'On Account',
            amount: frm.doc.amount_usd || 0
        });
    } 
}
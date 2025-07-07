// Copyright (c) 2025, SSDolui
// For license information, please see license.txt

function calculate_running_balance(frm) {
    let total = flt(frm.doc.amount_usd) || 0;
    let running_balance = total;

    frm.doc.cc_breakup.forEach(row => {
        if (!row.amount) {
            row.amount = running_balance;
        }
        row.balance = running_balance - flt(row.amount);

        if (row.balance === 0) {
            row.balance = "";
        }

        running_balance = flt(row.balance) || 0;
    });

    frm.refresh_field('cc_breakup');

    if (running_balance !== 0) {
        frm.disable_save();
    } else {
        frm.enable_save();
    }
}

function add_first_cc_breakup_row_if_needed(frm) {
    if (!frm.doc.amount_usd) return;
    if (!(frm.doc.cc_breakup && frm.doc.cc_breakup.length)) {
        const child = frm.add_child('cc_breakup', {
            ref_no: 'On Account',
            amount: flt(frm.doc.amount_usd)
        });
        frm.refresh_field('cc_breakup');
    }
    calculate_running_balance(frm);
}

function auto_fill_amount_on_add(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const table = frm.doc.cc_breakup || [];
    const idx = table.findIndex(r => r.name === row.name);

    if (!frm.doc.amount_usd) {
        frappe.msgprint("🚫 Please enter Amount before adding breakup rows.");
        frm.doc.cc_breakup.pop();
        frm.refresh_field('cc_breakup');
        return;
    }

    if (!row.amount) {
        if (idx === 0) {
            row.amount = flt(frm.doc.amount_usd);
        } else {
            const prev = table[idx - 1];
            row.amount = flt(prev.balance) || 0;
        }
        frm.refresh_field('cc_breakup');
    }
    calculate_running_balance(frm);
}

frappe.ui.form.on("CC Received", {
    onload_post_render(frm) {
        frm.set_value('date', frappe.datetime.get_today());
        frm.set_value('currency', "USD");
        frm.set_value('ex_rate', 1);
    },
    refresh(frm) {
        calculate_running_balance(frm);
    },
    amount_usd(frm) {
        add_first_cc_breakup_row_if_needed(frm);
    },
    amount(frm){
        if(frm.doc.amount && frm.doc.ex_rate){
            frm.set_value('amount_usd', frm.doc.amount * frm.doc.ex_rate);
        }
    },
    ex_rate(frm){
        if(frm.doc.amount && frm.doc.ex_rate){
            frm.set_value('amount_usd', frm.doc.amount * frm.doc.ex_rate);
        }
    },
    cc_breakup_add(frm, cdt, cdn) {
        auto_fill_amount_on_add(frm, cdt, cdn);
    },
    cc_breakup_remove(frm) {
        calculate_running_balance(frm);
    }
});

frappe.ui.form.on("CC Breakup", {
    amount(frm, cdt, cdn) {
        calculate_running_balance(frm);
    },
    ref_no(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.amount) {
            auto_fill_amount_on_add(frm, cdt, cdn);
        }
    }
});

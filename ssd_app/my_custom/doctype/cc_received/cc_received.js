// Copyright (c) 2025, SSDolui
// For license information, please see license.txt

// --------------------- Core Calculation ---------------------

function calculate_running_balance(frm) {
    let total = flt(frm.doc.amount_usd) || 0;
    let running_balance = total;

    frm.doc.cc_breakup.forEach((row, idx) => {

        // 🟩 First Row: Set defaults if empty
        if (idx === 0) {
            row.ref_no = row.ref_no || "On Account";
            if (!row.amount) {
                row.amount = flt(frm.doc.amount_usd);
            }
        } 
        // 🟩 Subsequent Rows: Set defaults if empty
        else {
            row.ref_no = row.ref_no || "";
            if (!row.amount) {
                const prev = frm.doc.cc_breakup[idx - 1];
                row.amount = flt(prev.balance) || 0;
            }
        }

        // 🟩 Calculate balance for the row
        row.balance = flt(running_balance) - flt(row.amount);
        if (row.balance === 0) {
            row.balance = ""; // Display clean empty if zero
        }

        // Update running_balance for the next row
        running_balance = flt(row.balance) || 0;
    });

    frm.refresh_field('cc_breakup');

    // 🟩 Disable save if balance not fully cleared
    if (running_balance !== 0) {
        frm.disable_save();
    } else {
        frm.enable_save();
    }
}

// --------------------- Add First Row If Needed ---------------------

function add_first_cc_breakup_row_if_needed(frm) {
    if (!frm.doc.amount_usd) return;

    if (!(frm.doc.cc_breakup && frm.doc.cc_breakup.length)) {
        frm.add_child('cc_breakup', {
            ref_no: 'On Account',
            amount: flt(frm.doc.amount_usd)
        });
        frm.refresh_field('cc_breakup');
    }

    calculate_running_balance(frm);
}

// --------------------- Auto Fill on Row Add ---------------------

function auto_fill_amount_on_add(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const table = frm.doc.cc_breakup || [];
    const idx = table.findIndex(r => r.name === row.name);

    // 🚫 Prevent adding if amount_usd is not set
    if (!frm.doc.amount_usd) {
        frappe.msgprint("🚫 Please enter Amount before adding breakup rows.");
        frm.doc.cc_breakup.pop();
        frm.refresh_field('cc_breakup');
        return;
    }

    // 🟩 Fill defaults only if empty (do not overwrite user input)
    if (idx === 0) {
        row.ref_no = row.ref_no || "On Account";
        if (!row.amount) {
            row.amount = flt(frm.doc.amount_usd);
        }
    } else {
        row.ref_no = row.ref_no || "";
        if (!row.amount) {
            const prev = table[idx - 1];
            row.amount = flt(prev.balance) || 0;
        }
    }

    frm.refresh_field('cc_breakup');
    calculate_running_balance(frm);
}

// --------------------- Main Form Triggers ---------------------

frappe.ui.form.on("CC Received", {
    onload_post_render(frm) {
        // 🟩 Pre-fill defaults on load
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

    amount(frm) {
        // 🟩 Auto-calculate amount_usd when amount or ex_rate changes
        if (frm.doc.amount && frm.doc.ex_rate) {
            frm.set_value('amount_usd', frm.doc.amount * frm.doc.ex_rate - frm.doc.bank_charges);
        }
    },

    ex_rate(frm) {
        if (frm.doc.amount && frm.doc.ex_rate) {
            frm.set_value('amount_usd', frm.doc.amount * frm.doc.ex_rate - frm.doc.bank_charges );
        }
    },
    bank_charges(frm) {
        if (frm.doc.amount && frm.doc.ex_rate) {
            frm.set_value('amount_usd', frm.doc.amount * frm.doc.ex_rate - frm.doc.bank_charges);
        }
    },

    cc_breakup_add(frm, cdt, cdn) {
        auto_fill_amount_on_add(frm, cdt, cdn);
    },

    cc_breakup_remove(frm) {
        calculate_running_balance(frm);
    }
});

// --------------------- Child Table Triggers ---------------------

frappe.ui.form.on("CC Breakup", {
    amount(frm, cdt, cdn) {
        calculate_running_balance(frm);
    },
    ref_no(frm, cdt, cdn) {
        calculate_running_balance(frm);
    }
});

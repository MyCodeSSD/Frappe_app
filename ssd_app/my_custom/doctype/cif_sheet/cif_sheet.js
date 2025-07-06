// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

// Function to check uniqueness of 'inv_no' in 'CIF Sheet' doctype
function check_unique_inv_no(frm) {
    if (!frm.doc.inv_no) return;

    frappe.db.get_value('CIF Sheet', { inv_no: frm.doc.inv_no }, 'name')
        .then(r => {
            if (r && r.message && r.message.name && r.message.name !== frm.doc.name) {
                frappe.msgprint({
                    title: __(`Duplicate Entry: ${frm.doc.inv_no}`),
                    message: __('Invoice Number must be unique. This one already exists.'),
                    indicator: 'red'
                });
                frm.set_value('inv_no', '');
            }
        });
}

// det default from_date= inv_date
function set_from_date(frm){
    if (!frm.doc.inv_date) return;
    if (!frm.doc.from_date){
        frm.set_value("from_date",frm.doc.inv_date)
    }
    
}
// set default final destination city= notifycity
function set_default_final_detination(frm){
    if (!frm.doc.notify) return;
    frappe.db.get_value("Notify",frm.doc.notify,"city").then(r=>{
        if(r.message){
            frm.set_value("final_destination",r.message.city);
        }

    })
}

// Toggle SC No field
function toggle_sc_no_field(frm) {
    const hidden = !!frm.doc.multiple_sc;
    frm.set_df_property('sc_no', 'hidden', hidden);
    frm.set_df_property('sc_no', 'reqd', !hidden);

    if (hidden) frm.set_value('sc_no', '');

    // const enable = !hidden;
    // frm.fields_dict.product_details.grid.toggle_enable('sc_no', !enable);
    // frappe.msgprint("hiiiii "+ !hidden);
    // frm.fields_dict.product_details.grid.update_docfield_property('sc_no', 'hidden', !hidden );
    frm.fields_dict.product_details.grid.update_docfield_property('sc_no', 'reqd', hidden);
    frm.fields_dict.product_details.grid.update_docfield_property('sc_no', 'read_only', !hidden);
}

// Propagate SC No to child rows
function put_sc_no_in_child_row(frm) {

    if (!frm.doc.multiple_sc){
        frappe.msgprint(frm.doc.multiple_sc);
        frm.doc.product_details.forEach(row=>{
            row.sc_no= frm.doc.sc_no;
        });
        frm.refresh_field('product_details');
    }
}

// Filter products by category
function set_product_query_filter(frm) {
    frm.fields_dict.product_details.grid.get_field('product').get_query = () => ({
        filters: {
            category: frm.doc.category || "blank"
        }
    });
}

// if Data in Product in product_item then category read_only
function toggle_category_readonly(frm) {
    const hasProduct = frm.doc.product_details?.some(row => row.product);
    frm.set_df_property('category', 'read_only', !!hasProduct);
}

// Calculate gross sales (USD)
function calculate_gross_sales(frm) {
    const total = frm.doc.product_details.reduce((sum, row) => sum + flt(row.gross_usd), 0);
    frm.set_value('gross_sales', flt(total, 2));
}

// Calculate total expenses (USD)
function calculate_total_exp(frm) {
    return frm.doc.expenses.reduce((sum, row) => sum + flt(row.amount_usd), 0);
}

// Calculate insurance
function calculate_insurance(frm) {
    const pct = flt(frm.doc.insurance_pct);
    let base = 0;

    if (pct) {
        if (frm.doc.insurance_based_on === "On Gross") {
            base = frm.doc.gross_sales;
        } else if (frm.doc.insurance_based_on === "On Total") {
            base = frm.doc.gross_sales + calculate_total_exp(frm);
        }
    }

    frm.set_value('insurance', flt(base * pct / 100));
}

// Calculate handling
function calculate_handling(frm) {
    const pct = flt(frm.doc.handling_pct);
    let base = 0;

    if (pct) {
        if (frm.doc.handling_based_on === "On Gross") {
            base = frm.doc.gross_sales;
        } else if (frm.doc.handling_based_on === "On Total") {
            base = frm.doc.gross_sales + calculate_total_exp(frm) + flt(frm.doc.insurance);
        }
    }

    frm.set_value('handling_charges', flt((base * pct / 100),2));
}

// Calculate overall sales
function calculate_sales(frm) {
    calculate_gross_sales(frm);
    calculate_insurance(frm);
    calculate_handling(frm);

    const total = flt(frm.doc.gross_sales) +
                  calculate_total_exp(frm) +
                  flt(frm.doc.insurance) +
                  flt(frm.doc.handling_charges);

    frm.set_value('sales', flt(total, 2));
}


// Calculate CC amount
function calculate_cc(frm) {
    const sales = flt(frm.doc.sales);
    const doc_amt = flt(frm.doc.document);
    frm.set_value('cc', sales - doc_amt);
}

//  Calculate due_date
function calculate_due_date(frm) {
    if (frm.doc.from_date && frm.doc.term_days) {
        const fromDate = frappe.datetime.str_to_obj(frm.doc.from_date);
        const dueDate = frappe.datetime.add_days(fromDate, frm.doc.term_days);
        frm.set_value('due_date', frappe.datetime.obj_to_str(dueDate));
    } else {
        frm.set_value('due_date', null); // clear if incomplete input
    }
}

// collapse child table if no rows.
function toggle_expense_section(frm) {
    const has_expenses = frm.doc.expenses && frm.doc.expenses.length > 0;

    if (frm.fields_dict.expenses_section) {
        frm.fields_dict.expenses_section.collapse(!has_expenses); // collapse if no rows
    }
}

//  Create Custom Print button
function custom_print(frm){
    frm.add_custom_button("Custom Print", function() {
        showCIFDetails(frm.doc.name, frm.doc.inv_no);
    });
}

// ------------------------------------------------------- Main DocType ------------------------------------------------------

frappe.ui.form.on("CIF Sheet", {
    refresh(frm) {
        toggle_sc_no_field(frm);
        toggle_category_readonly(frm);
        custom_print(frm);
    },
    onload(frm) {
        set_product_query_filter(frm);
        toggle_category_readonly(frm);
        calculate_gross_sales(frm);
        calculate_insurance(frm);
        toggle_expense_section(frm);
        check_and_lock_fields(frm);
    },
	inv_no(frm) {
        check_unique_inv_no(frm);
        check_and_lock_fields(frm);
	},
    inv_date(frm) {
        set_from_date(frm);
	},
    notify(frm){
        set_default_final_detination(frm);
    },
    multiple_sc(frm) {
        toggle_sc_no_field(frm);
    },
    validate(frm) {
        calculate_sales(frm);
        put_sc_no_in_child_row(frm);
        toggle_category_readonly(frm);
        calculate_cc(frm);
        checkDuplicateExpensesOnValidation(frm);
    },
    from_date: function(frm) {
        calculate_due_date(frm);
    },
    term_days: function(frm) {
        calculate_due_date(frm);
    },
    document(frm) {
        calculate_cc(frm);
        handle_payment_term_lock(frm);
        lock_bank_in_tt(frm);
        lock_term_days(frm);
        calculate_due_date(frm);
    },
    payment_term(frm){
        lock_bank_in_tt(frm);
        lock_term_days(frm);
        calculate_due_date(frm);
    },
    after_save(frm) {
        showCIFDetails(frm.doc.name, frm.doc.inv_no);
    },
    insurance_pct: calculate_and_refresh,
    insurance_based_on: calculate_and_refresh,
    handling_pct: calculate_and_refresh,
    handling_based_on: calculate_and_refresh,
    
});

// Shared logic for handling/insurance field changes
function calculate_and_refresh(frm) {
    calculate_sales(frm);
    calculate_cc(frm); 
}

// payment term on document ==0
function handle_payment_term_lock(frm) {
    if (frm.doc.document == 0) {
        frm.set_value('payment_term', 'TT');
        frm.set_df_property('payment_term', 'read_only', 1);
        frm.set_df_property('bank_ref_no', 'read_only', 1);
    } else {
        frm.set_df_property('payment_term', 'read_only', 0);
        frm.set_df_property('bank_ref_no', 'read_only', 0);
    }
}

// Lock bank for payment term=TT
function lock_bank_in_tt(frm) {
    if (frm.doc.payment_term == "TT") {
        frm.set_df_property('bank', 'read_only', 1);
    } else {
        frm.set_df_property('bank', 'read_only', 0);
    }
}
// Fixed & lock Term-days
function lock_term_days(frm) {
    if (frm.doc.payment_term == "TT" || 
        frm.doc.payment_term == "DP" || 
        frm.doc.payment_term == "LC at Sight") {
            frm.set_value("term_days", 30);
            frm.set_df_property('term_days', 'read_only', 1);
    } else {
        frm.set_df_property('term_days', 'read_only', 0);
    }
}

// ---------------------- Product Child Table ----------------------

// set default unit
function fetch_unit(product, cdt, cdn) {
    if (product) {
        frappe.db.get_value("Product", product, "unit").then(r => {
            if (r.message?.unit) {
                frappe.model.set_value(cdt, cdn, "unit", r.message.unit);
            }
        });
    }
}

// Calculate the gross amount for a row in the child table.
function calculate_gross(cdt, cdn) {
    const row = locals[cdt][cdn];
    const gross = flt(row.qty) * flt(row.rate) + flt(row.charges_amount);
    frappe.model.set_value(cdt, cdn, "gross", gross);
}

// Calculate the gross(USD) amount for a row in the child table.
function calculate_gross_usd(cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.ex_rate) {
        const usd = (flt(row.gross) / flt(row.ex_rate));
        frappe.model.set_value(cdt, cdn, "gross_usd", flt(usd,2) + flt(row.round_off_usd));
    }
}

// Reusable async function to check if product category matches doc category
async function check_category(frm, row) {
    if (!row.product) return;

    const r = await frappe.db.get_value("Product", row.product, "category");
    if (r.message && r.message.category !== frm.doc.category) {
        frappe.model.set_value(row.doctype, row.name, "product", "");
        frappe.throw(`Product "${row.product}" is not under the selected category.`);
    }
}

frappe.ui.form.on("Product CIF", {
    // When product field is changed
    async product(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        toggle_category_readonly(frm);
        fetch_unit(row.product, cdt, cdn);
        await check_category(frm, row);
    },

    // When form is being validated before save
    async validate(frm) {
        for (const row of frm.doc.product_cif_table || []) {
            await check_category(frm, row);
        }
    },
    // Bind other triggers
    rate: update_all,
    qty: update_all,
    charges_amount: update_all,
    ex_rate: update_all,
    product_item_remove: update_all,
    round_off_usd: update_all
});

// Update all calculations for product child table
function update_all(frm, cdt, cdn) {
    calculate_gross(cdt, cdn);
    calculate_gross_usd(cdt, cdn);
    calculate_sales(frm);
    calculate_cc(frm);
}

// ---------------------- Expense Child Table: Expenses CIF ----------------------

frappe.ui.form.on("Expenses CIF", {
    amount: update_exp_and_totals,
    ex_rate: update_exp_and_totals,
    expenses: checkDuplicateExpenses
});

function calculate_exp(cdt, cdn) {
    const row = locals[cdt][cdn];
    frappe.model.set_value(cdt, cdn, "amount_usd", flt(flt(row.amount) / flt(row.ex_rate)), 2);
}

function update_exp_and_totals(frm, cdt, cdn) {
    calculate_exp(cdt, cdn);
    calculate_sales(frm);
    calculate_cc(frm);
}

// protect duplicate expnses entry
function checkDuplicateExpenses(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let table = frm.doc.expenses;  

    let is_duplicate = table.some(r =>
        r.name !== row.name && r.expenses === row.expenses
    );

    if (is_duplicate) {
        frappe.msgprint('Expenses must be unique.');
        frappe.model.set_value(cdt, cdn, 'expenses', null); // clear the field
    }
}
 

// Check duplicates on validation
function checkDuplicateExpensesOnValidation(frm) {
    let table = frm.doc.expenses || [];
    let expenses_values = table.map(r => r.expenses).filter(Boolean);

    let unique_values = new Set(expenses_values);

    if (expenses_values.length !== unique_values.size) {
        frappe.throw(__('Expenses must be unique.'));
    }
}



//If Doc Nego or Receive then lock Bank Name & document Amount 
function check_and_lock_fields(frm) {
    if (frm.is_new() || !frm.doc.inv_no) return;

    frappe.call({
        method: "ssd_app.my_custom.doctype.cif_sheet.cif_sheet.check_related_docs",
        args: { inv_id: frm.doc.name },
        callback: function(r) {
            if (r.message === true) {
                frm.set_df_property("document", "read_only", 1);
                frm.set_df_property("bank", "read_only", 1);
                frm.refresh_field("document");
                frm.refresh_field("bank");
            }
        }
    });
}


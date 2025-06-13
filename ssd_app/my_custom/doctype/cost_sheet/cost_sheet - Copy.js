// Utility: Toggle SC No field
function toggle_po_no_field(frm) {
    const hidden = !!frm.doc.multiple_po;
    frm.toggle_display('po_no', !hidden);
    frm.toggle_reqd('po_no', !hidden);
    if (hidden) frm.set_value('po_no', '');

    const grid = frm.fields_dict.product_details.grid;
    grid.update_docfield_property('po_no', 'reqd', hidden);
    grid.update_docfield_property('po_no', 'read_only', !hidden);
}

// Utility: Toggle Supplier No field
function toggle_supplier_field(frm) {
    const hidden = !!frm.doc.multiple_supplier;
    frm.toggle_display('supplier', !hidden);
    frm.toggle_reqd('supplier', !hidden);
    if (hidden) frm.set_value('supplier', '');

    const grid = frm.fields_dict.product_details.grid;
    grid.update_docfield_property('supplier', 'reqd', hidden);
    grid.update_docfield_property('supplier', 'read_only', !hidden);
}

// Utility: Set PO and Supplier in child table
function put_po_no_sup_in_child_row(frm) {
    let updated = false;

    if (!frm.doc.multiple_po) {
        frm.doc.product_details.forEach(row => row.po_no = frm.doc.po_no);
        updated = true;
    }

    if (!frm.doc.multiple_supplier) {
        frm.doc.product_details.forEach(row => row.supplier = frm.doc.supplier);
        updated = true;
    }

    if (updated) frm.refresh_field('product_details');
}

// Calculate total purchase
function calculate_purchase(frm) {
    const total = frm.doc.product_details.reduce((sum, row) => sum + flt(row.gross_usd), 0);
    frm.set_value('purchase', flt(total, 2));
}

function calculate_total_exp(frm) {
    return frm.doc.expenses.reduce((sum, row) => sum + flt(row.amount_usd), 0);
}

function calculate_total_qty(frm) {
    return frm.doc.product_details.reduce((sum, row) => sum + flt(row.qty), 0);
}

// Commission calculation
function calculate_commission(frm) {
    const rate = frm.doc.comm_rate;

    if (rate) {
        frm.toggle_reqd('agent', true);
        const base = frm.doc.comm_based_on === "Sales"
            ? flt(frm.doc.sales) * rate / 100
            : calculate_total_qty(frm) * rate;

        frm.set_value('commission', flt(base, 2));
    } else {
        frm.toggle_reqd('agent', false);
        frm.set_value('commission', 0);
    }
}

// Final cost/profit calculation
function calculate_cost(frm) {
    if (!frm.doc.inv_no) return;

    frappe.db.get_value("CIF Sheet", frm.doc.inv_no, "sales")
        .then(r => {
            if (!r.message) return;

            const sales = flt(r.message.sales);
            const commission = flt(frm.doc.commission);
            const purchase = flt(frm.doc.purchase);
            const expenses = flt(calculate_total_exp(frm));

            const total_cost = flt(purchase + expenses + commission, 2);
            const profit = flt(sales - total_cost, 2);
            const profit_pct = total_cost ? flt((profit / total_cost) * 100, 2) : 0;

            frm.set_value({
                cost: total_cost,
                profit,
                profit_pct
            });
        })
        .catch(() => {
            frappe.msgprint("Failed to fetch sales value from CIF Sheet.");
        });
}

// Populate data from CIF Sheet
function get_cif_data(frm) {
    if (!frm.doc.inv_no) return;

    frappe.call({
        method: "ssd_app.my_custom.doctype.cost_sheet.cost_sheet.get_cif_data",
        args: { inv_no: frm.doc.inv_no },
        callback({ message: data }) {
            if (!data) return;

            frm.set_value({
                custom_title: data.inv_no,
                inv_date: data.inv_date,
                customer: data.customer,
                category: data.category,
                notify: data.notify,
                accounting_company: data.accounting_company,
                shipping_company: data.shipping_company,
                multiple_po: data.multiple_sc,
                po_no: data.sc_no,
                sales: data.sales
            });

            frm.clear_table("product_details");
            (data.product_details || []).forEach(row => {
                frm.add_child("product_details", {
                    product: row.product,
                    qty: row.qty,
                    unit: row.unit,
                    id_code: row.name,
                    po_no: row.sc_no,
                    ...(data.handling_charges && {
                        rate: row.rate,
                        currency: row.currency,
                        ex_rate: row.ex_rate,
                        charges: row.charges,
                        charges_amount: row.charges_amount,
                        round_off_usd: row.round_off_usd
                    })
                });
            });

            frm.clear_table("expenses");
            (data.expenses || []).forEach(row => {
                if (data.handling_charges) {
                    frm.add_child("expenses", {
                        expenses: row.expenses,
                        amount: row.amount,
                        currency: row.currency,
                        ex_rate: row.ex_rate
                    });
                }
            });

            if (data.insurance) {
                frm.add_child("expenses", {
                    expenses: "Insurance",
                    amount: data.insurance,
                    currency: "USD",
                    ex_rate: 1
                });
            }

            frm.refresh_fields();
            run_all_calculations(frm);
        }
    });
    
}

// Custom filter
function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.cost_sheet.cost_sheet.get_available_inv_no'
    }));
}

// Child calculations
function calculate_gross(cdt, cdn) {
    const row = locals[cdt][cdn];
    const gross = flt(row.qty) * flt(row.rate) + flt(row.charges_amount);
    frappe.model.set_value(cdt, cdn, 'gross', flt(gross, 2));
}

function calculate_gross_usd(cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.ex_rate) {
        const usd = flt(row.gross / row.ex_rate) + flt(row.round_off_usd);
        frappe.model.set_value(cdt, cdn, 'gross_usd', flt(usd, 2));
    }
}

function calculate_exp(cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.ex_rate) {
        frappe.model.set_value(cdt, cdn, 'amount_usd', flt(row.amount / row.ex_rate, 2));
    }
}

// Shared triggers
function update_all(frm, cdt, cdn) {
    calculate_gross(cdt, cdn);
    calculate_gross_usd(cdt, cdn);
    calculate_purchase(frm);
    calculate_commission(frm);
    calculate_cost(frm);
}

function update_exp_and_totals(frm, cdt, cdn) {
    calculate_exp(cdt, cdn);
    calculate_cost(frm);
}

function run_all_calculations(frm) {
    frm.doc.product_details.forEach(row => update_all(frm, row.doctype, row.name));
    frm.doc.expenses.forEach(row => update_exp_and_totals(frm, row.doctype, row.name));
    calculate_purchase(frm);
}

// Hooks
frappe.ui.form.on("Cost Sheet", {
    setup: inv_no_filter,
    onload_post_render: run_all_calculations,
    inv_no: get_cif_data,
    validate: put_po_no_sup_in_child_row,
    refresh(frm) {
        toggle_po_no_field(frm);
        toggle_supplier_field(frm);
    },
    multiple_po: toggle_po_no_field,
    multiple_supplier: toggle_supplier_field,
    comm_rate(frm) {
        calculate_commission(frm);
        calculate_cost(frm);
    },
    comm_based_on(frm) {
        calculate_commission(frm);
        calculate_cost(frm);
    }
});

frappe.ui.form.on("Product Cost", {
    rate: update_all,
    qty: update_all,
    charges_amount: update_all,
    ex_rate: update_all,
    round_off_usd: update_all,
    product_item_remove: update_all
});

frappe.ui.form.on("Expenses Cost", {
    amount: update_exp_and_totals,
    ex_rate: update_exp_and_totals
});

// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt
// function set_custom_title(frm) {
//     if (frm.doc.product_category) {
        
//         frappe.db.get_value("Product Category", frm.doc.product_category, "product_category")
//             .then(r => {
//                 if (r.message && r.message.product_category) {
//                     frm.set_value("custom_title", `${r.message.product_category} :: ${frm.doc.product_group}`);
//                 } else {
//                     frappe.msgprint("No product_category value found in the selected Product Category.");
//                 }
//             });
//     }
// }

// frappe.ui.form.on("Product Group", {
//     product_category: function(frm) {
//         set_custom_title(frm);
        
//     },
// });


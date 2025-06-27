// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt
// function set_custom_title(frm){
//     if(frm.doc.product_group){
//         frappe.db.get_value("Product Group",frm.doc.product_group, "product_group")
//         .then(r=>{
//             if(r.message){
//                 frm.set_value("custom_title",`${r.message.product_group} :: ${frm.doc.product}`)
//             }
//         })
//     }
// }

// frappe.ui.form.on("Product", {
// 	product_group(frm) {
//         set_custom_title(frm);
// 	},
// });

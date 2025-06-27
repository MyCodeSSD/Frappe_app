// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt

// function set_custom_title(frm){
//     if(frm.doc.country){
//         frappe.db.get_value("Country",frm.doc.country, "country_name")
//         .then(r=>{
//             if(r.message){
//                 frm.set_value("custom_title",`${r.message.country_name} :: ${frm.doc.city}`)
//             }
//         })
//     }
// }

// frappe.ui.form.on("City", {
//     onload_post_render: function(frm) {
//         frm.set_value('country', '');
//     },
// 	country(frm) {
//         set_custom_title(frm);
// 	},
// });

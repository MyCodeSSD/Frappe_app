// Separate function to filter cities based on selected country
// function set_city_filter(frm) {
//     if (frm.doc.country) {
//         frm.set_query('city', function() {
//             return {
//                 filters: {
//                     country: frm.doc.country  
//                 }
//             };
//         });
//     }
// }

// frappe.ui.form.on('Company', {
//     country: function(frm) {
//         set_city_filter(frm);
//     }
// });
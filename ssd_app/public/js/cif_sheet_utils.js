// // 🧾 Modal Dialog to Show CIF Sheet Details & PDF
// function showCIFDetails(inv_name, inv_no) {
//     if (!inv_no) {
//         inv_no = inv_name;
//     }

//     frappe.call({
//         method: "ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_cif_sheet_pdf",
//         args: { inv_name },
//         callback: function (r) {
//             if (!r.message) return;
//             const htmlContent = `
//                 <div id="cif-details-a4" style="
//                     width: 20cm;
//                     max-width: 100%;
//                     min-height: 28.7cm;
//                     padding: 0.3cm;
//                     background: white;
//                     font-size: 13px;
//                     box-shadow: 0 0 8px rgba(0,0,0,0.2);"
//                 >${r.message}</div>
//             `;

//             const dialog = new frappe.ui.Dialog({
//                 title: `CIF Sheet: ${inv_no}`,
//                 size: 'large',
//                 primary_action_label: 'PDF',
//                 primary_action() {
//                     window.open(
//                         `/api/method/ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_cif_sheet_pdf?inv_name=${inv_name}&pdf=1`,
//                         '_blank'
//                     );
//                 },
//                 fields: [
//                     {
//                         fieldtype: 'HTML',
//                         fieldname: 'details_html',
//                         options: htmlContent
//                     }
//                 ]
//             });

//             dialog.show();
//         }
//     });
// } 



// // 🧾 Modal Dialog to Show Document Flow
// function showDocFlow(inv_name, inv_no) {
//     frappe.call({
//         method: "ssd_app.my_custom.report.document_receivable.document_receivable.get_doc_flow",
//         args: { inv_name },
//         callback: function (r) {
//             if (r.message) {
//                 const d = new frappe.ui.Dialog({
//                     title: `Document Flow for: ${inv_no}`,
//                     size: 'extra-large',
//                     fields: [
//                         {
//                             fieldtype: 'HTML',
//                             fieldname: 'details_html',
//                             options: `
//                                 <div id="cif-details-a4" style="box-shadow: 0 0 8px rgba(0,0,0,0.2);">
//                                     ${r.message}
//                                 </div>`
//                         }
//                     ]
//                 });

//                 d.show();

//                 // Add refresh button with better styling
//                 const $header = $(d.$wrapper).find('.modal-header');
//                 const refreshBtn = $(`
//                     <button 
//                         type="button" 
//                         class="btn btn-light btn-sm" 
//                         title="Refresh"
//                         style="
//                             margin-left: auto; 
//                             margin-right: 20px; 
//                             display: flex; 
//                             align-items: center; 
//                             gap: 8px;
//                             border: 1px solid #ddd;
//                             padding: 4px 8px;
//                             font-size: 13px;
//                         ">
//                         <span style="font-size: 14px;">🔄</span> Refresh
//                     </button>
//                 `);

//                 refreshBtn.on('click', function(e) {
//                     e.preventDefault();
//                     frappe.call({
//                         method: "ssd_app.my_custom.report.document_receivable.document_receivable.get_doc_flow",
//                         args: { inv_name },
//                         callback: function (res) {
//                             if (res.message) {
//                                 d.set_value('details_html', `
//                                     <div id="cif-details-a4" style="box-shadow: 0 0 8px rgba(0,0,0,0.2);">
//                                         ${res.message}
//                                     </div>`);
//                             }
//                         }
//                     });
//                 });

//                 // Insert before the close (X) button for better spacing
//                 $header.find('.modal-title').after(refreshBtn);
//             }
//         }
//     });
// }

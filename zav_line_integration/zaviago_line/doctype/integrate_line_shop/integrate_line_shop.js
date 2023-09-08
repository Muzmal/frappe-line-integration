// Copyright (c) 2023, Zaviago and contributors
// For license information, please see license.txt

frappe.ui.form.on('Integrate Line Shop', {
	fetch_orders:function(frm){
		if( frm.doc.enable_line_integration == '' ){
			frappe.msgprint("Please Enable API to start")
			return
		}
		if( frm.doc.line_api_key == '' ){
			frappe.msgprint("Please add api key and save before fetching orders")
			return
		}
		frappe.call({
			method: "zav_line_integration.zaviago_line.doctype.integrate_line_shop.integrate_line_shop.ajax_init_fetch_orders",
			type: "POST",
			args: {},
			success: function(r) {
			},
			error: function(r) {},
			always: function(r) {},
			freeze: true,
			freeze_message: "Fetching Orders...",
		});
	},
	fetch_products:function(frm){
		if( frm.doc.enable_line_integration == '' ){
			frappe.msgprint("Please Enable API to start")
			return
		}
		if( frm.doc.line_api_key == '' ){
			frappe.msgprint("Please add api key and save before fetching orders")
			return
		}
		frappe.call({
			method: "zav_line_integration.zaviago_line.doctype.integrate_line_shop.integrate_line_shop.ajax_init_fetch_products",
			type: "POST",
			args: {},
			success: function(r) {
			},
			error: function(r) {},
			always: function(r) {},
			freeze: true,
			freeze_message: "Fetching Products...",
		});
	},
});

# Copyright (c) 2023, Zaviago and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import webbrowser
import requests
from frappe.utils import today
class IntegrateLineShop(Document):
	pass
class handleLineRequests:
	next_cursor=False
	limit = 10
	added_orders=0
	app_details = frappe.get_doc('Integrate Line Shop')
	def fetchOrderDetails(self,orderIDs):
		api_key = self.app_details.get_password('line_api_key')
		payload = {}
		headers = {
		'X-API-KEY': api_key
		}
		for order in orderIDs:
			url = "https://developers-oaplus.line.biz/myshop/v1/orders/"+str(order)
			response = requests.request("GET", url, headers=headers, data=payload)
			data = response.json()
			if( 'code' in data  ):
				print(f"\n\n something is wrong {response} ")
			else:
				self.save_line_order(data)
				print(f"\n\n got order and order is {data} ")
		return
	
	def save_line_order(self,o):
		prev_order = frappe.db.exists({"doctype": "Sales Order", "custom_line_order_id": o['orderNumber']})
		if( prev_order ):
			print(f"\n\n Order is already saved {prev_order}: {o['orderNumber']} \n\n")
			return
		new_order = frappe.new_doc('Sales Order')
		customer_flag = frappe.db.exists("Customer", o['shippingAddress']['recipientName'] )
		if( customer_flag ==None ):
			self.create_customer( o['shippingAddress'],o['shippingAddress']['recipientName'] )
		
		new_order.title=o['shippingAddress']['recipientName']
		new_order.customer=o['shippingAddress']['recipientName']
		new_order.order_type="Sales"
		if( 'checkoutAt' in o ):
			date = o['checkoutAt']
			date = date[:10]
		else:
			date = today()
		print(f" The Date is {date}")
		# date = int(date)/1000
		# date = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d') 
		new_order.delivery_date=date
		new_order.transaction_date=date
		new_order.custom_line_order_id=o['orderNumber']
		 
		# new_order.marketplace_name="Tiktok"
		new_order.marketplace="Line"
		new_order.marketplace_order_number=o['orderNumber']

		new_order.custom_line_order_status = o['orderStatus']
		# add status here

		for product in o['orderItems']:
			if( product['sku'] =='' ):
					product['sku']="no-sku-"+str(product['productId'])
			item_code = product['sku']
			Item = frappe.db.exists("Item", str(item_code))
			if( Item == None ):
				self.create_product(product['name'],product['sku'],"By-product","no")
				p_img = product['imageURL']
				if( p_img ):
					print(f" Got product image { p_img }")
					self.addImageToItem(p_img,product['sku'])
				# ifExist=self.checkIfDocExists( product['productId'] )
				# return str(product['product_id']) + "test"
				# if( ifExist == None ):	
				# 	
			if( product['discountedPrice'] is not None ):
				product['discountedPrice'] =  float( product['price'] )-float( product['discountedPrice'] )
			else:
				product['discountedPrice'] = int( 0 )
			new_order.append("items",{
				"item_code": product['sku'],
				"item_name": product['name'],
				"uom": "Kg",
				"qty": product['quantity'],
				"price_list_rate": product['price'],
				"rate": product['price'],
				"amount": product['price'],
				"stock_uom_rate": product['price'],
				"net_rate": product['price']-product['discountedPrice'],
				"net_amount": product['price']-product['discountedPrice'],
				"billed_amt": product['price']-product['discountedPrice'],
				"valuation_rate":  product['price']-product['discountedPrice'],
				})	
		
		if( 'shipmentPrice' in o ):
			shipmentDetail = o['shipmentDetail']
			shipping = frappe.db.exists("Item", str('item_shipping_cost'))
			if( shipping == None ):	
				self.create_product(shipmentDetail['shipmentCompanyNameTh'],'it-is-overridden',"By-product","yes")
			shipping_provider=shipmentDetail['shipmentCompanyNameTh']
			 
			shipping_fee=o['shipmentPrice']
			# shipping_fee=shipping_fee-payment_info['shipping_fee_platform_discount']
			# shipping_fee=shipping_fee-payment_info['shipping_fee_seller_discount']


			new_order.append("items",{
			"item_code": 'item_shipping_cost',
			"item_name": shipping_provider,
			"uom": "Kg",
			"qty": "1",
			"price_list_rate": shipping_fee,
			"rate": shipping_fee,
			"amount": shipping_fee,
			"stock_uom_rate": shipping_fee,
			"net_rate": shipping_fee,
			"net_amount": shipping_fee,
			"billed_amt": shipping_fee,
			"valuation_rate": shipping_fee,
			})	
		
		response = new_order.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		new_order.submit()
		frappe.db.commit()
		# frappe.msgprint("Created order")
		self.added_orders=self.added_orders+1
		return 
	
	def addImageToItem(self,image_url,item_title):

		new_file = frappe.new_doc("File")
		new_file.file_name=str(item_title)+"_photo.jpeg"

		new_file.attached_to_doctype='Item'
		new_file.attached_to_name=str(item_title)

		new_file.file_url=image_url
		response = new_file.insert(
				ignore_mandatory=True,
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, )
		frappe.db.commit()
		return
	
	def create_product(self,item_name,item_code,item_group,is_shipping):
		item_group="Line Products"
		if( is_shipping=='yes' ):
			item_name='shipping'
			item_code='item_shipping_cost'
		item = frappe.new_doc('Item')
		item.item_name=item_name
		item.item_code=item_code
		item_group = frappe.db.exists("Item Group", item_group )
		if( item_group == None ):
			print( f"  \n \n \n \n  Creating item group   \n \n \n \n ")
			new_item_group = frappe.new_doc('Item Group')
			new_item_group.item_group_name="Line Products"
			new_item_group.parent_item_group="All Item Groups"
			new_item_group.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)

		item.item_group="Line Products"
		response = item.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		frappe.db.commit()
		return

	def create_customer(self,order_address,customer_name):
		customer_group = frappe.db.exists("Customer Group", "Line Customer")
		if( customer_group == None ):
			print( f"  \n \n \n \n  Creating customer group \n \n \n \n ")
			new_customer_group = frappe.new_doc('Customer Group')
			new_customer_group.customer_group_name="Line Customer"
			new_customer_group.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		frappe.db.commit()
		# territory  = frappe.db.exists({"doctype": "Territory", "territory_name": "Thailand"})
		territory = frappe.db.exists("Territory", "Thailand")
		if( territory == None ):
			print( f"  \n \n \n \n  Creating customer territory \n \n \n \n ")
			new_territory = frappe.new_doc('Territory')
			
			new_territory.territory_name="Thailand"
			new_territory.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		frappe.db.commit()
		new_customer = frappe.new_doc('Customer')
		new_customer.customer_name=customer_name
		new_customer.customer_group="Line Customer"
		new_customer.territory="Thailand"
		response = new_customer.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		# frappe.msgprint("Created customer")
		frappe.db.commit()
		country = zav_country_map.get(order_address["country"])
		address_type = "Billing"
		also_shipping=False
		frappe.get_doc(
		{
			"address_line1": order_address["address"] or "Not provided",
			"address_line2": '',
			"address_type": address_type,
			"city": order_address["district"],
			"country": country,
			"county": order_address["subDistrict"] or "Not provided",
			"doctype": "Address",
			
			"phone": order_address["phoneNumber"],
			 
			 
			"links": [{"link_doctype": "Customer", "link_name": customer_name}],
			"is_primary_address": int(address_type == "Billing"),
			"is_shipping_address": int(also_shipping or address_type == "Shipping"),
		}
		).insert(ignore_mandatory=True)
		frappe.db.commit()
		return
	
	def fetch_orders(self):
		url = "https://developers-oaplus.line.biz/myshop/v1/orders"
		payload = {}
		api_key = self.app_details.get_password('line_api_key')
		headers = {
		'X-API-KEY': api_key
		}
		
		response = requests.request("GET", url, headers=headers, data=payload)
		data = response.json()
		if( 'data' in data  ):
			print(f"\n\n got response {data} ")
			order_list=[]
			if ( 'data' in data ) :
				for order in data['data']:
					order_list.append(order['orderNumber'])
				print(f" orders to fetch {order_list} ")
				self.fetchOrderDetails(order_list)
			# if( data['data']['more']==True ):
			# 	print(f"\n\n next cursor is {data['data']['next_cursor']} \n\n")
			# 	self.next_cursor=data['data']['next_cursor']
			# else:
			# 	self.next_cursor=False
		else:
			print(f"\n\n something is wrong {response} ")
		return

	def fetch_products(self):
		url = "https://developers-oaplus.line.biz/myshop/v1/products"
		payload = {}
		api_key = self.app_details.get_password('line_api_key')
		headers = {
		'X-API-KEY': api_key
		}
		
		response = requests.request("GET", url, headers=headers, data=payload)
		data = response.json()
		if( 'data' in data  ):
			print(f"\n\n got response {data} ")
			
			if ( 'data' in data ) :
				for p in data['data']:
					self.saveLineItem(p)
		else:
			print(f"\n\n something is wrong {response} ")
		return
	def saveLineItem(self,p):
		ifExist= frappe.db.exists({"doctype": "LINE MY SHOP Item", "line_my_shop_item_id": p['id']})
		if( ifExist == None ):
			new_product = frappe.new_doc('LINE MY SHOP Item')
			item_group = "Line Products"
			item_group = frappe.db.exists("Item Group", item_group )
			if( item_group == None ):
				print( f"  \n \n \n \n  Creating item group   \n \n \n \n ")
				new_item_group = frappe.new_doc('Item Group')
				new_item_group.item_group_name="Line Products"
				new_item_group.parent_item_group="All Item Groups"
				new_item_group.insert(
					ignore_permissions=True, # ignore write permissions during insert
					ignore_links=True, # ignore Link validation in the document
					ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
					ignore_mandatory=True # insert even if mandatory fields are not set
				)
			new_product.item_group="Line Products"
			new_product.line_my_shop_item_name=p['name']
			k = 0
			is_variable=False
			profileImg=''
			cat_local_display_name=''
			if( 'category' in p ):
				category_list = p['category']
				cat_local_display_name =  category_list['nameEn']
			new_product.category_name=cat_local_display_name
			array_of_images=False
			if( 'imageUrls' in p ):
				images=p['imageUrls']
				k=0
				array_of_images=[]
				for i in images:
					if( k==0 ):
						profileImg = images[0]
					array_of_images.append(i)
					k=k+1
			if( array_of_images ):
				del array_of_images[0]
				for addImg in array_of_images: 	
					print(f" image to add is {addImg} ")
					new_product.append('line_additional_images',{
						"additional_image":addImg,
						"image_preview":addImg
					})
			description=''
			if( 'description' in p ):
				description = p['description']
			brand_name=''
			if( 'brand' in p ):
				brand_name=p['brand']
			seller_sku='...'
			price=''
			l=0
			item_code=''
			if( 'code' in p ):
				item_code=p['code']
			is_variable=False
			if( p['hasOnlyDefaultVariant'] == False ):
				is_variable=True
			new_product.has_variants=is_variable
			new_product.item_name=p['name']
			new_product.document_name_series=p['name']
			# new_product.erpnext_item_name=tiktokProduct['product_name']
			new_product.line_my_shop_item_id=p['id']
			new_product.brand=brand_name
			new_product.item_code_sku=item_code
			new_product.image=profileImg
			if( is_variable == False ):
				defaultVariation=p['variants']
				new_product.stock_piece=defaultVariation[0]['onHandNumber']
				new_product.full_price=defaultVariation[0]['price']
				new_product.sale_price=float(defaultVariation[0]['price']) - float(p['instantDiscount'])
			if( is_variable == True ):
				for variant in p['variants']:
					option_str = ''
					for option in variant['options']:
						option_str = option_str + str( option['name'] ) + " : " +  str( option['value'] ) + " , "
					
					option_str = option_str[:len(option_str) - 2]
					new_product.append('all_variants',{
						"variant_id":variant['id'],
						"variant_barcode":variant['barcode'],
						"variant_sku":variant['sku'],
						"variant_price":variant['price'],
						"variant_discounted_price":variant['discountedPrice'],
						"variant_weight":variant['weight'],
						"variant_options":option_str,
						"variant_onhandnumber":variant['onHandNumber'],
						"variant_available_number":variant['availableNumber'],
					})
			new_product.product_description = description
			new_product.insert(
			ignore_permissions=True, # ignore write permissions during insert
			ignore_links=True, # ignore Link validation in the document
			ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
			ignore_mandatory=True # insert even if mandatory fields are not set
			)
			print("inserted")
			
			frappe.db.commit()
			
		return

@frappe.whitelist( )
def ajax_init_fetch_products():
	app_details = frappe.get_doc('Integrate Line Shop')
	if( app_details.enable_line_integration == True ):
		line_oa_shop = handleLineRequests()
		line_oa_shop.fetch_products( )
		count= 1 
		url = frappe.utils.get_url()+"app/sales-order"
		print(f"\n\n url is {url} ")
		# webbrowser.open( url,new=0 )
	else:
		frappe.throw("Please Enable Line API to start fetching orders")
	return



@frappe.whitelist( )
def ajax_init_fetch_orders():
	app_details = frappe.get_doc('Integrate Line Shop')
	if( app_details.enable_line_integration == True ):
		# if( app_details.maximum_orders_to_fetch and app_details.maximum_orders_to_fetch<=100 ):
		# 	max_number=app_details.maximum_orders_to_fetch
		# else:
		# 	max_number = 100
		
		line_oa_shop = handleLineRequests()
		line_oa_shop.fetch_orders( )
		count= 1 
		# while( line_oa_shop.next_cursor and .added_orders <= max_number ):
		# 	print(f" .added_order is  {.added_orders} ")
		# 	# return
		# 	count=count+1
		# 	print(f"\n\n next cursor is set {count} added orders are {.added_orders}")
		# 	.fetch_orders()
		url = frappe.utils.get_url()+"app/sales-order"
		print(f"\n\n url is {url} ")
		# webbrowser.open( url,new=0 )
	else:
		frappe.throw("Please Enable Line API to start fetching orders")
	return





zav_country_map = {
	"AD": "Andorra",
	"AE": "United Arab Emirates",
	"AF": "Afghanistan",
	"AG": "Antigua and Barbuda",
	"AI": "Anguilla",
	"AL": "Albania",
	"AM": "Armenia",
	"AO": "Angola",
	"AQ": "Antarctica",
	"AR": "Argentina",
	"AS": "American Samoa",
	"AT": "Austria",
	"AU": "Australia",
	"AW": "Aruba",
	"AZ": "Azerbaijan",
	"BA": "Bosnia and Herzegovina",
	"BB": "Barbados",
	"BD": "Bangladesh",
	"BE": "Belgium",
	"BF": "Burkina Faso",
	"BG": "Bulgaria",
	"BH": "Bahrain",
	"BI": "Burundi",
	"BJ": "Benin",
	"BM": "Bermuda",
	"BR": "Brazil",
	"BS": "Bahamas",
	"BT": "Bhutan",
	"BV": "Bouvet Island",
	"BW": "Botswana",
	"BY": "Belarus",
	"BZ": "Belize",
	"CA": "Canada",
	"CF": "Central African Republic",
	"CH": "Switzerland",
	"CI": "Ivory Coast",
	"CK": "Cook Islands",
	"CL": "Chile",
	"CM": "Cameroon",
	"CN": "China",
	"CO": "Colombia",
	"CR": "Costa Rica",
	"CU": "Cuba",
	"CV": "Cape Verde",
	"CX": "Christmas Island",
	"CY": "Cyprus",
	"CZ": "Czech Republic",
	"DE": "Germany",
	"DJ": "Djibouti",
	"DK": "Denmark",
	"DM": "Dominica",
	"DO": "Dominican Republic",
	"DZ": "Algeria",
	"EC": "Ecuador",
	"EE": "Estonia",
	"EG": "Egypt",
	"EH": "Western Sahara",
	"ER": "Eritrea",
	"ES": "Spain",
	"ET": "Ethiopia",
	"FI": "Finland",
	"FJ": "Fiji",
	"FK": "Falkland Islands",
	"FM": "Micronesia",
	"FO": "Faroe Islands",
	"FR": "France",
	"GA": "Gabon",
	"GB": "United Kingdom",
	"GD": "Grenada",
	"GE": "Georgia",
	"GF": "French Guiana",
	"GG": "Guernsey",
	"GH": "Ghana",
	"GI": "Gibraltar",
	"GL": "Greenland",
	"GM": "Gambia",
	"GN": "Guinea",
	"GP": "Guadeloupe",
	"GQ": "Equatorial Guinea",
	"GR": "Greece",
	"GS": "South Georgia and the South Sandwich Islands",
	"GT": "Guatemala",
	"GU": "Guam",
	"GW": "Guinea-Bissau",
	"GY": "Guyana",
	"HK": "Hong Kong",
	"HM": "Heard Island and McDonald Islands",
	"HN": "Honduras",
	"HR": "Croatia",
	"HT": "Haiti",
	"HU": "Hungary",
	"ID": "Indonesia",
	"IE": "Ireland",
	"IL": "Israel",
	"IM": "Isle of Man",
	"IN": "India",
	"IO": "British Indian Ocean Territory",
	"IQ": "Iraq",
	"IR": "Iran",
	"IS": "Iceland",
	"IT": "Italy",
	"JE": "Jersey",
	"JM": "Jamaica",
	"JO": "Jordan",
	"JP": "Japan",
	"KE": "Kenya",
	"KG": "Kyrgyzstan",
	"KH": "Cambodia",
	"KI": "Kiribati",
	"KM": "Comoros",
	"KN": "Saint Kitts and Nevis",
	"KR": "Korea, Republic of",
	"KW": "Kuwait",
	"KY": "Cayman Islands",
	"KZ": "Kazakhstan",
	"LB": "Lebanon",
	"LC": "Saint Lucia",
	"LI": "Liechtenstein",
	"LK": "Sri Lanka",
	"LR": "Liberia",
	"LS": "Lesotho",
	"LT": "Lithuania",
	"LU": "Luxembourg",
	"LV": "Latvia",
	"LY": "Libya",
	"MA": "Morocco",
	"MC": "Monaco",
	"MD": "Moldova, Republic of",
	"ME": "Montenegro",
	"MG": "Madagascar",
	"MH": "Marshall Islands",
	"MK": "Macedonia",
	"ML": "Mali",
	"MM": "Myanmar",
	"MN": "Mongolia",
	"MO": "Macao",
	"MP": "Northern Mariana Islands",
	"MQ": "Martinique",
	"MR": "Mauritania",
	"MS": "Montserrat",
	"MT": "Malta",
	"MU": "Mauritius",
	"MV": "Maldives",
	"MW": "Malawi",
	"MX": "Mexico",
	"MY": "Malaysia",
	"MZ": "Mozambique",
	"NA": "Namibia",
	"NC": "New Caledonia",
	"NE": "Niger",
	"NF": "Norfolk Island",
	"NG": "Nigeria",
	"NI": "Nicaragua",
	"NL": "Netherlands",
	"NO": "Norway",
	"NP": "Nepal",
	"NR": "Nauru",
	"NU": "Niue",
	"NZ": "New Zealand",
	"OM": "Oman",
	"PA": "Panama",
	"PE": "Peru",
	"PF": "French Polynesia",
	"PG": "Papua New Guinea",
	"PH": "Philippines",
	"PK": "Pakistan",
	"PL": "Poland",
	"PM": "Saint Pierre and Miquelon",
	"PN": "Pitcairn",
	"PR": "Puerto Rico",
	"PT": "Portugal",
	"PW": "Palau",
	"PY": "Paraguay",
	"QA": "Qatar",
	"RO": "Romania",
	"RS": "Serbia",
	"RU": "Russian Federation",
	"RW": "Rwanda",
	"SA": "Saudi Arabia",
	"SB": "Solomon Islands",
	"SC": "Seychelles",
	"SD": "Sudan",
	"SE": "Sweden",
	"SG": "Singapore",
	"SI": "Slovenia",
	"SJ": "Svalbard and Jan Mayen",
	"SK": "Slovakia",
	"SL": "Sierra Leone",
	"SM": "San Marino",
	"SN": "Senegal",
	"SO": "Somalia",
	"SR": "Suriname",
	"ST": "Sao Tome and Principe",
	"SV": "El Salvador",
	"SY": "Syria",
	"SZ": "Swaziland",
	"TC": "Turks and Caicos Islands",
	"TD": "Chad",
	"TF": "French Southern Territories",
	"TG": "Togo",
	"TH": "Thailand",
	"TJ": "Tajikistan",
	"TK": "Tokelau",
	"TM": "Turkmenistan",
	"TN": "Tunisia",
	"TO": "Tonga",
	"TR": "Turkey",
	"TT": "Trinidad and Tobago",
	"TV": "Tuvalu",
	"TW": "Taiwan",
	"TZ": "Tanzania",
	"UA": "Ukraine",
	"UG": "Uganda",
	"UM": "United States Minor Outlying Islands",
	"US": "United States",
	"UY": "Uruguay",
	"UZ": "Uzbekistan",
	"VC": "Saint Vincent and the Grenadines",
	"VE": "Venezuela, Bolivarian Republic of",
	"VN": "Vietnam",
	"VU": "Vanuatu",
	"WF": "Wallis and Futuna",
	"WS": "Samoa",
	"YE": "Yemen",
	"YT": "Mayotte",
	"ZA": "South Africa",
	"ZM": "Zambia",
	"ZW": "Zimbabwe",
}

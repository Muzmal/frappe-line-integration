from wsgiref.util import request_uri
import frappe
from urllib.parse import urlencode
import webbrowser
import requests
import json
import unicodedata
import calendar;
import time;
import hashlib
import hmac
import binascii
from frappe.utils import cstr, flt, cint, get_files_path
from PIL import Image
import requests
from zav_line_integration.zaviago_line.doctype.line_shop_with_erpnext.line_shop_with_erpnext import handleLineRequests
import base64


@frappe.whitelist(allow_guest=True)
def webhook_line_shop( **kwargs ):
    # signature = frappe.request.headers.get("Authorization")
    # save_order = saveTiktokData()
    # app_details = frappe.get_doc('Tiktok with ERPnext') 
    # app_secret = app_details.get_password('app_secret')
    handle_line=handleLineRequests()
    response=frappe._dict(kwargs)
    # get_data = frappe.request.get_data()
    # data=response
    print(f"\n\n\n webhook is called data is {response}  and limit is {handle_line.limit} \n\n\n")
    handle_line.save_line_order(response)
    return 

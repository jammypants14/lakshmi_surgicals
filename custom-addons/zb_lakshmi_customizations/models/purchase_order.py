from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
   
    cust_name = fields.Char(string="Customer Name")
    end_cust_name = fields.Char(string="End Customer Name")
    end_cust_po_number = fields.Char(string="End Customer PO Number")
    cust_po_number = fields.Char(string="PO Number")
    cust_po_date = fields.Char(string="PO Date")
    cust_quote_id = fields.Char(string="Quote ID")
    cust_service_id = fields.Char(string="Service ID")
    cust_tendor_no = fields.Char(string="Tendor No & Name")

    
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
   
    cust_name = fields.Char(string="Customer Name")
    end_cust_name = fields.Char(string="End Customer Name")
    end_cust_po_number = fields.Char(string="Customer PO Number")
    cust_po_number = fields.Char(string="PO Number")
    cust_po_date = fields.Char(string="PO Date")
    cust_quote_id = fields.Char(string="Quote ID")
    cust_service_id = fields.Char(string="Service ID")
    cust_tendor_no = fields.Char(string="Tendor No & Name")
    
    @api.onchange('order_line')
    def _onchange_order_line_sl_no(self):
        for idx, line in enumerate(self.order_line, 1):
            line.sl_no = idx

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    sl_no = fields.Integer("Sl No.")
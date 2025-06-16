from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



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
    
    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        self._onchange_order_line_sl_no()
        return res
    
    def resequence_po_lines_by_sale_order(self):
        for order in self:
            if not order.origin:
                continue

            sale_order = self.env['sale.order'].search([('name', '=', order.origin)], limit=1)
            if not sale_order:
                continue

            # Sort SO lines by serial_no
            so_lines = sale_order.order_line.sorted(key=lambda l: l.sl_no or 9999)
            po_lines = list(order.order_line)
            matched_po_lines = []

            for so_line in so_lines:
                # Match same product (and optionally quantity)
                match = next((
                    po_line for po_line in po_lines
                    if po_line not in matched_po_lines
                    and po_line.product_id.id == so_line.product_id.id
                ), None)
                if match:
                    matched_po_lines.append(match)

            # Add remaining unmatched lines at the end
            unmatched_lines = [line for line in po_lines if line not in matched_po_lines]
            final_order = matched_po_lines + unmatched_lines

            # Reassign sequence numbers
            for index, line in enumerate(final_order):
                line.sequence = index



    
    @api.onchange('order_line')
    def _onchange_order_line_sl_no(self):
        for idx, line in enumerate(self.order_line.sorted('sequence'), 1):
            line.sl_no = idx
    

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    sl_no = fields.Integer("Sl No.")
    
    
        
        
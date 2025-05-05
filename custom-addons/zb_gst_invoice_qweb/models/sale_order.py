from odoo import models, fields, api

class SaleOrder(models.Model):
	
	_inherit = "sale.order"
	
	def _create_invoices(self, grouped=False, final=False, date=None):
		invoices = super()._create_invoices(grouped=grouped, final=final, date=date)
		for invoice in invoices:
			for line in invoice.invoice_line_ids:
				line._onchange_name_set_editable_label()
		return invoices

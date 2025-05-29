from odoo import api, fields, models, _


class StockRule(models.Model):
    _inherit = 'stock.rule'


    # customization done for lakshmi surgicals to not merge similar products to one from sale order lines to purchase order lines
    @api.model
    def _merge_procurements(self, procurements_to_merge):
	    """
	    Instead of merging procurements into one, apply shared fields like
	    move_dest_ids and orderpoint_id to each procurement in the group.
	    """
	    synced_procurements = []
	    for procurements in procurements_to_merge:
	        # Prepare shared values
	        move_dest_ids = self.env['stock.move']
	        orderpoint_id = self.env['stock.warehouse.orderpoint']
	        for procurement in procurements:
	            if procurement.values.get('move_dest_ids'):
	                move_dest_ids |= procurement.values['move_dest_ids']
	            if not orderpoint_id and procurement.values.get('orderpoint_id'):
	                orderpoint_id = procurement.values['orderpoint_id']
	        
	        # Now apply shared values to each procurement individually
	        for procurement in procurements:
	            values = dict(procurement.values)
	            values.update({
	                'move_dest_ids': move_dest_ids,
	                'orderpoint_id': orderpoint_id,
	            })
	            synced_proc = self.env['procurement.group'].Procurement(
	                procurement.product_id, procurement.product_qty, procurement.product_uom,
	                procurement.location_id, procurement.name, procurement.origin,
	                procurement.company_id, values
	            )
	            synced_procurements.append(synced_proc)
	    return synced_procurements

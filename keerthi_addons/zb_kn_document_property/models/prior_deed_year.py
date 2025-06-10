from odoo import models, fields, api
class PriorDeedYear(models.Model):
    _name = 'prior.deed.year'
    _description = 'Prior Deed Year'

    name = fields.Char(string='Prior Deed Year', required=True)
    
    @api.model
    def create_years_1947_to_2025(self):
        existing_years = self.search([]).mapped('name')
        for year in range(1947, 2026):
            year_str = str(year)
            if year_str not in existing_years:
                self.create({'name': year_str})
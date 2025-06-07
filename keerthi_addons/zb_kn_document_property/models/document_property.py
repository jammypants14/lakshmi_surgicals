from odoo import models, fields,api
from datetime import datetime

class DocumentProperty(models.Model):
    _name = 'document.property'
    _description = 'Property Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    no = fields.Char(string='No',readonly=True)
    company_id = fields.Many2one('res.company', string='Company')
    seller_name = fields.Char(string='Seller Name')
    deed_no = fields.Char(string='Deed No')
    #deed_year = fields.Char(string='Deed Year')
    old_survey_sy_no = fields.Char(string='Old Survey Sy No')
    old_survey_sub_division = fields.Char(string='Old Survey Sub Division')
    re_survey_sy_no = fields.Char(string='Re Survey Sy No')
    re_survey_sub_division = fields.Char(string='Re Survey Sub Division')
    extent_area = fields.Char(string='Extent Area')
    #prior_deed_no = fields.Char(string='Prior Deed No')
    #prior_deed_year = fields.Char(string='Prior Deed Year')
    thandaper = fields.Char(string='Thandaper')
    block = fields.Char(string='Block')
    village_id = fields.Many2one('document.village', string='Village')
    sub_registrar_id = fields.Many2one('sub.registrar', string='Sub Registrar')
    building_no = fields.Char(string='Building No') 
    building_ward = fields.Char(string='Building Ward')
    ec_upto = fields.Char(string='EC Upto')
    water_connection_no = fields.Char(string='Water Connection No')
    electricity_consumer_no = fields.Char(string='Electricity Consumer No')
    hypothecated_id = fields.Many2one('document.hypothecated', string='Hypothecated')
    attachment = fields.Binary(string='Attachment',attachment=True)
    attachment_name = fields.Char(string='File Name')
    hectare = fields.Char(string='Heactare/Are/Sqaure meter')
    are = fields.Char(string='Are')
    sqaure_meter = fields.Char(string='Sqaure meter')
    
    bldg_tax_validity = fields.Date(string='Building Tax Validity')
    land_tax_validity = fields.Date(string='Land Tax Validity')
    seq_generated = fields.Boolean('Seq Generated',default=False)
    prior_deed_no_ids = fields.Many2many(
        'prior.deed.no',
        'document_property_deed_no_rel',
        'property_id',
        'deed_no_id',
        string='Prior Deed Numbers'
    )

    prior_deed_year_ids = fields.Many2many(
        'prior.deed.year',
        'document_property_deed_year_rel',
        'property_id',
        'deed_year_id',
        string='Prior Deed Years'
    )
    
    def _get_year_selection(self):
        current_year = datetime.now().year
        return [(str(y), str(y)) for y in range(current_year - 10, current_year + 1)]
        
    deed_year = fields.Selection(
	    selection=_get_year_selection,
	    string='Deed Year'
	)
    
    @api.model
    def create(self, vals):
        vals['no']= self.env['ir.sequence'].next_by_code('document.property')
        vals['seq_generated'] = True
        res=super(DocumentProperty, self).create(vals)
        return res

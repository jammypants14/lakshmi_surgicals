from odoo import models, fields,api
from datetime import datetime

class DocumentProperty(models.Model):
    _name = 'document.property'
    _description = 'Property Document'
    _rec_name = 'no'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    no = fields.Char(string='No',readonly=True)
    company_id = fields.Many2one('res.company', string='Company')
    seller_name = fields.Char(string='Seller Name')
    deed_no = fields.Char(string='Deed No')
    #deed_year = fields.Char(string='Deed Year')
    old_survey_sy_no = fields.Char(string='Old Survey No')
    old_survey_sub_division = fields.Char(string='Old Survey Sub Div No.')
    re_survey_sy_no = fields.Char(string='Re Survey No')
    re_survey_sub_division = fields.Char(string='Re Survey Sub Div No.')
    #extent_area = fields.Char(string='Extent Area')
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
    remarks = fields.Text(string='Remarks')
    survey_remarks = fields.Text(string='Survey Remarks')
    building_remarks = fields.Text(string='Building Remarks')
    
    
    bldg_tax_validity = fields.Date(string='Building Tax Validity')
    land_tax_validity = fields.Date(string='Land Tax Validity')
    seq_generated = fields.Boolean('Seq Generated',default=False)
    prior_deed_no_ids = fields.Many2many(
        'prior.deed.no',
        'document_property_deed_no_rel',
        'property_id',
        'deed_no_id',
        string='Prior Deed Numbers / Years'
    )

    prior_deed_year_ids = fields.Many2many(
        'prior.deed.year',
        'document_property_deed_year_rel',
        'property_id',
        'deed_year_id',
        string='Prior Deed Years'
    )
    
    survey_details_ids = fields.One2many('survey.details', 'property_id',  string="Survey Details")
    building_details_ids = fields.One2many('building.details', 'property_id', string='Building Details')
    total_survey_area = fields.Float(string='Total Survey Area', compute='_compute_total_survey_area', store=True)
    total_building_area = fields.Float(string='Total Building Area', compute='_compute_total_building_area', store=True)
    
    @api.depends('building_details_ids.square_feet')
    def _compute_total_building_area(self):
        for record in self:
            record.total_building_area = sum(line.square_feet for line in record.building_details_ids)
    
    @api.depends('survey_details_ids.total_value')
    def _compute_total_survey_area(self):
        for record in self:
            record.total_survey_area = sum(line.total_value for line in record.survey_details_ids)
    
    def _get_year_selection(self):
        return [(str(y), str(y)) for y in range(1947, 2026)]
        
    deed_year = fields.Selection(
	    selection=_get_year_selection,
	    string='Deed Year'
	)
    
    @api.onchange('survey_details_ids')
    def _onchange_sl_no_update(self):
        for prop in self:
            for idx, line in enumerate(prop.survey_details_ids, 1):
                line.sl_no = idx
    
    
    @api.onchange('building_details_ids')
    def _onchange_sl_no__building_update(self):
        for prop in self:
            for idx, line in enumerate(prop.building_details_ids, 1):
                line.sl_no = idx
    
    @api.model
    def create(self, vals):
        vals['no']= self.env['ir.sequence'].next_by_code('document.property')
        vals['seq_generated'] = True
        res=super(DocumentProperty, self).create(vals)
        return res

        
class SurveyDetails(models.Model):
    _name = 'survey.details'
    _description = 'Survey Details'
    
    sl_no = fields.Integer(string='Sl No',readonly=True)
    village_id = fields.Many2one('document.village', string='Village Name')
    surno = fields.Char(string='Surno')
    sbdno = fields.Char(string='Sbdno')
    rsurno = fields.Char(string='RSurno')
    rsbdno = fields.Char(string='RSbdno')
    #unit = fields.Selection([('sq_meter', 'Square Meter'),('hectare', 'Hectare'),('acre', 'Acre'),('sq_ft', 'Square Foot'),('sq_yd', 'Square Yard'),('cent', 'Cent'),], string="Unit")
    unit = fields.Char(string='Unit')
    hr_acre = fields.Char(string='Hr/Acre')
    ar_cent = fields.Char(string='Ar/Cent')
    sqmtr = fields.Char(string='SqM')
    property_id = fields.Many2one('document.property', string='Property')  
    total_value = fields.Float(string='Total', compute='_compute_total_value')       
    
    @api.model
    def create(self, vals):
        record = super(SurveyDetails, self).create(vals)
        if record.property_id:
            record.property_id._onchange_sl_no_update()
        return record

    def unlink(self):
        properties = self.mapped('property_id')
        res = super(SurveyDetails, self).unlink()
        for prop in properties:
            prop._onchange_sl_no_update()
        return res
    
    @api.depends('ar_cent', 'sqmtr')
    def _compute_total_value(self):
        for rec in self:
            try:
                ar_str = str(int(float(rec.ar_cent or 0)))
                sq_str = str(int(float(rec.sqmtr or 0))).rstrip('0') or '0'
                rec.total_value = float(f"{ar_str}.{sq_str}")
            except (ValueError, TypeError):
                rec.total_value = 0.0
                
    @api.onchange('property_id')
    def _onchange_property_id(self):
        # Set serial number
        if self.property_id:
            existing_lines = self.property_id.survey_details_ids
            self.sl_no = len(existing_lines) + 1

    @api.onchange('sl_no')
    def _onchange_sl_no_set_village(self):
        if self.sl_no > 1 and self.property_id:
            first_line = self.property_id.survey_details_ids.filtered(lambda r: r.sl_no == 1)
            if first_line:
                self.village_id = first_line.village_id
    


class BuildingDetails(models.Model):
    _name = 'building.details'
    _description = 'Building Details'

    sl_no = fields.Integer(string='Sl No', readonly=True)
    building_no = fields.Char(string='Building No')
    building_ward = fields.Char(string='Building Ward')
    location = fields.Char(string='Location')
    square_feet = fields.Float(string='Square Feet')
    bldng_tax_validity = fields.Date(string='Building Tax Validity')
    property_id = fields.Many2one('document.property', string='Property')
    
    @api.model
    def create(self, vals):
        record = super(BuildingDetails, self).create(vals)
        if record.property_id:
            record.property_id._onchange_sl_no__building_update()
        return record

    def unlink(self):
        properties = self.mapped('property_id')
        res = super(BuildingDetails, self).unlink()
        for prop in properties:
            prop._onchange_sl_no__building_update()
        return res
    

    

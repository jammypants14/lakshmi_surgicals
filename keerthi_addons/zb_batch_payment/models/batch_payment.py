from odoo import fields, models, api, _
import werkzeug

class BatchPayment(models.Model):
    _name = "batch.payment"
    _description = "Batch Payment"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Reference", default="New")
    date = fields.Date(string="Date", tracking=True)
    total = fields.Float(string="Total", compute="compute_total", store=True, tracking=True)
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 required=True,
                                 domain=[('type', 'in', ['bank', 'cash'])], tracking=True
                                 )
    state = fields.Selection([
        ('new', 'Draft'),
        ('confirm', 'Confirmed'),
        ('sent', 'Submitted To Bank'),
        ('done', 'Processed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='new', tracking=True)
    batch_option = fields.Selection([
        ('employee', 'Employee'),
        ('vendor', 'Vendor')
    ], string="Batch", tracking=True)
    batch_payment_line_ids = fields.One2many('batch.payment.lines','batch_payment_id',string="Create Batch Line")
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('batch.payment.code') or '/'
        return super(BatchPayment, self).create(vals)
        
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'   
    def action_sent(self):
        for rec in self:
            rec.state = 'sent'
            
    def action_done(self):
        all_payment_ids = []
        move_ids_list = []
        if self.batch_payment_line_ids:
            for line in self.batch_payment_line_ids:
                line.confirm()
                all_payment_ids.append(line.payment_id.id)
                
                # Code to write ref in account move
                if line.type == 'expense':
                    if line.expense_ids:
                        for exp in line.expense_ids:
                            if exp.account_move_ids and exp.account_move_ids.line_ids:
                                for mv_line in exp.account_move_ids.line_ids:
                                    if mv_line.move_id and mv_line.move_id not in move_ids_list:
                                        move_ids_list.append(mv_line.move_id)
        # Code to write ref in account move                                
        if move_ids_list:
            for move in move_ids_list:
                move.write({'ref': move.ref + ' - ' + self.name})
        self.state = 'done'
                
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'  
    def action_reset_draft(self):
        for rec in self:
            rec.state = 'new'

    @api.depends('batch_payment_line_ids.expense_ids', 'batch_payment_line_ids.expense_ids.total_amount')
    def compute_total(self):
        for record in self:
            total = 0.0
            for line in record.batch_payment_line_ids:
                total += sum(line.expense_ids.mapped('total_amount'))
            record.total = total

    def action_view_payments(self):
        self.ensure_one()

        partner_ids = []
        for line in self.batch_payment_line_ids:
            if line.vendor_id:
                partner_ids.append(line.vendor_id.id)
            elif line.employee_id and line.employee_id.id:
                partner_ids.append(line.employee_id.id)

        payment_ids = self.batch_payment_line_ids.mapped('payment_id').filtered(lambda p: p.id).ids
        domain = [('id', 'in', payment_ids)] if payment_ids else [('id', '=', 0)]



        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Payments',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
            'target': 'current',
        }


class BatchPaymentLines(models.Model):
    _name = "batch.payment.lines"
    _description = "Batch Payment Lines"

    batch_type = fields.Selection([
        ('employee','Employee'),
        ('vendor','Vendor')
    ],string="Batch")
    vendor_id = fields.Many2one('res.partner',string="Vendor")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    type = fields.Selection([('expense', 'Expense Sheet'), ('request', 'Payment Request'),
                             ('reconcile', 'Reconcile Move Line'),
                             ('direct_entry', 'Direct Journal Entry')], required=True, default='expense')
    account = fields.Many2one('account.account',string="Account")
    expense_ids = fields.Many2many('hr.expense.sheet','account_expense_relation','ac_id','exp_id', string="Expenses")
    payment_method_id = fields.Many2one('account.journal', string="Journal")
    payment_methods_id = fields.Many2one('account.payment.method', string="Payment Method")
    batch_payment_id = fields.Many2one('batch.payment', string="Batch Payment One2many")
    payment_id = fields.Many2one('account.payment', string="Payment")
    amount = fields.Float('Amount', compute='compute_total_payment_amount')
    company_id = fields.Many2one('res.company', related='payment_method_id.company_id', string='Company', readonly=True,
                                required=True)
    bill_ids = fields.Many2many('account.move','batch_line_id',string="Bills")    
      
    @api.depends('expense_ids')
    def compute_total_payment_amount(self):
        for record in self:
            record.amount = 0
            if record.expense_ids and record.type == 'expense':
                for expense in record.expense_ids:
                    record.amount += expense.total_amount
    
    
    def get_payment_vals(self):
        invoice_ids = []
        partner = self.employee_id.user_id.partner_id or self.vendor_id
        if self.batch_type == 'employee':
	        for exp in self.expense_ids:
	            if exp.account_move_ids:
	                invoice_ids += exp.account_move_ids.ids
	            else:
	                move = self.env['account.move'].search([('expense_sheet_id', '=', exp.id)], limit=1)
	                if move:
	                    invoice_ids.append(move.id)
        elif self.batch_type == 'vendor':
	        invoice_ids = self.bill_ids.ids
		        
        return {
                    'partner_id': partner.id,
                    'amount': self.amount,
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'payment_method_id': self.payment_methods_id.id,
                    'journal_id': self.payment_method_id.id,
                    'date': self.batch_payment_id and self.batch_payment_id.date or False,
                    'memo': self.batch_payment_id.name or '',
                    'invoice_ids': [(6, 0, invoice_ids)],
                    
                }
    
    def confirm(self):
	    if self.amount <= 0 and self.type != 'reconcile':
	        raise ValidationError("Cannot create Journal Entry for this amount")
	    if not self.batch_payment_id or not self.batch_payment_id.date:
	        raise ValidationError("Date is required in batch for payment creation")
	
	    payment = self.env['account.payment'].create(self.get_payment_vals())
	    payment.action_post()
	    payment.action_validate()
	    self.payment_id = payment.id
	
	    partner = self.employee_id.user_id.partner_id or self.vendor_id
        payment_lines = payment.move_id.line_ids.filtered(
            lambda l: l.debit > 0 and l.account_id.account_type == 'liability_payable'
	    )
	
	    if self.batch_type == 'vendor':
	        self.reconcile_bill_lines(payment_lines, partner)
	    elif self.batch_type == 'employee':
	        self.reconcile_expense_lines(payment_lines, partner)

		    
    def reconsile_expense_lines(self,payment_lines, partner ):
        expense_lines = payment.invoice_ids.mapped('line_ids').filtered(
                 lambda l: l.credit > 0 and l.account_id.account_type == 'liability_payable'
            )
	    payment_lines = payment_lines.filtered(lambda l: l.partner_id.id == partner.id)
	    expense_lines = expense_lines.filtered(lambda l: l.partner_id.id == partner.id)
	
	    lines_to_reconcile = payment_lines | expense_lines
	    if lines_to_reconcile:
	        lines_to_reconcile.reconcile()

    def reconcile_bill_lines(self, payment_lines, partner):
	    bill_lines = self.bill_ids.mapped('line_ids').filtered(
	        lambda l: l.credit > 0 and l.account_id.account_type == 'liability_payable' and l.partner_id.id == partner.id
	    )
	    lines_to_reconcile = payment_lines | bill_lines
	    if lines_to_reconcile:
	        lines_to_reconcile.reconcile()

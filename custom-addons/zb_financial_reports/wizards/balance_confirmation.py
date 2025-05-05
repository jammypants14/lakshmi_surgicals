from odoo import fields, models, api

class BalanceConfirmationReport(models.TransientModel):
    _name = 'balance.confirmation.wiz'
    _description = 'Balance Confirmation Report'

    date = fields.Date("Date",required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    partner_ids = fields.Many2many('res.partner')
    
    # def get_partner_balance(self, partner, date):
#         balance = 0.0
#         if not date or not partner:
#             return balance
    
#         # Build the query using the updated methods
#         domain = [
# 	        ('parent_state', '=', 'posted'),
# 	        ('company_id', 'child_of', self.company_id.root_id.id),
# 	        ('partner_id', '=', partner.id),
# 	        ('date', '<=', date),
# 	        ('reconciled', '=', False),
# 	    ]

#         # Build the query using the ORM
#         move_line_obj = self.env['account.move.line']
#         query = move_line_obj.search(domain)

#         # Filter on account types using SQL directly
#         query = query.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

#         # Calculate the sum of residual amounts
#         balance = sum(query.mapped('amount_residual'))
#         return balance
    
#     def get_partner_balance(self,partner,date):
#         balance = 0.0
#         if not date or not partner:
#             return balance
#         tables, where_clause, where_params = self.env['account.move.line']._where_calc([
#             ('parent_state', '=', 'posted'),
#             ('company_id', 'child_of', self.company_id.root_id.id),
#             ('partner_id', '=', partner.id),
#             ('date', '<=', date),
#             ('reconciled', '=', False),
#         ]).get_sql()
#         if where_clause:
#             where_clause = 'AND ' + where_clause
#         self._cr.execute(f"""
#             SELECT SUM(account_move_line.amount_residual)
#             FROM {tables}
#             LEFT JOIN account_account a ON (account_move_line.account_id = a.id)
#             WHERE a.account_type IN ('asset_receivable', 'liability_payable')
#             {where_clause}
#         """, where_params)
#         balance = self._cr.fetchone()[0] or 0.0
#         return balance    
        
    def action_balance_confirmation_report(self):
        # active_ids = self.env.context.get('active_ids')
        # partners = self.env['res.partner'].browse(active_ids)
        # data = {
        #     'partners': partners.ids,
        #     # 'report_name':'Balance Confirmation'.with_context(data=data)
        # }
        return self.env.ref('zb_financial_reports.action_balance_confirmation_saudi').report_action(self)
    
    
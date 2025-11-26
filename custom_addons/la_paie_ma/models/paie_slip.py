# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class PaieSlip(models.Model):
    _name = 'paie.slip'
    _description = 'Payslip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, id desc'

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        readonly=False,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
    )
    contract_id = fields.Many2one(
        'hr.contract',
        string='Contract',
        compute='_compute_contract_id',
        store=True,
        readonly=False,
    )
    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=lambda self: fields.Date.end_of(fields.Date.today(), 'month'),
    )
    wage = fields.Monetary(
        string='Wage',
        currency_field='currency_id',
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    line_ids = fields.One2many(
        'paie.slip.line',
        'slip_id',
        string='Payslip Lines',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_name(self):
        for slip in self:
            if slip.employee_id and slip.date_from and slip.date_to:
                slip.name = _('Payslip of %(employee)s from %(date_from)s to %(date_to)s',
                             employee=slip.employee_id.name,
                             date_from=slip.date_from,
                             date_to=slip.date_to)
            else:
                slip.name = _('New Payslip')

    @api.depends('employee_id')
    def _compute_contract_id(self):
        for slip in self:
            if slip.employee_id:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', slip.employee_id.id),
                    ('state', '=', 'open'),
                ], limit=1)
                slip.contract_id = contract
            else:
                slip.contract_id = False

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            self.wage = self.contract_id.wage

    def action_compute_sheet(self):
        """Compute the payslip by evaluating all salary rules."""
        for slip in self:
            if slip.state == 'done':
                raise UserError(_("Cannot recompute a confirmed payslip."))

            # Clear existing lines
            slip.line_ids.unlink()

            # Get all active rules ordered by sequence
            rules = self.env['paie.rule'].search([('active', '=', True)], order='sequence, id')

            if not rules:
                raise UserError(_("No salary rules found. Please configure salary rules first."))

            # Initialize category totals
            categories = {
                'BASIC': 0.0,
                'GROSS': 0.0,
                'DEDUCTION': 0.0,
                'NET': 0.0,
            }

            # Create a mock contract object if no contract
            class MockContract:
                def __init__(self, wage):
                    self.wage = wage

            contract = slip.contract_id or MockContract(slip.wage or 0.0)

            # Process each rule
            lines_vals = []
            for rule in rules:
                # Prepare evaluation context
                localdict = {
                    'contract': contract,
                    'categories': categories,
                    'payslip': slip,
                    'employee': slip.employee_id,
                    'result': 0.0,
                    'min': min,
                    'max': max,
                }

                # Execute the Python code
                try:
                    safe_eval(
                        rule.python_code or 'result = 0',
                        globals_dict=localdict,
                        locals_dict={},
                        mode='exec',
                        nocopy=True,
                    )
                    result = localdict.get('result', 0.0)
                except Exception as e:
                    raise UserError(_("Error computing rule '%(rule)s': %(error)s",
                                    rule=rule.name, error=str(e)))

                # Update category totals
                category_key = rule.category.upper()
                if category_key in categories:
                    categories[category_key] += result

                # Prepare line values
                lines_vals.append({
                    'slip_id': slip.id,
                    'rule_id': rule.id,
                    'name': rule.name,
                    'code': rule.code,
                    'sequence': rule.sequence,
                    'total': result,
                })

            # Create all lines at once
            self.env['paie.slip.line'].create(lines_vals)

        return True

    def action_confirm(self):
        """Confirm the payslip."""
        for slip in self:
            if slip.state == 'draft':
                if not slip.line_ids:
                    raise UserError(_("Please compute the payslip before confirming."))
                slip.state = 'done'
        return True

    def action_set_to_draft(self):
        """Set the payslip back to draft."""
        for slip in self:
            if slip.state == 'done':
                slip.state = 'draft'
        return True

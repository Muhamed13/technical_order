from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TechnicalOrder(models.Model):
    _name = 'technical.order'
    _description = "Technical Order"

    sequence = fields.Char(string="Sequence", default="New", copy=False)
    request_name = fields.Char(string="Request Name", required=True)
    requested_by = fields.Many2one('res.users', string="Requested By",
                                   required=True, default=lambda self: self.env.user)
    customer_id = fields.Many2one('res.partner', string="Customer", required=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.today)
    end_date = fields.Date(string="End Date")
    rejection_reason = fields.Text(string="Rejection Reason")
    order_line_ids = fields.One2many('technical.order.line',
                                      'order_id', string="OrderLines")
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_be_approved', 'To Be Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel'),

    ], default='draft', string="State")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
           Validate that the end date is not earlier than the start date.
        """
        for rec in self:
            if rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(
                    _("End Date cannot be earlier than Start Date.")
                )

    @api.depends('order_line_ids.line_total')
    def _compute_total_price(self):
        """Compute the total amount of the technical order."""
        for order in self:
            order.total_price = sum(order.order_line_ids.mapped('line_total'))


    @api.model
    def create(self, vals):
        """Generate sequence before creating a technical order."""

        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('technical.order')

        return super().create(vals)

    def action_to_be_approved(self):
        self.write({
            'state': 'to_be_approved'
        })

    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })

    def action_approved(self):
        """
        Approve the technical order and notify all Sales Managers by email.
        """

        self.ensure_one()

        self.write({
            'state': 'approved'
        })

        group = self.env.ref('sales_team.group_sale_manager')

        for user in group.users:
            email = user.partner_id.email

            if not email:
                continue

            body_html = f"""
            <p>Hello {user.name},</p>

            <p>
                Technical Order <strong>{self.request_name}</strong> has been approved.
            </p>

            <p>
                <strong>Customer:</strong> {self.customer_id.name}<br/>
                <strong>Start Date:</strong> {self.start_date}<br/>
                <strong>End Date:</strong> {self.end_date}
            </p>

            <p>Regards,</p>
            """

            mail = self.env['mail.mail'].create({
                'email_to': email,
                'subject': f'Technical Order {self.request_name} Approved',
                'body_html': body_html,
            })

            mail.send()

    def action_draft(self):
        self.write({
            'state': 'draft'
        })



class TechnicalOrderLine(models.Model):
    _name = 'technical.order.line'
    _description = 'Technical Order Line'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", default=1)
    price = fields.Float(string="Price")
    line_total = fields.Float(string="Total Price", compute="_compute_line_total", store=True)
    order_id = fields.Many2one('technical.order', string="Order", required=True, ondelete='cascade')

    @api.depends('quantity', 'price')
    def _compute_line_total(self):
        """Compute the total amount for each technical order line."""
        for line in self:
            line.line_total = line.quantity * line.price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update the line price when the selected product changes."""
        if self.product_id:
            self.price = self.product_id.list_price

    @api.constrains('quantity')
    def _check_quantity(self):
        """Ensure the quantity is greater than zero."""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(
                    _("Quantity must be greater than 0.")
                )
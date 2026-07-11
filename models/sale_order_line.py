from odoo import models, api,_
from odoo.exceptions import ValidationError


class SalesOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_id', 'product_uom_qty', 'order_id')
    def _check_requested_quantity(self):
        """
        Validate that the requested sales order quantity does not exceed
        the remaining quantity available in the related technical order.
        """

        for line in self:
            technical_order = line.order_id.technical_order_id

            if not technical_order:
                continue

            technical_line = technical_order.order_line_ids.filtered(
                lambda l: l.product_id == line.product_id
            )

            if not technical_line:
                continue

            confirmed_sale_orders = technical_order.sale_order_ids.filtered(
                lambda so: so.state == 'sale'
            )

            sale_order_lines = confirmed_sale_orders.mapped('order_line')

            product_lines = sale_order_lines.filtered(
                lambda l: l.product_id == line.product_id
            )

            other_lines = product_lines.filtered(
                lambda l: l != line
            )

            requested_qty = sum(
                other_lines.mapped('product_uom_qty')
            ) + line.product_uom_qty

            allowed_qty = technical_line.quantity

            if requested_qty > allowed_qty:
                raise ValidationError(
                    _("You cannot request more than the remaining quantity available in the related Technical Order.")
                )
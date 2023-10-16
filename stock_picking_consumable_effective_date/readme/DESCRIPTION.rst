This module adds a computed field show_consumable_date to stock.picking.
When all the items in the picking are consumable products, the accounting_date field
will be displayed as 'Consumable Effective Date'.
If certain transfers in Odoo cannot be confirmed on the same date as the products are
received or delivered, the accounting_date for consumable products will be used to
record the actual transfer date.

Background
~~~~~~~~~~

For companies that must accurately record incoming and outgoing transfers date,
regardless of whether a product is designated as a Storable Product,
it becomes challenging to capture the actual transfer date when the transfer occurs at a later time,
as in Odoo's default behavior, the effective date is set to the confirmation date of the records and cannot be modified.

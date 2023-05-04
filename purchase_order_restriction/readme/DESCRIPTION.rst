This module does the following:
- Adds restrict_purchase_order boolean field in purchase order form for Purchase Manager to mark that the record is restricted
- Adds new record rule to restrict Purchase Users to have access only to record that have restrict_purchase_order value is False
- Adds restrict_purchase_order to RFQ and Purchase Orders Tree view for Purchase Manager to monitor which records is currently restricted on the list

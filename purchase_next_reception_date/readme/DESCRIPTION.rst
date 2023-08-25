This module adds next_reception_date in purchase order to recognize the upcoming receipt date of the orders.

Background
~~~~~~~~~~

For purchase orders with multiple order lines, each having different 'date_planned' values,
the expected arrival date field will not display the next order line's 'date_planned' after the first reception has been completed.
Due to this condition, purchase users are required to open each record individually to see the upcoming receipt dates of the other order lines.

The 'Next Reception Date' field is designed to provide information about the upcoming reception date of orders at a glance in the purchase order list view.

This module add acceptance_date field on stock move. When Accounting Date is specified in the stock picking,
the acceptance_date field will be populated with the value of the accounting date.
Otherwise, the acceptance_date field will be filled with the Scheduled Date.
In order to satisfy the requirement, this module changed the Scheduled Date field type to Date in stock picking.

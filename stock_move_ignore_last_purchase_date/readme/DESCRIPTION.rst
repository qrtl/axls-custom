This module adds the *Ignore Last Purchase Date* field to the stock move to adjust
assigning to last_purchase_date of product.

Background
~~~~~~~~~~

Certain receipts might be validated later than their actual reception date.
Therefore, the "last purchase date" should not always correspond to the validation date.
In such cases, instead of assigning the validation date to the "last purchase date",
the "man last purchase date" should be used instead.

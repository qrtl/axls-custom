This module adds a new group group_create_bill_allowed, and hides
"Create Bill" button of the purchase order form for users without
group_account_invoice or group_create_bill_allowed.

This functionality intends to prevent the situation where purchase users
accidentally create vendor bills from purchase orders, when bills are
supposed to be created by authorized users.

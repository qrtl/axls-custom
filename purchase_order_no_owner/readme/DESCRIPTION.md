This module is designed to prevent users from accidentally forgetting to
input owner information on a purchase order by implementing an order
confirmation prevention if the owner_id is not filled in. If the order
is not associated with any specific owner, users have the option to set
the no_owner field to "True" instead.

## Background

Users may unintentionally overlook filling out the owner_id field when
creating a purchase order for inventory items that should be linked to a
specific owner and subsequently confirm the order. Once the PO is
confirmed, users are not be able to edit the owner_id field to fill in
the correct owner.

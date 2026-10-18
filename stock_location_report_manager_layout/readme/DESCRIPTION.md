This module changes the Locations report (*Inventory > Reporting >
Locations*) so that non-managers see a read-only copy of the manager layout.

Depending on the user's groups, the Locations report list view resolves to:

- Stock managers: the existing editable manager layout (unchanged).
- All other users: a read-only copy of the manager layout, so they see the
  richer manager column set (and its extension columns, such as expiration
  date) without being able to create, edit or delete records.

A module such as `stock_reporting_access` should be installed to let non-manager
users access the *Inventory > Reporting* menu item.

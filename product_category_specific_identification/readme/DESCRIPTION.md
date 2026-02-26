This module adds two new fields — enable_specific_identification_method and
axls_property_cost_method — to the product category model. The
axls_property_cost_method field mirrors the standard Odoo costing method
with an additional value: "Specific Identification".

When enable_specific_identification_method is enabled and the standard costing
method is set to FIFO, the axls_property_cost_method will display
"Specific Identification". Otherwise, it will reflect the standard costing
method value.

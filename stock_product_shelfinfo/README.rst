===============================
Stock Product Shelf Information
===============================

.. 
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! source digest: sha256:18cd9cdb7eb3d32a5558419d37940588fcc32a477ace926095dcbdb2facb444d
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-qrtl%2Faxls--custom-lightgray.png?logo=github
    :target: https://github.com/qrtl/axls-custom/tree/16.0/stock_product_shelfinfo
    :alt: qrtl/axls-custom

|badge1| |badge2| |badge3|

This module adds a new model Product Shelf Information
(product.shelfinfo) to keep the static shelf details per product per
location, and show the information in relevant transactions and reports
to facilitate warehouse operations.

**Table of contents**

.. contents::
   :local:

Configuration
=============

Go to the menu items under *Inventory > Settings > Product Shelf Info*
and create area 1, area 2 and position records to be selected in the
product shelf information accordingly.

Usage
=====

Go to *Inventory > Products > Product Shelf Information* and create
records for combinations of product, location and company. These records
show in product forms (Inventory tab) as well.

Generated ID (name) of the Shelf Information record should show for
relevant internal locations in the stock move records of the picking
form, as well as in the picking report, to facilitate the picking/store
operations.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/qrtl/axls-custom/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/qrtl/axls-custom/issues/new?body=module:%20stock_product_shelfinfo%0Aversion:%2016.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
-------

* Quartile Limited

Maintainers
-----------

This module is part of the `qrtl/axls-custom <https://github.com/qrtl/axls-custom/tree/16.0/stock_product_shelfinfo>`_ project on GitHub.

You are welcome to contribute.

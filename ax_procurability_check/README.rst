======================
Ax Procurability Check
======================

Check part procurability and save status of check

Configuration
=============

To configure this module, you need to:

#. Go to ...

Usage
=====

To use this module, you need to:

1. Set Nexar API key to Settings>General Settings>Product Procurability Check API
2. Set number of items update at one time (prefer value is 50)
3. Change Scheduled Actions (cron) setting from Settings>Technical>Automation>Scheduled Actions
 a. Open Procurability update Actions
 b. Check Execute Every and enable the action by set Active flag to ON
4. Procurability information will be updated in Purchase>Products>Procurability
  
Special attention!!
If the DB is running in a docker and the instance has two or more DB, cron task will stop once finished a task.
https://github.com/odoo/odoo/issues/79823

Changelog
=========

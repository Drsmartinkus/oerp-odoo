Purchase - No Vendor Grouping
#############################

When purchase is about to be created via procurement (e.g. sale order confirmation),
it will not try to find existing purchase RFQ to merge it with. Instead it will always
create new one.

Configuration
=============

Go to ``Purchase / Configuration / Settings / Orders`` and check ``No Vendor Grouping``.

NOTE. Currently when enabled this only works for all products per company.

Contributors
------------

* Author: Andrius Laukavičius <timefordev>

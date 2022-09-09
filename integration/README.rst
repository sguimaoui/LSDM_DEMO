Integration
===========

Changelog
---------

1.7.0 (2022-09-05)
***********************

* NEW! Major feature. Introduced auto workflow that allows based on sales order status: to validate sales order, create and validate invoice for it and register payment on created invoice. Configuration is flexible and can be done individually for every SO status.
* NEW! Added logic to allow creating webhooks on e-Commerce system for automatic tracking of the order status changes.
* Implemented separate functionality of products mapping (trying to map with existing Odoo Product) from products import (trying to map and if not found create product in Odoo).
* Add possibility to call "Try Map Products" from External -> Products and External -> Mappings menus.
* During creation of sales order if mapping for product was not found trying to auto-map by reference OR barcode with existing Odoo Product before failing creation of sales order.
* Send tracking numbers only when sales order is fully shipped (all related pickings are either "done" or "cancelled" and there are at least some delivered items).
* Made improvements for connector to support 50 000 Products.
* Fixing issue with synchronizing records with special symbols in their name ("%", "_" , etc.)
* Allow to disable export of product images from Odoo to e-Commerce Systems

1.6.0 (2022-07-21)
***********************

* Added possibility to define Cancel action for the integration.
* Added Product Features / Product Feature values related models (to be used in specific connectors).
* Added possibility to define “Default Sales Person” on sales integration. So it will be automatically set when new received SO is created.
* Saving external e-commerce system sales order reference to separate field “External Sales Order Ref“ on Sales Order.
* Allow to select only Sales Taxes in “Mappings - Taxes” menu.
* Try automatically map products not only by internal reference, but also by barcode (if it exists).
* Added the ability to work both with the Manufacturing module and without it.
* Added the ability to work both with the eCommerce module and without it.
* Not Allow to define for 2 integrations same “Sales order prefix“.
* If sales order prefix is used, don't generate standard SOXXX and use PREFIX/Order_name instead.
* Added hierarchy to External Categories view for easier navigation.
* TECHNICAL: Added possibility to easily extend module for adding custom fields

1.5.5 (2022-06-16)
***********************

* Fixed incorrect name of constraint for internal records
* Automatically cleanup non-existing external product and product variants records (in case not found in external system)
* Do not fail job in case images or inventory where not exported properly during Export Template job. That helps to avoid duplicates in external system
* Before exporting products from Odoo to external system double check that same product already exists in external e-Commerce system. If exists then map it automatically by internal reference.

1.5.4 (2022-06-12)
***********************

* Group taxes and tax groups together according to the integration
* Link external product variants and product templates
* Link external product attributes to corresponding external attribute values
* When exporting product from Odoo to Prestashop make sure to export also External Reference
* Added functionality to auto-create missing integration settings (so we have flexibility to add them without migrations)

1.5.3 (2022-06-09)
***********************

* Give ability define allowed sales integrations separately for every product variant
* Add quick filters for product variants/templates list to be able to quickly find which product belongs to which integration
* Add mass action on product variants/templates to change integration product is attached to
* Allow to define if product should be automatically attached to the specific integration on its creation with special checkbox on sales integration object
* Add to the integration possibility to associate all mapped products with this integration (in action "Link All Mapped Products")

1.5.2 (2022-06-02)
***********************

* Added possibility to import payment transactions
* When creating taxes from integration, set link to the specific integration from Odoo Tax (to know from which integration tax was created)

1.5.1 (2022-05-16)
***********************

* Solve issue with multi-company setup and automatic sales order download
* Set proper currency on Sales Order if it is different from company standard
* Multi-step delivery: Send tracking number ONLY for outgoing picking

1.5.0 (2022-05-01)
***********************

* Added Quick Configuration Wizard
* Added taxes and tax groups quick manual import
* Version of prestapyt library changed to 0.10.1
* Fixed initial payment methods import
* Fixed import BOMs with no product variant components
* Fixed incorrect tax rate applied to order shipping line
* When importing sales order, payment method is also created if it doesn't exist
* When integration is deleted, also delete related Sales Order download Scheduled Action

1.4.4 (2022-04-20)
***********************

* Added filter by active countries and states in initial import
* Fixed order import when line has several taxes
* Fixed product import

1.4.3 (2022-03-31)
***********************

* Added import of payment method before creating an order if it does not exists
* Added integration info in Queue Job for errors with mapping
* Added possibility to import product categories by action “Import Categories“ in menus “External → Categories“ and “Mappings → Categories“
* Added button "Import Product" on unmapped products in menu “Mapping → Products“
* Fixed issue with export new products
* Fixed product and product variant mapping in initial import
* Fixed empty external names after export products and import orders

1.4.2 (2022-03-11)
***********************

* Sale order line description for discount and price difference is assigned from product

1.4.1 (2022-03-01)
***********************

* Fix issue with difference per cent of the total order amount

1.4.0 (2022-02-17)
***********************

* Added possibility to import product attributes and values by action “Import Products Attributes“ in menus “External → Product Attributes“ and “Mappings → Product Attributes“
* Added creation of Order Discount from e-Commerce System as a separate product line in a sell order
* Fix issue with trying to send stock to e-Commerce for products that has disabled integration
* Fix bug of mapping modification for users without role Job Queue Manager

1.3.5 (2021-12-31)
***********************

* Added button "Import Stock Levels" to “Initial Import“ tab that tries to download stock levels for storable products
* Fixed bug of delivery line tax calculation

1.3.4 (2021-12-24)
***********************

* Added “Initial Import“ tab with two separate buttons into “Sale Integration“:
    - “Import Master Data“ - download and try to map common data
    - “Import products“ - try to import products from e-Commerce System to Odoo (with pre-validation step)
* Added possibility to import products by action Import Products in menu “External → Products“
* Import of products is run in jobs separately for each product

1.3.3 (2021-11-22)
***********************

* Downloaded sales order now is moved from file to JSON format and can be edited/viewed in menu “e-Commerce Integration → Sales Raw Data“

1.3.2 (2021-10-27)
***********************

* Synchronize tracking only after it is added to the stock picking. Some carrier connectors

1.3.1 (2021-10-18)
***********************

* Added synchronization of partner language and partner email (to delivery and shipping address)

1.3 (2021-10-02)
***********************

* Automapping of the Countries, Country States, Languages, Payment Methods
* Added Default Sales Team to Sales Order created via e-Commerce Integration
* Added synchronization of VAT and Personal Identification Number field
* In case purchase is done form the company, create Company and Contact inside Odoo

1.2 (2021-09-20)
***********************

* Added possibility to define field mappings and specify if field should be updatable or not
* Avoid creation of duplicated products under some conditions

1.1 (2021-06-28)
***********************

* Add field for Delivery Notes on Sales Order
* Added configuration to define on Sales Integration which fields should be used on SO and Delivery Order for Delivery Notes
* Allow to specify which product should be exported to which channel
* If e-Commerce Product Name is not empty, send it instead of standard Product Name

1.0.5 (2021-06-25)
***********************

* Fixed a bug of creating duplicate sale orders

1.0.4 (2021-06-01)
***********************

* FIX: Prestashop should send name of the product, not display_name

1.0.3 (2021-05-28)
***********************

* Fixed warnings on Odoo.sh with empty description on new models

1.0.2 (2021-04-21)
***********************

* Added statistics widget
* Create missing mappings on receiving of orders
* Requeue needed jobs when mappings are fixed

1.0.1 (2021-04-13)
***********************

* Added Check Connection

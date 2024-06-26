######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Test cases for Item Model
"""

import logging
import os
from unittest import TestCase
from wsgi import app
from service.models import Order, Item, DataValidationError, db
from tests.factories import ItemFactory, OrderFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#        I T E M   M O D E L   T E S T   C A S E S
######################################################################
class TestItem(TestCase):
    """Item Model Test Cases"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Order).delete()  # clean up the last tests
        db.session.query(Item).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_serialize_an_item(self):
        """It should serialize an Item"""
        item = ItemFactory()
        serial_item = item.serialize()
        self.assertEqual(serial_item["id"], item.id)
        self.assertEqual(serial_item["order_id"], item.order_id)
        self.assertEqual(serial_item["product_id"], item.product_id)
        self.assertEqual(serial_item["name"], item.name)
        self.assertEqual(serial_item["quantity"], item.quantity)
        self.assertEqual(serial_item["unit_price"], item.unit_price)
        self.assertEqual(serial_item["total_price"], item.total_price)
        self.assertEqual(serial_item["description"], item.description)

    def test_deserialize_an_item(self):
        """It should deserialize an Item"""
        item = ItemFactory()
        item.create()
        new_item = Item()
        new_item.deserialize(item.serialize())
        self.assertEqual(new_item.order_id, item.order_id)
        self.assertEqual(new_item.product_id, item.product_id)
        self.assertEqual(new_item.name, item.name)
        self.assertEqual(new_item.quantity, item.quantity)
        self.assertEqual(new_item.unit_price, item.unit_price)
        self.assertEqual(new_item.total_price, item.total_price)
        self.assertEqual(new_item.description, item.description)

    def test_deserialize_item_key_error(self):
        """It should not Deserialize an item with a KeyError"""
        item = Item()
        self.assertRaises(DataValidationError, item.deserialize, {})

    def test_deserialize_item_type_error(self):
        """It should not Deserialize an item with a TypeError"""
        item = Item()
        self.assertRaises(DataValidationError, item.deserialize, [])

    def test_delete_order_item(self):
        """It should Delete an order's items"""
        orders = Order.all()
        self.assertEqual(orders, [])

        order = OrderFactory()
        item = ItemFactory(order=order)
        order.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(order.id)
        orders = Order.all()
        self.assertEqual(len(orders), 1)

        # Fetch it back
        order = Order.find(order.id)
        item = order.items[0]
        item.delete()
        order.update()

        # Fetch it back again
        order = Order.find(order.id)
        self.assertEqual(len(order.items), 0)

    def test_add_an_item(self):
        """It should create an item and add it to the database"""
        items = Item.all()
        self.assertEqual(items, [])
        item = ItemFactory()
        item.create()
        self.assertIsNotNone(item.id)
        items = Item.all()
        self.assertEqual(len(items), 1)

    def test_list_order_items(self):
        """It should list all items in an order"""
        self.assertEqual(Order.all(), [])
        order = OrderFactory()
        order.create()
        self.assertEqual(len(Order.all()), 1)
        for _ in range(10):
            item = ItemFactory(order=order)
            item.create()
        self.assertEqual(len(Item.all()), 10)
        for item in Item.all():
            self.assertEqual(item.order.id, order.id)

    def test_update_order_item(self):
        """It should Update an orders item"""
        orders = Order.all()
        self.assertEqual(orders, [])

        order = OrderFactory()
        item = ItemFactory(order=order)
        order.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(order.id)
        orders = Order.all()
        self.assertEqual(len(orders), 1)

        # Fetch it back
        order = Order.find(order.id)
        old_item = order.items[0]
        print("%r", old_item)
        self.assertEqual(old_item.name, item.name)
        # Change the city
        old_item.name = "XX"
        order.update()

        # Fetch it back again
        order = Order.find(order.id)
        item = order.items[0]
        self.assertEqual(item.name, "XX")

    def test_find_by_product_id(self):
        """Find Items by product_id"""
        order = OrderFactory()
        order.create()
        o_id = order.id
        print(o_id)
        item = ItemFactory(
            order_id=o_id, product_id=1, name="ruler", quantity=1, unit_price=10.50
        )
        item.create()
        item2 = ItemFactory(
            order_id=o_id, product_id=2, name="drill", quantity=2, unit_price=11
        )
        item2.create()
        print(order.serialize())
        print(item2.serialize())
        print(item.serialize())
        items = Item.find_by_product_id(item.order_id, 1)
        print(items)
        self.assertEqual(items[0].product_id, 1)
        self.assertEqual(items[0].name, "ruler")
        self.assertEqual(items[0].quantity, 1)
        self.assertEqual(items[0].unit_price, 10.50)

    def test_find_by_name(self):
        """Find Items by Name"""
        items = ItemFactory.create_batch(5)
        for item in items:
            item.create()

        found = Item.find_by_name(items[0].order_id, items[0].name)
        self.assertEqual(found[0].serialize(), items[0].serialize())

        found = Item.find_by_name(items[0].order_id, items[0].name[:3])
        self.assertGreaterEqual(len(found), 1)
        for item in found:
            self.assertTrue(items[0].name[:3].lower() in item.name.lower())

        found = Item.find_by_name(items[0].order_id, "XYZ")
        self.assertEqual(found, [])

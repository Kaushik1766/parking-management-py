import unittest
from dataclasses import dataclass, field

from app.utils.alias_deserializer import alias_init
from app.utils.singleton import singleton


class TestAliasDeserializer(unittest.TestCase):
    def test_alias_init_with_alias(self):
        """Test that alias_init correctly maps alias to field name"""
        @alias_init
        @dataclass
        class TestClass:
            my_field: str = field(metadata={"alias": "myField"})
            another_field: int = field(metadata={"alias": "anotherField"})

        # Test with alias
        obj = TestClass(myField="test", anotherField=42)
        self.assertEqual(obj.my_field, "test")
        self.assertEqual(obj.another_field, 42)

    def test_alias_init_without_alias(self):
        """Test that alias_init works with direct field names"""
        @alias_init
        @dataclass
        class TestClass:
            my_field: str = field(metadata={"alias": "myField"})
            another_field: int = field(default=0)

        # Test with direct field name
        obj = TestClass(my_field="test", another_field=42)
        self.assertEqual(obj.my_field, "test")
        self.assertEqual(obj.another_field, 42)

    def test_alias_init_mixed(self):
        """Test that alias_init works with both alias and direct field names"""
        @alias_init
        @dataclass
        class TestClass:
            my_field: str = field(metadata={"alias": "myField"})
            another_field: int = field(metadata={"alias": "anotherField"})
            direct_field: str = "default"

        # Test with mixed inputs
        obj = TestClass(myField="test", another_field=42, direct_field="direct")
        self.assertEqual(obj.my_field, "test")
        self.assertEqual(obj.another_field, 42)
        self.assertEqual(obj.direct_field, "direct")


class TestSingleton(unittest.TestCase):
    def test_singleton_returns_same_instance(self):
        """Test that singleton decorator returns the same instance"""
        @singleton
        class TestClass:
            def __init__(self):
                self.value = 42

        obj1 = TestClass()
        obj2 = TestClass()  # Should return same instance
        
        self.assertIs(obj1, obj2)
        self.assertEqual(obj1.value, 42)
        self.assertEqual(obj2.value, 42)

    def test_singleton_init_called_once(self):
        """Test that __init__ is called only once for singleton"""
        init_count = []

        @singleton
        class TestClass:
            def __init__(self):
                init_count.append(1)

        obj1 = TestClass()
        obj2 = TestClass()
        obj3 = TestClass()

        self.assertIs(obj1, obj2)
        self.assertIs(obj2, obj3)
        self.assertEqual(len(init_count), 1)

    def test_singleton_with_no_args(self):
        """Test that singleton works with no constructor arguments"""
        @singleton
        class TestClass:
            pass

        obj1 = TestClass()
        obj2 = TestClass()

        self.assertIs(obj1, obj2)


if __name__ == "__main__":
    unittest.main()

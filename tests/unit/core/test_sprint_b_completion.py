from django.test import TestCase
from core.models import ToolRun, CofWorkbook, BtplWorkbook
from django.core.cache import cache
import uuid
import os

class SprintBCompletionTests(TestCase):
    def test_database_indexes(self):
        """Verify models have the expected Meta.indexes."""
        self.assertTrue(hasattr(ToolRun._meta, 'indexes'))
        self.assertTrue(len(ToolRun._meta.indexes) > 0)
        self.assertTrue(hasattr(CofWorkbook._meta, 'indexes'))
        self.assertTrue(len(CofWorkbook._meta.indexes) > 0)
        
    def test_safe_int_utility(self):
        """Verify the safe_int parsing utility works."""
        from core.utils.parsing import safe_int
        self.assertEqual(safe_int("123"), 123)
        self.assertEqual(safe_int("abc", 5), 5)
        self.assertEqual(safe_int(None, 10), 10)
        
    def test_uuid_generation(self):
        """Just checking uuid logic."""
        ext = ".xlsx"
        generated_name = f"attendance_{uuid.uuid4().hex}{ext}"
        self.assertTrue(generated_name.startswith("attendance_"))
        self.assertTrue(generated_name.endswith(".xlsx"))

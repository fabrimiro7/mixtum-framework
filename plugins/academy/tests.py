from django.test import TestCase
from .models import Category

# Create your tests here.

class CategoryModelTest(TestCase):

    def setUp(self):
        self.parent_category = Category.objects.create(title="Parent", description="Parent category")
        self.child_category = Category.objects.create(title="Child", description="Child category", parent=self.parent_category)

    def test_category_creation(self):
        self.assertEqual(self.parent_category.title, "Parent")
        self.assertEqual(self.child_category.parent, self.parent_category)

    def test_category_str(self):
        self.assertEqual(str(self.parent_category), "Parent")

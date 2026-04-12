from django.test import TestCase
from taxi.forms import OrderForm

class OrderFormTest(TestCase):
    def test_empty_points_validation(self):
        """Форма не должна быть валидной, если точки А и Б пусты."""
        form = OrderForm(data={'point_a': '', 'point_b': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('point_a', form.errors)
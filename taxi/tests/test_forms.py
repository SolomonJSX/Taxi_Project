from django.test import TestCase
from taxi.forms import OrderForm, ReviewForm

class OrderFormTest(TestCase):
    def test_empty_points_validation(self):
        """Форма не должна быть валидной, если точки А и Б пусты."""
        form = OrderForm(data={'point_a': '', 'point_b': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('point_a', form.errors)

class ReviewFormTest(TestCase):
    def test_review_form_valid(self):
        """Проверка валидности формы с правильными данными."""
        form = ReviewForm(data={'rating': 5, 'comment': 'Все супер'})
        self.assertTrue(form.is_valid())

    def test_review_form_invalid_rating(self):
        """Проверка, что оценка 6 не пройдет валидацию."""
        form = ReviewForm(data={'rating': 6, 'comment': 'Ошибка'})
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
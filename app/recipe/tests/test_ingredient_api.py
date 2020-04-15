from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test for pubicaly available api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test the login required for ingredient model"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Tests for private autharised apis"""

    def setUp(self):
        self.user = get_user_model().objects.create(
            email='naevee@ajsd.com',
            password='test1234'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test for retreibving ingrdient"""
        Ingredient.objects.create(user=self.user, name='salt')
        Ingredient.objects.create(user=self.user, name='kara')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test ingredient for the autharized user"""
        user2 = get_user_model().objects.create(
            email='test@test.com',
            password='test124'
        )
        Ingredient.objects.create(user=user2, name='vinegar')

        ingredient = Ingredient.objects.create(user=self.user, name='vinegar2')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_success(self):
        """Test creating the ingrdient successfully"""
        payload = {'name': 'cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test ingredient invalid"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        '''Test filtering ingredients by those assigned to recipe'''
        ingredient1 = Ingredient.objects.create(
            user=self.user, name='as1212aS'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user, name='aSas121213213'
        )
        recipe = Recipe.objects.create(
            title='Test',
            time_miniutes=2,
            price=12.0,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        '''Test filter ingredients assign unique'''
        ingredient = Ingredient.objects.create(user=self.user, name='1asd')
        # ingredient.objects.create(user=self.user, name='asd_djahsbd')
        recipe1 = Recipe.objects.create(
            title='Test',
            time_miniutes=2,
            price=12.0,
            user=self.user
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            title='Test1212',
            time_miniutes=2,
            price=12.0,
            user=self.user
        )
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)

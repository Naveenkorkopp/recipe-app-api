from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPES_URLS = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    '''Create and return a sample recipe'''
    default = {
        'title': 'sample recipe',
        'time_miniutes': 10,
        'price': 5.00
    }
    default.update(params)

    return Recipe.objects.create(user=user, **default)


class PublicRecipeApiTests(TestCase):
    '''Test class for unauthenticated recipe api class'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test for auth is required'''
        res = self.client.get(RECIPES_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    '''Test unautheicated recipe api access'''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='naevee@ajsd.com',
            password='test1234'
        )
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        '''Test retriving a list of recipes'''
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URLS)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        '''Test recipe limit for user'''
        user2 = get_user_model().objects.create(
            email='test@test.com',
            password='test124'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URLS)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

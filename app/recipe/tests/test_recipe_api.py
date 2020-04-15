import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URLS = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    '''Return URL for recipe image for upload'''
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    '''Return recipe detail url'''
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main Course'):
    '''Create and return sample tag'''
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cineman'):
    '''Create and return sample tag'''
    return Ingredient.objects.create(user=user, name=name)


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

    def test_view_recipe_detail(self):
        '''Test viewing a recipe deatil'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        '''Test creating recipe'''
        payload = {
            'title': 'Chocolate',
            'time_miniutes': 30,
            'price': 5.00
        }
        res = self.client.post(RECIPES_URLS, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        '''Test creating recipe wuth tags'''
        tag1 = sample_tag(user=self.user, name='vigan')
        tag2 = sample_tag(user=self.user, name='vigan111')

        payload = {
            'title': 'Avocado lime cheese cake',
            'tags': [tag1.id, tag2.id],
            'time_miniutes': 30,
            'price': 25.00
        }
        res = self.client.post(RECIPES_URLS, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredient(self):
        '''Test creating recipe wuth ingredient'''
        ingredient1 = sample_ingredient(user=self.user, name='Prawn')
        ingredient2 = sample_ingredient(user=self.user, name='ili')

        payload = {
            'title': 'Avocado lime cheese cake',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_miniutes': 30,
            'price': 25.00
        }
        res = self.client.post(RECIPES_URLS, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        '''Test the updating recipe partially patch'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='curries')

        payload = {
            'title': 'Chicken tea cup',
            'tags': [new_tag.id]
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        '''Test updating recipe with put'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Spider tea cup',
            'time_miniutes': 30,
            'price': 25.00
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_miniutes, payload['time_miniutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='naevee@ajsd.com',
            password='test1234'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        '''test uploading the image to recipe'''
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', [10, 10])
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        '''Test uploading bad image'''
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipe_by_tags(self):
        '''Test returning recipes with specific tag'''
        recipe1 = sample_recipe(user=self.user, title='Naven')
        recipe2 = sample_recipe(user=self.user, title='Naven_1')
        tag1 = sample_tag(user=self.user, name='1')
        tag2 = sample_tag(user=self.user, name='2')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Naven_3')

        res = self.client.get(
            RECIPES_URLS,
            {'tags': f'{tag1.id},{tag2.id}'}
        )
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipe_by_ingredients(self):
        '''Test returning recipes with specific ingredient'''
        recipe1 = sample_recipe(user=self.user, title='Naven')
        recipe2 = sample_recipe(user=self.user, title='Naven_1')
        ingredient1 = sample_ingredient(user=self.user, name='1')
        ingredient2 = sample_ingredient(user=self.user, name='2')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Naven_3')

        res = self.client.get(
            RECIPES_URLS,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTest(TestCase):
    """Test the publicaly available tag apis"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test login is required for reteiving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test the autharized available tag apis"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@naveen.com',
            'test123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test rertrive tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Naveen')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test that tags returned are for  authenticated user'''
        user2 = get_user_model().objects.create_user(
            'test@naveen1.com',
            'test1234'
        )
        Tag.objects.create(user=user2, name='Hello')
        tag = Tag.objects.create(user=self.user, name='panda')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'Test tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(user=self.user, name=payload['name']).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Tesrt Creating new tag with invalid tag name"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        '''Test filtering tags by those assigned to recipe'''
        tag1 = Tag.objects.create(user=self.user, name='as1212aS')
        tag2 = Tag.objects.create(user=self.user, name='aSas121213213')
        recipe = Recipe.objects.create(
            title='Test',
            time_miniutes=2,
            price=12.0,
            user=self.user
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        '''Test filter tags assign unique'''
        tag = Tag.objects.create(user=self.user, name='1asd')
        # tag.objects.create(user=self.user, name='asd_djahsbd')
        recipe1 = Recipe.objects.create(
            title='Test',
            time_miniutes=2,
            price=12.0,
            user=self.user
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Test1212',
            time_miniutes=2,
            price=12.0,
            user=self.user
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)

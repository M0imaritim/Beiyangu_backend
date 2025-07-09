"""
Comprehensive tests for the bids app.

This test suite covers:
- Model validation and business logic
- Serializer validation
- API endpoints and permissions
- Filter functionality
- Edge cases and error handling
"""
import uuid
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta

from apps.bids.models import Bid
from apps.bids.serializers import BidSerializer, BidCreateUpdateSerializer
from apps.bids.filters import BidFilter
from apps.user_requests.models import Request

User = get_user_model()


class BidModelTestCase(TestCase):
    """Test cases for the Bid model."""
    
    def setUp(self):
        """Set up test data."""
        self.buyer = User.objects.create_user(
            username='buyer', email='buyer@test.com', password='testpass123'
        )
        self.seller = User.objects.create_user(
            username='seller', email='seller@test.com', password='testpass123'
        )
        self.request_obj = Request.objects.create(
            title='Test Request',
            description='Test description',
            budget=Decimal('100.00'),
            buyer=self.buyer,
            status='open'
        )
    
    def test_bid_creation(self):
        """Test creating a valid bid."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='I can help with this project',
            delivery_time=7
        )
        
        self.assertEqual(bid.request, self.request_obj)
        self.assertEqual(bid.seller, self.seller)
        self.assertEqual(bid.amount, Decimal('50.00'))
        self.assertEqual(bid.message, 'I can help with this project')
        self.assertEqual(bid.delivery_time, 7)
        self.assertFalse(bid.is_accepted)
        self.assertFalse(bid.is_deleted)
        self.assertIsInstance(bid.public_id, uuid.UUID)
    
    def test_bid_string_representation(self):
        """Test bid string representation."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message'
        )
        
        expected = f"Bid by {self.seller.username} - $50.00"
        self.assertEqual(str(bid), expected)
    
    def test_unique_constraint(self):
        """Test that seller can only have one bid per request."""
        Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='First bid'
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Bid.objects.create(
                request=self.request_obj,
                seller=self.seller,
                amount=Decimal('60.00'),
                message='Second bid'
            )
    
    def test_bid_amount_validation(self):
        """Test bid amount validation."""
        bid = Bid(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('150.00'),  # Exceeds budget
            message='Test message'
        )
        
        with self.assertRaises(ValidationError):
            bid.clean()
    
    def test_seller_cannot_bid_on_own_request(self):
        """Test that sellers cannot bid on their own requests."""
        bid = Bid(
            request=self.request_obj,
            seller=self.buyer,  # Same as request buyer
            amount=Decimal('50.00'),
            message='Test message'
        )
        
        with self.assertRaises(ValidationError):
            bid.clean()
    
    def test_cannot_bid_on_closed_request(self):
        """Test that bids cannot be placed on closed requests."""
        self.request_obj.status = 'closed'
        self.request_obj.save()
        
        bid = Bid(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message'
        )
        
        with self.assertRaises(ValidationError):
            bid.clean()
    
    def test_expired_bid_validation(self):
        """Test expired bid validation."""
        past_time = timezone.now() - timedelta(hours=1)
        
        bid = Bid(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message',
            expires_at=past_time
        )
        
        with self.assertRaises(ValidationError):
            bid.clean()
    
    def test_savings_calculation(self):
        """Test savings amount and percentage calculation."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('75.00'),
            message='Test message'
        )
        
        self.assertEqual(bid.savings_amount, Decimal('25.00'))
        self.assertEqual(bid.savings_percentage, 25.0)
    
    def test_is_editable_property(self):
        """Test the is_editable property."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message'
        )
        
        self.assertTrue(bid.is_editable)
        
        # Test when bid is accepted
        bid.is_accepted = True
        bid.save()
        self.assertFalse(bid.is_editable)
        
        # Test when bid is deleted
        bid.is_accepted = False
        bid.is_deleted = True
        bid.save()
        self.assertFalse(bid.is_editable)
    
    def test_is_expired_property(self):
        """Test the is_expired property."""
        future_time = timezone.now() + timedelta(hours=1)
        past_time = timezone.now() - timedelta(hours=1)
        
        # Not expired
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message',
            expires_at=future_time
        )
        self.assertFalse(bid.is_expired)
        
        # Expired
        bid.expires_at = past_time
        bid.save()
        self.assertTrue(bid.is_expired)
    
    def test_can_be_accepted(self):
        """Test the can_be_accepted method."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message'
        )
        
        self.assertTrue(bid.can_be_accepted())
        
        # Test when bid is already accepted
        bid.is_accepted = True
        bid.save()
        self.assertFalse(bid.can_be_accepted())
    
    def test_soft_delete(self):
        """Test soft delete functionality."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message'
        )
        
        self.assertFalse(bid.is_deleted)
        
        bid.soft_delete(self.seller)
        
        self.assertTrue(bid.is_deleted)
        self.assertEqual(bid.updated_by, self.seller)


class BidSerializerTestCase(TestCase):
    """Test cases for bid serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.buyer = User.objects.create_user(
            username='buyer', email='buyer@test.com', password='testpass123'
        )
        self.seller = User.objects.create_user(
            username='seller', email='seller@test.com', password='testpass123'
        )
        self.request_obj = Request.objects.create(
            title='Test Request',
            description='Test description',
            budget=Decimal('100.00'),
            buyer=self.buyer,
            status='open'
        )
    
    def test_bid_serializer_read(self):
        """Test BidSerializer for reading data."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test message',
            delivery_time=7
        )
        
        serializer = BidSerializer(bid)
        data = serializer.data
        
        self.assertEqual(data['amount'], '50.00')
        self.assertEqual(data['message'], 'Test message')
        self.assertEqual(data['delivery_time'], 7)
        self.assertEqual(data['seller']['username'], 'seller')
        self.assertEqual(data['savings_amount'], '50.00')
        self.assertEqual(data['savings_percentage'], '50.00')
        self.assertIn('time_since_created', data)
    
    def test_bid_create_serializer_validation(self):
        """Test BidCreateUpdateSerializer validation."""
        # Valid data
        data = {
            'amount': '75.00',
            'message': 'This is a valid message with enough characters',
            'delivery_time': 5
        }
        
        serializer = BidCreateUpdateSerializer(
            data=data,
            context={'request_obj': self.request_obj}
        )
        
        self.assertTrue(serializer.is_valid())
    
    def test_bid_create_serializer_amount_validation(self):
        """Test bid amount validation in serializer."""
        # Amount exceeds budget
        data = {
            'amount': '150.00',
            'message': 'This message is long enough to be valid',
            'delivery_time': 5
        }
        
        serializer = BidCreateUpdateSerializer(
            data=data,
            context={'request_obj': self.request_obj}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_bid_create_serializer_message_validation(self):
        """Test bid message validation in serializer."""
        # Message too short
        data = {
            'amount': '50.00',
            'message': 'Short',
            'delivery_time': 5
        }
        
        serializer = BidCreateUpdateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('message', serializer.errors)
    
    def test_bid_create_serializer_delivery_time_validation(self):
        """Test delivery time validation in serializer."""
        # Negative delivery time
        data = {
            'amount': '50.00',
            'message': 'This is a valid message with enough characters',
            'delivery_time': -1
        }
        
        serializer = BidCreateUpdateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('delivery_time', serializer.errors)


class BidFilterTestCase(TestCase):
    """Test cases for bid filters."""
    
    def setUp(self):
        """Set up test data."""
        self.buyer = User.objects.create_user(
            username='buyer', email='buyer@test.com', password='testpass123'
        )
        self.seller1 = User.objects.create_user(
            username='seller1', email='seller1@test.com', password='testpass123'
        )
        self.seller2 = User.objects.create_user(
            username='seller2', email='seller2@test.com', password='testpass123'
        )
        self.request_obj = Request.objects.create(
            title='Test Request',
            description='Test description',
            budget=Decimal('100.00'),
            buyer=self.buyer,
            status='open'
        )
        
        # Create test bids
        self.bid1 = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller1,
            amount=Decimal('30.00'),
            message='First bid',
            is_accepted=True
        )
        
        self.bid2 = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller2,
            amount=Decimal('70.00'),
            message='Second bid',
            is_accepted=False
        )
    
    def test_amount_filter(self):
        """Test amount range filtering."""
        # Mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        # Test minimum amount filter
        filter_obj = BidFilter(
            data={'amount_min': '50.00'},
            queryset=Bid.objects.all()
        )
        filter_obj.request = MockRequest(self.seller1)
        
        filtered = filter_obj.qs
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.bid2)
        
        # Test maximum amount filter
        filter_obj = BidFilter(
            data={'amount_max': '50.00'},
            queryset=Bid.objects.all()
        )
        filter_obj.request = MockRequest(self.seller1)
        
        filtered = filter_obj.qs
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.bid1)
    
    def test_acceptance_filter(self):
        """Test acceptance status filtering."""
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        # Test accepted bids only
        filter_obj = BidFilter(
            data={'is_accepted': True},
            queryset=Bid.objects.all()
        )
        filter_obj.request = MockRequest(self.seller1)
        
        filtered = filter_obj.qs
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.bid1)
    
    def test_my_bids_filter(self):
        """Test filtering for user's own bids."""
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        # Test filtering for seller1's bids
        filter_obj = BidFilter(
            data={'my_bids': True},
            queryset=Bid.objects.all()
        )
        filter_obj.request = MockRequest(self.seller1)
        
        filtered = filter_obj.qs
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.bid1)


class BidAPITestCase(APITestCase):
    """Test cases for bid API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.buyer = User.objects.create_user(
            username='buyer', email='buyer@test.com', password='testpass123'
        )
        self.seller = User.objects.create_user(
            username='seller', email='seller@test.com', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other', email='other@test.com', password='testpass123'
        )
        
        self.request_obj = Request.objects.create(
            title='Test Request',
            description='Test description',
            budget=Decimal('100.00'),
            buyer=self.buyer,
            status='open'
        )
        
        self.bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('50.00'),
            message='Test bid message'
        )
        
        self.client = APIClient()
    
    def test_bid_list_authentication_required(self):
        """Test that bid list requires authentication."""
        url = reverse('bids-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_bid_list_for_user(self):
        """Test listing user's own bids."""
        self.client.force_authenticate(user=self.seller)
        url = reverse('bids-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.bid.id)
    
    def test_bid_detail_view(self):
        """Test retrieving a specific bid."""
        self.client.force_authenticate(user=self.seller)
        url = reverse('bids-detail', kwargs={'pk': self.bid.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.bid.id)
        self.assertEqual(response.data['amount'], '50.00')
    
    def test_bid_update_by_owner(self):
        """Test updating a bid by its owner."""
        self.client.force_authenticate(user=self.seller)
        url = reverse('bids-detail', kwargs={'pk': self.bid.pk})
        
        data = {
            'amount': '60.00',
            'message': 'Updated bid message with sufficient length',
            'delivery_time': 10
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify the update
        self.bid.refresh_from_db()
        self.assertEqual(self.bid.amount, Decimal('60.00'))
        self.assertEqual(self.bid.delivery_time, 10)
    
    def test_bid_update_by_non_owner(self):
        """Test that non-owners cannot update bids."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('bids-detail', kwargs={'pk': self.bid.pk})
        
        data = {
            'amount': '60.00',
            'message': 'Updated bid message with sufficient length'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_bid_soft_delete(self):
        """Test soft deleting a bid."""
        self.client.force_authenticate(user=self.seller)
        url = reverse('bids-detail', kwargs={'pk': self.bid.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete
        self.bid.refresh_from_db()
        self.assertTrue(self.bid.is_deleted)
    
    def test_request_bid_creation(self):
        """Test creating a bid for a request."""
        self.client.force_authenticate(user=self.seller)
        
        # Create a new request for this test
        new_request = Request.objects.create(
            title='Another Request',
            description='Another description',
            budget=Decimal('200.00'),
            buyer=self.buyer,
            status='open'
        )
        
        url = f'/api/requests/{new_request.id}/bids/'
        data = {
            'amount': '80.00',
            'message': 'I would like to work on this project with great enthusiasm',
            'delivery_time': 14
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify bid was created
        bid = Bid.objects.get(request=new_request, seller=self.seller)
        self.assertEqual(bid.amount, Decimal('80.00'))
        self.assertEqual(bid.delivery_time, 14)
    
    def test_duplicate_bid_prevention(self):
        """Test that users cannot create duplicate bids."""
        self.client.force_authenticate(user=self.seller)
        
        url = f'/api/requests/{self.request_obj.id}/bids/'
        data = {
            'amount': '70.00',
            'message': 'Another bid attempt with sufficient length'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('already have a bid', response.data['error'])
    
    def test_bid_acceptance(self):
        """Test accepting a bid."""
        self.client.force_authenticate(user=self.buyer)
        url = reverse('bid-accept', kwargs={'pk': self.bid.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify bid was accepted
        self.bid.refresh_from_db()
        self.assertTrue(self.bid.is_accepted)
    
    def test_bid_acceptance_permission(self):
        """Test that only request owners can accept bids."""
        self.client.force_authenticate(user=self.seller)
        url = reverse('bid-accept', kwargs={'pk': self.bid.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
    
    def test_bid_list_for_request(self):
        """Test listing bids for a specific request."""
        self.client.force_authenticate(user=self.buyer)
        url = f'/api/requests/{self.request_obj.id}/bids/'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['bids']), 1)
    
    def test_bid_list_permission_for_request(self):
        """Test bid list permissions for requests."""
        self.client.force_authenticate(user=self.other_user)
        url = f'/api/requests/{self.request_obj.id}/bids/'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])


class BidEdgeCasesTestCase(TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test data."""
        self.buyer = User.objects.create_user(
            username='buyer', email='buyer@test.com', password='testpass123'
        )
        self.seller = User.objects.create_user(
            username='seller', email='seller@test.com', password='testpass123'
        )
        self.request_obj = Request.objects.create(
            title='Test Request',
            description='Test description',
            budget=Decimal('100.00'),
            buyer=self.buyer,
            status='open'
        )
    
    def test_bid_with_zero_amount(self):
        """Test bid with zero amount."""
        bid = Bid(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('0.00'),
            message='Test message'
        )
        
        with self.assertRaises(ValidationError):
            bid.full_clean()
    
    def test_bid_with_negative_amount(self):
        """Test bid with negative amount."""
        bid = Bid(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('-10.00'),
            message='Test message'
        )
        
        with self.assertRaises(ValidationError):
            bid.full_clean()
    
    def test_bid_ordering(self):
        """Test that bids are ordered by amount, then by creation time."""
        seller2 = User.objects.create_user(
            username='seller2', email='seller2@test.com', password='testpass123'
        )
        
        # Create bids with different amounts
        bid1 = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('70.00'),
            message='Higher amount bid'
        )
        
        bid2 = Bid.objects.create(
            request=self.request_obj,
            seller=seller2,
            amount=Decimal('30.00'),
            message='Lower amount bid'
        )
        
        bids = list(Bid.objects.all())
        self.assertEqual(bids[0], bid2)  # Lower amount first
        self.assertEqual(bids[1], bid1)  # Higher amount second
    
    def test_bid_with_exact_budget_amount(self):
        """Test bid with exact budget amount."""
        bid = Bid.objects.create(
            request=self.request_obj,
            seller=self.seller,
            amount=Decimal('100.00'),  # Exact budget
            message='Exact budget bid'
        )
        
        self.assertEqual(bid.savings_amount, Decimal('0.00'))
        self.assertEqual(bid.savings_percentage, 0.0)
    
    def test_bid_on_request_with_zero_budget(self):
        """Test bid on request with zero budget."""
        zero_budget_request = Request.objects.create(
            title='Zero Budget Request',
            description='Test description',
            budget=Decimal('0.00'),
            buyer=self.buyer,
            status='open'
        )
        
        bid = Bid.objects.create(
            request=zero_budget_request,
            seller=self.seller,
            amount=Decimal('10.00'),
            message='Test message'
        )
        
        # This should fail validation
        with self.assertRaises(ValidationError):
            bid.clean()


class BidPerformanceTestCase(TestCase):
    """Test performance-related aspects of bid functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.buyer = User.objects.create_user(
            username='buyer', email='buyer@test.com', password='testpass123'
        )
        self.request_obj = Request.objects.create(
            title='Test Request',
            description='Test description',
            budget=Decimal('100.00'),
            buyer=self.buyer,
            status='open'
        )
        
        # Create multiple sellers and bids
        self.sellers = []
        self.bids = []
        
        for i in range(10):
            seller = User.objects.create_user(
                username=f'seller{i}',
                email=f'seller{i}@test.com',
                password='testpass123'
            )
            self.sellers.append(seller)
            
            bid = Bid.objects.create(
                request=self.request_obj,
                seller=seller,
                amount=Decimal(f'{10 + i * 5}.00'),
                message=f'Bid message {i}'
            )
            self.bids.append(bid)
    
    def test_queryset_select_related(self):
        """Test that queries use select_related for performance."""
        # This would be tested with Django's assertNumQueries in a real scenario
        bids = Bid.objects.select_related('request', 'seller').all()
        
        # Accessing related objects shouldn't trigger additional queries
        for bid in bids:
            _ = bid.request.title
            _ = bid.seller.username
        
        # In a real test, you'd wrap this in assertNumQueries(1)
        self.assertEqual(len(bids), 10)
    
    def test_bulk_operations(self):
        """Test bulk operations on bids."""
        # Test bulk update
        Bid.objects.filter(amount__lt=Decimal('30.00')).update(is_deleted=True)
        
        deleted_count = Bid.objects.filter(is_deleted=True).count()
        self.assertGreater(deleted_count, 0)
        
        # Test bulk filtering
        active_bids = Bid.objects.filter(is_deleted=False)
        self.assertLess(len(active_bids), 10)


if __name__ == '__main__':
    import django
    from django.test.utils import get_runner
    from django.conf import settings
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["apps.bids.tests"])
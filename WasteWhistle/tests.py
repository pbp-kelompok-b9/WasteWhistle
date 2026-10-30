from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse, resolve

from directory.models import WasteBank
from reporting.models import Report
from comment.models import Comment
from WasteWhistle.views import register_user, login_user, logout_user, dashboard


class WasteWhistleURLTests(TestCase):
    """Tests to verify that root URLs correctly resolve to their respective view functions."""

    def test_register_url_resolves(self):
        match = resolve('/')
        self.assertEqual(match.func, register_user)

    def test_login_url_resolves(self):
        match = resolve('/login/')
        self.assertEqual(match.func, login_user)

    def test_logout_url_resolves(self):
        match = resolve('/logout/')
        self.assertEqual(match.func, logout_user)

    def test_dashboard_url_resolves(self):
        match = resolve('/dashboard/')
        self.assertEqual(match.func, dashboard)


class WasteWhistleViewsTests(TestCase):
    """Unit tests for register_user, login_user, logout_user, and dashboard views."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register_user')
        self.login_url = reverse('login_user')
        self.logout_url = reverse('logout_user')
        self.dashboard_url = reverse('dashboard')

        self.username = "testuser"
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    # ------------------------------------------------------------------
    # 1. Registration View Tests
    # ------------------------------------------------------------------
    def test_register_user_get_unauthenticated(self):
        """Unauthenticated user accessing register view should receive 200 and form context."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIn('form', response.context)

    def test_register_user_get_authenticated_redirect(self):
        """Authenticated user trying to access register view should redirect to dashboard."""
        self.client.force_login(self.user)
        response = self.client.get(self.register_url)
        self.assertRedirects(response, '/dashboard/')

    def test_register_user_post_success(self):
        """Submitting valid user creation data should create user and redirect to login."""
        post_data = {
            'username': 'newuser',
            'password1': 'NewUserPass123!',
            'password2': 'NewUserPass123!',
        }
        response = self.client.post(self.register_url, post_data)
        self.assertRedirects(response, '/login/')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    # ------------------------------------------------------------------
    # 2. Login View Tests
    # ------------------------------------------------------------------
    def test_login_user_get_unauthenticated(self):
        """GET request to login view renders login page with context."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertEqual(response.context['name'], 'Waste Whistle')

    def test_login_user_post_valid_credentials(self):
        """Submitting valid credentials logs user in and redirects to dashboard."""
        post_data = {
            'username': self.username,
            'password': self.password,
        }
        response = self.client.post(self.login_url, post_data)
        self.assertRedirects(response, self.dashboard_url)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_user_post_custom_next_redirect(self):
        """Submitting valid credentials redirects to safe 'next' parameter URL."""
        next_path = '/directory/'
        post_data = {
            'username': self.username,
            'password': self.password,
            'next': next_path
        }
        response = self.client.post(self.login_url, post_data)
        self.assertRedirects(response, next_path)

    def test_login_user_already_authenticated(self):
        """Authenticated user accessing login view should immediately redirect."""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.dashboard_url)

    # ------------------------------------------------------------------
    # 3. Dashboard View Tests
    # ------------------------------------------------------------------
    def test_dashboard_unauthenticated_redirect(self):
        """Unauthenticated user attempting to view dashboard is redirected to login page."""
        response = self.client.get(self.dashboard_url)
        expected_redirect = f"/login/?next={self.dashboard_url}"
        self.assertRedirects(response, expected_redirect)

    def test_dashboard_authenticated_success_and_context_stats(self):
        """Authenticated dashboard view correctly calculates stats and context values."""
        self.client.force_login(self.user)

        # Create dummy user 2
        other_user = User.objects.create_user(username="otheruser", password="Password123!")

        # Create dummy WasteBanks
        WasteBank.objects.create(name="Bank A", latitude=-6.2, longitude=106.8)
        WasteBank.objects.create(name="Bank B", latitude=-6.3, longitude=106.9)

        # Create Reports (2 by self.user, 1 by other_user)
        Report.objects.create(reporter=self.user, title="Dump 1", latitude=-6.2, longitude=106.8)
        Report.objects.create(reporter=self.user, title="Dump 2", latitude=-6.2, longitude=106.8)
        Report.objects.create(reporter=other_user, title="Dump 3", latitude=-6.2, longitude=106.8)

        # Create Comment
        Comment.objects.create(user=self.user, content="Community test comment")

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

        # Check Context Calculations
        self.assertEqual(response.context['username'], self.username)
        self.assertEqual(response.context['stat_total_reports'], 3)
        self.assertEqual(response.context['stat_user_reports'], 2)
        self.assertEqual(response.context['stat_waste_banks'], 2)
        self.assertEqual(response.context['stat_points'], 20)  # 2 reports * 10 points
        self.assertEqual(len(response.context['dispatch_logs']), 3)
        self.assertEqual(len(response.context['comments']), 1)

    # ------------------------------------------------------------------
    # 4. Logout View Tests
    # ------------------------------------------------------------------
    def test_logout_user(self):
        """Logout logs user out, clears session, deletes 'last_login' cookie, and redirects to home."""
        self.client.force_login(self.user)
        self.client.cookies['last_login'] = '2026-03-30 10:00:00'

        response = self.client.get(self.logout_url)

        self.assertRedirects(response, '/')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(response.cookies['last_login'].value, '')

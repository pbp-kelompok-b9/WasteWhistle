import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from .models import QuizAttempt, QuizQuestion, WasteGuide


class EducationApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="learner", password="correct-horse")
        self.staff = user_model.objects.create_user(
            username="editor", password="correct-horse", is_staff=True,
        )
        self.guides = [self.make_guide(index) for index in range(4)]
        self.questions = [QuizQuestion.objects.create(item=guide) for guide in self.guides[:3]]

    def make_guide(self, index=0):
        categories = ["organik", "anorganik", "b3", "kertas"]
        return WasteGuide.objects.create(
            name=f"Waste {index}", category=categories[index % len(categories)],
            description="Description", handling_instruction="Handling",
        )

    def json_post(self, url, payload=None, **extra):
        return self.client.post(
            url, data=json.dumps(payload or {}), content_type="application/json", **extra,
        )

    def test_public_lists_use_results_envelope_and_guides_can_be_searched(self):
        response = self.client.get(reverse("waste_guide_api"), {"q": " WASTE 2 "})
        self.assertEqual([row["name"] for row in response.json()["results"]], ["Waste 2"])
        self.assertEqual(self.client.get(reverse("decomposition_info_api")).json(), {"results": []})
        self.assertEqual(self.client.get(reverse("myth_or_fact_api")).json(), {"results": []})

    def test_content_writes_require_staff_and_staff_can_create_patch_and_delete(self):
        list_url = reverse("waste_guide_api")
        payload = {
            "name": "New guide", "category": "organik",
            "description": "Description", "handling_instruction": "Handling",
        }
        self.assertIn(self.json_post(list_url, payload).status_code, (401, 403))
        self.client.force_login(self.staff)

        created = self.json_post(list_url, payload)
        self.assertEqual(created.status_code, 201)
        detail_url = reverse("waste_guide_detail_api", args=[created.json()["id"]])
        updated = self.client.patch(
            detail_url, data=json.dumps({"name": "Updated guide"}), content_type="application/json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["name"], "Updated guide")
        self.assertEqual(self.client.delete(detail_url).status_code, 204)

    def test_other_resources_accept_staff_creates(self):
        self.client.force_login(self.staff)
        cases = [
            ("decomposition_info_api", {"material_name": "Kaca", "estimated_days": 100}),
            ("myth_or_fact_api", {
                "statement": "A statement", "is_myth": True,
                "explanation": "Why", "source_url": "",
            }),
        ]
        for route, payload in cases:
            with self.subTest(route=route):
                response = self.json_post(reverse(route), payload)
                self.assertEqual(response.status_code, 201)
                self.assertIn("id", response.json())

    def test_token_login_and_revoke(self):
        login = self.json_post(reverse("api_token_auth"), {
            "username": "learner", "password": "correct-horse",
        })
        self.assertEqual(login.status_code, 200)
        key = login.json()["token"]
        self.assertTrue(Token.objects.filter(key=key, user=self.user).exists())
        today_response = self.client.get(
            reverse("today_quiz_api"), HTTP_AUTHORIZATION=f"Token {key}",
        )
        self.assertEqual(today_response.status_code, 200)
        self.assertEqual(today_response.json()["status"], "not_started")
        revoked = self.client.post(
            reverse("api_token_revoke"), HTTP_AUTHORIZATION=f"Token {key}",
        )
        self.assertEqual(revoked.status_code, 204)
        self.assertFalse(Token.objects.filter(key=key).exists())

    def test_quiz_start_is_stable_and_does_not_expose_correct_category(self):
        self.client.force_login(self.user)
        start_url = reverse("start_quiz_api")
        first = self.json_post(start_url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json(), self.json_post(start_url).json())
        self.assertEqual(first.json(), self.client.get(reverse("today_quiz_api")).json())
        self.assertEqual(first.json()["status"], "in_progress")
        self.assertEqual(len(first.json()["questions"]), 3)
        self.assertEqual(set(first.json()["questions"][0]), {"id", "item_name"})
        attempt = QuizAttempt.objects.get(user=self.user, attempt_date=timezone.localdate())
        self.assertIsNone(attempt.score)
        self.assertEqual(len(attempt.question_ids), QuizAttempt.QUIZ_SIZE)

    def test_answer_submit_history_and_completed_state(self):
        self.client.force_login(self.user)
        today = self.json_post(reverse("start_quiz_api")).json()
        for question in today["questions"]:
            model_question = QuizQuestion.objects.get(pk=question["id"])
            response = self.json_post(reverse("answer_question_api"), {
                "question_id": question["id"], "answer": model_question.item.category,
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["correct"])

        first_id = today["questions"][0]["id"]
        locked = self.json_post(reverse("answer_question_api"), {
            "question_id": first_id, "answer": "residu",
        })
        self.assertNotEqual(locked.json()["chosen"], "residu")

        submitted = self.json_post(reverse("quiz_attempt_list_api"))
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual((submitted.json()["score"], submitted.json()["total"]), (3, 3))
        self.assertEqual(QuizAttempt.objects.filter(user=self.user).count(), 1)
        self.assertEqual(self.client.get(reverse("today_quiz_api")).json()["status"], "completed")
        history = self.client.get(reverse("quiz_attempt_list_api")).json()["results"]
        self.assertEqual(history[0]["score"], 3)
        self.assertEqual(self.json_post(reverse("quiz_attempt_list_api")).json(), submitted.json())

    def test_quiz_requires_auth_and_rejects_foreign_question(self):
        self.assertIn(self.client.get(reverse("today_quiz_api")).status_code, (401, 403))
        self.client.force_login(self.user)
        self.json_post(reverse("start_quiz_api"))
        response = self.json_post(reverse("answer_question_api"), {
            "question_id": str(self.guides[3].id), "answer": "organik",
        })
        self.assertEqual(response.status_code, 400)

    def test_quiz_unavailable_without_three_questions_and_submit_requires_answers(self):
        self.client.force_login(self.user)
        self.assertEqual(self.json_post(reverse("start_quiz_api")).status_code, 200)
        QuizQuestion.objects.all().delete()
        other_user = get_user_model().objects.create_user(username="other", password="password")
        self.client.force_login(other_user)
        unavailable = self.json_post(reverse("start_quiz_api"))
        self.assertEqual(unavailable.status_code, 503)

        for guide in self.guides[:3]:
            QuizQuestion.objects.create(item=guide)
        self.json_post(reverse("start_quiz_api"))
        incomplete = self.json_post(reverse("quiz_attempt_list_api"))
        self.assertEqual(incomplete.status_code, 400)


class EducationPageTests(TestCase):
    def test_authenticated_page_uses_persistent_daily_quiz(self):
        user = get_user_model().objects.create_user(username="web-user", password="password")
        for index in range(3):
            guide = WasteGuide.objects.create(
                name=f"Material {index}", category="organik",
                description="Description", handling_instruction="Handling",
            )
            QuizQuestion.objects.create(item=guide)
        self.client.force_login(user)

        response = self.client.get(reverse("education"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["questions"]), 3)
        attempt = QuizAttempt.objects.get(user=user, attempt_date=timezone.localdate())
        self.assertIsNone(attempt.score)

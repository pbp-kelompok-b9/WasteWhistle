import json
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
from .models import DecompositionInfo, MythOrFact, QuizAttempt, QuizQuestion, WasteGuide
from .views import SESSION_KEY

class EducationModelTests(TestCase):
    def test_waste_guide_string_and_category_choices(self):
        guide = WasteGuide.objects.create(
            name="Kulit pisang",
            category="organik",
            description="Sisa buah.",
            handling_instruction="Masukkan ke komposter.",
        )

        self.assertEqual(str(guide), "Kulit pisang")
        self.assertIn(("organik", "Sampah Organik"), WasteGuide.CATEGORY_CHOICES)

    def test_myth_or_fact_string(self):
        statement = MythOrFact.objects.create(
            statement="Sampah organik dapat dikomposkan.",
            is_myth=False,
            explanation="Bahan organik dapat diolah menjadi kompos.",
        )

        self.assertEqual(str(statement), statement.statement)

    def test_decomposition_formatted_duration_boundaries(self):
        cases = [
            (0, "0 hari"),
            (29, "29 hari"),
            (30, "1 bulan"),
            (180, "6 bulan"),
            (364, "11 bulan"),
            (365, "1 tahun"),
            (730, "2 tahun"),
        ]
        for days, expected in cases:
            with self.subTest(days=days):
                info = DecompositionInfo(material_name="Bahan", estimated_days=days)
                self.assertEqual(info.formatted_duration, expected)

    def test_decomposition_bar_percent_is_clamped_and_rounded(self):
        self.assertEqual(
            DecompositionInfo(material_name="Bahan", estimated_days=0).bar_percent,
            0,
        )
        self.assertEqual(
            DecompositionInfo(
                material_name="Bahan", estimated_days=365 * 1_000_000
            ).bar_percent,
            100,
        )
        self.assertGreaterEqual(
            DecompositionInfo(material_name="Bahan", estimated_days=100).bar_percent,
            5,
        )

    def test_decomposition_bar_level_boundaries(self):
        cases = [(123, "short"), (364, "short"), (365, "medium"), (365 * 300 - 1, "medium"), (365 * 300, "long"), (365 * 400, "long")]
        for days, expected in cases:
            with self.subTest(days=days):
                info = DecompositionInfo(material_name="Bahan", estimated_days=days)
                self.assertEqual(info.bar_level, expected)

    def test_quiz_question_is_unique_per_waste_guide_and_string(self):
        guide = self.make_guide("Botol", "anorganik")
        question = QuizQuestion.objects.create(item=guide)

        self.assertEqual(str(question), "Botol")
        with self.assertRaises(IntegrityError):
            QuizQuestion.objects.create(item=guide)

    def test_quiz_attempt_string_default_score_and_unique_daily_attempt(self):
        user = get_user_model().objects.create_user(username="Park Moondae", password="cutitout")
        attempt = QuizAttempt.objects.create(user=user)

        self.assertEqual(attempt.attempt_date, timezone.localdate())
        self.assertEqual(attempt.score, 0)
        self.assertEqual(str(attempt), f"{user} - {timezone.localdate()}")
        with self.assertRaises(Exception):
            QuizAttempt.objects.create(user=user, attempt_date=timezone.localdate())

    @staticmethod
    def make_guide(name, category):
        return WasteGuide.objects.create(
            name=name,
            category=category,
            description=f"Deskripsi {name}",
            handling_instruction=f"Tangani {name}",
        )

class EducationPageTests(TestCase):
    def setUp(self):
        self.url = reverse("education")
        self.guide = WasteGuide.objects.create(
            name="Kulit jeruk",
            category="organik",
            description="Sisa buah yang dapat dikomposkan.",
            handling_instruction="Pisahkan untuk kompos.",
        )
        self.info = DecompositionInfo.objects.create(
            material_name="Kulit jeruk", estimated_days=180
        )
        self.fact = MythOrFact.objects.create(
            statement="Memilah sampah membantu daur ulang.",
            is_myth=False,
            explanation="Sampah terpilah lebih mudah diolah.",
            source_url="https://example.com/fakta",
        )

    def test_page_renders_education_sections_and_database_content(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education.html")
        self.assertEqual(response.context["active_page"], "education")
        self.assertContains(response, "Waste Education")
        self.assertContains(response, "Lama Penguraian")
        self.assertContains(response, "Penanganan Sampah")
        self.assertContains(response, "Flip Card: Mitos atau Fakta?")
        self.assertContains(response, self.guide.name)
        self.assertContains(response, self.guide.description)
        self.assertContains(response, self.guide.handling_instruction)
        self.assertContains(response, self.info.material_name)
        self.assertContains(response, self.info.formatted_duration)
        self.assertContains(response, self.fact.statement)
        self.assertContains(response, self.fact.explanation)
        self.assertContains(response, "Fakta")
        self.assertContains(response, self.fact.source_url)
        self.assertContains(response, "education.js")

    def test_anonymous_page_shows_login_prompt_without_quiz_questions(self):
        self.make_questions(3)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["questions"])
        self.assertFalse(response.context["already_played"])
        self.assertContains(response, "Masuk untuk mengikuti kuis")
        self.assertContains(response, reverse("login_user"))
        self.assertContains(response, 'data-can-play="false"')

    def test_authenticated_user_gets_three_stable_daily_questions(self):
        user = get_user_model().objects.create_user(username="Kim Dokja", password="uglysquid")
        self.client.force_login(user)
        self.make_questions(4)

        first = self.client.get(self.url)
        first_ids = [str(question.id) for question in first.context["questions"]]
        second = self.client.get(self.url)
        second_ids = [str(question.id) for question in second.context["questions"]]

        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first_ids), 3)
        self.assertEqual(len(set(first_ids)), 3)
        self.assertEqual(second_ids, first_ids)
        self.assertContains(first, 'data-can-play="true"')
        self.assertEqual(
            self.client.session[SESSION_KEY]["date"], timezone.localdate().isoformat()
        )

    def test_authenticated_user_without_three_questions_sees_empty_state(self):
        user = get_user_model().objects.create_user(username="Halo", password="evensowedo")
        self.client.force_login(user)
        self.make_questions(2)

        response = self.client.get(self.url)

        self.assertEqual(response.context["questions"], [])
        self.assertContains(response, "Belum ada kuis yang tersedia")
        self.assertContains(response, 'data-can-play="false"')

    def test_already_played_user_sees_saved_score(self):
        user = get_user_model().objects.create_user(username="Roh Haeil", password="anotherday")
        self.client.force_login(user)
        self.make_questions(3)
        QuizAttempt.objects.create(user=user, attempt_date=timezone.localdate(), score=2)

        response = self.client.get(self.url)

        self.assertTrue(response.context["already_played"])
        self.assertEqual(response.context["daily_score"], 2)
        self.assertEqual(response.context["questions"], [])
        self.assertContains(response, "skor: 2/3")
        self.assertContains(response, 'data-can-play="false"')

    def test_page_orders_guides_and_decomposition_data(self):
        guide_last = WasteGuide.objects.create(
            name="Sisa sayuran", category="organik", description="Sisa sayur dari masakan", handling_instruction="Kumpulkan untuk pengomposan."
        )
        guide_first = WasteGuide.objects.create(
            name="Aki", category="b3", description="Aki bekas", handling_instruction="Pisahkan"
        )
        info_long = DecompositionInfo.objects.create(material_name="Kaleng alumunium", estimated_days=365*100)

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["waste_guides"]), [guide_first, self.guide, guide_last])
        self.assertEqual(
            list(response.context["decomposition_infos"]),
            [self.info, info_long],
        )

    def make_questions(self, count):
        categories = [choice[0] for choice in WasteGuide.CATEGORY_CHOICES]
        for index in range(count):
            guide = WasteGuide.objects.create(
                name=f"Item kuis {index}",
                category=categories[index % len(categories)],
                description="Deskripsi",
                handling_instruction="Instruksi",
            )
            QuizQuestion.objects.create(item=guide)


class WasteGuideApiTests(TestCase):
    def setUp(self):
        self.url = reverse("waste_guide_api")
        self.guide_a = WasteGuide.objects.create(
            name="Botol plastik",
            category="anorganik",
            description="Kemasan plastik.",
            handling_instruction="Bersihkan dan setor ke bank sampah.",
        )
        self.guide_b = WasteGuide.objects.create(
            name="Kulit pisang",
            category="organik",
            description="Sisa buah.",
            handling_instruction="Olah menjadi kompos.",
        )

    def test_returns_all_guides_alphabetically_with_display_category(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [
            {
                "id": str(self.guide_a.id),
                "name": self.guide_a.name,
                "category": "anorganik",
                "category_display": "Sampah Anorganik",
                "description": self.guide_a.description,
                "handling_instruction": self.guide_a.handling_instruction,
            },
            {
                "id": str(self.guide_b.id),
                "name": self.guide_b.name,
                "category": "organik",
                "category_display": "Sampah Organik",
                "description": self.guide_b.description,
                "handling_instruction": self.guide_b.handling_instruction,
            },
        ])

    def test_search_is_case_insensitive_and_ignores_outer_spaces(self):
        response = self.client.get(self.url, {"q": "  BOTOL  "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()["results"]], [str(self.guide_a.id)])

    def test_search_without_match_returns_empty_list(self):
        response = self.client.get(self.url, {"q": "kaca"})

        self.assertEqual(response.json(), {"results": []})

    def test_api_rejects_non_get_methods(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 405)


class SubmitQuizApiTests(TestCase):
    def setUp(self):
        self.url = reverse("submit_quiz_api")
        self.user = get_user_model().objects.create_user(username="Lloyd Frontera", password="money")
        self.questions = []
        categories = ["organik", "anorganik", "b3"]
        for index, category in enumerate(categories):
            guide = WasteGuide.objects.create(
                name=f"Quiz item {index}",
                category=category,
                description="Deskripsi",
                handling_instruction="Instruksi",
            )
            self.questions.append(QuizQuestion.objects.create(item=guide))

    def put_quiz_in_session(self, ids=None, day=None):
        session = self.client.session
        session[SESSION_KEY] = {
            "date": (day or timezone.localdate()).isoformat(),
            "question_ids": ids if ids is not None else [str(q.id) for q in self.questions],
        }
        session.save()

    def submit(self, answers=None, raw=None):
        if raw is not None:
            return self.client.post(self.url, data=raw, content_type="application/json")
        return self.client.post(
            self.url,
            data=json.dumps({"answers": answers}),
            content_type="application/json",
        )

    def test_anonymous_submission_is_unauthorized(self):
        response = self.submit({})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Silakan masuk terlebih dahulu."})

    def test_non_post_method_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_submission_requires_a_valid_current_quiz_session(self):
        self.client.force_login(self.user)
        response = self.submit({})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Kuis tidak ditemukan", response.json()["error"])

        self.put_quiz_in_session(day=date(2000, 1, 1))
        response = self.submit({})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Kuis tidak ditemukan", response.json()["error"])

    def test_submission_rejects_malformed_session_and_duplicate_ids(self):
        self.client.force_login(self.user)
        for ids in ["not-a-list", [str(self.questions[0].id)] * 3, [1, 2, 3]]:
            with self.subTest(ids=ids):
                self.put_quiz_in_session(ids=ids)
                response = self.submit({})
                self.assertEqual(response.status_code, 400)
                self.assertIn("Kuis tidak ditemukan", response.json()["error"])

    def test_submission_rejects_invalid_json_and_invalid_answers_shape(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()

        for raw in ["{", json.dumps([]), json.dumps({"answers": []}), json.dumps({})]:
            with self.subTest(raw=raw):
                response = self.submit(raw=raw)
                self.assertEqual(response.status_code, 400)

    def test_submission_requires_exactly_all_question_ids_and_valid_categories(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        expected = {str(question.id): question.item.category for question in self.questions}

        invalid_answers = [
            {},
            {**expected, "unexpected-id": "organik"},
            {key: value for key, value in list(expected.items())[:-1]},
            {**expected, str(self.questions[0].id): "kategori-salah"},
            {**expected, str(self.questions[0].id): 1},
        ]
        for answers in invalid_answers:
            with self.subTest(answers=answers):
                response = self.submit(answers)
                self.assertEqual(response.status_code, 400)
                self.assertIn("Jawab semua soal", response.json()["error"])
                self.assertFalse(QuizAttempt.objects.filter(user=self.user).exists())

    def test_submission_scores_answers_saves_attempt_and_consumes_session(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        answers = {
            str(question.id): question.item.category for question in self.questions
        }
        answers[str(self.questions[1].id)] = "residu"

        response = self.submit(answers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"score": 2, "total": 3})
        attempt = QuizAttempt.objects.get(user=self.user, attempt_date=timezone.localdate())
        self.assertEqual(attempt.score, 2)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_submission_reports_deleted_quiz_questions(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        self.questions[0].delete()

        response = self.submit({})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Soal kuis berubah", response.json()["error"])
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_can_only_submit_once_per_day(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        answers = {str(q.id): q.item.category for q in self.questions}
        first = self.submit(answers)
        self.assertEqual(first.status_code, 200)

        second = self.submit(answers)

        self.assertEqual(second.status_code, 409)
        self.assertIn("sudah mengikuti", second.json()["error"])
        self.assertEqual(QuizAttempt.objects.filter(user=self.user).count(), 1)

    def test_existing_attempt_is_rejected_even_if_session_exists(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        QuizAttempt.objects.create(user=self.user, attempt_date=timezone.localdate(), score=1)

        response = self.submit({})

        self.assertEqual(response.status_code, 409)

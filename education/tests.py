import json
import uuid
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
from .models import DecompositionInfo, MythOrFact, QuizAttempt, QuizQuestion, WasteGuide
from .views import SESSION_KEY, QUIZ_SIZE
from .forms import DecompositionInfoForm, MythOrFactForm, WasteGuideForm

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
            (365 * 450, "450 tahun"),
            (365 * 1000, "1.000 tahun"),
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

    def test_stale_session_questions_are_replaced(self):
        user = get_user_model().objects.create_user(username="Han Sooyoung", password="omniscient")
        self.client.force_login(user)
        self.make_questions(3)
        session = self.client.session
        session[SESSION_KEY] = {"date": "2000-01-01", "question_ids": ["a", "b", "c"]}
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["questions"]), 3)
        self.assertEqual(
            self.client.session[SESSION_KEY]["date"], timezone.localdate().isoformat()
        )

    def test_quiz_markup_does_not_leak_answers(self):
        user = get_user_model().objects.create_user(username="Jung Heewon", password="sword")
        self.client.force_login(user)
        self.make_questions(3)

        response = self.client.get(self.url)

        self.assertNotContains(response, 'data-answer="')
        self.assertContains(response, 'data-answer-url="')
        self.assertEqual(self.client.session[SESSION_KEY]["answers"], {})

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
        self.assertContains(response, f"skor: 2/{QUIZ_SIZE}")
        self.assertEqual(response.context["quiz_size"], QUIZ_SIZE)
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


class EducationFormTests(TestCase):
    def test_waste_guide_form_strips_html_from_plain_text_fields(self):
        form = WasteGuideForm(data={
            "name": "<b>Botol</b>",
            "category": "anorganik",
            "description": "<p>Kemasan plastik.</p>",
            "handling_instruction": "<em>Bersihkan dahulu.</em>",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["name"], "Botol")
        self.assertEqual(form.cleaned_data["description"], "Kemasan plastik.")
        self.assertEqual(
            form.cleaned_data["handling_instruction"], "Bersihkan dahulu."
        )

    def test_plain_text_fields_reject_values_containing_only_html(self):
        cases = [
            (WasteGuideForm, {
                "name": "<b></b>", "category": "organik",
                "description": "<p>Deskripsi</p>",
                "handling_instruction": "Instruksi",
            }, "name"),
            (DecompositionInfoForm, {
                "material_name": "<b></b>", "estimated_days": "12",
            }, "material_name"),
            (MythOrFactForm, {
                "statement": "Pernyataan", "is_myth": "False",
                "explanation": "<p></p>", "source_url": "",
            }, "explanation"),
        ]

        for form_class, data, field in cases:
            with self.subTest(form=form_class.__name__, field=field):
                form = form_class(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_myth_or_fact_form_coerces_classification_to_boolean(self):
        data = {
            "statement": "Sampah harus dipilah.",
            "is_myth": "False",
            "explanation": "Pernyataan benar.",
            "source_url": "",
        }
        form = MythOrFactForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIs(form.cleaned_data["is_myth"], False)


class EducationCrudViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="education-admin", password="test-password"
        )
        self.manage_permission = Permission.objects.get(
            content_type__app_label="education",
            codename="manage_education_content",
        )

    def grant_manage_permission(self):
        self.user.user_permissions.add(self.manage_permission)
        self.client.force_login(self.user)

    def make_guide(self, name="Botol", description="Kemasan plastik."):
        return WasteGuide.objects.create(
            name=name,
            category="anorganik",
            description=description,
            handling_instruction="Bersihkan sebelum disetor.",
        )

    def test_crud_management_requires_login_and_permission(self):
        create_url = reverse("education_create", args=["guide"])
        anonymous_response = self.client.post(create_url, data={})
        self.assertEqual(anonymous_response.status_code, 302)

        self.client.force_login(self.user)
        forbidden_response = self.client.post(create_url, data={})
        self.assertEqual(forbidden_response.status_code, 403)

    def test_create_form_and_picker_render_for_permitted_user(self):
        guide = self.make_guide()
        self.grant_manage_permission()

        form_response = self.client.get(
            reverse("education_create_form", args=["guide"])
        )
        picker_response = self.client.get(
            reverse("education_item_picker", args=["guide"]),
            {"action": "edit"},
        )

        self.assertEqual(form_response.status_code, 200)
        self.assertContains(form_response, "Tambah Panduan Sampah")
        self.assertEqual(picker_response.status_code, 200)
        self.assertContains(picker_response, guide.name)

    def test_create_update_and_delete_guide(self):
        self.grant_manage_permission()
        create_url = reverse("education_create", args=["guide"])
        data = {
            "name": "<b>Kaleng</b>",
            "category": "anorganik",
            "description": "<p>Kemasan logam.</p>",
            "handling_instruction": "Pisahkan.",
        }

        create_response = self.client.post(create_url, data=data)

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(
            create_response.headers["HX-Trigger"], "educationContentChanged"
        )
        guide = WasteGuide.objects.get(name="Kaleng")
        update_response = self.client.post(
            reverse("education_update", args=["guide", guide.pk]),
            {**data, "name": "<b>Kaleng bekas</b>"},
        )
        guide.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(guide.name, "Kaleng bekas")

        delete_response = self.client.post(
            reverse("education_delete", args=["guide", guide.pk])
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(WasteGuide.objects.filter(pk=guide.pk).exists())

    def test_invalid_create_and_update_render_form_errors_without_saving(self):
        self.grant_manage_permission()
        create_response = self.client.post(
            reverse("education_create", args=["guide"]),
            {
                "name": "<b></b>", "category": "anorganik",
                "description": "Deskripsi", "handling_instruction": "Instruksi",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, "tidak boleh kosong", status_code=200)
        self.assertEqual(WasteGuide.objects.count(), 0)

        guide = self.make_guide()
        update_response = self.client.post(
            reverse("education_update", args=["guide", guide.pk]),
            {
                "name": "Nama baru", "category": "anorganik",
                "description": "<p></p>", "handling_instruction": "Instruksi",
            },
        )
        guide.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertContains(update_response, "tidak boleh kosong", status_code=200)
        self.assertEqual(guide.name, "Botol")


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
                "description": self.guide_a.description,
                "handling_instruction": self.guide_a.handling_instruction,
            },
            {
                "id": str(self.guide_b.id),
                "name": self.guide_b.name,
                "category": "organik",
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

class QuizFixtureMixin:
    """Dipakai SubmitQuizApiTests dan AnswerQuestionApiTests."""

    def create_quiz_questions(self):
        self.questions = []
        for index, category in enumerate(["organik", "anorganik", "b3"]):
            guide = WasteGuide.objects.create(
                name=f"Quiz item {index}",
                category=category,
                description="Deskripsi",
                handling_instruction="Instruksi",
            )
            self.questions.append(QuizQuestion.objects.create(item=guide))

    def put_quiz_in_session(self, ids=None, day=None, answers=None):
        session = self.client.session
        session[SESSION_KEY] = {
            "date": (day or timezone.localdate()).isoformat(),
            "question_ids": ids if ids is not None else [str(q.id) for q in self.questions],
            "answers": answers if answers is not None else {},
        }
        session.save()

    def correct_answers(self):
        return {str(q.id): q.item.category for q in self.questions}
    
class SubmitQuizApiTests(QuizFixtureMixin, TestCase):
    def setUp(self):
        self.url = reverse("submit_quiz_api")
        self.user = get_user_model().objects.create_user(username="Lloyd Frontera", password="money")
        self.create_quiz_questions()

    def submit(self):
        return self.client.post(self.url)

    def test_anonymous_submission_is_unauthorized(self):
        response = self.submit()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Silakan masuk terlebih dahulu."})

    def test_non_post_method_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_submission_requires_a_valid_current_quiz_session(self):
        self.client.force_login(self.user)
        response = self.submit()
        self.assertEqual(response.status_code, 400)
        self.assertIn("Kuis tidak ditemukan", response.json()["error"])

        self.put_quiz_in_session(day=date(2000, 1, 1))
        response = self.submit()
        self.assertEqual(response.status_code, 400)
        self.assertIn("Kuis tidak ditemukan", response.json()["error"])

    def test_submission_rejects_malformed_session_and_duplicate_ids(self):
        self.client.force_login(self.user)
        for ids in ["not-a-list", [str(self.questions[0].id)] * 3, [1, 2, 3]]:
            with self.subTest(ids=ids):
                self.put_quiz_in_session(ids=ids)
                response = self.submit()
                self.assertEqual(response.status_code, 400)
                self.assertIn("Kuis tidak ditemukan", response.json()["error"])

    def test_submission_requires_all_questions_answered_in_session(self):
        self.client.force_login(self.user)
        partial = dict(list(self.correct_answers().items())[:-1])

        for answers in [{}, partial]:
            with self.subTest(answers=answers):
                self.put_quiz_in_session(answers=answers)
                response = self.submit()
                self.assertEqual(response.status_code, 400)
                self.assertIn("Jawab semua soal", response.json()["error"])
                self.assertFalse(QuizAttempt.objects.filter(user=self.user).exists())

    def test_submission_ignores_answers_sent_in_request_body(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session(answers={str(q.id): "residu" for q in self.questions})
        forged = json.dumps({"answers": self.correct_answers(), "score": 3})

        response = self.client.post(self.url, data=forged, content_type="application/json")

        self.assertEqual(response.json(), {"score": 0, "total": 3})

    def test_submission_scores_answers_saves_attempt_and_consumes_session(self):
        self.client.force_login(self.user)
        answers = self.correct_answers()
        answers[str(self.questions[1].id)] = "residu"
        self.put_quiz_in_session(answers=answers)

        response = self.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"score": 2, "total": 3})
        attempt = QuizAttempt.objects.get(user=self.user, attempt_date=timezone.localdate())
        self.assertEqual(attempt.score, 2)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_submission_reports_deleted_quiz_questions(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session(answers=self.correct_answers())
        self.questions[0].delete()

        response = self.submit()

        self.assertEqual(response.status_code, 400)
        self.assertIn("Soal kuis berubah", response.json()["error"])
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_can_only_submit_once_per_day(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session(answers=self.correct_answers())
        first = self.submit()
        self.assertEqual(first.status_code, 200)

        second = self.submit()

        self.assertEqual(second.status_code, 409)
        self.assertIn("sudah mengikuti", second.json()["error"])
        self.assertEqual(QuizAttempt.objects.filter(user=self.user).count(), 1)

    def test_existing_attempt_is_rejected_even_if_session_exists(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        QuizAttempt.objects.create(user=self.user, attempt_date=timezone.localdate(), score=1)

        response = self.submit()

        self.assertEqual(response.status_code, 409)

class AnswerQuestionApiTests(QuizFixtureMixin, TestCase):
    def setUp(self):
        self.url = reverse("answer_question_api")
        self.user = get_user_model().objects.create_user(username="Yoo Joonghyuk", password="regressor")
        self.create_quiz_questions()
        self.question = self.questions[0]        

    def answer(self, question_id=None, answer="organik", raw=None):
        if raw is not None:
            return self.client.post(self.url, data=raw, content_type="application/json")
        body = {"question_id": question_id or str(self.question.id), "answer": answer}
        return self.client.post(self.url, data=json.dumps(body), content_type="application/json")

    def test_anonymous_is_unauthorized(self):
        self.assertEqual(self.answer().status_code, 401)

    def test_non_post_method_is_rejected(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_requires_a_valid_current_quiz_session(self):
        self.client.force_login(self.user)
        self.assertEqual(self.answer().status_code, 400)

    def test_rejects_malformed_session_answers(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session(answers=["not", "a", "dictionary"])

        response = self.answer()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Data jawaban tidak valid."})

    def test_existing_attempt_is_rejected(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        QuizAttempt.objects.create(user=self.user, attempt_date=timezone.localdate(), score=1)

        self.assertEqual(self.answer().status_code, 409)

    def test_rejects_invalid_payloads(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        qid = str(self.question.id)

        bad_bodies = [
            "{",
            json.dumps([]),
            json.dumps({}),
            json.dumps({"question_id": qid}),                           # tanpa answer
            json.dumps({"question_id": qid, "answer": "kategori-salah"}),
            json.dumps({"question_id": qid, "answer": 1}),
            json.dumps({"question_id": 1, "answer": "organik"}),
            json.dumps({"question_id": str(uuid.uuid4()), "answer": "organik"}),  # bukan soal hari ini
        ]
        for raw in bad_bodies:
            with self.subTest(raw=raw):
                self.assertEqual(self.answer(raw=raw).status_code, 400)

    def test_correct_answer_is_reported_and_stored_in_session(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()

        response = self.answer(answer="organik")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"correct": True, "correct_bin": "organik", "chosen": "organik"},
        )
        self.assertEqual(
            self.client.session[SESSION_KEY]["answers"],
            {str(self.question.id): "organik"},
        )

    def test_wrong_answer_reveals_correct_bin(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()

        response = self.answer(answer="residu")

        self.assertEqual(
            response.json(),
            {"correct": False, "correct_bin": "organik", "chosen": "residu"},
        )

    def test_first_answer_is_locked(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        self.answer(answer="residu")

        response = self.answer(answer="organik")     # coba ganti jawaban

        self.assertFalse(response.json()["correct"])
        self.assertEqual(response.json()["chosen"], "residu")

    def test_answers_flow_into_submit_score(self):
        self.client.force_login(self.user)
        self.put_quiz_in_session()
        for question in self.questions:
            self.answer(question_id=str(question.id), answer=question.item.category)

        response = self.client.post(reverse("submit_quiz_api"))

        self.assertEqual(response.json(), {"score": 3, "total": 3})

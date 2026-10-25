/* Quiz: Which Bin? */
function setupQuiz() {

    /* Area bermain */
    const playArea = document.getElementById("quiz-play");
    if (playArea === null) {
        return;
    }

    /* Ambil elemen-elemen yang akan diubah */
    const progressText = document.getElementById("quiz-progress");
    const itemText = document.getElementById("quiz-item");
    const feedbackText = document.getElementById("quiz-feedback");
    const nextButton = document.getElementById("quiz-next");
    const resultBox = document.getElementById("quiz-result");
    const scoreText = document.getElementById("quiz-score");
    const scoreIndicator = document.getElementById("quiz-score-indicator");
    const binButtons = document.querySelectorAll(".bin");

    /* Ubah daftar <li> di #quiz-data menjadi daftar soal. */
    const questionElements = document.querySelectorAll("#quiz-data li");
    const questions = [...questionElements].map(function (element) {
        return {
            id: element.dataset.id,
            item: element.textContent.trim(),
            answer: element.dataset.answer,
            tip: element.dataset.tip
        };
    });

    if (playArea.dataset.canPlay !== "true") {
        binButtons.forEach(function (button) { button.disabled = true; });
    }

    if (questions.length === 0) {
        return;
    }

    /* Data yang berubah selama kuis berjalan */
    let currentQuestion = 0;    // soal ke berapa (0 = soal pertama)
    let score = 0;              // jumlah jawaban benar
    let hasAnswered = false;    // sudah menjawab soal ini atau belum
    const answers = {};

    /* Tampilkan soal yang sedang aktif */
    function showQuestion() {
        const question = questions[currentQuestion];

        progressText.textContent = "Item " + (currentQuestion + 1) + " of " + questions.length;
        scoreIndicator.textContent = "Score: " + score + "/3";
        itemText.textContent = question.item;

        // Reset: sembunyikan penjelasan, aktifkan lagi semua tong
        feedbackText.hidden = true;
        nextButton.hidden = true;
        hasAnswered = false;

        binButtons.forEach(function (button) {
            button.disabled = false;
            button.classList.remove("is-correct");
        });
    }


    /* Dipanggil saat pengguna mengklik salah satu tong */
    function handleAnswer(chosenBin) {
        // Kalau soal ini sudah dijawab, abaikan klik berikutnya
        if (hasAnswered) {
            return;
        }
        hasAnswered = true;

        const question = questions[currentQuestion];
        answers[question.id] = chosenBin;
        const isCorrect = (chosenBin === question.answer);

        if (isCorrect) {
            score = score + 1;
        }
        scoreIndicator.textContent = "Score: " + score + "/3";

        // Cari tulisan di tong yang benar
        let correctLabel = question.answer;
        binButtons.forEach(function (button) {
            if (button.dataset.bin === question.answer) {
                correctLabel = button.textContent;
            }
        });

        // Tampilkan hasil + penjelasan cara menanganinya
        if (isCorrect) {
            feedbackText.textContent = "Correct. " + question.tip;
        } else {
            feedbackText.textContent = "Not quite. It goes in " + correctLabel + ". " + question.tip;
        }
        feedbackText.hidden = false;

        // Matikan semua tong, beri garis pada tong yang benar
        binButtons.forEach(function (button) {
            button.disabled = true;

            if (button.dataset.bin === question.answer) {
                button.classList.add("is-correct");
            }
        });

        // Tombol berikutnya berubah jadi "See score" di soal terakhir
        const isLastQuestion = (currentQuestion === questions.length - 1);
        nextButton.textContent = isLastQuestion ? "See score" : "Next item";
        nextButton.hidden = false;
    }


    /* Pindah ke soal berikutnya, atau tampilkan skor kalau soal sudah habis */
    function goToNext() {
        currentQuestion = currentQuestion + 1;

        if (currentQuestion < questions.length) {
            showQuestion();
        } else {
            showResult();
        }
    }


    /* Tampilkan skor akhir */        
    async function showResult() {
        const submitUrl = playArea.dataset.submitUrl;
        const csrfInput = document.querySelector(
            "#quiz-csrf-form [name=csrfmiddlewaretoken]"
        );

        nextButton.disabled = true;
        scoreText.textContent = "Saving your result...";

        try {
            const response = await fetch(submitUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfInput ? csrfInput.value : ""
                },
                body: JSON.stringify({ answers: answers })
            });

            const data = await response.json();

            if (!response.ok) {
                scoreText.textContent = data.error ||
                    "Unable to save your quiz result. Please reload the page.";
                resultBox.hidden = false;
                nextButton.disabled = false;
                return;
            }

            scoreText.textContent =
                data.score + "/3";
            scoreIndicator.textContent = "Score: " + data.score + "/3";

            playArea.hidden = true;
            resultBox.hidden = false;

        } catch (error) {
            console.error(error);
            scoreText.textContent =
                "Unable to connect to the server. Please try again.";
            resultBox.hidden = false;
            nextButton.disabled = false;
        }
    }

    /* Hubungkan tombol-tombol dengan fungsi di atas */
    binButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            handleAnswer(button.dataset.bin);
        });
    });

    nextButton.addEventListener("click", goToNext);

    // Tampilkan soal pertama saat halaman dibuka
    showQuestion();
}


/* Pencarian Waste Guide */
function createGuideItem(guide) {
    const item = document.createElement("details");
    item.className = "guide-item";

    // Baris judul: nama + badge kategori
    const summary = document.createElement("summary");

    const name = document.createElement("span");
    name.className = "guide-name";
    name.textContent = guide.name;

    const badge = document.createElement("span");
    badge.className = "category-badge category-" + guide.category;
    badge.textContent = guide.category_display || guide.category;

    summary.append(name, badge);

    // Isi: deskripsi + cara menangani
    const description = document.createElement("p");
    description.textContent = guide.description;

    const handling = document.createElement("p");
    const handlingLabel = document.createElement("strong");
    handlingLabel.textContent = "Cara menangani: ";
    handling.append(handlingLabel, " " + guide.handling_instruction);

    item.append(summary, description, handling);
    return item;
}


/* Menampilkan satu pesan teks di kotak hasil (untuk "kosong" atau "error") */
function showMessage(container, text) {
    const message = document.createElement("p");
    message.className = "text-soft";
    message.textContent = text;
    container.replaceChildren(message);
}


function setupGuideSearch() {
    const searchInput = document.getElementById("guide-search");
    const resultsBox = document.getElementById("guide-results");

    if (searchInput === null || resultsBox === null) {
        return;
    }

    // Alamat API dititipkan Django lewat atribut data-api-url
    const apiUrl = resultsBox.dataset.apiUrl;
    let timerId;

    /* Minta data ke API lalu tampilkan */
    async function loadGuides(keyword) {
        try {
            const url = new URL(apiUrl, window.location.origin);
            url.searchParams.set("q", keyword);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error("Failed to fetch waste guides");
            }

            const data = await response.json();

            if (data.results.length === 0) {
                showMessage(resultsBox, "No matching waste guides found.");
                return;
            }

            // Bangun semua item, lalu ganti isi kotak hasil sekaligus
            const items = data.results.map(createGuideItem);
            resultsBox.replaceChildren(...items);

        } catch (error) {
            console.error(error);
            showMessage(resultsBox, "Unable to load waste guides. Please try again.");
        }
    }

    /* Setiap ketikan: batalkan timer lama, pasang timer baru */
    searchInput.addEventListener("input", function () {
        clearTimeout(timerId);

        timerId = setTimeout(function () {
            loadGuides(searchInput.value.trim());
        }, 250);
    });
}


setupQuiz();
setupGuideSearch();


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

        progressText.textContent = "Soal " + (currentQuestion + 1) + " dari " + questions.length;
        scoreIndicator.textContent = "Skor: " + score + "/3";
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
        scoreIndicator.textContent = "Skor: " + score + "/3";

        // Cari tulisan di tong yang benar
        let correctLabel = question.answer;
        binButtons.forEach(function (button) {
            if (button.dataset.bin === question.answer) {
                correctLabel = button.textContent;
            }
        });

        // Tampilkan hasil + penjelasan cara menanganinya
        if (isCorrect) {
            feedbackText.textContent = "Benar!";
        } else {
            feedbackText.textContent = "Belum tepat. Sampah ini masuk ke " + correctLabel + ".";
        }
        feedbackText.hidden = false;

        // Matikan semua tong selain tong yang benar
        binButtons.forEach(function (button) {
            button.disabled = true;

            if (button.dataset.bin === question.answer) {
                button.classList.add("is-correct");
            }
        });

        // Tombol berikutnya berubah jadi "Lihat skor" di soal terakhir
        const isLastQuestion = (currentQuestion === questions.length - 1);
        nextButton.textContent = isLastQuestion ? "Lihat skor" : "Soal berikutnya";
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
        scoreText.textContent = "Menyimpan hasil kuis...";

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
                feedbackText.textContent = data.error ||
                    "Hasil kuis tidak dapat disimpan. Muat ulang halaman dan coba lagi.";
                feedbackText.hidden = false;
                nextButton.disabled = false;
                return;
            }

            scoreText.textContent =
                data.score + "/3";
            scoreIndicator.textContent = "Skor: " + data.score + "/3";

            playArea.hidden = true;
            resultBox.hidden = false;

        } catch (error) {
            console.error(error);
            feedbackText.textContent = "Tidak dapat terhubung ke server. Silakan coba lagi.";
            feedbackText.hidden = false;
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
    item.className = "guide-item mt-2 rounded-xl border border-[#E2EDE6] bg-white px-3.5 py-3";

    // Baris judul: nama + badge kategori
    const summary = document.createElement("summary");
    summary.className = "flex items-center justify-start gap-2 text-[13px] font-semibold";

    const name = document.createElement("span");
    name.className = "guide-name";
    name.textContent = guide.name;

    const badge = document.createElement("span");
    badge.className = "ml-auto shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-bold capitalize tracking-[0.04em] category-badge category-" + guide.category;
    badge.textContent = guide.category_display || guide.category;

    summary.append(name, badge);

    // Isi: deskripsi + cara menangani
    const description = document.createElement("p");
    description.className = "mt-2 text-[12px] text-[#6C7D75]";
    description.textContent = guide.description;

    const handling = document.createElement("p");
    handling.className = "mt-2 text-[12px] text-[#6C7D75]";
    const handlingLabel = document.createElement("strong");
    handlingLabel.textContent = "Cara penanganan:";
    handling.append(handlingLabel, " " + guide.handling_instruction);

    item.append(summary, description, handling);
    return item;
}


/* Menampilkan satu pesan teks di kotak hasil (untuk "kosong" atau "error") */
function showMessage(container, text) {
    const message = document.createElement("p");
    message.className = "mt-3 text-[13px] text-[#6C7D75]";
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
    let latestRequest = 0;

    /* Minta data ke API lalu tampilkan */
    async function loadGuides(keyword) {
        const requestId = ++latestRequest;
        try {
            const url = new URL(apiUrl, window.location.origin);
            url.searchParams.set("q", keyword);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error("Gagal memuat panduan sampah.");
            }

            const data = await response.json();
            if (requestId !== latestRequest) {
                return;
            }

            if (!data || !Array.isArray(data.results)) {
                throw new Error("Format data panduan tidak valid.");
            }

            if (data.results.length === 0) {
                showMessage(resultsBox, "Panduan sampah yang cocok tidak ditemukan.");
                return;
            }

            // Bangun semua item, lalu ganti isi kotak hasil sekaligus
            const items = data.results.map(createGuideItem);
            resultsBox.replaceChildren(...items);

        } catch (error) {
            if (requestId !== latestRequest) {
                return;
            }
            console.error(error);
            showMessage(resultsBox, "Panduan sampah gagal dimuat. Silakan coba lagi.");
        }
    }

    /* Setiap ketik: batalkan timer lama, pasang timer baru */
    searchInput.addEventListener("input", function () {
        clearTimeout(timerId);

        timerId = setTimeout(function () {
            loadGuides(searchInput.value.trim());
        }, 250);
    });
}


setupQuiz();
setupGuideSearch();


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
    const totalText = document.getElementById("quiz-total");
    const resultStars = document.querySelectorAll("[data-score-star]");
    const resultStarsLabel = document.getElementById("quiz-result-stars");
    const binButtons = document.querySelectorAll(".bin");

    /* Ubah daftar <li> di #quiz-data menjadi daftar soal. */
    const questionElements = document.querySelectorAll("#quiz-data li");
    const questions = [...questionElements].map(function (element) {
        return {
            id: element.dataset.id,
            item: element.textContent.trim(),
        };
    });

    if (playArea.dataset.canPlay !== "true") {
        binButtons.forEach(function (button) { button.disabled = true; });
    }

    function renderResultScore(value, total) {
        scoreText.textContent = value;
        totalText.textContent = total;
        resultStars.forEach(function (star, index) {
            star.classList.toggle("is-filled", index < value);
        });
        resultStarsLabel.setAttribute("aria-label", "Skor " + value + " dari " + total);
    }

    renderResultScore(
        Number(resultBox.dataset.score || 0),
        Number(resultBox.dataset.total || questions.length)
    );

    if (questions.length === 0) {
        return;
    }

    /* Data yang berubah selama kuis berjalan */
    let currentQuestion = 0;    // soal ke berapa (0 = soal pertama)
    let score = 0;              // jumlah jawaban benar
    let hasAnswered = false;    // sudah menjawab soal ini atau belum
    
    const answerUrl = playArea.dataset.answerUrl;

    async function postJson(url, body) {
        const csrfInput = document.querySelector(
            "#quiz-csrf-form [name=csrfmiddlewaretoken]"
        );
        const response = await fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfInput ? csrfInput.value : ""
            },
            body: JSON.stringify(body)
        });
        const data = await response.json();
        return { ok: response.ok, data: data };
    }

    /* Tampilkan soal yang sedang aktif */
    function showQuestion() {
        const question = questions[currentQuestion];

        progressText.textContent = "Soal " + (currentQuestion + 1) + " dari " + questions.length;
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
    async function handleAnswer(chosenBin) {
        if (hasAnswered) {
            return;
        }
        hasAnswered = true;

        // Matikan tombol langsung supaya tidak bisa klik dua kali selagi menunggu server
        binButtons.forEach(function (button) { button.disabled = true; });

        const question = questions[currentQuestion];

        try {
            const result = await postJson(answerUrl, {
                question_id: question.id,
                answer: chosenBin
            });

            if (!result.ok) {
                feedbackText.textContent = result.data.error ||
                    "Jawaban tidak dapat dikirim. Coba lagi.";
                feedbackText.hidden = false;
                hasAnswered = false;
                binButtons.forEach(function (button) { button.disabled = false; });
                return;
            }

            const data = result.data;

            if (data.correct) {
                score = score + 1;
            }
            // Cari tulisan tong yang benar + tandai tombolnya
            let correctLabel = data.correct_bin;
            binButtons.forEach(function (button) {
                if (button.dataset.bin === data.correct_bin) {
                    correctLabel = button.textContent;
                    button.classList.add("is-correct");
                }
            });

            let message = data.correct
                ? "Benar!"
                : "Belum tepat. Sampah ini masuk ke " + correctLabel + ".";
            if (data.chosen !== chosenBin) {
                message = "Jawaban pertamamu untuk soal ini yang dipakai. " + message;
            }
            feedbackText.textContent = message;
            feedbackText.hidden = false;

            if (currentQuestion === questions.length - 1) {
                showResult();
            } else {
                nextButton.textContent = "Soal berikutnya";
                nextButton.hidden = false;
            }

        } catch (error) {
            console.error(error);
            feedbackText.textContent = "Tidak dapat terhubung ke server. Silakan coba lagi.";
            feedbackText.hidden = false;
            hasAnswered = false;
            binButtons.forEach(function (button) { button.disabled = false; });
        }
    }

    /* Pindah ke soal berikutnya, atau tampilkan skor kalau soal sudah habis */
    function goToNext() {
        if (currentQuestion === questions.length - 1) {
            showResult();
            return;
        }

        currentQuestion = currentQuestion + 1;
        showQuestion();
    }

    /* Tampilkan skor akhir */        
    async function showResult() {
        nextButton.disabled = true;
        nextButton.hidden = true;
        scoreText.textContent = "Menyimpan hasil kuis...";

        try {
            const result = await postJson(playArea.dataset.submitUrl, {});

            if (!result.ok) {
                feedbackText.textContent = result.data.error ||
                    "Hasil kuis tidak dapat disimpan. Muat ulang halaman dan coba lagi.";
                feedbackText.hidden = false;
                nextButton.disabled = false;
                nextButton.textContent = "Coba lagi";
                nextButton.hidden = false;
                return;
            }

            renderResultScore(result.data.score, result.data.total);

            playArea.hidden = true;
            resultBox.hidden = false;

        } catch (error) {
            console.error(error);
            feedbackText.textContent = "Tidak dapat terhubung ke server. Silakan coba lagi.";
            feedbackText.hidden = false;
            nextButton.disabled = false;
            nextButton.textContent = "Coba lagi";
            nextButton.hidden = false;
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
    badge.textContent = guide.category;

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

    document.body.addEventListener("educationContentChanged", async function () {
        try {
            const response = await fetch(window.location.href, { credentials: "same-origin" });
            if (!response.ok) throw new Error("Gagal menyegarkan konten edukasi.");
            const page = new DOMParser().parseFromString(await response.text(), "text/html");
            ["decomposition", "myths-facts"].forEach(function (id) {
                const current = document.getElementById(id);
                const fresh = page.getElementById(id);
                if (current && fresh) {
                    current.replaceChildren(...fresh.childNodes);
                    htmx.process(current);
                }
            });
            const freshGuides = page.getElementById("guide-results");
            if (freshGuides) {
                resultsBox.replaceChildren(...freshGuides.childNodes);
                htmx.process(resultsBox);
                await loadGuides(searchInput.value.trim());
            }
        } catch (error) {
            console.error(error);
        }
    });

    /* Setiap ketik: batalkan timer lama, pasang timer baru */
    searchInput.addEventListener("input", function () {
        clearTimeout(timerId);

        timerId = setTimeout(function () {
            loadGuides(searchInput.value.trim());
        }, 250);
    });
}

document.body.addEventListener("htmx:afterSwap", function (event) {
    if (event.detail.target?.id === "education-modal-content") {
        if (event.detail.xhr?.getResponseHeader("HX-Trigger")?.includes("educationContentChanged")) return;
        const modal = document.getElementById("educationModal");
        if (modal && !modal.open) modal.showModal();
    }
});

document.body.addEventListener("htmx:afterRequest", function (event) {
    const xhr = event.detail.xhr;
    if (event.detail.successful && xhr?.getResponseHeader("HX-Trigger")?.includes("educationContentChanged")) {
        document.getElementById("educationModal")?.close();
        const status = document.getElementById("education-crud-status");
        if (status) {
            status.textContent = "Konten edukasi berhasil diperbarui.";
            window.setTimeout(function () { status.textContent = ""; }, 3500);
        }
    }
});


setupQuiz();
setupGuideSearch();


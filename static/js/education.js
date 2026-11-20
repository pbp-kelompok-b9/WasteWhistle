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

    function responseMessage(data, fallback) {
        if (data?.error) return data.error;
        if (data?.detail) return data.detail;
        if (data && typeof data === "object") {
            const firstError = Object.values(data)[0];
            if (Array.isArray(firstError)) return firstError.join(" ");
            if (typeof firstError === "string") return firstError;
        }
        return fallback;
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
                feedbackText.textContent = responseMessage(
                    result.data, "Jawaban tidak dapat dikirim. Coba lagi."
                );
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
                feedbackText.textContent = responseMessage(
                    result.data, "Hasil kuis tidak dapat disimpan. Muat ulang halaman dan coba lagi."
                );
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
            const urls = document.getElementById("education-api-urls").dataset;
            const [decomposition, myths] = await Promise.all([
                fetch(urls.decomposition).then(function (response) { return response.json(); }),
                fetch(urls.myths).then(function (response) { return response.json(); })
            ]);
            const decompositionBox = document.getElementById("decomposition");
            decompositionBox.querySelectorAll("article, .education-empty").forEach(function (node) { node.remove(); });
            const decompositionItems = Array.isArray(decomposition) ? decomposition : decomposition.results;
            if (decompositionItems.length === 0) {
                const empty = document.createElement("p");
                empty.className = "education-empty mt-3 text-[13px] text-[#6C7D75]";
                empty.textContent = "Belum ada informasi yang tersedia.";
                decompositionBox.append(empty);
            }
            decompositionItems.forEach(function (info) {
                const article = document.createElement("article");
                article.className = "mt-3.5";
                article.innerHTML = '<div class="grid grid-cols-[110px_minmax(0,1fr)_135px] items-center gap-3"><span class="text-[13px]"></span><div class="lifespan-track"><div class="lifespan-bar"></div></div><strong class="lifespan-years text-[12px]"></strong></div>';
                article.querySelector("span").textContent = info.material_name;
                const bar = article.querySelector(".lifespan-bar");
                bar.classList.add("bar-" + info.bar_level);
                bar.style.width = info.bar_percent + "%";
                article.querySelector("strong").textContent = info.formatted_duration;
                decompositionBox.append(article);
            });
            const mythSection = document.getElementById("myths-facts");
            let grid = mythSection.querySelector(".myth-grid");
            const mythItems = Array.isArray(myths) ? myths : myths.results;
            mythSection.querySelectorAll(".education-empty").forEach(function (node) { node.remove(); });
            if (mythItems.length === 0) {
                const empty = document.createElement("p");
                empty.className = "education-empty text-[13px] text-[#6C7D75]";
                empty.textContent = "Belum ada mitos/fakta yang tersedia.";
                mythSection.append(empty);
            }
            if (!grid) {
                grid = document.createElement("div");
                grid.className = "myth-grid grid grid-cols-3 gap-4";
                mythSection.append(grid);
            }
            grid.replaceChildren(...mythItems.map(createMythCard));
            await loadGuides(searchInput.value.trim());
            document.body.dispatchEvent(new Event("educationContentRefreshed"));
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

function createMythCard(item) {
    const label = document.createElement("label");
    label.className = "flip-card relative block h-[210px]";
    const toggle = document.createElement("input");
    toggle.className = "flip-toggle absolute h-px w-px opacity-0";
    toggle.type = "checkbox";
    const front = document.createElement("span");
    front.className = "flip-front flex flex-col items-center justify-center gap-3.5 border border-[#E2EDE6] bg-white text-center";
    const statement = document.createElement("span");
    statement.className = "text-[17px] font-bold leading-[1.3]";
    statement.textContent = item.statement;
    const hint = document.createElement("span");
    hint.className = "text-[14px] text-[#6C7D75]";
    hint.textContent = "Balik kartu untuk melihat jawaban";
    front.append(statement, hint);
    const back = document.createElement("span");
    back.className = "flip-back flex flex-col gap-1.5 overflow-y-auto bg-[#0B3B2E] text-[13px] text-white";
    const classification = document.createElement("strong");
    classification.className = "text-[14px] text-[#B9F2CD]";
    classification.textContent = item.is_myth ? "Mitos" : "Fakta";
    const explanation = document.createElement("span");
    explanation.className = "flip-explanation";
    explanation.textContent = item.explanation;
    back.append(classification, explanation);
    if (item.source_url) {
        const link = document.createElement("a");
        link.className = "mt-auto font-semibold text-[#B9F2CD] underline underline-offset-2 hover:text-white";
        link.href = item.source_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Pelajari lebih lanjut";
        back.append(link);
    }
    label.append(toggle, front, back);
    return label;
}

document.body.addEventListener("submit", async function (event) {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.dataset.apiUrl) return;
    event.preventDefault();
    const csrf = form.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
    const method = form.dataset.apiMethod;
    let response;
    try {
        if (method === "DELETE") {
            response = await fetch(form.dataset.apiUrl, { method: method, credentials: "same-origin", headers: { "X-CSRFToken": csrf } });
        } else {
            const data = Object.fromEntries(new FormData(form).entries());
            delete data.csrfmiddlewaretoken;
            response = await fetch(form.dataset.apiUrl, {
                method: method, credentials: "same-origin",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
                body: JSON.stringify(data)
            });
        }
        const payload = response.status === 204 ? {} : await response.json();
        if (!response.ok) {
            const errors = Object.entries(payload).map(function ([field, messages]) {
                return field + ": " + (Array.isArray(messages) ? messages.join(" ") : messages);
            }).join(" ");
            const alert = document.createElement("div");
            alert.className = "education-admin-errors";
            alert.setAttribute("role", "alert");
            alert.textContent = errors || "Perubahan tidak dapat disimpan.";
            form.querySelector("[role=alert]")?.remove();
            form.prepend(alert);
            return;
        }
        document.getElementById("educationModal")?.close();
        document.body.dispatchEvent(new Event("educationContentChanged"));
        const status = document.getElementById("education-crud-status");
        if (status) {
            status.textContent = "Konten edukasi berhasil diperbarui.";
            window.setTimeout(function () { status.textContent = ""; }, 3500);
        }
    } catch (error) {
        console.error(error);
    }
});

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


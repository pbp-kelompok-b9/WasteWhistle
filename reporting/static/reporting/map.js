(() => {
    "use strict";

    const container = document.getElementById("report-map");
    if (!container) return;

    const latitude = document.getElementById("id_latitude");
    const longitude = document.getElementById("id_longitude");
    const status = document.getElementById("map-status");
    const error = document.getElementById("map-error");
    const centerButton = document.getElementById("use-map-center");
    const zoomInButton = document.getElementById("report-zoom-in");
    const zoomOutButton = document.getElementById("report-zoom-out");
    const loading = document.getElementById("map-loading");

    const showError = (message) => {
        error.textContent = message;
        error.classList.remove("hidden");
    };

    if (!window.L) {
        loading.textContent = "Peta belum tersedia.";
        showError("Peta gagal dimuat. Periksa koneksi internet atau isi kedua koordinat secara manual.");
        return;
    }

    // Match the dashboard's Jakarta view without selecting a report location.
    // Keep fields empty
    // until the user chooses a point, and restore only valid submitted values.
    const readCoordinates = () => {
        if (!latitude.value.trim() || !longitude.value.trim()) return null;
        const lat = Number(latitude.value);
        const lng = Number(longitude.value);
        if (!Number.isFinite(lat) || !Number.isFinite(lng) ||
            lat < -90 || lat > 90 || lng < -180 || lng > 180 ||
            !latitude.validity.valid || !longitude.validity.valid) return null;
        return [lat, lng];
    };

    const savedPoint = readCoordinates();
    let map;
    try {
        loading.remove();
        map = L.map(container, {
            scrollWheelZoom: false, zoomControl: false, minZoom: 1, maxZoom: 19,
        }).setView(savedPoint || [-6.2088, 106.8456], savedPoint ? 16 : 13);
        L.tileLayer(container.dataset.tileUrl, {
            minZoom: 1,
            maxZoom: 19,
            // Send only the app origin with external tile requests, not form data.
            referrerPolicy: "strict-origin-when-cross-origin",
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/">HOT</a>',
        }).on("tileerror", () => {
            showError("Sebagian peta tidak bisa dimuat. Coba muat ulang halaman atau gunakan koordinat manual.");
        }).addTo(map);
    } catch (err) {
        showError("Peta tidak dapat ditampilkan. Kamu tetap bisa mengisi kedua koordinat secara manual.");
        return;
    }

    const syncZoomButtons = () => {
        zoomInButton.disabled = map.getZoom() >= map.getMaxZoom();
        zoomOutButton.disabled = map.getZoom() <= map.getMinZoom();
    };
    zoomInButton.addEventListener("click", () => map.zoomIn());
    zoomOutButton.addEventListener("click", () => map.zoomOut());
    map.on("zoomend", syncZoomButtons);
    syncZoomButtons();

    let marker;
    const updateMarker = (point) => {
        if (!marker) {
            marker = L.marker(point, {
                draggable: true,
                autoPan: true,
                title: "Lokasi sampah: geser pin untuk mengubah titik",
                alt: "Pin lokasi sampah",
            }).addTo(map);
            marker.on("dragend", () => selectPoint(marker.getLatLng()));
        } else {
            marker.setLatLng(point);
        }
        status.textContent = `Titik dipilih: ${Number(point[0]).toFixed(6)}, ${Number(point[1]).toFixed(6)}`;
    };

    const selectPoint = (latlng) => {
        const point = latlng.wrap();
        // Server validation is still authoritative; rounding keeps map clicks
        // within the six decimal places accepted by the form.
        latitude.value = point.lat.toFixed(6);
        longitude.value = point.lng.toFixed(6);
        updateMarker([Number(latitude.value), Number(longitude.value)]);
    };

    const syncManualCoordinates = () => {
        const point = readCoordinates();
        if (point) {
            updateMarker(point);
            map.panTo(point);
        } else {
            if (marker) map.removeLayer(marker);
            marker = null;
            status.textContent = "Isi kedua koordinat yang valid atau pilih titik di peta.";
        }
    };

    map.on("click", (event) => selectPoint(event.latlng));
    centerButton.disabled = false;
    centerButton.addEventListener("click", () => selectPoint(map.getCenter()));
    latitude.addEventListener("input", syncManualCoordinates);
    longitude.addEventListener("input", syncManualCoordinates);

    // Browsers can restore form values after this script runs on Back/reload.
    window.addEventListener("pageshow", () => {
        window.requestAnimationFrame(() => {
            if (readCoordinates()) syncManualCoordinates();
        });
    });

    if (savedPoint) updateMarker(savedPoint);
    else status.textContent = "Belum ada titik dipilih. Tampilan awal: Jakarta.";
})();

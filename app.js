/**
 * KawanBaca Dashboard – Frontend Logic
 * ==========================================
 * Fetches data from the Flask API and renders metric cards + Chart.js charts.
 */

(function () {
  "use strict";

  // ── DOM References ──────────────────────────────────────────────
  const overlay     = document.getElementById("loading-overlay");
  const valLaporan  = document.getElementById("val-laporan");
  const valHalaman  = document.getElementById("val-halaman");
  const valAnggota  = document.getElementById("val-anggota");
  const valSkor     = document.getElementById("val-skor");
  const lastUpdated = document.getElementById("last-updated");
  const btnRefresh  = document.getElementById("btn-refresh");

  let chartSkor    = null;
  let chartLaporan = null;

  // ── Chart.js Shared Options ─────────────────────────────────────
  const fontFamily = "'Inter', sans-serif";

  const gridColor   = "rgba(0,0,0,.06)";
  const tickColor   = "#94a3b8";

  function sharedScales(yLabel) {
    return {
      x: {
        grid: { display: false },
        ticks: { font: { family: fontFamily, size: 11 }, color: tickColor },
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: yLabel,
          font: { family: fontFamily, size: 12, weight: "600" },
          color: tickColor,
        },
        grid: { color: gridColor },
        ticks: { font: { family: fontFamily, size: 11 }, color: tickColor },
      },
    };
  }

  // ── Animate Number ──────────────────────────────────────────────
  function animateValue(el, end, decimals) {
    const duration = 800;
    const startTime = performance.now();
    const start = 0;

    function step(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = start + (end - start) * eased;
      el.textContent = decimals > 0 ? current.toFixed(decimals) : Math.round(current).toLocaleString("id-ID");
      if (progress < 1) requestAnimationFrame(step);
    }

    el.classList.remove("pop-in");
    void el.offsetWidth; // trigger reflow
    el.classList.add("pop-in");
    requestAnimationFrame(step);
  }

  // ── Gradient Helper ─────────────────────────────────────────────
  function createGradient(ctx, r, g, b) {
    const grad = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    grad.addColorStop(0, `rgba(${r},${g},${b},.28)`);
    grad.addColorStop(1, `rgba(${r},${g},${b},.02)`);
    return grad;
  }

  // ── Render Charts ───────────────────────────────────────────────
  function renderChartSkor(labels, data) {
    const ctx = document.getElementById("chart-skor").getContext("2d");

    if (chartSkor) chartSkor.destroy();

    chartSkor = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Rata-rata Skor Empati",
          data,
          fill: true,
          backgroundColor: createGradient(ctx, 124, 58, 237),   // purple
          borderColor: "#7c3aed",
          borderWidth: 2.5,
          pointBackgroundColor: "#7c3aed",
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 8,
          tension: 0.4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(30,41,59,.88)",
            titleFont: { family: fontFamily, weight: "600" },
            bodyFont: { family: fontFamily },
            padding: 12,
            cornerRadius: 10,
            displayColors: false,
            callbacks: {
              label: (tip) => `Skor: ${tip.parsed.y.toFixed(2)}`,
            },
          },
        },
        scales: sharedScales("Skor Empati"),
      },
    });
  }

  function renderChartLaporan(labels, data) {
    const ctx = document.getElementById("chart-laporan").getContext("2d");

    if (chartLaporan) chartLaporan.destroy();

    chartLaporan = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Jumlah Laporan",
          data,
          backgroundColor: createGradient(ctx, 66, 133, 244),  // blue
          borderColor: "#4285f4",
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
          hoverBackgroundColor: "rgba(66,133,244,.55)",
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(30,41,59,.88)",
            titleFont: { family: fontFamily, weight: "600" },
            bodyFont: { family: fontFamily },
            padding: 12,
            cornerRadius: 10,
            displayColors: false,
            callbacks: {
              label: (tip) => `Laporan: ${tip.parsed.y}`,
            },
          },
        },
        scales: sharedScales("Jumlah Laporan"),
      },
    });
  }

  // ── Fetch & Render ──────────────────────────────────────────────
  async function loadDashboard() {
    overlay.classList.remove("hidden");

    try {
      const res  = await fetch("/api/dashboard-data");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();

      const m = json.metrics;
      animateValue(valLaporan, m.total_laporan, 0);
      animateValue(valHalaman, m.total_halaman, 0);
      animateValue(valAnggota, m.anggota_partisipasi, 0);
      animateValue(valSkor,    m.rata_rata_skor, 2);

      const c = json.charts;
      renderChartSkor(c.tren_skor.labels, c.tren_skor.data);
      renderChartLaporan(c.tren_laporan.labels, c.tren_laporan.data);

      lastUpdated.textContent = "Diperbarui: " + new Date().toLocaleTimeString("id-ID");
    } catch (err) {
      console.error("Dashboard load error:", err);
      valLaporan.textContent = "!";
      valHalaman.textContent = "!";
      valAnggota.textContent = "!";
      valSkor.textContent    = "!";
      lastUpdated.textContent = "Gagal memuat data";
    } finally {
      overlay.classList.add("hidden");
    }
  }

  // ── Init ────────────────────────────────────────────────────────
  btnRefresh.addEventListener("click", loadDashboard);
  loadDashboard();
})();

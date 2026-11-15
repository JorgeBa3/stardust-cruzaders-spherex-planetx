// Frontend minimo (sin build step) para "Planet X and SPHEREx".
// Asume que el backend FastAPI corre en BACKEND_URL (default: localhost:8000).

const BACKEND_URL = window.BACKEND_URL || "http://localhost:8000";

const state = {
  epochs: [],
  ra: null,
  dec: null,
  cutoutSize: 0.02,
  playTimer: null,
  blinkTimer: null,
  currentIndex: 0,
  source: "live",
  targetName: null,
};

const el = {
  presetSelect: document.getElementById("preset-select"),
  raInput: document.getElementById("ra-input"),
  decInput: document.getElementById("dec-input"),
  radiusInput: document.getElementById("radius-input"),
  searchBtn: document.getElementById("search-btn"),
  statusMsg: document.getElementById("status-msg"),
  viewerImage: document.getElementById("viewer-image"),
  playBtn: document.getElementById("play-btn"),
  epochSlider: document.getElementById("epoch-slider"),
  epochLabel: document.getElementById("epoch-label"),
  blinkA: document.getElementById("blink-a"),
  blinkB: document.getElementById("blink-b"),
  blinkBtn: document.getElementById("blink-btn"),
  epochsTableBody: document.querySelector("#epochs-table tbody"),
  demoModeCheckbox: document.getElementById("demo-mode"),
  demoBanner: document.getElementById("demo-banner"),
};

let aladin = null;

function setStatus(msg) {
  el.statusMsg.textContent = msg;
}

function cutoutUrl(epoch, index) {
  const params = new URLSearchParams({
    ra: state.ra,
    dec: state.dec,
    size: state.cutoutSize,
    source: state.source,
  });
  if (state.source === "demo") {
    params.set("target", state.targetName);
    params.set("epoch", index);
  } else {
    params.set("access_url", epoch.access_url);
  }
  return `${BACKEND_URL}/api/cutout?${params.toString()}`;
}

function showEpoch(index) {
  if (!state.epochs.length) return;
  state.currentIndex = ((index % state.epochs.length) + state.epochs.length) % state.epochs.length;
  const epoch = state.epochs[state.currentIndex];
  el.viewerImage.src = cutoutUrl(epoch, state.currentIndex);
  el.epochSlider.value = state.currentIndex;
  el.epochLabel.textContent = `Epoca ${state.currentIndex + 1}/${state.epochs.length} - obs_id ${epoch.obs_id ?? "?"} - MJD ${epoch.t_min_mjd ?? "?"}`;
}

function stopPlay() {
  if (state.playTimer) {
    clearInterval(state.playTimer);
    state.playTimer = null;
    el.playBtn.textContent = "Play";
  }
}

function togglePlay() {
  if (state.playTimer) {
    stopPlay();
    return;
  }
  stopBlink();
  el.playBtn.textContent = "Pause";
  state.playTimer = setInterval(() => showEpoch(state.currentIndex + 1), 900);
}

function stopBlink() {
  if (state.blinkTimer) {
    clearInterval(state.blinkTimer);
    state.blinkTimer = null;
  }
}

function toggleBlink() {
  if (state.blinkTimer) {
    stopBlink();
    return;
  }
  stopPlay();
  const idxA = Number(el.blinkA.value);
  const idxB = Number(el.blinkB.value);
  if (Number.isNaN(idxA) || Number.isNaN(idxB)) return;
  let showingA = true;
  showEpoch(idxA);
  state.blinkTimer = setInterval(() => {
    showEpoch(showingA ? idxB : idxA);
    showingA = !showingA;
  }, 600);
}

function populateEpochUi() {
  el.epochSlider.max = Math.max(0, state.epochs.length - 1);
  el.blinkA.innerHTML = "";
  el.blinkB.innerHTML = "";
  el.epochsTableBody.innerHTML = "";

  state.epochs.forEach((epoch, i) => {
    const optA = document.createElement("option");
    optA.value = i;
    optA.textContent = `#${i + 1} (MJD ${epoch.t_min_mjd ?? "?"})`;
    el.blinkA.appendChild(optA);
    el.blinkB.appendChild(optA.cloneNode(true));

    const row = document.createElement("tr");
    row.innerHTML = `<td>${i + 1}</td><td>${epoch.obs_id ?? ""}</td><td>${epoch.obs_collection ?? ""}</td><td>${epoch.t_min_mjd ?? ""}</td><td>${epoch.t_max_mjd ?? ""}</td>`;
    el.epochsTableBody.appendChild(row);
  });

  if (el.blinkB.options.length > 1) el.blinkB.selectedIndex = 1;
}

async function runSearch() {
  const ra = parseFloat(el.raInput.value);
  const dec = parseFloat(el.decInput.value);
  const radius = parseFloat(el.radiusInput.value) || 0.05;
  if (Number.isNaN(ra) || Number.isNaN(dec)) {
    setStatus("Ingresa RA y Dec validos (grados decimales).");
    return;
  }

  const isDemo = el.demoModeCheckbox.checked;
  const presetOpt = el.presetSelect.selectedOptions[0];
  if (isDemo && (!presetOpt || !presetOpt.dataset.ra)) {
    setStatus("El modo demo necesita que elijas un objeto de prueba de la lista.");
    return;
  }

  state.ra = ra;
  state.dec = dec;
  state.cutoutSize = Math.max(radius / 2, 0.005);
  state.source = isDemo ? "demo" : "live";
  state.targetName = isDemo ? presetOpt.textContent : null;
  el.demoBanner.hidden = !isDemo;

  stopPlay();
  stopBlink();
  setStatus(isDemo ? "Generando secuencia de demo..." : "Buscando epocas en IRSA...");
  el.viewerImage.removeAttribute("src");

  if (aladin) {
    aladin.gotoRaDec(ra, dec);
  }

  try {
    const params = new URLSearchParams({ ra, dec, radius, source: state.source });
    if (isDemo) params.set("target", state.targetName);
    const resp = await fetch(`${BACKEND_URL}/api/search?${params.toString()}`);
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    state.epochs = data.epochs || [];
    populateEpochUi();
    if (state.epochs.length) {
      setStatus(`${state.epochs.length} epocas encontradas.`);
      showEpoch(0);
    } else {
      setStatus("Sin resultados para esa posicion/radio. Prueba otro radio, o activa el modo demo offline si IRSA no responde.");
    }
  } catch (err) {
    console.error(err);
    setStatus(`Error buscando datos: ${err.message}. Si persiste, proba el modo demo offline.`);
  }
}

function loadPresets() {
  fetch(`${BACKEND_URL}/api/targets`)
    .then((r) => r.json())
    .then((targets) => {
      targets.forEach((t, i) => {
        const opt = document.createElement("option");
        opt.value = i;
        opt.textContent = t.name;
        opt.dataset.ra = t.ra_deg;
        opt.dataset.dec = t.dec_deg;
        el.presetSelect.appendChild(opt);
      });
    })
    .catch((err) => setStatus(`No se pudo cargar la lista de objetos de prueba: ${err.message}`));
}

el.presetSelect.addEventListener("change", () => {
  const opt = el.presetSelect.selectedOptions[0];
  if (!opt || !opt.dataset.ra) return;
  el.raInput.value = opt.dataset.ra;
  el.decInput.value = opt.dataset.dec;
});

el.searchBtn.addEventListener("click", runSearch);
el.playBtn.addEventListener("click", togglePlay);
el.blinkBtn.addEventListener("click", toggleBlink);
el.epochSlider.addEventListener("input", () => {
  stopPlay();
  stopBlink();
  showEpoch(Number(el.epochSlider.value));
});

function initAladin() {
  const container = document.getElementById("aladin-div");
  if (window.A && typeof window.A.aladin === "function") {
    aladin = A.aladin("#aladin-div", { survey: "P/DSS2/color", fov: 0.2 });
    return;
  }
  // El CDN de CDS (aladin.cds.unistra.fr) a veces esta caido; este panel es
  // solo contexto visual, no bloquea busqueda/play/blink si no carga.
  container.innerHTML =
    '<p style="padding:1rem;color:#9aa3b8;font-size:0.85rem;">' +
    "Aladin Lite no disponible (el CDN de CDS no respondio). " +
    "El resto de la app funciona igual." +
    "</p>";
}

window.addEventListener("DOMContentLoaded", () => {
  loadPresets();
  initAladin();
});

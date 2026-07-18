import { pipeline } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1";
import { rankCatalog } from "./lab-core.mjs";

const MODEL_ID = "Xenova/all-MiniLM-L6-v2";
const MODEL_REVISION = "751bff37182d3f1213fa05d7196b954e230abad9";
const TOP_K = 6;

const catalog = [
  {
    id: "mouse-wireless-pro",
    title: "Northstar G5 Wireless Gaming Mouse",
    category: "Gaming mouse",
    description: "Low-latency wireless mouse with a lightweight shell and adjustable DPI.",
    tags: ["wireless", "gaming", "mouse"],
  },
  {
    id: "mouse-vertical",
    title: "ErgoLift Vertical Wireless Mouse",
    category: "Office mouse",
    description: "Ergonomic vertical mouse designed for long work sessions and quiet clicking.",
    tags: ["ergonomic", "wireless", "office"],
  },
  {
    id: "mouse-wired",
    title: "Vector M2 Wired Precision Mouse",
    category: "Wired mouse",
    description: "Compact wired optical mouse for reliable everyday desktop use.",
    tags: ["wired", "mouse", "desktop"],
  },
  {
    id: "mouse-pad",
    title: "Atlas Extended Gaming Mouse Pad",
    category: "Mouse accessory",
    description: "Large desk mat with a low-friction surface for keyboard and mouse.",
    tags: ["mouse pad", "desk mat", "gaming"],
  },
  {
    id: "mouse-receiver",
    title: "Universal 2.4 GHz USB Mouse Receiver",
    category: "Mouse accessory",
    description: "Replacement USB receiver for compatible wireless mice and keyboards.",
    tags: ["receiver", "usb", "wireless"],
  },
  {
    id: "keyboard-mechanical",
    title: "Nova 75 Mechanical Gaming Keyboard",
    category: "Keyboard",
    description: "Hot-swappable compact mechanical keyboard with tactile switches.",
    tags: ["mechanical", "gaming", "keyboard"],
  },
  {
    id: "headphones-anc",
    title: "SilenceAir Noise-Cancelling Headphones",
    category: "Headphones",
    description: "Over-ear Bluetooth headphones with active noise cancellation for travel.",
    tags: ["headphones", "bluetooth", "noise cancelling"],
  },
  {
    id: "headset-gaming",
    title: "Pulse X7 Wireless Gaming Headset",
    category: "Gaming headset",
    description: "Low-latency wireless headset with a detachable microphone.",
    tags: ["gaming", "headset", "microphone"],
  },
  {
    id: "earbuds",
    title: "PocketBeat True Wireless Earbuds",
    category: "Earbuds",
    description: "Compact Bluetooth earbuds with a pocket charging case.",
    tags: ["earbuds", "wireless", "portable"],
  },
  {
    id: "laptop-stand",
    title: "FoldLite Portable Aluminum Laptop Stand",
    category: "Laptop stand",
    description: "Foldable ventilated notebook riser for travel and ergonomic desk setups.",
    tags: ["portable", "laptop stand", "ergonomic"],
  },
  {
    id: "usb-hub",
    title: "DockFlow 8-in-1 USB-C Hub",
    category: "Laptop accessory",
    description: "USB-C adapter with HDMI, card reader, power delivery, and USB ports.",
    tags: ["usb-c", "hub", "laptop"],
  },
  {
    id: "charger",
    title: "GaN 65W USB-C Laptop Charger",
    category: "Charger",
    description: "Compact fast charger for USB-C notebooks, tablets, and phones.",
    tags: ["charger", "usb-c", "laptop"],
  },
  {
    id: "ssd",
    title: "Velocity 1TB NVMe Internal SSD",
    category: "Storage",
    description: "PCIe solid-state drive for a fast desktop or laptop storage upgrade.",
    tags: ["ssd", "storage", "upgrade"],
  },
  {
    id: "portable-ssd",
    title: "RoamDrive 1TB Portable SSD",
    category: "External storage",
    description: "Pocket-size USB-C solid-state drive for backups and large project files.",
    tags: ["portable", "ssd", "backup"],
  },
  {
    id: "monitor",
    title: "ViewPoint 27-inch QHD Monitor",
    category: "Monitor",
    description: "High-resolution IPS desktop display with an adjustable stand.",
    tags: ["monitor", "display", "desktop"],
  },
  {
    id: "webcam",
    title: "ClearMeet 1080p USB Webcam",
    category: "Webcam",
    description: "Full-HD camera with dual microphones for calls and streaming.",
    tags: ["webcam", "video", "usb"],
  },
  {
    id: "phone-case",
    title: "ShieldCase Rugged Phone Cover",
    category: "Phone accessory",
    description: "Shock-resistant protective smartphone case with raised edges.",
    tags: ["phone", "case", "protective"],
  },
  {
    id: "coffee-grinder",
    title: "BurrCraft Electric Coffee Grinder",
    category: "Kitchen",
    description: "Adjustable burr grinder for espresso, filter, and French press coffee.",
    tags: ["coffee", "grinder", "kitchen"],
  },
  {
    id: "running-shoes",
    title: "AeroStride Lightweight Running Shoes",
    category: "Footwear",
    description: "Breathable cushioned shoes for road running and daily training.",
    tags: ["running", "shoes", "fitness"],
  },
  {
    id: "hdmi-cable",
    title: "UltraLink 2-metre HDMI Cable",
    category: "Cable",
    description: "Braided digital video cable for monitors, televisions, and game consoles.",
    tags: ["hdmi", "cable", "display"],
  },
];

const form = document.querySelector("#search-form");
const queryInput = document.querySelector("#query");
const searchButton = document.querySelector("#search-button");
const modelStatus = document.querySelector("#model-status");
const progressWrap = document.querySelector("#progress-wrap");
const progressLabel = document.querySelector("#progress-label");
const progressValue = document.querySelector("#progress-value");
const progressBar = document.querySelector("#progress-bar");
const resultsElement = document.querySelector("#results");
const timingElement = document.querySelector("#timing");
const errorElement = document.querySelector("#error-message");
const exampleButtons = [...document.querySelectorAll("[data-query]")];

let extractorPromise;
let catalogEmbeddingsPromise;
let activeSearchId = 0;

function productText(product) {
  return [
    product.title,
    product.category,
    product.description,
    product.tags.join(" "),
  ].join(". ");
}

function setStatus(message, state = "") {
  modelStatus.className = "model-status";
  if (state) {
    modelStatus.classList.add(state);
  }
  modelStatus.lastChild.textContent = " " + message;
}

function setProgress(event) {
  progressWrap.hidden = false;
  if (event.file) {
    progressLabel.textContent = "Loading " + event.file.split("/").pop();
  } else if (event.status) {
    progressLabel.textContent = String(event.status).replaceAll("_", " ");
  }

  if (typeof event.progress === "number") {
    const percent = Math.max(0, Math.min(100, Math.round(event.progress)));
    progressValue.textContent = percent + "%";
    progressBar.style.width = percent + "%";
  }
}

async function loadExtractor() {
  if (!extractorPromise) {
    setStatus("Loading neural model");
    progressWrap.hidden = false;
    extractorPromise = pipeline("feature-extraction", MODEL_ID, {
      dtype: "q8",
      revision: MODEL_REVISION,
      progress_callback: setProgress,
    })
      .then((model) => {
        setStatus("Neural model ready", "ready");
        progressLabel.textContent = "Model cached and ready";
        progressValue.textContent = "100%";
        progressBar.style.width = "100%";
        window.setTimeout(() => {
          progressWrap.hidden = true;
        }, 900);
        return model;
      })
      .catch((error) => {
        extractorPromise = undefined;
        setStatus("Model load failed", "error");
        throw error;
      });
  }
  return extractorPromise;
}

async function embed(texts) {
  const extractor = await loadExtractor();
  const output = await extractor(texts, {
    pooling: "mean",
    normalize: true,
  });
  return output.tolist();
}

async function getCatalogEmbeddings() {
  if (!catalogEmbeddingsPromise) {
    catalogEmbeddingsPromise = embed(catalog.map(productText)).catch((error) => {
      catalogEmbeddingsPromise = undefined;
      throw error;
    });
  }
  return catalogEmbeddingsPromise;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderResults(ranked) {
  resultsElement.innerHTML = ranked
    .map((item, index) => {
      const safeTitle = escapeHtml(item.product.title);
      const safeDescription = escapeHtml(item.product.description);
      const safeCategory = escapeHtml(item.product.category);
      const tags = item.product.tags
        .map((tag) => '<span class="tag">' + escapeHtml(tag) + "</span>")
        .join("");
      const normalizedWidth = Math.max(4, Math.min(100, ((item.score + 1) / 2) * 100));

      return (
        '<article class="result-card" style="animation-delay:' +
        index * 45 +
        'ms">' +
        '<span class="rank">#' +
        String(index + 1).padStart(2, "0") +
        "</span>" +
        '<div class="result-copy">' +
        "<strong>" +
        safeTitle +
        "</strong>" +
        "<p>" +
        safeCategory +
        " · " +
        safeDescription +
        "</p>" +
        '<div class="tag-row">' +
        tags +
        "</div>" +
        "</div>" +
        '<div class="result-score">' +
        '<div class="score-copy"><span>cosine similarity</span><strong>' +
        item.score.toFixed(3) +
        "</strong></div>" +
        '<div class="score-track"><div class="score-fill" style="width:' +
        normalizedWidth.toFixed(1) +
        '%"></div></div>' +
        "</div>" +
        "</article>"
      );
    })
    .join("");
}

function setControlsDisabled(disabled) {
  searchButton.disabled = disabled;
  queryInput.disabled = disabled;
  exampleButtons.forEach((button) => {
    button.disabled = disabled;
  });
  form.setAttribute("aria-busy", String(disabled));
}

async function runSearch(query) {
  const searchId = ++activeSearchId;
  errorElement.hidden = true;
  setControlsDisabled(true);
  searchButton.querySelector("span").textContent = "Running…";
  timingElement.textContent = "Embedding the query and catalogue on this device…";

  const startedAt = performance.now();
  try {
    const [queryEmbeddingRows, catalogEmbeddings] = await Promise.all([
      embed([query]),
      getCatalogEmbeddings(),
    ]);
    const queryEmbedding = queryEmbeddingRows[0];
    const ranked = rankCatalog(catalog, catalogEmbeddings, queryEmbedding, TOP_K);

    if (searchId !== activeSearchId) {
      return;
    }

    renderResults(ranked);
    const elapsed = Math.round(performance.now() - startedAt);
    timingElement.textContent =
      TOP_K + " of " + catalog.length + " products · " + elapsed.toLocaleString() + " ms";

    const url = new URL(window.location.href);
    url.searchParams.set("q", query);
    window.history.replaceState({}, "", url);
  } catch (error) {
    console.error(error);
    if (searchId !== activeSearchId) {
      return;
    }
    errorElement.textContent =
      "The browser model could not load. Check that this page can reach Hugging Face and the jsDelivr CDN, then retry. No query data was sent to this project.";
    errorElement.hidden = false;
    timingElement.textContent = "Search did not complete.";
  } finally {
    if (searchId === activeSearchId) {
      setControlsDisabled(false);
      searchButton.querySelector("span").textContent = "Search";
    }
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();
  if (query) {
    runSearch(query);
  }
});

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    queryInput.value = button.dataset.query;
    queryInput.focus();
    runSearch(button.dataset.query);
  });
});

const initialQuery = new URL(window.location.href).searchParams.get("q");
if (initialQuery) {
  queryInput.value = initialQuery.slice(0, 120);
  void runSearch(queryInput.value);
}

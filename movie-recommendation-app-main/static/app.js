const API = "";
const tokenKey = "cinepulse_token";
const userKey = "cinepulse_user";

const els = {
  movieGrid: document.getElementById("movieGrid"),
  recommendGrid: document.getElementById("recommendGrid"),
  favGrid: document.getElementById("favGrid"),
  authBox: document.getElementById("authBox"),
  userChip: document.getElementById("userChip"),
  userLabel: document.getElementById("userLabel"),
  moodResult: document.getElementById("moodResult"),
};

function token() {
  return localStorage.getItem(tokenKey);
}

function authHeaders() {
  const t = token();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function toast(message, isError = false) {
  let node = document.getElementById("toast");
  if (!node) {
    node = document.createElement("div");
    node.id = "toast";
    node.className = "toast";
    document.body.appendChild(node);
  }
  node.textContent = message;
  node.classList.toggle("error", isError);
  node.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => node.classList.remove("show"), 2800);
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    let detail = data?.detail || res.statusText;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function posterNode(movie) {
  const wrap = document.createElement("div");
  wrap.className = "poster-wrap";
  wrap.appendChild(fallbackPoster(movie.title));

  if (!movie.image) return wrap;

  const img = document.createElement("img");
  img.className = "poster";
  img.alt = movie.title;
  img.loading = "lazy";
  img.decoding = "async";
  img.referrerPolicy = "no-referrer";
  img.src = movie.image;
  img.onload = () => {
    wrap.querySelector(".poster-fallback")?.remove();
  };
  img.onerror = () => {
    img.remove();
  };
  wrap.appendChild(img);
  return wrap;
}

function fallbackPoster(title) {
  const div = document.createElement("div");
  div.className = "poster-fallback";
  const initials = title
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0] || "")
    .join("")
    .toUpperCase();
  div.innerHTML = `<span class="poster-initials">${escapeHtml(initials)}</span><span>${escapeHtml(title)}</span>`;
  return div;
}

function movieCard(movie, { favourited = false, showReason = false } = {}) {
  const card = document.createElement("article");
  card.className = "card";
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML = `
    <h3>${escapeHtml(movie.title)}</h3>
    <p>${escapeHtml(movie.genre || "—")} · ${movie.year || "—"} · ★ ${movie.rating ?? "—"}</p>
    ${showReason && movie.reason ? `<p class="reason">${escapeHtml(movie.reason)}</p>` : ""}
  `;
  const actions = document.createElement("div");
  actions.className = "actions";
  const favBtn = document.createElement("button");
  favBtn.className = favourited ? "btn" : "btn ghost";
  favBtn.type = "button";
  favBtn.textContent = favourited ? "Saved" : "Favourite";
  favBtn.onclick = async () => {
    if (!token()) {
      toast("Sign in to save favourites.", true);
      return;
    }
    try {
      if (favourited) {
        await api(`/api/favourites/${movie.id}`, { method: "DELETE" });
        toast("Removed from favourites");
      } else {
        await api(`/api/favourites/${movie.id}`, { method: "POST" });
        toast("Added to favourites");
      }
      await loadFavourites();
      await loadMovies(els.movieGrid.dataset.path || "/api/movies");
      if (els.recommendGrid.dataset.seed) {
        await runRecommend(els.recommendGrid.dataset.seed, false);
      }
    } catch (err) {
      toast(err.message, true);
    }
  };
  actions.appendChild(favBtn);
  meta.appendChild(actions);
  card.appendChild(posterNode(movie));
  card.appendChild(meta);
  return card;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderGrid(node, movies, options = {}) {
  node.innerHTML = "";
  if (!movies?.length) {
    node.innerHTML = `<p class="mood-result">Nothing here yet.</p>`;
    return;
  }
  const favIds = new Set(options.favIds || []);
  movies.forEach((m) => {
    node.appendChild(
      movieCard(m, {
        favourited: favIds.has(m.id),
        showReason: options.showReason,
      })
    );
  });
}

let favouriteIds = new Set();

async function loadMovies(path = "/api/movies") {
  els.movieGrid.dataset.path = path;
  const movies = await api(path);
  renderGrid(els.movieGrid, movies, { favIds: favouriteIds });
}

async function loadFavourites() {
  if (!token()) {
    favouriteIds = new Set();
    els.favGrid.innerHTML = `<p class="mood-result">Sign in to see favourites.</p>`;
    return;
  }
  try {
    const favs = await api("/api/favourites");
    favouriteIds = new Set(favs.map((m) => m.id));
    renderGrid(els.favGrid, favs, { favIds: favouriteIds });
  } catch {
    favouriteIds = new Set();
    els.favGrid.innerHTML = `<p class="mood-result">Could not load favourites.</p>`;
  }
}

function setAuthUI() {
  const user = localStorage.getItem(userKey);
  if (token() && user) {
    els.authBox.classList.add("hidden");
    els.userChip.classList.remove("hidden");
    els.userLabel.textContent = user;
  } else {
    els.authBox.classList.remove("hidden");
    els.userChip.classList.add("hidden");
  }
}

async function auth(path) {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  if (username.length < 3) {
    throw new Error("Username must be at least 3 characters.");
  }
  if (password.length < 4) {
    throw new Error("Password must be at least 4 characters.");
  }
  const data = await api(path, {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  localStorage.setItem(tokenKey, data.access_token);
  localStorage.setItem(userKey, data.username);
  setAuthUI();
  await loadFavourites();
  await loadMovies();
  toast(path.includes("register") ? "Welcome aboard" : "Signed in");
}

document.getElementById("loginBtn").onclick = async () => {
  try {
    await auth("/api/auth/login");
  } catch (err) {
    toast(err.message, true);
  }
};
document.getElementById("registerBtn").onclick = async () => {
  try {
    await auth("/api/auth/register");
  } catch (err) {
    toast(err.message, true);
  }
};
document.getElementById("logoutBtn").onclick = async () => {
  localStorage.removeItem(tokenKey);
  localStorage.removeItem(userKey);
  setAuthUI();
  await loadFavourites();
  await loadMovies();
  toast("Signed out");
};

document.getElementById("searchBtn").onclick = async () => {
  const title = document.getElementById("searchInput").value.trim();
  if (!title) return loadMovies();
  await loadMovies(`/api/movies/search?title=${encodeURIComponent(title)}`);
};
document.getElementById("filterBtn").onclick = async () => {
  const genre = document.getElementById("genreInput").value.trim();
  if (!genre) return loadMovies();
  await loadMovies(`/api/movies/filter?genre=${encodeURIComponent(genre)}`);
};
document.getElementById("resetBtn").onclick = () => loadMovies();

async function runRecommend(seed, showToast = true) {
  els.recommendGrid.dataset.seed = seed;
  const recs = await api(`/api/recommend?movie=${encodeURIComponent(seed)}`);
  renderGrid(els.recommendGrid, recs, { favIds: favouriteIds, showReason: true });
  if (showToast) toast(`Found ${recs.length} recommendations`);
}

document.getElementById("recommendBtn").onclick = async () => {
  const seed = document.getElementById("seedInput").value.trim();
  if (!seed) return toast("Enter a movie title or genre.", true);
  try {
    await runRecommend(seed);
  } catch (err) {
    toast(err.message, true);
  }
};

document.getElementById("moodBtn").onclick = async () => {
  const mood = document.getElementById("moodInput").value.trim() || "happy";
  els.moodResult.textContent = "Asking Gemini…";
  try {
    const data = await api(`/api/gemini/movies?mood=${encodeURIComponent(mood)}`);
    const genres = (data.genres || []).join(", ") || data.text;
    els.moodResult.textContent = `Genres for “${mood}”: ${genres}`;
    if (data.genres?.[0]) {
      document.getElementById("seedInput").value = data.genres[0];
    }
  } catch (err) {
    els.moodResult.textContent = err.message;
  }
};

document.querySelectorAll("[data-scroll]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.getElementById(btn.dataset.scroll)?.scrollIntoView({ behavior: "smooth" });
  });
});

["searchInput", "genreInput", "seedInput"].forEach((id) => {
  document.getElementById(id)?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    if (id === "searchInput") document.getElementById("searchBtn").click();
    if (id === "genreInput") document.getElementById("filterBtn").click();
    if (id === "seedInput") document.getElementById("recommendBtn").click();
  });
});

(async function init() {
  setAuthUI();
  try {
    await loadFavourites();
    await loadMovies();
  } catch (err) {
    els.movieGrid.innerHTML = `<p class="mood-result">${escapeHtml(err.message)}</p>`;
  }
})();

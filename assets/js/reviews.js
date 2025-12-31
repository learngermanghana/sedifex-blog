const SHEET_ID = '137HANmV9jmMWJEdcA1klqGiP8nYihkDugcIbA-2V1Wc';
const SHEET_GID = '0'; // worksheet gid

const endpoint = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?gid=${SHEET_GID}`;

function toInitials(name = '') {
  if (!name) return '';
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '';
  return parts.map(p => p[0].toUpperCase() + '.').join(' ');
}

async function fetchReviews() {
  const container = document.querySelector('#testimonials .reviews-container');
  if (!container) return;
  try {
    const res = await fetch(endpoint);
    const text = await res.text();
    const json = JSON.parse(text.substring(47).slice(0, -2));
    const rows = json.table.rows || [];
    const reviews = rows.map(row => ({
      student_name: row.c[0]?.v || '',
      rating: Number(row.c[1]?.v) || 0,
      review_text: row.c[2]?.v || ''
    }));

    // Show a rotating subset of three reviews based on the current day
    const dailyIndex = Math.floor(Date.now() / 86400000);
    const start = reviews.length ? dailyIndex % reviews.length : 0;
    const selected = [];
    for (let i = 0; i < 3 && i < reviews.length; i++) {
      selected.push(reviews[(start + i) % reviews.length]);
    }

    if (selected.length === 0) {
      container.innerHTML = '<p>No testimonials yet.</p>';
    } else {
      renderReviews(selected, container);
    }
  } catch (err) {
    console.error('Failed to load reviews', err);
    container.innerHTML = '<p class="error">Unable to load testimonials.</p>';
  }
}

function renderReviews(reviews, container) {
  container.innerHTML = '';
  reviews.forEach(r => {
    const card = document.createElement('div');
    card.className = 'review-card';

    const name = document.createElement('h3');
    name.textContent = toInitials(r.student_name);
    card.appendChild(name);

    const stars = document.createElement('div');
    stars.className = 'stars';
    const rating = Math.max(0, Math.min(5, r.rating));
    stars.textContent = '★'.repeat(rating) + '☆'.repeat(5 - rating);
    stars.setAttribute('aria-label', `Rating: ${rating} out of 5`);
    card.appendChild(stars);

    const text = document.createElement('p');
    text.textContent = r.review_text;
    card.appendChild(text);

    container.appendChild(card);
  });
}

fetchReviews();

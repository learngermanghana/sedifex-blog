---
layout: page
title: Search
permalink: /search/
---

<input type="text" id="search-input" placeholder="Search posts...">
<ul id="results-container" class="search-results"></ul>

<script src="https://cdn.jsdelivr.net/npm/simple-jekyll-search@1.11.1/dest/simple-jekyll-search.min.js"></script>
<script>
  SimpleJekyllSearch({
    searchInput: document.getElementById('search-input'),
    resultsContainer: document.getElementById('results-container'),
    json: '/search.json',
    searchResultTemplate: '<li><a href="{url}">{title}</a><span> — {date}</span></li>',
    noResultsText: '<li>No results</li>',
    limit: 20,
    fuzzy: true
  })
</script>

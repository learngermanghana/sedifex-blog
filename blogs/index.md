---
layout: page
title: Blogs
pagination:
  enabled: true
  per_page: 10
  permalink: '/blogs/page:num/'
---

<section class="blog-index-hero">
  <span class="eyebrow muted-eyebrow">Sedifex knowledge hub</span>
  <h1>Blog articles for buyers, sellers, and growing businesses</h1>
  <p>Explore product spotlights, buyer guides, seller education, online payments, inventory management, and Sedifex Market updates.</p>
</section>

<section class="category-cloud" aria-label="Blog categories">
  <a href="#sedifex-market">Sedifex Market</a>
  <a href="#business-automation">Business Automation</a>
  <a href="#inventory-management">Inventory Management</a>
  <a href="#online-payments">Online Payments</a>
  <a href="#small-business-ghana">Small Business Ghana</a>
  <a href="#product-spotlight">Product Spotlight</a>
  <a href="#seller-education">Seller Education</a>
  <a href="#buyer-guide">Buyer Guide</a>
</section>

<div class="blog-index-grid">
{% for post in site.posts %}
  <article class="blog-list-card" id="{% if post.categories and post.categories.size > 0 %}{{ post.categories[0] | slugify }}{% endif %}">
    <a href="{{ post.url | relative_url }}">
      {% if post.image %}
      <img src="{{ post.image }}" alt="{{ post.title }}" loading="lazy">
      {% endif %}
      <div class="blog-list-card-body">
        <div class="meta">
          {{ post.date | date: "%b %d, %Y" }}
          {% if post.categories and post.categories.size > 0 %} · {{ post.categories[0] }}{% endif %}
        </div>
        <h2>{{ post.title }}</h2>
        {% if post.excerpt %}
          <p>{{ post.excerpt | strip_html | truncate: 150 }}</p>
        {% endif %}
      </div>
    </a>
  </article>
{% endfor %}
</div>

{% if paginator.total_pages > 1 %}
<nav class="pagination" role="navigation">
  {% if paginator.previous_page %}
    <a href="{{ paginator.previous_page_path | relative_url }}" class="previous">&laquo; Previous</a>
  {% endif %}
  <span class="page-number">Page {{ paginator.page }} of {{ paginator.total_pages }}</span>
  {% if paginator.next_page %}
    <a href="{{ paginator.next_page_path | relative_url }}" class="next">Next &raquo;</a>
  {% endif %}
</nav>
{% endif %}

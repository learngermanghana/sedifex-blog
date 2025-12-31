---
layout: page
title: Blogs
pagination:
  enabled: true
  per_page: 10
  permalink: '/blogs/page:num/'
---

<ul>
{% for post in site.posts %}
  <li>
    <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    <small>— {{ post.date | date: "%Y-%m-%d" }}</small>
  </li>
{% endfor %}
</ul>

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


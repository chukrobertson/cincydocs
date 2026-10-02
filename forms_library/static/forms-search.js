(function () {
  "use strict";

  var forms = [];
  var container = document.getElementById("forms-grid");
  var input = document.getElementById("search-input");
  var countEl = document.getElementById("results-count");
  var noResults = document.getElementById("no-results");

  if (!container || !input || !countEl || !noResults) return;

  function escapeHTML(value) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(value || ""));
    return div.innerHTML;
  }

  function formatDate(value) {
    if (!value) return "";
    var date = new Date(value + "T00:00:00Z");
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      timeZone: "UTC"
    }).format(date);
  }

  function render(list) {
    if (list.length === 0) {
      container.innerHTML = "";
      noResults.style.display = "block";
      countEl.textContent = "0 forms found";
      return;
    }

    noResults.style.display = "none";
    countEl.textContent = list.length + " form" + (list.length === 1 ? "" : "s") + " found";

    var html = "";
    list.forEach(function (form) {
      var checked = form.last_verified_at
        ? " &middot; Checked " + escapeHTML(formatDate(form.last_verified_at))
        : "";

      html += '<article class="form-card">';
      html += '<h3><a href="' + encodeURIComponent(form.slug) + '/">' + escapeHTML(form.title) + "</a></h3>";
      html += '<div class="form-card-meta">';
      if (form.agency) html += '<span class="card-badge">' + escapeHTML(form.agency) + "</span>";
      if (form.jurisdiction) html += '<span class="card-badge">' + escapeHTML(form.jurisdiction) + "</span>";
      if (form.category) html += '<span class="card-badge">' + escapeHTML(form.category) + "</span>";
      if (form.form_number) html += '<span class="card-badge">' + escapeHTML(form.form_number) + "</span>";
      html += "</div>";
      if (form.summary) {
        html += "<p>" + escapeHTML(form.summary.substring(0, 240)) + (form.summary.length > 240 ? "&hellip;" : "") + "</p>";
      }
      html += '<div class="card-footer">' + (form.locally_stored ? "Download available here" : "Link to issuing agency") + checked + "</div>";
      html += "</article>";
    });
    container.innerHTML = html;
  }

  function search(query) {
    var terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (terms.length === 0) {
      render(forms);
      return;
    }

    render(forms.filter(function (form) {
      var haystack = [
        form.title,
        form.form_number,
        form.agency,
        form.jurisdiction,
        form.category,
        form.description,
        form.summary,
        (form.tags || []).join(" ")
      ].join(" ").toLowerCase();
      return terms.every(function (term) { return haystack.indexOf(term) !== -1; });
    }));
  }

  input.addEventListener("input", function () { search(input.value); });

  fetch("forms.json")
    .then(function (response) {
      if (!response.ok) throw new Error("Unable to load forms index");
      return response.json();
    })
    .then(function (data) {
      forms = data.filter(function (form) {
        return form.publication_status !== "hidden" && form.publication_status !== "internal_only";
      });
      render(forms);
    })
    .catch(function () {
      countEl.textContent = "Published forms are listed below. Search is unavailable right now.";
    });
})();

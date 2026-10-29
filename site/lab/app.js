"use strict";

(function () {
  var $ = function (id) { return document.getElementById(id); };
  var dom = {
    app: $("lab-app"), replayStatus: $("replay-status"), replayContent: $("replay-content"),
    scenario: $("scenario-select"), previous: $("previous-scenario"), next: $("next-scenario"),
    scenarioShare: $("scenario-share-url"), copyScenario: $("copy-scenario-link"),
    scenarioFeedback: $("scenario-feedback-link"), scenarioShareStatus: $("scenario-share-status"),
    prompt: $("scenario-prompt"), explanation: $("scenario-explanation"),
    claims: $("claims-list"), claimCount: $("claims-count"), tabs: $("evidence-tabs"),
    panel: $("evidence-panel"), editor: $("review-editor"), reviewStatus: $("review-status-select"),
    note: $("review-note"), noteContext: $("review-context"), noteStatus: $("note-status"),
    downloadReview: $("download-review"), clearReview: $("clear-review"),
    disclaimer: $("replay-disclaimer"), catalogStatus: $("catalog-status"),
    catalogSearch: $("catalog-search"), catalogType: $("catalog-type"),
    catalogResults: $("catalog-results"), catalogCount: $("catalog-count"),
    catalogDate: $("catalog-date"), catalogIntro: $("catalog-introduction"), catalogScope: $("catalog-scope"),
    catalogTopic: $("catalog-topic"), catalogReview: $("catalog-review"), catalogSort: $("catalog-sort"),
    catalogClear: $("catalog-clear"), catalogPagination: $("catalog-pagination"), catalogPage: $("catalog-page"),
    catalogPrevious: $("catalog-previous"), catalogNext: $("catalog-next"),
    downloadCatalogJson: $("download-catalog-json"), downloadCatalogBibtex: $("download-catalog-bibtex"),
    libraryHealth: $("library-health"), libraryMessage: $("library-status-message"),
    libraryDates: $("library-refresh-dates"), libraryCoverage: $("library-coverage"),
    librarySources: $("library-source-runs"), libraryRetry: $("library-retry"), retryLibrary: $("retry-library"),
    guideIntent: $("guide-intent"), guideAnswer: $("guide-answer"),
    verification: $("verification-record"), downloadReceipts: $("download-receipts"),
    announcement: $("app-announcement")
  };
  // Retain this historical key so existing visitors keep their saved notes.
  var NOTE_STORAGE_KEY = "sparks-lab-review-notes-v1";
  var NOTE_STATUSES = ["no-decision", "follow-up-needed", "comment-recorded"];
  var CATALOG_PAGE_SIZE = 12;
  var LIBRARY_STALE_MS = 48 * 60 * 60 * 1000;
  var REVIEW_LABELS = {source_inspected:"Source inspected",metadata_only:"Metadata only",needs_review:"Needs review"};
  var state = {
    replay: null, catalog: null, scenarioIndex: 0, claimId: null, sourceIndex: 0,
    tab: "before", notes: Object.create(null), storageAvailable: true,
    library: null, libraryLoading: false, libraryLoadError: false, catalogPage: 1, filteredItems: []
  };

  function node(tag, text, className) {
    var element = document.createElement(tag);
    if (text !== undefined && text !== null) element.textContent = String(text);
    if (className) element.className = className;
    return element;
  }
  function text(value, fallback) {
    return typeof value === "string" && value.trim() ? value : (fallback || "");
  }
  function list(value) { return Array.isArray(value) ? value : []; }
  function record(value) { return value && typeof value === "object" && !Array.isArray(value) ? value : {}; }
  function stringList(value) { return list(value).filter(function (item) { return typeof item === "string" && item.trim(); }); }
  function useFor(item) { return text(item.use_for) || stringList(item.use_for).join("; "); }
  function niceId(value) { return String(value || "").replace(/[-_]/g, " "); }
  function shortRevision(value) { return text(value).slice(0, 12); }
  function safeUrl(value) {
    if (typeof value !== "string" || !value.trim()) return null;
    try {
      var url = new URL(value, document.baseURI);
      return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
    } catch (_) { return null; }
  }
  function link(label, value, className) {
    var href = safeUrl(value);
    if (!href) return node("span", label, className);
    var element = node("a", label, className);
    element.href = href;
    return element;
  }
  function setLink(id, value) {
    var href = safeUrl(value);
    if (href && $(id)) $(id).href = href;
  }
  function announce(message) { dom.announcement.textContent = message; }
  function dateLabel(value) {
    if (!value) return "";
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      var day = new Date(value + "T12:00:00Z");
      return day.toLocaleDateString("en-GB", {day:"numeric",month:"short",year:"numeric",timeZone:"UTC"});
    }
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString("en-GB", {day:"numeric",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",timeZone:"Asia/Singapore"}) + " SGT";
  }
  function timestamp(value) {
    if (typeof value !== "string" || !value.trim()) return null;
    var parsed = Date.parse(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  function recordedDate(value) { return timestamp(value) === null ? "Not recorded" : dateLabel(value); }
  function publicationLabel(value) {
    value = text(value);
    if (/^\d{4}$/.test(value)) return value;
    if (/^\d{4}-\d{2}$/.test(value) && timestamp(value + "-01") !== null) {
      return new Date(value + "-01T12:00:00Z").toLocaleDateString("en-GB",{month:"short",year:"numeric",timeZone:"UTC"});
    }
    return timestamp(value) === null ? value : dateLabel(value);
  }
  function jsonText(value) {
    try { return JSON.stringify(value, null, 2); } catch (_) { return String(value); }
  }
  function downloadJson(value, filename) {
    downloadContent(jsonText(value) + "\n", filename, "application/json");
  }
  function downloadContent(value, filename, type) {
    var blob = new Blob([value], {type:type + ";charset=utf-8"});
    var url = URL.createObjectURL(blob);
    var anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.hidden = true;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1500);
  }
  function today() { return new Date().toISOString().slice(0, 10); }
  function copyText(value, button) {
    function done() {
      var previous = button.textContent;
      button.textContent = "Copied";
      announce("Copied to clipboard.");
      window.setTimeout(function () { button.textContent = previous; }, 1800);
    }
    function fallback() {
      var area = node("textarea", value);
      area.className = "sr-only";
      document.body.appendChild(area);
      area.select();
      var copied = false;
      try { copied = document.execCommand("copy"); } catch (_) {}
      area.remove();
      button.focus();
      if (copied) done();
      else announce("Clipboard access is unavailable. Select and copy the text shown above the button.");
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(value).then(done, fallback);
    else fallback();
  }

  function readNotes() {
    try {
      var parsed = JSON.parse(localStorage.getItem(NOTE_STORAGE_KEY) || "{}");
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return;
      Object.keys(parsed).forEach(function (key) {
        var entry = parsed[key];
        if (entry && typeof entry === "object" && typeof entry.note === "string" &&
            entry.note.length <= 6000 && NOTE_STATUSES.includes(entry.next_step)) {
          state.notes[key] = entry;
        }
      });
    } catch (_) { state.storageAvailable = false; }
  }
  function persistNotes() {
    try {
      localStorage.setItem(NOTE_STORAGE_KEY, JSON.stringify(state.notes));
      state.storageAvailable = true;
    } catch (_) { state.storageAvailable = false; }
  }
  function scenario() {
    return state.replay ? list(state.replay.scenarios)[state.scenarioIndex] : null;
  }
  function claimsFor(current) {
    if (!current) return [];
    var display = current.display || {};
    if (Array.isArray(display.claims)) return display.claims;
    var input = current.input || {};
    var ledger = input.ledger || input.base_ledger || {};
    return list(ledger.claims).map(function (claim) {
      return {
        id:claim.id, text:claim.text, before_status:claim.review_status,
        after_status:claim.review_status, evidence:list(claim.evidence),
        review_note:claim.review && claim.review.note
      };
    });
  }
  function selectedClaim() {
    return claimsFor(scenario()).find(function (claim) { return String(claim.id) === state.claimId; }) || null;
  }
  function snapshotId() {
    return state.replay ? text(state.replay.generated_at, "undated") : "";
  }
  function noteKey() {
    var current = scenario();
    return current ? [text(state.replay.id,"regnav"),snapshotId(),String(current.id),state.claimId || "scenario"].join("::") : "";
  }
  function currentNotes() {
    if (!state.replay) return [];
    return Object.values(state.notes).filter(function (entry) {
      return entry.dataset_id === text(state.replay.id,"regnav") && entry.recorded_at === snapshotId();
    });
  }
  function updateNoteButtons() {
    var entry = state.notes[noteKey()];
    dom.clearReview.disabled = !entry;
    dom.downloadReview.disabled = currentNotes().length === 0;
  }
  function loadNoteEditor() {
    var current = scenario(), claim = selectedClaim();
    var entry = state.notes[noteKey()];
    dom.note.value = entry ? entry.note : "";
    dom.reviewStatus.value = entry ? entry.next_step : "no-decision";
    dom.noteContext.textContent = "Attached to " + text(current && current.title, "the selected scenario") +
      (claim ? " · " + String(claim.id) : " · scenario-level note") + ". Maximum 6,000 characters.";
    dom.noteStatus.textContent = entry
      ? (state.storageAvailable ? "Saved in this browser." : "Kept for this session. Download to retain your notes.")
      : (state.storageAvailable ? "Nothing is sent to a server." : "Browser storage is unavailable. Download your notes before closing this tab.");
    updateNoteButtons();
  }
  function saveCurrentNote() {
    var current = scenario();
    if (!current) return;
    var key = noteKey();
    var previous = state.notes[key];
    var note = dom.note.value.slice(0, 6000);
    var nextStep = NOTE_STATUSES.includes(dom.reviewStatus.value) ? dom.reviewStatus.value : "no-decision";
    if (!note.trim() && nextStep === "no-decision") {
      delete state.notes[key];
    } else {
      var now = new Date().toISOString();
      state.notes[key] = {
        dataset_id:text(state.replay.id,"regnav"), recorded_at:snapshotId(),
        scenario_id:String(current.id), scenario_title:text(current.title),
        claim_id:state.claimId, next_step:nextStep, note:note,
        source_revisions:list(state.replay.provenance && state.replay.provenance.sources).map(function (source) {
          return {repository:source.repository,revision:source.revision,url:source.url};
        }),
        receipt_ids:list(current.receipt_ids), created_at:previous ? previous.created_at : now,
        updated_at:now
      };
    }
    persistNotes();
    dom.noteStatus.textContent = state.storageAvailable ? "Saved in this browser." : "Kept for this session. Download to retain your notes.";
    updateNoteButtons();
  }

  async function fetchJson(path) {
    var response = await fetch(path, {cache:"no-cache",credentials:"same-origin"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    var data = await response.json();
    if (!data || data.schema_version !== 1) throw new Error("Unsupported data schema");
    return data;
  }
  function loadError(container, kind, filename, retry) {
    container.hidden = false;
    container.className = "load-state error";
    container.replaceChildren(node("p", "The " + kind + " could not be loaded. You can inspect the source record or try again."));
    container.appendChild(link("Open the source record", "https://github.com/Albertito-AI/Albertito-AI/blob/main/site/lab/data/" + filename));
    var button = node("button", "Try again", "button button-secondary");
    button.type = "button";
    button.addEventListener("click", retry);
    container.appendChild(button);
  }
  async function loadReplay() {
    dom.replayStatus.hidden = false;
    dom.replayStatus.className = "load-state";
    dom.replayStatus.textContent = "Loading the recorded example…";
    try {
      var data = await fetchJson("data/regnav.json");
      if (!list(data.scenarios).length || !Array.isArray(data.receipts)) throw new Error("The example has no scenarios or receipts");
      var firstLoad = !state.replay;
      state.replay = data;
      state.scenarioIndex = Math.min(state.scenarioIndex, data.scenarios.length - 1);
      var sharedNotice = "";
      if (firstLoad) {
        var parameters = new URL(window.location.href).searchParams;
        var requested = parameters.get("scenario");
        if (requested !== null) {
          var requestedIndex = data.scenarios.findIndex(function (item) { return String(item.id) === requested; });
          state.scenarioIndex = requestedIndex < 0 ? 0 : requestedIndex;
          if (requestedIndex < 0) sharedNotice = "That shared scenario is unavailable. Showing the first recorded example.";
          else if (parameters.has("record") && parameters.get("record") !== snapshotId()) {
            sharedNotice = "The recorded dataset has changed since this link was shared. Showing the current recorded version of this example.";
          }
        }
      }
      dom.scenario.replaceChildren();
      data.scenarios.forEach(function (item, index) {
        var option = node("option", (index + 1) + ". " + text(item.title, niceId(item.id)));
        option.value = String(index);
        dom.scenario.appendChild(option);
      });
      dom.disclaimer.textContent = text(data.disclaimer, "Structural checks can expose gaps and changes. They cannot determine whether a passage substantively supports a legal proposition.");
      dom.replayContent.hidden = false;
      dom.replayStatus.hidden = true;
      dom.downloadReceipts.disabled = false;
      setScenario(state.scenarioIndex, false);
      if (sharedNotice) dom.scenarioShareStatus.textContent = sharedNotice + " Your review notes stay in this browser.";
    } catch (error) {
      console.warn("Recorded example unavailable:", error);
      loadError(dom.replayStatus, "recorded example", "regnav.json", loadReplay);
      if (!state.replay) dom.replayContent.hidden = true;
    }
  }
  async function loadCatalog() {
    dom.catalogStatus.hidden = false;
    dom.catalogStatus.className = "load-state";
    dom.catalogStatus.textContent = "Loading the public catalog…";
    try {
      var data = await fetchJson("data/catalog.json");
      if (!Array.isArray(data.items)) throw new Error("The catalog has no item list");
      state.catalog = data;
      dom.catalogStatus.hidden = true;
      dom.catalogDate.textContent = data.updated_at ? "Original catalog updated " + dateLabel(data.updated_at) : "";
      if (text(data.introduction)) dom.catalogIntro.textContent = data.introduction;
      dom.catalogScope.textContent = text(data.scope_note);
      var links = data.links || {};
      setLink("feedback-link", links.feedback);
      setLink("evaluation-link", links.evaluation);
      syncCatalogTopics();
      filterFromHash(false);
      renderCatalog();
      renderGuide();
      renderLibraryStatus();
    } catch (error) {
      console.warn("Public catalog unavailable:", error);
      loadError(dom.catalogStatus, "public catalog", "catalog.json", loadCatalog);
      renderCatalog();
      renderLibraryStatus();
    }
  }
  async function loadLibrary() {
    if (state.libraryLoading) return;
    state.libraryLoading = true;
    state.libraryLoadError = false;
    renderLibraryStatus();
    try {
      var data = await fetchJson("data/library.json");
      if (data.items !== undefined && !Array.isArray(data.items)) throw new Error("The library item list is invalid");
      state.library = data;
      syncCatalogTopics();
      renderCatalog();
    } catch (error) {
      console.warn("Reference library unavailable:", error);
      state.libraryLoadError = true;
    } finally {
      state.libraryLoading = false;
      renderLibraryStatus();
    }
  }
  function catalogEntries() {
    var entries = [], seen = new Set();
    function append(items, fromLibrary) {
      list(items).forEach(function (item, index) {
        if (!item || typeof item !== "object" || Array.isArray(item)) return;
        var id = text(item.id, (fromLibrary ? "library" : "catalog") + "-entry-" + index);
        if (seen.has(id)) return;
        seen.add(id);
        var type = ["project","research","teaching","reference"].includes(item.type) ? item.type : (fromLibrary ? "reference" : "unknown");
        entries.push(Object.assign(Object.create(null), item, {id:id, type:type, _fromLibrary:fromLibrary}));
      });
    }
    append(state.catalog && state.catalog.items, false);
    append(state.library && state.library.items, true);
    return entries;
  }
  function reviewStatusFor(item) {
    if (Object.prototype.hasOwnProperty.call(REVIEW_LABELS, item.review_status)) return item.review_status;
    if (!item._fromLibrary && record(item.verification).checked_at) return "source_inspected";
    return "needs_review";
  }
  function syncCatalogTopics() {
    var previous = dom.catalogTopic.value;
    var topics = new Set();
    catalogEntries().forEach(function (item) { stringList(item.topics).forEach(function (topic) { topics.add(topic); }); });
    dom.catalogTopic.replaceChildren();
    var all = node("option", "All topics");
    all.value = "all";
    dom.catalogTopic.appendChild(all);
    Array.from(topics).sort(function (a,b) { return a.localeCompare(b,"en",{sensitivity:"base"}); }).forEach(function (topic) {
      var option = node("option", topic);
      option.value = topic;
      dom.catalogTopic.appendChild(option);
    });
    dom.catalogTopic.value = topics.has(previous) ? previous : "all";
  }
  function renderLibraryStatus() {
    var data = state.library || {};
    var successTime = timestamp(data.last_successful_refresh);
    var stale = successTime !== null && Date.now() - successTime > LIBRARY_STALE_MS;
    var future = successTime !== null && successTime - Date.now() > 5 * 60 * 1000;
    var label = "No update record", css = "label-plain";
    var message = "No successful reference update is recorded. The original catalog remains available independently.";
    if (state.libraryLoading) {
      label = "Checking update record";
      message = "Loading the additional reference library. Available catalog entries remain searchable.";
    } else if (state.libraryLoadError) {
      label = "Library update unavailable";
      css = "label-red";
      message = "The reference library could not be loaded. " + (state.library
        ? "The previously loaded records remain available with their recorded dates."
        : "The original catalog remains available when its separate record has loaded.") + " Try again or inspect the published data.";
    } else if (state.library) {
      if (data.status === "failed") {
        label = "Latest update failed";
        css = "label-red";
        message = "The latest update did not succeed. Retained records remain searchable; their dates and source status are shown below.";
      } else if (data.status === "degraded") {
        label = "Some sources need attention";
        css = "label-warm";
        message = "Some source updates did not complete. Available records remain searchable; inspect the individual source results below.";
      } else if (future) {
        label = "Update date needs review";
        css = "label-warm";
        message = "The recorded success date is ahead of this browser's clock. Check the source history before treating the update as recent.";
      } else if (stale) {
        label = "Source update overdue";
        css = "label-warm";
        message = "The latest recorded successful source update is more than 48 hours old. The retained records are available, but current source coverage needs another check.";
      } else if (data.status === "ok" && successTime !== null) {
        label = "Last update succeeded";
        css = "label-green";
        message = "The recorded source update completed. Review labels show which entries received source inspection and which contain bibliographic metadata only.";
      } else {
        label = "Update status not established";
        message = "Reference records are available, but a successful update date and status are not both recorded. Check the source history before relying on update recency.";
      }
      if (stale && data.status !== "ok") message += " The last recorded success is also more than 48 hours old.";
    }
    dom.libraryHealth.textContent = label;
    dom.libraryHealth.className = "label " + css;
    dom.libraryHealth.dataset.state = state.libraryLoadError ? "unavailable" : (stale ? "stale" : text(data.status,"unknown"));
    dom.libraryMessage.textContent = message;
    dom.libraryRetry.hidden = !state.libraryLoadError;
    dom.retryLibrary.disabled = state.libraryLoading;
    var entries = catalogEntries();
    var inspectedDates = entries.filter(function (item) { return reviewStatusFor(item) === "source_inspected"; })
      .map(function (item) { return record(item.verification).checked_at; })
      .filter(function (value) { return timestamp(value) !== null; });
    inspectedDates.sort(function (a,b) { return timestamp(b) - timestamp(a); });
    var sourceAttemptDates = list(data.source_runs)
      .map(function (source) { return record(source).checked_at; })
      .filter(function (value) { return timestamp(value) !== null; });
    sourceAttemptDates.sort(function (a,b) { return timestamp(b) - timestamp(a); });
    dom.libraryDates.replaceChildren();
    [
      ["Latest source-update attempt", sourceAttemptDates[0]],
      ["Latest successful source update", data.last_successful_refresh],
      ["Snapshot rebuilt", data.generated_at],
      ["Latest recorded curated inspection", inspectedDates[0]],
      ["Original catalog updated", state.catalog && state.catalog.updated_at]
    ].forEach(function (pair) {
      var field = node("div");
      field.append(node("dt",pair[0]),node("dd",recordedDate(pair[1])));
      dom.libraryDates.appendChild(field);
    });
    var originalCount = entries.filter(function (item) { return !item._fromLibrary; }).length;
    var referenceCount = entries.length - originalCount;
    var metadataCount = entries.filter(function (item) { return reviewStatusFor(item) === "metadata_only"; }).length;
    dom.libraryCoverage.textContent = originalCount + " original catalog " + (originalCount === 1 ? "entry" : "entries") +
      " · " + referenceCount + " added " + (referenceCount === 1 ? "reference" : "references") +
      (metadataCount ? " · " + metadataCount + " metadata-only records in total" : "") + ".";
    dom.librarySources.replaceChildren();
    list(data.source_runs).forEach(function (source) {
      if (!source || typeof source !== "object" || Array.isArray(source)) return;
      var row = node("li");
      var runLabels = {ok:"Completed",success:"Completed",succeeded:"Completed",degraded:"Partial",partial:"Partial",failed:"Failed",error:"Failed",skipped:"Skipped"};
      var runLabel = Object.prototype.hasOwnProperty.call(runLabels,source.status) ? runLabels[source.status] : "Status not recorded";
      row.appendChild(node("strong",text(source.label,text(source.id,"Source")) + " · " + runLabel));
      var parts = ["Checked: " + recordedDate(source.checked_at)];
      if (Number.isInteger(source.discovered) && source.discovered >= 0) parts.push(source.discovered + " discovered");
      if (Number.isInteger(source.accepted) && source.accepted >= 0) parts.push(source.accepted + " accepted");
      row.appendChild(node("span",parts.join(" · "),"source-run-meta"));
      if (text(source.error)) row.appendChild(node("span",source.error,"source-run-meta"));
      dom.librarySources.appendChild(row);
    });
    if (!dom.librarySources.childNodes.length) dom.librarySources.appendChild(node("li","No individual source-update results are recorded."));
  }

  function setScenario(index, shouldAnnounce) {
    if (!state.replay) return;
    var scenarios = list(state.replay.scenarios);
    state.scenarioIndex = Math.max(0, Math.min(index, scenarios.length - 1));
    var current = scenario();
    dom.scenario.value = String(state.scenarioIndex);
    dom.previous.disabled = state.scenarioIndex === 0;
    dom.next.disabled = state.scenarioIndex === scenarios.length - 1;
    dom.prompt.textContent = text(current.prompt, current.title);
    dom.explanation.textContent = text(current.explanation);
    var claims = claimsFor(current);
    state.claimId = claims.length ? String(claims[0].id) : null;
    state.sourceIndex = 0;
    renderClaims();
    renderEvidence();
    renderVerification();
    updateNoteButtons();
    renderScenarioLinks();
    if (shouldAnnounce !== false) announce("Showing recorded scenario: " + text(current.title, current.id) + ".");
  }
  function renderScenarioLinks() {
    var current = scenario();
    if (!current) return;
    var shared = new URL(window.location.href);
    shared.search = "";
    shared.hash = "replay";
    shared.searchParams.set("scenario", String(current.id));
    shared.searchParams.set("record", snapshotId());
    dom.scenarioShare.value = shared.href;
    dom.copyScenario.disabled = false;

    var report = new URL("https://github.com/Albertito-AI/Albertito-AI/issues/new");
    report.searchParams.set("template", "lab-feedback.yml");
    report.searchParams.set("title", "[Research lab] " + text(current.title, current.id));
    var context = [text(current.title, current.id) + " (" + String(current.id) + ")",
      "Recorded dataset: " + text(state.replay.id, "regnav") + " at " + snapshotId()];
    list(state.replay.provenance && state.replay.provenance.sources).forEach(function (source) {
      if (text(source.repository) && text(source.revision)) context.push(source.repository + "@" + source.revision);
    });
    report.searchParams.set("version", context.join(" | "));
    dom.scenarioFeedback.href = report.href;
    dom.scenarioShareStatus.textContent = "Share the recorded example or open a public GitHub feedback form. Your review notes stay in this browser.";
  }
  function renderClaims() {
    var claims = claimsFor(scenario());
    dom.claimCount.textContent = claims.length ? String(claims.length) : "";
    dom.claims.replaceChildren();
    if (!claims.length) {
      dom.claims.appendChild(node("p", "This is a source-level record. Inspect the scenario and its execution receipts.", "sidebar-note"));
      return;
    }
    claims.forEach(function (claim) {
      var button = node("button", null, "claim-button");
      button.type = "button";
      button.dataset.claimId = String(claim.id);
      button.setAttribute("aria-pressed", String(String(claim.id) === state.claimId));
      button.appendChild(node("strong", String(claim.id)));
      button.appendChild(node("span", text(claim.text, "Claim details are in the source record.")));
      button.addEventListener("click", function () {
        state.claimId = String(claim.id);
        state.sourceIndex = 0;
        renderClaims();
        var selected = dom.claims.querySelector('[aria-pressed="true"]');
        if (selected) selected.focus({preventScroll:true});
        renderEvidence();
        updateNoteButtons();
        announce("Selected claim " + String(claim.id) + ".");
      });
      dom.claims.appendChild(button);
    });
  }
  function chooseTab(tab, focusTab) {
    if (!["before","after","review"].includes(tab)) return;
    if (state.tab !== tab) state.sourceIndex = 0;
    state.tab = tab;
    Array.from(dom.tabs.querySelectorAll("[role=tab]")).forEach(function (button) {
      var selected = button.dataset.tab === tab;
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
      if (selected && focusTab) button.focus();
    });
    dom.panel.setAttribute("aria-labelledby", "tab-" + tab);
    renderEvidence();
  }
  function sourceOptions(claim) {
    var packet = state.replay && state.replay.source_packet || {};
    var sources = list(packet.sources);
    var evidence = claim ? list(claim.evidence) : [];
    if (evidence.length) return evidence.map(function (item) {
      var source = sources.find(function (candidate) { return String(candidate.id) === String(item.source_id); }) || {};
      var paragraph = list(source.paragraphs).find(function (candidate) { return String(candidate.id) === String(item.pinpoint); });
      return {
        label:text(source.title, String(item.source_id || "Recorded source")) + (item.pinpoint ? " · " + item.pinpoint : ""),
        quote:typeof item.quote === "string" ? item.quote : (paragraph && text(paragraph.text)),
        url:["temporary-fixture","unresolved-source"].includes(item.quote_origin) ? null : (item.source_url || source.url),
        originalUrl:item.original_source_url,
        quoteOrigin:text(item.quote_origin),
        quoteLabel:text(item.quote_label),
        relation:text(item.relation),
        pinpoint:text(item.pinpoint),
        context:false
      };
    });
    if (claim && (text(claim.source_quote) || safeUrl(claim.source_url))) {
      return [{label:"Cited passage",quote:text(claim.source_quote),url:claim.source_url,relation:"",pinpoint:"",context:false}];
    }
    return sources.map(function (source) {
      return {
        label:text(source.title, source.id),quote:list(source.paragraphs).map(function (paragraph) {
          return (paragraph.id ? paragraph.id + "  " : "") + text(paragraph.text);
        }).join("\n\n"),
        url:source.url,relation:"",pinpoint:"",context:true
      };
    });
  }
  function renderSource(parent, claim) {
    var options = sourceOptions(claim);
    if (!options.length) return;
    state.sourceIndex = Math.min(state.sourceIndex, options.length - 1);
    var field = node("div", null, "field source-chooser");
    var label = node("label", "Inspect a source passage");
    label.htmlFor = "source-select";
    var select = node("select");
    select.id = "source-select";
    options.forEach(function (item, index) {
      var option = node("option", item.label);
      option.value = String(index);
      select.appendChild(option);
    });
    select.value = String(state.sourceIndex);
    select.addEventListener("change", function () {
      state.sourceIndex = Number(select.value);
      renderEvidence();
      var replacement = $("source-select");
      if (replacement) replacement.focus();
      announce("Showing " + options[state.sourceIndex].label + ".");
    });
    field.append(label, select);
    parent.appendChild(field);
    var selected = options[state.sourceIndex];
    var figure = node("figure", null, "source-quote");
    figure.appendChild(node("blockquote", selected.quote || "No quoted passage is recorded for this source. Inspect the linked source and execution output."));
    var caption = node("figcaption", selected.quoteLabel || (selected.context ? "Full recorded source context" : "Passage quoted in the fictional example"));
    if (selected.relation) caption.appendChild(node("div", "Recorded relation: " + selected.relation + (selected.pinpoint ? " · " + selected.pinpoint : "")));
    if (safeUrl(selected.url)) caption.appendChild(link("Inspect the source at its recorded revision ↗", selected.url));
    if (selected.quoteOrigin === "temporary-fixture" && safeUrl(selected.originalUrl)) caption.appendChild(link("Original source context ↗", selected.originalUrl));
    figure.appendChild(caption);
    parent.appendChild(figure);
  }
  function renderFindings(parent, current) {
    var observed = current.observed || {};
    var validation = observed.validation;
    if (validation && typeof validation === "object") {
      var section = node("div", null, "findings");
      section.appendChild(node("h4", "Recorded structural check"));
      var summary = node("div", null, "finding-summary");
      if (typeof validation.error_count === "number") summary.appendChild(node("span", validation.error_count + " error" + (validation.error_count === 1 ? "" : "s"), validation.error_count ? "label label-red" : "label label-green"));
      if (typeof validation.warning_count === "number") summary.appendChild(node("span", validation.warning_count + " warning" + (validation.warning_count === 1 ? "" : "s"), validation.warning_count ? "label label-warm" : "label label-plain"));
      if (typeof validation.structurally_valid === "boolean") summary.appendChild(node("span", validation.structurally_valid ? "No structural errors reported" : "Structural errors reported", "label label-plain"));
      section.appendChild(summary);
      var findings = list(validation.findings);
      if (findings.length) {
        var rows = node("ul", null, "finding-list");
        findings.forEach(function (finding) {
          var item = node("li");
          item.appendChild(node("span", [finding.severity,finding.code].filter(Boolean).join(" · "), "finding-code"));
          item.appendChild(node("span", text(finding.message)));
          if (text(finding.path)) item.appendChild(node("div", finding.path, "field-help"));
          rows.appendChild(item);
        });
        section.appendChild(rows);
      }
      if (text(validation.notice)) section.appendChild(node("p", validation.notice, "claim-review-note"));
      parent.appendChild(section);
    }
    [["comparison","Recorded ledger comparison"],["source_watch","Recorded source-watch result"]].forEach(function (pair) {
      if (!observed[pair[0]]) return;
      var detail = node("details", null, "item-details");
      detail.appendChild(node("summary", pair[1]));
      var block = node("div", null, "output-block");
      block.appendChild(node("pre", jsonText(observed[pair[0]])));
      detail.appendChild(block);
      parent.appendChild(detail);
    });
  }
  function renderEvidence() {
    var current = scenario();
    if (!current) return;
    dom.panel.replaceChildren();
    if (state.tab === "review") {
      dom.editor.hidden = false;
      dom.panel.appendChild(dom.editor);
      loadNoteEditor();
      return;
    }
    dom.editor.hidden = true;
    var after = state.tab === "after";
    var display = current.display || {};
    var title = after ? text(display.after_title, "The recorded result") : text(display.before_title, "The starting record");
    var heading = node("div", null, "evidence-heading");
    heading.appendChild(node("h3", title));
    heading.appendChild(node("span", after ? "AFTER" : "BEFORE", "label label-plain"));
    dom.panel.appendChild(heading);
    var narrative = after ? display.after_text : display.before_text;
    if (text(narrative)) dom.panel.appendChild(node("p", narrative, "snapshot-narrative"));
    if (after && list(display.changed_fields).length) {
      var changes = node("ul", null, "change-list");
      changes.setAttribute("aria-label", "Changed fields in this scenario");
      list(display.changed_fields).forEach(function (value) {
        changes.appendChild(node("li", typeof value === "string" ? value : jsonText(value)));
      });
      dom.panel.appendChild(changes);
    }
    var claim = selectedClaim();
    if (claim) {
      var side = after ? "after" : "before";
      if (Array.isArray(claim[side + "_evidence"])) {
        claim = Object.assign({}, claim, {
          evidence:claim[side + "_evidence"],
          review_note:text(claim[side + "_review_note"]),
          source_quote:"",source_url:null
        });
      }
      var card = node("div", null, "claim-display");
      card.appendChild(node("div", "CLAIM " + String(claim.id), "claim-kicker"));
      card.appendChild(node("p", text(claim.text, "Read the claim in the recorded source."), "claim-text"));
      var status = after ? claim.after_status : claim.before_status;
      var statusLine = node("p", null, "claim-state");
      statusLine.appendChild(document.createTextNode("Recorded review status: "));
      statusLine.appendChild(node("strong", text(status, "not recorded for this view")));
      card.appendChild(statusLine);
      dom.panel.appendChild(card);
    }
    renderSource(dom.panel, claim);
    if (claim && text(claim.review_note)) dom.panel.appendChild(node("p", claim.review_note, "claim-review-note"));
    if (after) renderFindings(dom.panel, current);
    var receiptLink = node("p", null, "claim-review-note");
    receiptLink.appendChild(link("Examine this scenario's command and captured output ↓", "#verification"));
    dom.panel.appendChild(receiptLink);
  }

  function filteredCatalogEntries() {
    var query = dom.catalogSearch.value.trim().toLocaleLowerCase();
    var type = dom.catalogType.value;
    var topic = dom.catalogTopic.value, review = dom.catalogReview.value;
    var entries = catalogEntries().filter(function (item) {
      var haystack = [text(item.title),text(item.description),text(item.maturity),text(item.publisher),
        useFor(item),text(item.doi),text(record(item.citation).text)]
        .concat(stringList(item.topics),stringList(item.authors)).join(" ").toLocaleLowerCase();
      return (type === "all" || item.type === type) &&
        (topic === "all" || stringList(item.topics).includes(topic)) &&
        (review === "all" || reviewStatusFor(item) === review) && (!query || haystack.includes(query));
    });
    var sort = dom.catalogSort.value;
    return entries.sort(function (a,b) {
      if (sort === "title") return text(a.title,a.id).localeCompare(text(b.title,b.id),"en",{sensitivity:"base"});
      var left = timestamp(sort === "publication" ? a.publication_date : a.added_at);
      var right = timestamp(sort === "publication" ? b.publication_date : b.added_at);
      if (left === null && right === null) return 0;
      if (left === null) return 1;
      if (right === null) return -1;
      return right - left;
    });
  }
  function clearCatalogFilters() {
    dom.catalogSearch.value = "";
    dom.catalogType.value = "all";
    dom.catalogTopic.value = "all";
    dom.catalogReview.value = "all";
    state.catalogPage = 1;
  }
  function filterCatalog() {
    state.catalogPage = 1;
    renderCatalog();
  }
  function changeCatalogPage(offset) {
    state.catalogPage += offset;
    renderCatalog();
    dom.catalogResults.focus({preventScroll:true});
    dom.catalogResults.scrollIntoView({behavior:"auto",block:"start"});
    announce(dom.catalogCount.textContent);
  }
  function doiFor(item) {
    var value = text(item.doi,text(record(item.citation).doi)).replace(/^https?:\/\/(?:dx\.)?doi\.org\//i,"").replace(/^doi:\s*/i,"").trim();
    return /^10\.\d{4,9}\/[^\s]+$/i.test(value) ? value : "";
  }
  function primaryUrlFor(item) {
    var citation = record(item.citation), verification = record(item.verification);
    var source = list(item.links).find(function (entry) { return entry && entry.kind === "source" && safeUrl(entry.url); });
    var first = list(item.links).find(function (entry) { return entry && safeUrl(entry.url); });
    return safeUrl(item.url) || safeUrl(citation.url) ||
      (doiFor(item) ? "https://doi.org/" + encodeURIComponent(doiFor(item)).replace(/%2F/gi,"/") : null) ||
      safeUrl(source && source.url) || safeUrl(verification.source_url) || safeUrl(first && first.url);
  }
  function citationFor(item) {
    var citation = record(item.citation);
    if (citation.available && text(citation.text)) return citation;
    if (!item._fromLibrary && item.type !== "reference") return citation;
    var authors = stringList(item.authors).join("; ");
    var parts = [authors,text(item.title,item.id),text(item.publisher),text(item.publication_date),primaryUrlFor(item)].filter(Boolean);
    return {available:parts.length > 0,format:"text",text:parts.join(". "),url:primaryUrlFor(item),assembled:true};
  }
  function bibtexEscape(value) {
    var escapes = {"\\":"\\textbackslash{}","{":"\\{","}":"\\}","%":"\\%","&":"\\&","#":"\\#","_":"\\_","$":"\\$","^":"\\textasciicircum{}","~":"\\textasciitilde{}"};
    return String(value || "").replace(/[\u0000-\u001f\u007f]+/g," ").replace(/[\\{}%&#_$^~]/g,function (character) { return escapes[character]; });
  }
  function bibtexFor(items) {
    var keys = new Set();
    return items.map(function (item,index) {
      var baseKey = "lab-" + String(item.id).replace(/[^a-zA-Z0-9_-]/g,"-");
      var key = baseKey;
      var suffix = index + 1;
      while (keys.has(key)) key = baseKey + "-" + suffix++;
      keys.add(key);
      var fields = [["title",text(item.title,item.id)]];
      var authors = stringList(item.authors);
      if (authors.length) fields.push(["author",authors.join(" and ")]);
      if (text(item.publisher)) fields.push(["publisher",item.publisher]);
      var year = /^(\d{4})(?:-|$)/.exec(text(item.publication_date));
      if (year) fields.push(["year",year[1]]);
      if (doiFor(item)) fields.push(["doi",doiFor(item)]);
      if (primaryUrlFor(item)) fields.push(["url",primaryUrlFor(item)]);
      var notes = ["Review level: " + REVIEW_LABELS[reviewStatusFor(item)]];
      if (useFor(item)) notes.push("Useful for: " + useFor(item));
      if (!authors.length && text(record(item.citation).text)) notes.push("Recorded reference: " + item.citation.text);
      fields.push(["note",notes.join(". ")]);
      return "@misc{" + key + ",\n" + fields.map(function (field) { return "  " + field[0] + " = {" + bibtexEscape(field[1]) + "}"; }).join(",\n") + "\n}";
    }).join("\n\n") + "\n";
  }
  function exportCatalog(format) {
    var items = filteredCatalogEntries();
    if (!items.length) return;
    if (format === "bibtex") {
      downloadContent(bibtexFor(items),"research-library-" + today() + ".bib","application/x-bibtex");
    } else {
      downloadJson({
        schema_version:1,record_type:"filtered_library_metadata",exported_at:new Date().toISOString(),
        notice:"Metadata and recorded review scope only. Review labels do not establish full-text or legal verification. Check sources and citation style before use.",
        filters:{query:dom.catalogSearch.value.trim(),type:dom.catalogType.value,topic:dom.catalogTopic.value,review:dom.catalogReview.value,sort:dom.catalogSort.value},
        source_snapshot:{catalog_updated_at:state.catalog && state.catalog.updated_at || null,library_generated_at:state.library && state.library.generated_at || null,last_successful_refresh:state.library && state.library.last_successful_refresh || null,library_status:state.libraryLoadError ? "unavailable" : (state.library && state.library.status || "unknown")},
        items:items.map(function (item) {
          var exported = Object.assign(Object.create(null),item,{review_status:reviewStatusFor(item)});
          delete exported._fromLibrary;
          return exported;
        })
      },"research-library-" + today() + ".json");
    }
    announce("Downloaded " + items.length + " matching catalog " + (items.length === 1 ? "entry" : "entries") + " as " + (format === "bibtex" ? "BibTeX" : "JSON") + ".");
  }
  function renderCatalog() {
    if (!state.catalog && !state.library) return;
    var entries = filteredCatalogEntries();
    var allEntries = catalogEntries();
    state.filteredItems = entries;
    var totalPages = Math.max(1,Math.ceil(entries.length / CATALOG_PAGE_SIZE));
    state.catalogPage = Math.max(1,Math.min(state.catalogPage,totalPages));
    var start = (state.catalogPage - 1) * CATALOG_PAGE_SIZE;
    var visibleEntries = entries.slice(start,start + CATALOG_PAGE_SIZE);
    dom.catalogResults.replaceChildren();
    dom.catalogCount.textContent = entries.length + " of " + allEntries.length + " " + (allEntries.length === 1 ? "entry" : "entries") +
      (dom.catalogSearch.value.trim() ? ' matching “' + dom.catalogSearch.value.trim() + '”' : "") +
      (entries.length ? " · showing " + (start + 1) + "–" + (start + visibleEntries.length) : "") + ".";
    dom.downloadCatalogJson.disabled = entries.length === 0;
    dom.downloadCatalogBibtex.disabled = entries.length === 0;
    dom.catalogPagination.hidden = totalPages <= 1;
    dom.catalogPrevious.disabled = state.catalogPage <= 1;
    dom.catalogNext.disabled = state.catalogPage >= totalPages;
    dom.catalogPage.textContent = "Page " + state.catalogPage + " of " + totalPages;
    if (!entries.length) {
      var empty = node("div", null, "empty-state");
      empty.appendChild(node("p", "No entries match this selection. Try a broader term or show all work."));
      var clear = node("button", "Clear filters", "button button-secondary");
      clear.type = "button";
      clear.addEventListener("click", function () {
        clearCatalogFilters();
        renderCatalog();
        dom.catalogSearch.focus();
      });
      empty.appendChild(clear);
      dom.catalogResults.appendChild(empty);
      return;
    }
    visibleEntries.forEach(function (item) {
      var card = node("article", null, "catalog-card");
      card.dataset.itemId = String(item.id);
      card.tabIndex = -1;
      var top = node("div", null, "catalog-card-top");
      top.appendChild(node("span", ({project:"Project",research:"Research",teaching:"Teaching",reference:"Reference"})[item.type] || "Public work", "item-type"));
      if (text(item.maturity)) top.appendChild(node("span", item.maturity, "label label-plain"));
      card.appendChild(top);
      card.appendChild(node("h3", text(item.title, item.id)));
      if (stringList(item.authors).length) card.appendChild(node("p",stringList(item.authors).join("; "),"item-authors"));
      var publication = [text(item.publisher),text(item.publication_date) ? "Published " + publicationLabel(item.publication_date) : ""].filter(Boolean);
      if (publication.length) card.appendChild(node("p",publication.join(" · "),"item-publication"));
      card.appendChild(node("p", text(item.description), "item-description"));
      if (useFor(item)) card.appendChild(node("p","Useful for: " + useFor(item),"item-use-for"));
      var reviewStatus = reviewStatusFor(item);
      if (item._fromLibrary || text(item.review_status)) {
        var reviewLine = node("div",null,"item-review");
        reviewLine.appendChild(node("span",REVIEW_LABELS[reviewStatus],"label " + ({source_inspected:"label-green",metadata_only:"label-plain",needs_review:"label-warm"})[reviewStatus]));
        reviewLine.appendChild(node("span",({source_inspected:"Read the inspection scope below before relying on this source.",metadata_only:item.medium === "video" ? "Video metadata only. The recording and transcript have not been reviewed for this entry." : "Bibliographic metadata only. The full text has not been reviewed for this entry.",needs_review:"Further review is needed before relying on this entry."})[reviewStatus]));
        card.appendChild(reviewLine);
      }
      if (stringList(item.topics).length) {
        var topics = node("ul", null, "item-topics");
        topics.setAttribute("aria-label", "Topics");
        stringList(item.topics).forEach(function (topic) { topics.appendChild(node("li", topic)); });
        card.appendChild(topics);
      }
      var links = node("div", null, "item-links");
      list(item.links).forEach(function (entry) {
        if (entry && safeUrl(entry.url)) links.appendChild(link(text(entry.label,"Open source") + " ↗", entry.url));
      });
      if (!links.childNodes.length && primaryUrlFor(item)) links.appendChild(link("Open source ↗",primaryUrlFor(item)));
      card.appendChild(links);
      var verification = record(item.verification);
      var rights = record(item.rights);
      var citation = citationFor(item);
      var contributions = list(state.catalog && state.catalog.contributions).filter(function (entry) { return entry && entry.project_id === item.id; });
      if (contributions.length && item.type === "project") {
        var contribute = node("div", null, "item-contributions");
        contribute.appendChild(node("h4", "Ways to contribute"));
        contributions.forEach(function (entry) {
          var route = node("p");
          route.appendChild(link(text(entry.title, "Contribution route") + " ↗", entry.url));
          if (text(entry.description)) route.appendChild(node("span", ". " + entry.description));
          contribute.appendChild(route);
        });
        if (safeUrl(rights.url)) {
          var terms = node("p", null, "field-help");
          terms.appendChild(link("Project reuse terms ↗", rights.url));
          contribute.appendChild(terms);
        }
        card.appendChild(contribute);
      }
      if (item._fromLibrary || Object.keys(verification).length || Object.keys(rights).length || citation.available || text(item.limitation) || text(item.relationship_note) || list(item.related_item_ids).length || contributions.length) {
        var detail = node("details", null, "item-details");
        detail.appendChild(node("summary", "Source, scope and reuse"));
        if (verification.checked_at) detail.appendChild(node("p", (reviewStatus === "source_inspected" ? "Source inspected: " : "Record checked: ") + recordedDate(verification.checked_at) + "."));
        if (item.added_at) detail.appendChild(node("p","Added to this library: " + recordedDate(item.added_at) + "."));
        if (item.origin === "crossref") detail.appendChild(node("p","Discovered through Crossref bibliographic metadata. Inclusion is not an endorsement or a full-text review."));
        if (item.origin === "curated_reference") detail.appendChild(node("p","Curated reference. The recorded source scope describes what was inspected."));
        if (text(verification.scope)) detail.appendChild(node("p", verification.scope));
        if (text(item.limitation)) detail.appendChild(node("p", "Limitation: " + item.limitation));
        if (text(verification.revision)) {
          var revision = node("p", "Recorded revision: ");
          revision.appendChild(link(shortRevision(verification.revision), verification.source_url));
          detail.appendChild(revision);
        } else if (safeUrl(verification.source_url)) {
          detail.appendChild(link("Inspect the source record ↗", verification.source_url));
        }
        if (text(rights.summary)) {
          detail.appendChild(node("p", rights.summary));
          if (safeUrl(rights.url)) detail.appendChild(link("Read the reuse terms ↗", rights.url));
        }
        if (citation.available && text(citation.text)) {
          var citationBox = node("div", null, "citation-box");
          if (citation.assembled) citationBox.appendChild(node("p","Reference assembled from the recorded metadata. Check the source and your required citation style.","field-help"));
          citationBox.appendChild(node("pre", citation.text));
          var copy = node("button", "Copy citation", "button button-secondary");
          copy.type = "button";
          copy.addEventListener("click", function () { copyText(citation.text, copy); });
          citationBox.appendChild(copy);
          var download = node("button", "Download citation (.txt)", "button button-secondary");
          download.type = "button";
          download.addEventListener("click", function () {
            downloadContent(citation.text + "\n", String(item.id).replace(/[^a-zA-Z0-9_-]/g, "-") + "-citation.txt", "text/plain");
            announce("Citation text downloaded.");
          });
          citationBox.appendChild(download);
          if (safeUrl(citation.url)) citationBox.appendChild(node("p"));
          if (safeUrl(citation.url)) citationBox.lastChild.appendChild(link("Citation source ↗", citation.url));
          detail.appendChild(citationBox);
        }
        if (safeUrl(citation.download_url)) detail.appendChild(link("Download CITATION.cff ↗", citation.download_url));
        if (text(item.relationship_note)) detail.appendChild(node("p", item.relationship_note));
        var related = node("div", null, "item-links");
        list(item.related_item_ids).forEach(function (id) {
          var target = allEntries.find(function (entry) { return entry.id === id; });
          if (!target) return;
          var button = node("button", "Related: " + target.title, "button button-quiet");
          button.type = "button";
          button.dataset.relatedItemId = id;
          button.addEventListener("click", function () {
            clearCatalogFilters();
            var targetIndex = filteredCatalogEntries().findIndex(function (entry) { return entry.id === id; });
            state.catalogPage = Math.floor(Math.max(0,targetIndex) / CATALOG_PAGE_SIZE) + 1;
            renderCatalog();
            var targetCard = Array.from(dom.catalogResults.children).find(function (entry) { return entry.dataset.itemId === String(id); });
            if (targetCard) {
              targetCard.focus({preventScroll:true});
              targetCard.scrollIntoView({behavior:"auto",block:"start"});
              announce("Showing related entry: " + target.title + ". Filters cleared.");
            }
          });
          related.appendChild(button);
        });
        if (related.childNodes.length) detail.appendChild(related);
        card.appendChild(detail);
      }
      dom.catalogResults.appendChild(card);
    });
  }
  var GUIDE_ROUTES = {
    trace:{
      id:"project-regnav",title:"Start with a claim and its cited passage.",
      copy:"Open the recorded replay above to inspect a fictional evidence ledger. Compare what the source says with the claim, then use the RegNav quickstart to examine the underlying workflow.",
      kinds:["start","quickstart","demo"],match:/quickstart/i,local:true
    },
    watch:{
      id:"project-source-watch",title:"Follow the source revision.",
      copy:"RegNav Source Watch compares committed source records and identifies linked claims that need another review. Its documentation explains the comparison and its limits; an alert does not decide whether a claim remains correct.",
      kinds:["demo","source","repository"],match:/readme|install|demo|source|repository/i
    },
    teach:{
      id:"teaching-source-checking",title:"Practice checking evidence together.",
      copy:"Use the fictional source-checking exercise to trace claims, inspect disagreements and discuss what remains unsupported. The published teaching materials include the learner and facilitator routes.",
      kinds:["guide","source","materials"],match:/exercise|material|guide|readme|source/i
    },
    acceptance:{
      id:"project-piepowder",title:"Inspect an explicit acceptance decision.",
      copy:"The Piepowder example separates stated criteria, fictional evidence and questions requiring human judgement. Follow the recorded demonstration before interpreting the simulator's output.",
      kinds:["demo"],match:/demo|example/i
    }
  };
  function renderGuide() {
    if (!state.catalog) return;
    var route = GUIDE_ROUTES[dom.guideIntent.value] || GUIDE_ROUTES.trace;
    var item = list(state.catalog.items).find(function (candidate) { return candidate.id === route.id; });
    dom.guideAnswer.replaceChildren();
    dom.guideAnswer.appendChild(node("h3", route.title));
    dom.guideAnswer.appendChild(node("p", route.copy));
    if (route.local) dom.guideAnswer.appendChild(link("Inspect the recorded replay ↑", "#replay"));
    if (item) {
      var links = list(item.links).filter(function (entry) { return !!safeUrl(entry.url); });
      var source = route.kinds.map(function (kind) { return links.find(function (entry) { return entry.kind === kind; }); }).find(Boolean) ||
        links.find(function (entry) { return route.match.test(entry.label || "") || route.match.test(entry.url || ""); }) || links[0];
      if (source) {
        var line = node("div");
        line.appendChild(link(text(source.label, "Open the published guide") + " ↗", source.url));
        dom.guideAnswer.appendChild(line);
      }
      dom.guideAnswer.appendChild(node("p", "Curated route · " + item.title + ". Source scope and reuse terms are recorded in the catalog.", "guide-source"));
    } else {
      dom.guideAnswer.appendChild(node("p", "This route is not present in the loaded catalog. Explore the available entries below.", "guide-source"));
      dom.guideAnswer.appendChild(link("Browse the public catalog ↓", "#library"));
    }
  }
  function filterFromHash(shouldScroll) {
    var map = {"#projects":"project","#research":"research","#teaching":"teaching","#references":"reference"};
    var type = map[window.location.hash];
    if (!type) return;
    dom.catalogType.value = type;
    dom.catalogSearch.value = "";
    dom.catalogTopic.value = "all";
    dom.catalogReview.value = "all";
    state.catalogPage = 1;
    renderCatalog();
    if (shouldScroll) $("library").scrollIntoView({behavior:"auto",block:"start"});
  }

  function commandText(command) {
    if (!Array.isArray(command)) return text(command);
    return command.map(function (part) {
      part = String(part);
      return /^[A-Za-z0-9_./:=@+-]+$/.test(part) ? part : "'" + part.replace(/'/g, "'\\''") + "'";
    }).join(" ");
  }
  function renderReceipt(receipt) {
    var detail = node("details", null, "receipt");
    detail.dataset.receiptId = String(receipt.id);
    var matches = receipt.exit_code === receipt.expected_exit_code;
    var summary = node("summary", text(receipt.id,"Execution receipt") + " · recorded exit " + receipt.exit_code +
      " · expected " + receipt.expected_exit_code + (matches ? " · expected outcome" : " · outcome differs"));
    detail.appendChild(summary);
    var body = node("div", null, "receipt-body");
    if (text(receipt.cwd)) body.appendChild(node("p", "Working directory: " + receipt.cwd, "receipt-meta"));
    body.appendChild(node("h4", "Recorded command"));
    var command = commandText(receipt.command);
    var commandBlock = node("div", null, "command-block");
    commandBlock.appendChild(node("code", command));
    body.appendChild(commandBlock);
    var copy = node("button", "Copy recorded command", "button button-quiet");
    copy.type = "button";
    copy.style.marginTop = "12px";
    copy.addEventListener("click", function () { copyText(command, copy); });
    body.appendChild(copy);
    if (list(receipt.assertions).length) {
      body.appendChild(node("h4", "Recorded assertions"));
      var assertions = node("ul", null, "assertion-list");
      list(receipt.assertions).forEach(function (assertion) {
        var entry = node("li");
        entry.appendChild(node("span", assertion.passed === true ? "Passed" : "Not passed", "assertion-state" + (assertion.passed === true ? "" : " failed")));
        var label = node("span", text(assertion.name,"Assertion"));
        if (assertion.expected !== undefined || assertion.observed !== undefined) {
          var comparison = node("div", "Expected: " + jsonText(assertion.expected) + " · Observed: " + jsonText(assertion.observed), "field-help");
          label.appendChild(comparison);
        }
        entry.appendChild(label);
        assertions.appendChild(entry);
      });
      body.appendChild(assertions);
    }
    [["stdout","Standard output"],["stderr","Standard error"]].forEach(function (pair) {
      body.appendChild(node("h4", pair[1]));
      var block = node("div", null, "output-block");
      block.appendChild(node("pre", text(receipt[pair[0]], "(No output captured.)")));
      body.appendChild(block);
    });
    body.appendChild(node("p", "This is captured execution output. $POLICYKIT and $SOURCE_WATCH stand for the pinned repository checkouts; $FIXTURES is the generated fictional fixture directory. Resolve these path placeholders using the reproduction guide. Copying a command does not execute it in this browser.", "receipt-footnote"));
    detail.appendChild(body);
    return detail;
  }
  function renderVerification() {
    if (!state.replay) return;
    dom.verification.replaceChildren();
    var provenance = state.replay.provenance || {};
    var workflow = provenance.workflow || {};
    var panel = node("div", null, "provenance-panel");
    panel.appendChild(node("h3", "Source and execution provenance"));
    panel.appendChild(link("Reproduce the recorded executions ↗", "https://github.com/Albertito-AI/Albertito-AI/blob/main/docs/RESEARCH_LAB.md#reproduce-the-recorded-executions", "provenance-line"));
    if (state.replay.generated_at) panel.appendChild(node("p", "Record generated: " + dateLabel(state.replay.generated_at) + ".", "provenance-line"));
    if (safeUrl(workflow.run_url)) {
      var run = node("p", null, "provenance-line");
      run.appendChild(link("Inspect the GitHub Actions execution ↗", workflow.run_url));
      if (workflow.run_attempt) run.appendChild(document.createTextNode(" · attempt " + workflow.run_attempt));
      panel.appendChild(run);
    }
    if (text(workflow.commit)) {
      var commit = node("p", null, "provenance-line");
      commit.appendChild(document.createTextNode("Lab execution revision: "));
      var commitUrl = text(workflow.repository) ? "https://github.com/" + workflow.repository + "/commit/" + workflow.commit : null;
      commit.appendChild(link(shortRevision(workflow.commit), commitUrl));
      panel.appendChild(commit);
    }
    var environment = provenance.environment || {};
    var environmentText = ["python","node","git"].filter(function (key) { return environment[key] !== undefined; }).map(function (key) {
      return key.charAt(0).toUpperCase() + key.slice(1) + " " + String(environment[key]);
    }).join(" · ");
    if (environmentText) panel.appendChild(node("p", "Recorded environment: " + environmentText, "provenance-line"));
    var revisions = node("ul", null, "source-revisions");
    list(provenance.sources).forEach(function (source) {
      var item = node("li");
      item.appendChild(node("strong", text(source.repository,"Source repository")));
      var line = node("div");
      line.appendChild(link("Inspect revision " + shortRevision(source.revision) + " ↗", source.url));
      item.appendChild(line);
      if (safeUrl(source.rights_url)) item.appendChild(link("Source reuse terms ↗", source.rights_url));
      if (list(source.files).length) {
        var files = node("details", null, "item-details");
        files.appendChild(node("summary", "Recorded source files and checksums"));
        list(source.files).forEach(function (file) {
          var paragraph = node("p");
          paragraph.appendChild(link(text(file.path,"Source file"), file.url));
          if (text(file.sha256)) paragraph.appendChild(node("div", "SHA-256 " + file.sha256, "field-help"));
          files.appendChild(paragraph);
        });
        item.appendChild(files);
      }
      revisions.appendChild(item);
    });
    if (revisions.childNodes.length) panel.appendChild(revisions);
    dom.verification.appendChild(panel);
    var current = scenario();
    var receiptIds = list(current && current.receipt_ids);
    var receipts = list(state.replay.receipts).filter(function (receipt) { return receiptIds.includes(receipt.id); });
    dom.verification.appendChild(node("h3", "Execution receipts for " + text(current && current.title,"this scenario"), "receipts-heading"));
    if (!receipts.length) {
      dom.verification.appendChild(node("p", "No execution receipt is linked to this scenario in the loaded record.", "muted"));
    } else {
      receipts.forEach(function (receipt) { dom.verification.appendChild(renderReceipt(receipt)); });
    }
  }

  dom.scenario.addEventListener("change", function () { setScenario(Number(dom.scenario.value)); });
  dom.previous.addEventListener("click", function () { setScenario(state.scenarioIndex - 1); });
  dom.next.addEventListener("click", function () { setScenario(state.scenarioIndex + 1); });
  dom.tabs.addEventListener("click", function (event) {
    var tab = event.target.closest("[role=tab]");
    if (tab) chooseTab(tab.dataset.tab, false);
  });
  dom.tabs.addEventListener("keydown", function (event) {
    var tabs = Array.from(dom.tabs.querySelectorAll("[role=tab]"));
    var index = tabs.indexOf(document.activeElement);
    if (index < 0) return;
    var next;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next !== undefined) {
      event.preventDefault();
      chooseTab(tabs[next].dataset.tab, true);
    }
  });
  dom.note.addEventListener("input", saveCurrentNote);
  dom.reviewStatus.addEventListener("change", saveCurrentNote);
  dom.clearReview.addEventListener("click", function () {
    delete state.notes[noteKey()];
    persistNotes();
    loadNoteEditor();
    dom.note.focus();
    announce("The selected local note was cleared.");
  });
  dom.downloadReview.addEventListener("click", function () {
    var notes = currentNotes();
    if (!notes.length) return;
    downloadJson({
      schema_version:1,record_type:"local_reviewer_annotations",exported_at:new Date().toISOString(),
      notice:"These are visitor-authored notes about a recorded fictional example. They do not modify the source ledger or establish legal correctness.",
      recorded_dataset:{id:state.replay.id,generated_at:state.replay.generated_at},
      notes:notes
    }, "research-review-" + today() + ".json");
    announce("Downloaded " + notes.length + " local review " + (notes.length === 1 ? "note" : "notes") + " as JSON.");
  });
  dom.downloadReceipts.addEventListener("click", function () {
    if (!state.replay) return;
    downloadJson(state.replay, "regnav-recorded-receipts-" + today() + ".json");
    announce("Downloaded the recorded example and execution receipts.");
  });
  dom.catalogSearch.addEventListener("input", filterCatalog);
  dom.copyScenario.addEventListener("click", function () {
    if (dom.scenarioShare.value) copyText(dom.scenarioShare.value, dom.copyScenario);
  });
  dom.catalogType.addEventListener("change", filterCatalog);
  dom.catalogTopic.addEventListener("change", filterCatalog);
  dom.catalogReview.addEventListener("change", filterCatalog);
  dom.catalogSort.addEventListener("change", filterCatalog);
  dom.catalogClear.addEventListener("click", function () {
    clearCatalogFilters();
    renderCatalog();
    dom.catalogSearch.focus();
    announce("Catalog filters cleared.");
  });
  dom.catalogPrevious.addEventListener("click", function () { changeCatalogPage(-1); });
  dom.catalogNext.addEventListener("click", function () { changeCatalogPage(1); });
  dom.downloadCatalogJson.addEventListener("click", function () { exportCatalog("json"); });
  dom.downloadCatalogBibtex.addEventListener("click", function () { exportCatalog("bibtex"); });
  dom.retryLibrary.addEventListener("click", loadLibrary);
  dom.guideIntent.addEventListener("change", renderGuide);
  window.addEventListener("hashchange", function () { filterFromHash(true); });
  readNotes();
  dom.app.setAttribute("aria-busy","true");
  Promise.allSettled([loadReplay(),loadCatalog(),loadLibrary()]).then(function () {
    dom.app.setAttribute("aria-busy","false");
  });
  window.setInterval(renderLibraryStatus,60000);
})();

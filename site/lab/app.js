"use strict";

(function () {
  var $ = function (id) { return document.getElementById(id); };
  var dom = {
    app: $("lab-app"), replayStatus: $("replay-status"), replayContent: $("replay-content"),
    scenario: $("scenario-select"), previous: $("previous-scenario"), next: $("next-scenario"),
    prompt: $("scenario-prompt"), explanation: $("scenario-explanation"),
    claims: $("claims-list"), claimCount: $("claims-count"), tabs: $("evidence-tabs"),
    panel: $("evidence-panel"), editor: $("review-editor"), reviewStatus: $("review-status-select"),
    note: $("review-note"), noteContext: $("review-context"), noteStatus: $("note-status"),
    downloadReview: $("download-review"), clearReview: $("clear-review"),
    disclaimer: $("replay-disclaimer"), catalogStatus: $("catalog-status"),
    catalogSearch: $("catalog-search"), catalogType: $("catalog-type"),
    catalogResults: $("catalog-results"), catalogCount: $("catalog-count"),
    catalogDate: $("catalog-date"), catalogIntro: $("catalog-introduction"), catalogScope: $("catalog-scope"),
    guideIntent: $("guide-intent"), guideAnswer: $("guide-answer"),
    verification: $("verification-record"), downloadReceipts: $("download-receipts"),
    announcement: $("app-announcement")
  };
  var NOTE_STORAGE_KEY = "sparks-lab-review-notes-v1";
  var NOTE_STATUSES = ["no-decision", "follow-up-needed", "comment-recorded"];
  var state = {
    replay: null, catalog: null, scenarioIndex: 0, claimId: null, sourceIndex: 0,
    tab: "before", notes: Object.create(null), storageAvailable: true
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
      state.replay = data;
      state.scenarioIndex = Math.min(state.scenarioIndex, data.scenarios.length - 1);
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
      dom.catalogDate.textContent = data.updated_at ? "Catalog checked " + dateLabel(data.updated_at) : "";
      if (text(data.introduction)) dom.catalogIntro.textContent = data.introduction;
      dom.catalogScope.textContent = text(data.scope_note);
      var links = data.links || {};
      setLink("feedback-link", links.feedback);
      setLink("evaluation-link", links.evaluation);
      filterFromHash(false);
      renderCatalog();
      renderGuide();
    } catch (error) {
      console.warn("Public catalog unavailable:", error);
      loadError(dom.catalogStatus, "public catalog", "catalog.json", loadCatalog);
    }
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
    if (shouldAnnounce !== false) announce("Showing recorded scenario: " + text(current.title, current.id) + ".");
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

  function renderCatalog() {
    if (!state.catalog) return;
    var query = dom.catalogSearch.value.trim().toLocaleLowerCase();
    var type = dom.catalogType.value;
    var entries = list(state.catalog.items).filter(function (item) {
      var haystack = [item.title,item.description,item.maturity].concat(list(item.topics)).join(" ").toLocaleLowerCase();
      return (type === "all" || item.type === type) && (!query || haystack.includes(query));
    });
    dom.catalogResults.replaceChildren();
    dom.catalogCount.textContent = entries.length + " " + (entries.length === 1 ? "entry" : "entries") +
      (query ? ' matching “' + dom.catalogSearch.value.trim() + '”' : "") + ".";
    if (!entries.length) {
      var empty = node("div", null, "empty-state");
      empty.appendChild(node("p", "No entries match this selection. Try a broader term or show all work."));
      var clear = node("button", "Clear filters", "button button-secondary");
      clear.type = "button";
      clear.addEventListener("click", function () {
        dom.catalogSearch.value = "";
        dom.catalogType.value = "all";
        renderCatalog();
        dom.catalogSearch.focus();
      });
      empty.appendChild(clear);
      dom.catalogResults.appendChild(empty);
      return;
    }
    entries.forEach(function (item) {
      var card = node("article", null, "catalog-card");
      card.dataset.itemId = String(item.id);
      card.tabIndex = -1;
      var top = node("div", null, "catalog-card-top");
      top.appendChild(node("span", ({project:"Project",research:"Research",teaching:"Teaching"})[item.type] || "Public work", "item-type"));
      if (text(item.maturity)) top.appendChild(node("span", item.maturity, "label label-plain"));
      card.appendChild(top);
      card.appendChild(node("h3", text(item.title, item.id)));
      card.appendChild(node("p", text(item.description), "item-description"));
      if (list(item.topics).length) {
        var topics = node("ul", null, "item-topics");
        topics.setAttribute("aria-label", "Topics");
        list(item.topics).forEach(function (topic) { topics.appendChild(node("li", topic)); });
        card.appendChild(topics);
      }
      var links = node("div", null, "item-links");
      list(item.links).forEach(function (entry) {
        if (safeUrl(entry.url)) links.appendChild(link(text(entry.label,"Open source") + " ↗", entry.url));
      });
      card.appendChild(links);
      var verification = item.verification || {};
      var rights = item.rights || {};
      var citation = item.citation || {};
      var contributions = list(state.catalog.contributions).filter(function (entry) { return entry.project_id === item.id; });
      if (Object.keys(verification).length || Object.keys(rights).length || citation.available || text(item.limitation) || text(item.relationship_note) || list(item.related_item_ids).length || contributions.length) {
        var detail = node("details", null, "item-details");
        detail.appendChild(node("summary", "Source, scope and reuse"));
        if (verification.checked_at) detail.appendChild(node("p", "Source inspected: " + dateLabel(verification.checked_at) + "."));
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
          var target = list(state.catalog.items).find(function (entry) { return entry.id === id; });
          if (!target) return;
          var button = node("button", "Related: " + target.title, "button button-quiet");
          button.type = "button";
          button.dataset.relatedItemId = id;
          button.addEventListener("click", function () {
            dom.catalogSearch.value = "";
            dom.catalogType.value = "all";
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
        if (contributions.length) detail.appendChild(node("h4", "Contribution routes"));
        contributions.forEach(function (entry) {
          var route = node("p");
          route.appendChild(link(text(entry.title, "Contribution route") + " ↗", entry.url));
          if (text(entry.description)) route.appendChild(node("span", ". " + entry.description));
          detail.appendChild(route);
        });
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
    var map = {"#projects":"project","#research":"research","#teaching":"teaching"};
    var type = map[window.location.hash];
    if (!type) return;
    dom.catalogType.value = type;
    dom.catalogSearch.value = "";
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
    }, "sparks-review-" + today() + ".json");
    announce("Downloaded " + notes.length + " local review " + (notes.length === 1 ? "note" : "notes") + " as JSON.");
  });
  dom.downloadReceipts.addEventListener("click", function () {
    if (!state.replay) return;
    downloadJson(state.replay, "regnav-recorded-receipts-" + today() + ".json");
    announce("Downloaded the recorded example and execution receipts.");
  });
  dom.catalogSearch.addEventListener("input", renderCatalog);
  dom.catalogType.addEventListener("change", renderCatalog);
  dom.guideIntent.addEventListener("change", renderGuide);
  window.addEventListener("hashchange", function () { filterFromHash(true); });
  readNotes();
  dom.app.setAttribute("aria-busy","true");
  Promise.allSettled([loadReplay(),loadCatalog()]).then(function () {
    dom.app.setAttribute("aria-busy","false");
  });
})();

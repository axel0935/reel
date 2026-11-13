/* Reel Studio Playground Client */

(function () {
  "use strict";

  // Elements
  const exampleSelect = document.getElementById("example-select");
  const codeInput = document.getElementById("code-input");
  const codeHighlight = document.getElementById("code-highlight");
  const codeHighlightInner = document.getElementById("code-highlight-inner");
  const lineNumbers = document.getElementById("line-numbers");
  const lineCounter = document.getElementById("line-counter");
  const currentFilename = document.getElementById("current-filename");
  const errorLineHighlight = document.getElementById("error-line-highlight");

  const runBtn = document.getElementById("run-btn");
  const shareBtn = document.getElementById("share-btn");
  const clearBtn = document.getElementById("clear-btn");
  const outputBox = document.getElementById("output-box");
  const errorBanner = document.getElementById("error-banner");
  const errorMessage = document.getElementById("error-message");
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");
  const toast = document.getElementById("toast");

  // Constants
  const LINE_HEIGHT_PX = 22;
  const PADDING_TOP_PX = 16;

  // In-memory cache for loaded examples
  const examplesMap = new Map();

  // Current state
  let currentErrorLine = null;
  let toastTimer = null;

  // HTML escaping helper
  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Syntax Highlighting Tokenizer for Reel
  // Covers:
  // - Comments: -- ...
  // - Strings: "..."
  // - Keywords: v0.1 + v0.2 + v0.3 keywords (IMPORT, LIB, WITH, CALL, GIVE BACK, LIST, ADD, AT, LENGTH OF, FOR EACH, IN, WHILE, etc.)
  // - Numbers: integers and decimals
  const TOKEN_REGEX = /(--[^\n]*)|("[^"\n]*")|(\b(?:GIVE BACK|LENGTH OF|FOR EACH|DIVIDED BY|BIGGER THAN|SMALLER THAN|SCENE|CUT|SET|TO|SAY|IF|OTHERWISE|END|REPEAT|TIMES|PLUS|MINUS|DIVIDED|BY|JOIN|EQUALS|BIGGER|SMALLER|THAN|AND|OR|NOT|YES|NO|WITH|CALL|GIVE|BACK|LIST|ADD|AT|LENGTH|OF|FOR|EACH|IN|WHILE|NOTHING|IMPORT|LIB)\b)|(\b\d+(?:\.\d+)?\b)/g;

  function highlightReel(source) {
    let result = "";
    let lastIndex = 0;
    let match;

    TOKEN_REGEX.lastIndex = 0;
    while ((match = TOKEN_REGEX.exec(source)) !== null) {
      if (match.index > lastIndex) {
        result += escapeHtml(source.substring(lastIndex, match.index));
      }

      const [full, comment, string, keyword, number] = match;

      if (comment !== undefined) {
        result += `<span class="hl-comment">${escapeHtml(comment)}</span>`;
      } else if (string !== undefined) {
        result += `<span class="hl-string">${escapeHtml(string)}</span>`;
      } else if (keyword !== undefined) {
        result += `<span class="hl-keyword">${escapeHtml(keyword)}</span>`;
      } else if (number !== undefined) {
        result += `<span class="hl-number">${escapeHtml(number)}</span>`;
      }

      lastIndex = TOKEN_REGEX.lastIndex;
    }

    if (lastIndex < source.length) {
      result += escapeHtml(source.substring(lastIndex));
    }

    // Preserve trailing newline height
    if (source.endsWith("\n")) {
      result += " ";
    }

    return result;
  }

  // Update line numbers gutter and code highlighting
  function updateEditor() {
    const text = codeInput.value;
    const lines = text.split("\n");
    const count = lines.length;

    // 1. Update syntax highlighting
    codeHighlightInner.innerHTML = highlightReel(text);

    // 2. Update line numbers gutter
    let numbersHtml = "";
    for (let i = 1; i <= count; i++) {
      const isErr = currentErrorLine === i ? " error-line" : "";
      numbersHtml += `<div class="line-num${isErr}" data-line="${i}">${i}</div>`;
    }
    lineNumbers.innerHTML = numbersHtml;

    // 3. Update line counter badge
    lineCounter.textContent = `${count} ${count === 1 ? "line" : "lines"}`;

    // 4. Synchronize scrolling and error position
    syncScroll();
  }

  // Synchronize scroll positions across layers
  function syncScroll() {
    const sTop = codeInput.scrollTop;
    const sLeft = codeInput.scrollLeft;

    lineNumbers.scrollTop = sTop;
    codeHighlight.scrollTop = sTop;
    codeHighlight.scrollLeft = sLeft;

    // Update error line highlight position if active
    if (currentErrorLine !== null && currentErrorLine > 0) {
      const lineTop = (currentErrorLine - 1) * LINE_HEIGHT_PX + PADDING_TOP_PX - sTop;
      errorLineHighlight.style.top = `${lineTop}px`;
    }
  }

  // Highlight a faulty line on error
  function setErrorLine(line) {
    currentErrorLine = line;

    // Clear previous line-num error classes
    const existing = lineNumbers.querySelectorAll(".error-line");
    existing.forEach((el) => el.classList.remove("error-line"));

    if (line !== null && line > 0) {
      // Highlight in gutter
      const targetGutter = lineNumbers.querySelector(`[data-line="${line}"]`);
      if (targetGutter) {
        targetGutter.classList.add("error-line");
      }

      // Show faulty line band
      errorLineHighlight.classList.remove("hidden");
      const lineTop = (line - 1) * LINE_HEIGHT_PX + PADDING_TOP_PX - codeInput.scrollTop;
      errorLineHighlight.style.top = `${lineTop}px`;

      // Scroll editor so faulty line is centered in view
      const targetScroll = (line - 1) * LINE_HEIGHT_PX - 60;
      if (codeInput.scrollTop > targetScroll || codeInput.scrollTop + codeInput.clientHeight < (line * LINE_HEIGHT_PX)) {
        codeInput.scrollTop = Math.max(0, targetScroll);
        syncScroll();
      }
    } else {
      errorLineHighlight.classList.add("hidden");
    }
  }

  // Helper to set execution status indicator
  function setStatus(state, message) {
    statusIndicator.className = "status-dot " + state;
    statusText.textContent = message;
  }

  // Clear errors and line highlights
  function clearError() {
    errorBanner.classList.add("hidden");
    errorMessage.textContent = "";
    setErrorLine(null);
  }

  // Display a friendly error and extract line number
  function showError(errText) {
    errorMessage.textContent = errText;
    errorBanner.classList.remove("hidden");
    setStatus("error", "Interrupted");

    // Look for line number pattern (e.g. "Line 4: ...")
    const match = errText.match(/\bLine\s+(\d+)\b/i);
    if (match) {
      const lineNum = parseInt(match[1], 10);
      if (!isNaN(lineNum)) {
        setErrorLine(lineNum);
      }
    } else {
      setErrorLine(null);
    }
  }

  // Show a floating toast message
  function showToast(message) {
    if (toastTimer) clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.remove("hidden");
    toastTimer = setTimeout(() => {
      toast.classList.add("hidden");
    }, 2500);
  }

  // Load examples from the server
  async function loadExamples() {
    try {
      const response = await fetch("/api/examples");
      if (!response.ok) {
        throw new Error("HTTP error " + response.status);
      }
      const data = await response.json();
      const examples = data.examples || [];

      exampleSelect.innerHTML = "";
      examplesMap.clear();

      if (examples.length === 0) {
        const option = document.createElement("option");
        option.textContent = "No examples found";
        option.value = "";
        exampleSelect.appendChild(option);
        return;
      }

      // Check if a shared script was loaded from URL hash
      const hasSharedCode = loadFromHash();

      let defaultFilename = "hello.reel";
      let foundDefault = false;

      // Add default blank option
      const promptOption = document.createElement("option");
      promptOption.value = "";
      promptOption.textContent = hasSharedCode ? "Shared script (active)" : "-- Select an example --";
      if (hasSharedCode) promptOption.selected = true;
      exampleSelect.appendChild(promptOption);

      examples.forEach((item) => {
        examplesMap.set(item.filename, item.code);
        const option = document.createElement("option");
        option.value = item.filename;
        option.textContent = item.filename;
        if (!hasSharedCode && item.filename === defaultFilename) {
          foundDefault = true;
          option.selected = true;
        }
        exampleSelect.appendChild(option);
      });

      if (!hasSharedCode) {
        if (!foundDefault && examples.length > 0) {
          defaultFilename = examples[0].filename;
          exampleSelect.value = defaultFilename;
        }
        applySelectedExample(defaultFilename);
      }
    } catch (err) {
      console.warn("Could not load examples:", err);
      exampleSelect.innerHTML = '<option value="">Examples unavailable</option>';
      if (!loadFromHash()) {
        updateEditor();
      }
      setStatus("ready", "Ready (offline)");
    }
  }

  // Apply selected example code to textarea
  function applySelectedExample(filename) {
    if (!filename || !examplesMap.has(filename)) return;
    const code = examplesMap.get(filename);
    codeInput.value = code;
    currentFilename.textContent = filename;
    clearError();
    updateEditor();
    outputBox.textContent = 'Click "Action!" or press Ctrl+Enter to run this scene.';
    setStatus("ready", "Ready");
  }

  // Check URL hash for shared code
  function loadFromHash() {
    const hash = window.location.hash;
    if (!hash || hash.length <= 1) return false;

    let raw = hash.slice(1);
    if (raw.startsWith("code=")) {
      raw = raw.slice(5);
    }

    try {
      let decoded;
      if (raw.startsWith("b64:")) {
        decoded = decodeURIComponent(escape(atob(raw.slice(4))));
      } else {
        decoded = decodeURIComponent(raw);
      }

      if (decoded && decoded.trim().length > 0) {
        codeInput.value = decoded;
        currentFilename.textContent = "shared.reel";
        clearError();
        updateEditor();
        outputBox.textContent = 'Loaded shared script. Click "Action!" or press Ctrl+Enter to run.';
        setStatus("ready", "Shared script loaded");
        return true;
      }
    } catch (err) {
      console.warn("Could not decode script from URL hash:", err);
    }
    return false;
  }

  // Share current script: encode into URL hash and copy link
  async function shareCode() {
    const code = codeInput.value;
    const encoded = encodeURIComponent(code);
    const shareUrl = `${window.location.origin}${window.location.pathname}#${encoded}`;

    // Update browser URL bar without reload
    window.history.replaceState(null, "", shareUrl);

    // Copy to clipboard
    let copied = false;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(shareUrl);
        copied = true;
      } catch (e) {
        copied = false;
      }
    }

    if (!copied) {
      // Fallback for environments where navigator.clipboard is blocked
      const tempTextArea = document.createElement("textarea");
      tempTextArea.value = shareUrl;
      tempTextArea.style.position = "fixed";
      tempTextArea.style.left = "-9999px";
      document.body.appendChild(tempTextArea);
      tempTextArea.select();
      try {
        document.execCommand("copy");
        copied = true;
      } catch (err) {
        copied = false;
      }
      document.body.removeChild(tempTextArea);
    }

    // Visual feedback
    shareBtn.classList.add("copied");
    shareBtn.innerHTML = '<span class="btn-icon">✓</span> <span class="btn-text">Copied!</span>';
    showToast("Shareable link copied to clipboard!");

    setTimeout(() => {
      shareBtn.classList.remove("copied");
      shareBtn.innerHTML = '<span class="btn-icon">🔗</span> <span class="btn-text">Share</span>';
    }, 2000);
  }

  // Run the Reel code via POST /api/run
  async function runCode() {
    const source = codeInput.value;
    clearError();
    setStatus("running", "Rolling...");
    runBtn.disabled = true;

    try {
      const startTime = performance.now();
      const response = await fetch("/api/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ source: source })
      });

      const elapsed = Math.round(performance.now() - startTime);

      if (!response.ok) {
        throw new Error("Server error HTTP " + response.status);
      }

      const result = await response.json();

      if (result.error) {
        showError(result.error);
        if (result.output && result.output.length > 0) {
          outputBox.textContent = result.output;
        } else {
          outputBox.textContent = "(Scene stopped before producing any spoken lines)";
        }
      } else {
        setStatus("ready", `Scene complete (${elapsed}ms)`);
        if (!result.output || result.output.trim().length === 0) {
          outputBox.textContent = "(The scene executed with no spoken lines)";
        } else {
          outputBox.textContent = result.output;
        }
      }
    } catch (err) {
      showError("Connection error: " + err.message);
      outputBox.textContent = "Could not communicate with the local Reel server.";
    } finally {
      runBtn.disabled = false;
    }
  }

  // Handle text input, typing, pasting
  codeInput.addEventListener("input", function () {
    clearError();
    updateEditor();
  });

  // Handle scroll events
  codeInput.addEventListener("scroll", syncScroll);

  // Tab key & shortcuts
  codeInput.addEventListener("keydown", function (e) {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = this.selectionStart;
      const end = this.selectionEnd;

      // Insert 2 spaces
      this.value = this.value.substring(0, start) + "  " + this.value.substring(end);
      this.selectionStart = this.selectionEnd = start + 2;
      clearError();
      updateEditor();
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      runCode();
    }
  });

  // Global Ctrl+Enter shortcut
  window.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      runCode();
    }
  });

  // Example select change
  exampleSelect.addEventListener("change", function () {
    if (this.value) {
      applySelectedExample(this.value);
    }
  });

  // Buttons
  runBtn.addEventListener("click", runCode);
  shareBtn.addEventListener("click", shareCode);

  clearBtn.addEventListener("click", function () {
    codeInput.value = "";
    currentFilename.textContent = "untitled.reel";
    clearError();
    updateEditor();
    outputBox.textContent = 'Scene cleared. Write Reel code and click "Action!".';
    setStatus("ready", "Ready");
    codeInput.focus();
  });

  // Listen to hash changes (e.g. user pastes a new URL with hash)
  window.addEventListener("hashchange", function () {
    loadFromHash();
  });

  // Initial load
  loadExamples();
})();

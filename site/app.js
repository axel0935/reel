/* Reel Studio Client (Online Static Site via Pyodide Worker) */

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
  const EXECUTION_TIMEOUT_MS = 5000;

  // In-memory cache for loaded examples
  const examplesCodeMap = new Map();

  // State
  let worker = null;
  let isEngineReady = false;
  let isExecuting = false;
  let executionTimer = null;
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
  // - Keywords: v0.1 + v0.2 + v0.3 (IMPORT, LIB, WITH, CALL, GIVE BACK, LIST, ADD, AT, LENGTH OF, FOR EACH, IN, WHILE, etc.)
  // - Numbers: integer and decimal literals
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

  // ==========================================
  // Web Worker Management (Pyodide Execution)
  // ==========================================

  function initWorker() {
    if (worker) {
      try {
        worker.terminate();
      } catch (e) {}
    }

    isEngineReady = false;
    runBtn.disabled = true;
    runBtn.querySelector(".btn-text").textContent = "Loading engine...";
    setStatus("loading", "Downloading Pyodide (~10 MB)...");

    // Start Web Worker using relative URL
    worker = new Worker("worker.js");

    worker.onmessage = function (e) {
      const data = e.data || {};

      if (data.type === "status") {
        if (data.state === "ready") {
          isEngineReady = true;
          runBtn.disabled = false;
          runBtn.querySelector(".btn-text").textContent = "Action!";
          setStatus("ready", "Ready");
          if (outputBox.textContent.includes("Downloading in-browser Python")) {
            outputBox.textContent = 'Reel engine ready! Click "Action!" or press Ctrl+Enter to run your scene.';
          }
        } else if (data.state === "loading") {
          setStatus("loading", data.message || "Loading Pyodide...");
        } else if (data.state === "error") {
          showError(data.message || "Failed to initialize Reel runtime.");
          outputBox.textContent = "Could not load Pyodide runtime. Check your internet connection.";
        }
      } else if (data.type === "run_result") {
        handleRunResult(data.result);
      }
    };

    worker.onerror = function (err) {
      console.error("Worker error:", err);
      showError("Worker error: " + (err.message || "Unexpected error"));
      runBtn.disabled = false;
      runBtn.querySelector(".btn-text").textContent = "Action!";
      setStatus("error", "Engine error");
    };
  }

  function handleRunResult(result) {
    if (executionTimer) {
      clearTimeout(executionTimer);
      executionTimer = null;
    }
    isExecuting = false;
    runBtn.disabled = !isEngineReady;
    runBtn.querySelector(".btn-text").textContent = "Action!";

    if (result.error) {
      showError(result.error);
      if (result.output && result.output.length > 0) {
        outputBox.textContent = result.output;
      } else {
        outputBox.textContent = "(Scene stopped before producing any spoken lines)";
      }
    } else {
      setStatus("ready", "Scene complete");
      if (!result.output || result.output.trim().length === 0) {
        outputBox.textContent = "(The scene executed with no spoken lines)";
      } else {
        outputBox.textContent = result.output;
      }
    }
  }

  function runCode() {
    if (!isEngineReady) {
      showToast("Reel engine is still loading. Please wait a moment.");
      return;
    }
    if (isExecuting) return;

    const source = codeInput.value;
    clearError();
    setStatus("running", "Rolling...");
    isExecuting = true;
    runBtn.disabled = true;
    runBtn.querySelector(".btn-text").textContent = "Rolling...";

    // Safety contract: 5-second execution limit
    executionTimer = setTimeout(() => {
      // Terminate hanging worker
      if (worker) {
        worker.terminate();
      }
      isExecuting = false;
      showError("Scene timed out: execution took longer than 5 seconds. Did a loop run forever?");
      outputBox.textContent = "(Scene stopped before producing any spoken lines)";
      setStatus("error", "Scene timed out (5s limit)");

      // Restart worker
      initWorker();
    }, EXECUTION_TIMEOUT_MS);

    // Send code to worker
    worker.postMessage({
      type: "run",
      source: source
    });
  }

  // ==========================================
  // Examples and Code Sharing
  // ==========================================

  // Load example list from relative examples.json
  async function loadExamples() {
    try {
      const response = await fetch("examples.json");
      if (!response.ok) {
        throw new Error("HTTP error " + response.status);
      }
      const examples = await response.json();

      exampleSelect.innerHTML = "";

      const hasSharedCode = loadFromHash();

      let defaultFilename = "hello.reel";
      let foundDefault = false;

      const promptOption = document.createElement("option");
      promptOption.value = "";
      promptOption.textContent = hasSharedCode ? "Shared script (active)" : "-- Select an example --";
      if (hasSharedCode) promptOption.selected = true;
      exampleSelect.appendChild(promptOption);

      examples.forEach((filename) => {
        const option = document.createElement("option");
        option.value = filename;
        option.textContent = filename;
        if (!hasSharedCode && filename === defaultFilename) {
          foundDefault = true;
          option.selected = true;
        }
        exampleSelect.appendChild(option);
      });

      if (!hasSharedCode) {
        if (!foundDefault && examples.length > 0) {
          defaultFilename = examples[0];
          exampleSelect.value = defaultFilename;
        }
        fetchAndApplyExample(defaultFilename);
      }
    } catch (err) {
      console.warn("Could not load examples:", err);
      exampleSelect.innerHTML = '<option value="">Examples unavailable</option>';
      if (!loadFromHash()) {
        updateEditor();
      }
    }
  }

  // Fetch individual example code using relative URL
  async function fetchAndApplyExample(filename) {
    if (!filename) return;

    if (examplesCodeMap.has(filename)) {
      applyCode(filename, examplesCodeMap.get(filename));
      return;
    }

    try {
      const response = await fetch("examples/" + encodeURIComponent(filename));
      if (!response.ok) {
        throw new Error("HTTP error " + response.status);
      }
      const code = await response.text();
      examplesCodeMap.set(filename, code);
      applyCode(filename, code);
    } catch (err) {
      console.warn(`Could not load example ${filename}:`, err);
    }
  }

  function applyCode(filename, code) {
    codeInput.value = code;
    currentFilename.textContent = filename;
    clearError();
    updateEditor();
    if (isEngineReady) {
      outputBox.textContent = 'Click "Action!" or press Ctrl+Enter to run this scene.';
    }
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
        if (isEngineReady) {
          outputBox.textContent = 'Loaded shared script. Click "Action!" or press Ctrl+Enter to run.';
        }
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
    // Relative URL preserved by using current location without existing hash
    const baseUrl = window.location.href.split("#")[0];
    const shareUrl = `${baseUrl}#${encoded}`;

    window.history.replaceState(null, "", shareUrl);

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

    shareBtn.classList.add("copied");
    shareBtn.innerHTML = '<span class="btn-icon">✓</span> <span class="btn-text">Copied!</span>';
    showToast("Shareable link copied to clipboard!");

    setTimeout(() => {
      shareBtn.classList.remove("copied");
      shareBtn.innerHTML = '<span class="btn-icon">🔗</span> <span class="btn-text">Share</span>';
    }, 2000);
  }

  // ==========================================
  // Event Listeners
  // ==========================================

  codeInput.addEventListener("input", function () {
    clearError();
    updateEditor();
  });

  codeInput.addEventListener("scroll", syncScroll);

  codeInput.addEventListener("keydown", function (e) {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = this.selectionStart;
      const end = this.selectionEnd;

      this.value = this.value.substring(0, start) + "  " + this.value.substring(end);
      this.selectionStart = this.selectionEnd = start + 2;
      clearError();
      updateEditor();
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      runCode();
    }
  });

  window.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      runCode();
    }
  });

  exampleSelect.addEventListener("change", function () {
    if (this.value) {
      fetchAndApplyExample(this.value);
    }
  });

  runBtn.addEventListener("click", runCode);
  shareBtn.addEventListener("click", shareCode);

  clearBtn.addEventListener("click", function () {
    codeInput.value = "";
    currentFilename.textContent = "untitled.reel";
    clearError();
    updateEditor();
    outputBox.textContent = 'Scene cleared. Write Reel code and click "Action!".';
    if (isEngineReady) setStatus("ready", "Ready");
    codeInput.focus();
  });

  window.addEventListener("hashchange", function () {
    loadFromHash();
  });

  // Initialize
  initWorker();
  loadExamples();
})();

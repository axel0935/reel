/* Reel Studio Playground Client */

(function () {
  "use strict";

  // Elements
  const exampleSelect = document.getElementById("example-select");
  const codeInput = document.getElementById("code-input");
  const currentFilename = document.getElementById("current-filename");
  const runBtn = document.getElementById("run-btn");
  const clearBtn = document.getElementById("clear-btn");
  const outputBox = document.getElementById("output-box");
  const errorBanner = document.getElementById("error-banner");
  const errorMessage = document.getElementById("error-message");
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");

  // In-memory cache for loaded examples
  const examplesMap = new Map();

  // Helper to set execution status indicator
  function setStatus(state, message) {
    statusIndicator.className = "status-dot " + state;
    statusText.textContent = message;
  }

  // Hide the error banner
  function clearError() {
    errorBanner.classList.add("hidden");
    errorMessage.textContent = "";
  }

  // Display a friendly error
  function showError(errText) {
    errorMessage.textContent = errText;
    errorBanner.classList.remove("hidden");
    setStatus("error", "Interrupted");
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

      let defaultFilename = "hello.reel";
      let foundDefault = false;

      examples.forEach((item) => {
        examplesMap.set(item.filename, item.code);
        const option = document.createElement("option");
        option.value = item.filename;
        option.textContent = item.filename;
        if (item.filename === defaultFilename) {
          foundDefault = true;
          option.selected = true;
        }
        exampleSelect.appendChild(option);
      });

      if (!foundDefault && examples.length > 0) {
        defaultFilename = examples[0].filename;
        exampleSelect.value = defaultFilename;
      }

      // Load initial code into editor
      applySelectedExample(exampleSelect.value);
      setStatus("ready", "Ready");
    } catch (err) {
      console.warn("Could not load examples:", err);
      exampleSelect.innerHTML = '<option value="">Examples unavailable</option>';
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
    outputBox.textContent = 'Click "Action!" or press Ctrl+Enter to run this scene.';
    setStatus("ready", "Ready");
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
        throw new Error("Server responded with HTTP " + response.status);
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

  // Handle Tab indentation in the textarea
  codeInput.addEventListener("keydown", function (e) {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = this.selectionStart;
      const end = this.selectionEnd;

      // Insert 2 spaces
      this.value = this.value.substring(0, start) + "  " + this.value.substring(end);
      this.selectionStart = this.selectionEnd = start + 2;
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
    applySelectedExample(this.value);
  });

  // Action button click
  runBtn.addEventListener("click", runCode);

  // Clear button click
  clearBtn.addEventListener("click", function () {
    codeInput.value = "";
    currentFilename.textContent = "untitled.reel";
    clearError();
    outputBox.textContent = 'Scene cleared. Write Reel code and click "Action!".';
    setStatus("ready", "Ready");
    codeInput.focus();
  });

  // Start initialization
  loadExamples();
})();

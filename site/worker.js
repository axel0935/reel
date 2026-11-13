/* Web Worker for running Reel with Pyodide */

// Pinned exact version of Pyodide from jsDelivr
const PYODIDE_VERSION = "v0.26.4";
importScripts(`https://cdn.jsdelivr.net/pyodide/${PYODIDE_VERSION}/full/pyodide.js`);

let pyodideInstance = null;
let isReady = false;

async function initPyodide() {
  try {
    self.postMessage({
      type: "status",
      state: "loading",
      message: "Downloading Pyodide engine (~10 MB)..."
    });

    pyodideInstance = await loadPyodide({
      indexURL: `https://cdn.jsdelivr.net/pyodide/${PYODIDE_VERSION}/full/`
    });

    self.postMessage({
      type: "status",
      state: "loading",
      message: "Unpacking Reel standard library..."
    });

    // Fetch relative reel.zip built by site/build_site.py
    const response = await fetch("reel.zip");
    if (!response.ok) {
      throw new Error(`Could not load reel.zip (HTTP ${response.status})`);
    }
    const zipBytes = await response.arrayBuffer();
    await pyodideInstance.unpackArchive(zipBytes, "zip");

    // Initialize the Reel runner environment in Python
    pyodideInstance.runPython(`
import sys
import json
if "." not in sys.path:
    sys.path.insert(0, ".")

from reel.api import run

def execute_reel_script(source_code):
    try:
        # Contract: Always call run(source, safe=True)
        res = run(source_code, safe=True)
    except Exception as exc:
        res = {"output": "", "error": f"Execution error: {exc}"}
    return json.dumps(res)
`);

    isReady = true;
    self.postMessage({
      type: "status",
      state: "ready",
      message: "Reel engine ready!"
    });
  } catch (err) {
    self.postMessage({
      type: "status",
      state: "error",
      message: "Failed to initialize Reel runtime: " + err.message
    });
  }
}

self.onmessage = async function (e) {
  const data = e.data || {};
  if (data.type === "run") {
    if (!isReady) {
      self.postMessage({
        type: "run_result",
        result: {
          output: "",
          error: "The Reel engine is still downloading (~10 MB). Please wait a moment."
        }
      });
      return;
    }

    try {
      const runner = pyodideInstance.globals.get("execute_reel_script");
      const jsonStr = runner(data.source || "");
      const result = JSON.parse(jsonStr);
      self.postMessage({
        type: "run_result",
        result: result
      });
    } catch (err) {
      self.postMessage({
        type: "run_result",
        result: {
          output: "",
          error: "Execution error: " + err.message
        }
      });
    }
  }
};

initPyodide();

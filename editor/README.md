# Reel extension for VSCodium

This folder contains a small VSCodium extension for Reel files. It highlights
Reel keywords, built-in scenes, text, numbers, and `--` comments. It also adds
snippets for scenes and common blocks.

## Install on Ubuntu

1. Install VSCodium if you do not already have it. See the Ubuntu instructions
   at [vscodium.com](https://vscodium.com/#install).
2. Install the VS Code Extension Manager, if needed:

   ```bash
   sudo apt install npm
   sudo npm install --global @vscode/vsce
   ```

3. From the project folder, package the extension:

   ```bash
   cd editor/reel-vscode
   vsce package
   ```

4. In VSCodium, open the Extensions view, choose the `...` menu, choose
   **Install from VSIX...**, and select the new `reel-language-0.3.0.vsix`
   file.

5. Open any `.reel` file. It should now have Reel colors and snippets.

The extension only adds editor help. It does not run Reel programs.

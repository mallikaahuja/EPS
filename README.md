# EPS Interactive P&ID Generator

A modern, AI-powered, Streamlit-based tool for creating industry-grade P&ID diagrams with ISA/ISO-compliant symbols.

## 🚀 Features

- **Snap-to-grid P&ID drawing** with orthogonal pipes, scope boxes, and auto-tagging
- **Drag-and-drop equipment, pipelines, and inline components**
- **Legend/BOM and industrial title block** auto-generated on every drawing
- **High-res PNG and layered DXF export** (A3, 300 DPI)
- **AI-powered symbol generation** (Stability AI) for missing P&ID symbols
- **Predictive suggestions and error checking** (OpenAI)
- **Inline error handling** — never crashes, always tells you what's missing
- **Symbols/ folder**: all black-and-white transparent PNGs, 100x100px, referenced by CSVs

## 🛠️ Setup & Usage

1. **Install dependencies:**  
   ```
   pip install -r requirements.txt
   ```

2. **Set API Keys (in Railway, or locally as environment variables):**  
   - `OPENAI_API_KEY` for predictive checks and suggestions  
   - `STABILITY_API_KEY` for symbol generation

3. **Prepare your CSVs** in the root folder:  
   - `equipment_list.csv`
   - `pipeline_list.csv`
   - `inline_component_list.csv`

4. **Place all symbol PNGs** in `/symbols/` (100x100px, transparent background)

5. **Run the app:**  
   ```
   streamlit run app.py
   ```

## 🧠 AI Features

- **Generate missing symbols:**  
  When a symbol is missing, click "Generate with AI" to call Stability AI and add it automatically.

- **Get predictive suggestions:**  
  Click "Get AI Suggestions" to have OpenAI check your P&ID for common mistakes and missing components.

## 📦 Export

- Download your P&ID as PNG or DXF with a single click from the toolbar.

## 🙋 Troubleshooting

- If you see warnings about missing symbols, use the “Validate Symbols” button or generate with AI.
- For errors with AI features, check your API key setup in Railway.

## 📄 License

MIT License (or your chosen license here)

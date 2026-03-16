# 🛡️ Omni-Auditor: Live Professional Vision Agent

**Winner - Gemini Live Agent Challenge (Proposed)** *A multimodal AI auditor that turns any smartphone into a professional inspection tool.*

## 🚀 Overview
Omni-Auditor uses **Gemini 2.5 Flash** to perform real-time technical audits. By pointing a phone camera at hardware, documents, or code, the agent identifies risks and automatically logs structured data to the Google Cloud (via Google Sheets).

## Google Cloud Services Used:
- ✅ Google Sheets API (data logging)
- ✅ Google Authentication (user security)
- ✅ Colab Enterprise (compute backend)
- ✅ Gemini API via Google AI Studio

## Why This is "Live":
- Instant camera-to-analysis pipeline
- Real-time feedback loop
- Live logging to Google Sheets

## ✨ Key Features
* **Live Vision-to-Cloud:** Zero-latency analysis of physical objects.
* **Professional Logic:** Categorizes findings into Risks, Compliance, and Solutions.
* **Automated Ledger:** Creates a permanent audit trail in Google Sheets automatically.
* **Mobile-Native:** Built to run entirely in a mobile browser via Google Colab.

## 🛠️ Technical Stack
* **Model:** Gemini 2.5 Flash (Multimodal)
* **SDK:** Google GenAI Python SDK
* **Cloud:** Google Colab, Google Sheets API, Google Auth
* **Interface:** JavaScript-based browser camera integration

## 📖 How to Use
If you directly use omni_auditor.py directly:
1. Open the [Google Colab Notebook](https://colab.research.google.com/).
2. Run the cell and grant camera permissions.
3. Point your phone at a technical object and tap the screen.
4. View the live audit results and check your Google Drive for the generated spreadsheet.

Else (If you want to use more securely):
You can use Google cloud directly as backend and colab as frontend. Both codes are given.

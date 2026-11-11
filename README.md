# AI-Powered Academic Notes Summarizer

A locally hosted Flask web application that turns student-provided lecture notes and text-based PDF documents into structured study guides using the Groq API.

## Features

- Paste academic notes or upload a PDF (maximum 10 MB).
- Choose Short Summary, Detailed Summary, or Exam Preparation Notes.
- Generate output in English or Urdu.
- Separate sections for main summary, key concepts, definitions, important points, 15 revision questions, quick revision notes, and key takeaways.
- Copy the generated study guide or download it as a `.txt` file.
- Responsive interface for desktop, tablet, and mobile.
- API key stays on the Python backend; it is never sent to frontend JavaScript.
- Uploaded PDFs are processed in memory and are not saved to disk.
- The model is instructed to use only supplied material and flag missing information.

## Technologies

- Python 3.10+
- Flask
- Groq Python SDK
- python-dotenv
- PyMuPDF
- HTML, CSS, JavaScript

## Project structure

```text
academic-notes-summarizer/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
└── uploads/
    └── .gitkeep
```

## Requirements

- Windows 10/11, macOS, or Linux.
- Python 3.10 or newer.
- Internet connection for Groq API requests.
- A Groq API key.

Check Python on Windows PowerShell:

```powershell
py --version
```

If `py` is not recognized, try:

```powershell
python --version
```

## Installation on Windows PowerShell

Open PowerShell in the project folder.

### 1. Create and activate a virtual environment

Using the Python launcher:

```powershell
py -m venv venv
venv\Scripts\activate
```

If `py` is not available but `python` works:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow scripts for this terminal session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

If the `py` launcher is unavailable, use `python -m pip` instead.

### 3. Configure your Groq API key

Create a key in your Groq account. In the project folder, copy the example file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code and replace the placeholder:

```dotenv
GROQ_API_KEY=put_your_real_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
FLASK_DEBUG=true
PORT=5000
```

Do not add quotes around the key unless required by your environment. Never share `.env` or commit it to GitHub. The `.gitignore` file excludes it.

### 4. Run the application

```powershell
py app.py
```

If `py` is not recognized:

```powershell
python app.py
```

### 5. Open the website

Visit:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

Keep the terminal open while using the app. Press `Ctrl+C` in the terminal to stop the server.

## Using the application

1. Paste notes into the text area, or choose a PDF.
2. Select a summary style and output language.
3. Click **Generate Summary**.
4. Review the generated sections.
5. Use **Copy Summary** or **Download** to keep the study guide.
6. Use **Generate Again** to rerun the request with the current input and options.
7. Use **Clear All** to reset the page.

Pasted text and extracted PDF text can be combined in one request. The total source text is limited to 80,000 characters.

## API and privacy notes

- The backend reads `GROQ_API_KEY` from `.env`.
- The key is never embedded in HTML or JavaScript.
- PDFs are read into memory and are not written into the `uploads` folder.
- No database or persistent user-material storage is used by this starter version.
- Source material is sent to Groq to generate the requested study guide. Do not submit confidential or sensitive material unless you are permitted to share it with the API provider.
- The prompt strongly instructs the model to remain grounded in the supplied material. As with all generative AI, review important academic output against the original source.

## Common errors and solutions

### `ModuleNotFoundError: No module named 'flask'` (or `dotenv`, `fitz`, `groq`)

Activate the project's virtual environment and install requirements:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For `fitz`, the correct package is **PyMuPDF** (installed through requirements); do not install the unrelated package named `fitz`.

### `GROQ_API_KEY is missing`

Make sure `.env` exists in the same folder as `app.py`, contains `GROQ_API_KEY=...`, and restart the Flask server.

### Groq authentication failed / HTTP 401

Check that the key is valid, active, copied completely, and has no accidental spaces. Do not paste the key into chat or frontend code.

### Groq rate limit / HTTP 429

Wait and retry later, or check the limits and usage for your Groq account.

### Could not connect / timeout

Check your internet connection and try again. Groq API access requires connectivity.

### PDF is empty, invalid, or has no readable text

Use a valid, non-password-protected PDF with selectable text. This starter version does not perform OCR on scanned image-only PDFs.

### Port 5000 is already in use

Stop the other Flask process with `Ctrl+C`, or change `PORT` in `.env`, for example `PORT=5001`, then open `http://127.0.0.1:5001`.

### PowerShell says `py` is not recognized

Use `python` in place of `py` in the commands, for example:

```powershell
python -m venv venv
python -m pip install -r requirements.txt
python app.py
```

## Testing checklist

- [ ] App home page loads.
- [ ] Empty submission shows a validation message.
- [ ] Pasted text is sent to the backend.
- [ ] PDF upload accepts `.pdf` and rejects other extensions.
- [ ] Invalid, empty, oversized, and image-only PDFs show useful errors.
- [ ] Missing or invalid API key is handled.
- [ ] Successful Groq response renders all result sections.
- [ ] Copy, Download, Generate Again, and Clear All buttons work.

The Groq integration requires a valid API key and network access; without these, a live AI-generation test cannot be completed.

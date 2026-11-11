import json
import os
import re
from pathlib import Path

import fitz  # PyMuPDF
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB request limit
app.config["JSON_SORT_KEYS"] = False

ALLOWED_EXTENSION = ".pdf"
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 80_000
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are an academic learning assistant. Transform only the user-provided academic
material into accurate, organized, student-friendly study notes.

STRICT SOURCE-GROUNDING RULES:
- Use only information explicitly present in the supplied material.
- Do not invent facts, definitions, examples, references, dates, or claims.
- Preserve important technical terminology and the original meaning.
- If the material does not provide enough information, say so clearly.
- Questions must be answerable or discussable from the supplied material; do not
  introduce outside subject matter.
- Follow the requested summary style and output language.
- Return valid JSON only, matching the requested schema. Do not wrap it in
  Markdown fences.

Return this JSON object:
{
  "main_summary": "string",
  "key_concepts": ["string"],
  "definitions": [{"term": "string", "definition": "string"}],
  "important_points": ["string"],
  "exam_questions": {
    "short_answer": ["exactly 5 questions"],
    "conceptual": ["exactly 5 questions"],
    "long_answer": ["exactly 5 questions"]
  },
  "quick_revision_notes": ["string"],
  "key_takeaways": ["string"]
}
If a category is not covered in the source, return a concise note that the
provided material does not contain enough information rather than guessing.
"""

def extract_pdf_text(file_storage):
    """Extract text from a PDF held in memory; no file is saved to disk."""
    raw = file_storage.read()
    if not raw:
        raise ValueError("The uploaded PDF is empty.")
    if len(raw) > MAX_PDF_BYTES:
        raise ValueError("PDF is too large. Maximum allowed size is 10 MB.")
    if not raw.startswith(b"%PDF"):
        raise ValueError("The uploaded file does not appear to be a valid PDF.")

    try:
        with fitz.open(stream=raw, filetype="pdf") as document:
            pages = [page.get_text("text") for page in document]
    except Exception as exc:
        raise ValueError("The PDF could not be opened. It may be damaged or password-protected.") from exc

    text = "\n".join(pages).strip()
    if not text:
        raise ValueError("No readable text was found in this PDF. Scanned/image-only PDFs are not supported.")
    return text

def validate_result(data):
    """Normalize the model response to the keys expected by the frontend."""
    required_lists = ["key_concepts", "important_points", "quick_revision_notes", "key_takeaways"]
    if not isinstance(data, dict) or not isinstance(data.get("main_summary"), str):
        raise ValueError("The AI returned an unexpected response format.")

    for key in required_lists:
        if not isinstance(data.get(key), list):
            data[key] = []
        data[key] = [str(item) for item in data[key]]

    definitions = data.get("definitions", [])
    if not isinstance(definitions, list):
        definitions = []
    data["definitions"] = [
        {"term": str(item.get("term", "")), "definition": str(item.get("definition", ""))}
        for item in definitions if isinstance(item, dict)
    ]

    questions = data.get("exam_questions", {})
    if not isinstance(questions, dict):
        questions = {}
    data["exam_questions"] = {}
    for key in ("short_answer", "conceptual", "long_answer"):
        items = questions.get(key, [])
        data["exam_questions"][key] = [str(item) for item in items] if isinstance(items, list) else []
    return data

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/summarize")
def summarize():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return jsonify(error="Groq API key is missing. Add GROQ_API_KEY to your .env file and restart the app."), 503

    pasted_text = request.form.get("notes", "").strip()
    uploaded_file = request.files.get("pdf")
    material = pasted_text

    if uploaded_file and uploaded_file.filename:
        filename = secure_filename(uploaded_file.filename)
        if Path(filename).suffix.lower() != ALLOWED_EXTENSION:
            return jsonify(error="Unsupported file type. Please upload a PDF file."), 400
        try:
            pdf_text = extract_pdf_text(uploaded_file)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        material = (material + "\n\n" + pdf_text).strip() if material else pdf_text

    if not material:
        return jsonify(error="Paste your notes or upload a readable PDF before generating a summary."), 400
    if len(material) > MAX_TEXT_CHARS:
        return jsonify(error=f"Your material is too long. Please keep it under {MAX_TEXT_CHARS:,} characters."), 413

    style = request.form.get("style", "detailed")
    language = request.form.get("language", "English")
    style_instructions = {
        "short": "Short Summary: be concise while preserving all central ideas.",
        "detailed": "Detailed Summary: explain the important ideas clearly and with useful detail.",
        "exam": "Exam Preparation Notes: prioritize examinable ideas, definitions, comparisons, and revision usefulness."
    }
    if style not in style_instructions:
        return jsonify(error="Please choose a valid summary style."), 400
    if language not in ("English", "Urdu"):
        return jsonify(error="Please choose English or Urdu."), 400

    user_prompt = f"""Create study material from the source below.

Selected style: {style_instructions[style]}
Output language: {language}

Keep the exact JSON schema specified in the system instructions. Include exactly
5 questions in each question category. Do not add outside knowledge.

<SOURCE MATERIAL>
{material}
</SOURCE MATERIAL>"""

    try:
        client = Groq(api_key=api_key, timeout=90.0, max_retries=1)
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=6000,
            response_format={"type": "json_object"},
        )
        response_text = completion.choices[0].message.content or ""
        result = validate_result(json.loads(response_text))
        return jsonify(result=result, source_characters=len(material))
    except json.JSONDecodeError:
        app.logger.exception("Groq returned invalid JSON")
        return jsonify(error="The AI response could not be read. Please try again."), 502
    except Exception as exc:
        app.logger.exception("Summarization failed")
        message = str(exc).lower()
        if "401" in message or "authentication" in message or "api key" in message:
            return jsonify(error="Groq authentication failed. Check that your GROQ_API_KEY in .env is valid."), 401
        if "429" in message or "rate limit" in message:
            return jsonify(error="Groq rate limit reached. Wait a little and try again."), 429
        if "timeout" in message or "connection" in message:
            return jsonify(error="Could not connect to Groq. Check your internet connection and try again."), 502
        return jsonify(error="The summary could not be generated. Check your API settings and try again."), 502

@app.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    return jsonify(error="Upload is too large. Please keep the PDF under 10 MB."), 413

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")

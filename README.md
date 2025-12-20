# Voice‑First Agentic AI for Government Scheme Eligibility

## Project Overview

This project implements a **voice‑first, agentic AI system** that helps users **identify and (theoretically) apply for government or public welfare schemes** using a **native Indian language (Hindi)**.

The system demonstrates:

* Agentic reasoning (Planner–Executor–Evaluator)
* Tool usage
* Conversation memory
* Failure and ambiguity handling
* End‑to‑end voice interaction

---

## Assignment Alignment

✔ Voice‑first interaction (STT → LLM → TTS)
✔ Native Indian language throughout
✔ Agentic workflow
✔ Multiple tools
✔ Memory and contradiction handling
✔ Failure recovery

---

## System Flow

1. User speaks via microphone
2. Speech is converted to text (Whisper)
3. Agent plans next action
4. Tools are invoked for parsing and eligibility
5. Response is converted to speech
6. Agent confirms and completes task

---

## Technologies Used

* **Python 3.10+**
* **Groq API** (Whisper + LLaMA)
* **SpeechRecognition**
* **gTTS** (Text‑to‑Speech)
* **pygame** (Audio playback)
* **rich** (Terminal output)

---

## Project Structure

```
hindi_scheme_agent/
│
├── main.py                 # Agentic AI implementation
├── data/
│   └── schemes.json        # Government schemes data
├── temp/                   # Temporary audio files
├── .env                    # API keys
├── README.md               # This file
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo_url>
cd hindi_scheme_agent
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

---

## Running the Project

```bash
python main.py
```

Speak when prompted. The agent will guide you step‑by‑step.

---

## Failure Handling Examples

* Speak multiple values → agent asks to clarify
* Stay silent → agent retries
* Say wrong confirmation → agent resets

---

## Notes

* Application step is **mocked conceptually**
* Real government integration is out of academic scope
* Focus is on agentic behavior and system design

---

## Conclusion

This project is a complete, runnable demonstration of a **voice‑first agentic AI system** aligned with modern AI system design principles and academic assignment requirements.

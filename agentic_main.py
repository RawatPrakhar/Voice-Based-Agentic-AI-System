import os
import json
import time
import sys
import re
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
import speech_recognition as sr
from pygame import mixer
from rich.console import Console

# UTF-8 for Devanagari
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
console = Console()


class AgenticHindiGovtAgent:
    def __init__(self):
        # ===== MEMORY (Conversation State) =====
        self.user_data = {
            "age": None,
            "gender": None,
            "income": None,
            "caste": None
        }

        try:
            with open("data/schemes.json", "r", encoding="utf-8") as f:
                self.schemes = json.load(f)
        except:
            self.schemes = []

        mixer.init()
        if not os.path.exists("temp"):
            os.makedirs("temp")

    # ==================================================
    # EXECUTOR TOOLS
    # ==================================================
    def tool_stt(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            console.print("[bold yellow]सुन रहा हूँ...[/bold yellow]")
            r.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = r.listen(source, timeout=7, phrase_time_limit=10)
                with open("temp/input.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                with open("temp/input.wav", "rb") as file:
                    transcription = client.audio.transcriptions.create(
                        file=("temp/input.wav", file.read()),
                        model="whisper-large-v3",
                        language="hi"
                    )
                text = transcription.text.strip()
                console.print(f"[bold green]उपयोगकर्ता:[/bold green] {text}")
                return text
            except:
                return None

    def tool_parse(self, user_input, field):
        prompt = (
            "You are a strict data extractor.\n"
            f"Field: {field}\n"
            f"Input: {user_input}\n"
            "Rules:\n"
            "- Age/Income: digits only\n"
            "- Gender: MALE or FEMALE\n"
            "- Caste: GENERAL, OBC, SC, ST\n"
            "- Return ONLY one value"
        )
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0
        )
        return completion.choices[0].message.content.upper().split()[0]

    def tool_eligibility_engine(self):
        u_age = int(re.sub(r"\D", "", self.user_data["age"]))
        u_income = int(re.sub(r"\D", "", self.user_data["income"]))

        matches = []
        for s in self.schemes:
            if (
                s["min_age"] <= u_age <= s["max_age"]
                and s["min_income"] <= u_income <= s["max_income"]
                and self.user_data["caste"] in [c.upper() for c in s["caste"]]
                and self.user_data["gender"] in [g.upper() for g in s["gender"]]
            ):
                matches.append(s["name"])
        return matches

    def speak(self, text):
        console.print(f"\n[bold blue]मॉडल:[/bold blue] {text}")
        tts = gTTS(text=text, lang="hi")
        path = "temp/output.mp3"
        tts.save(path)
        mixer.music.load(path)
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.1)
        mixer.music.unload()

    # ==================================================
    # EVALUATOR HELPERS
    # ==================================================
    def is_ambiguous(self, text, field):
        text = text.lower()

        if field in ["age", "income"]:
            numbers = re.findall(r"\d[\d,]*", text)
            normalized = {n.replace(",", "") for n in numbers}
            return len(normalized) > 1

        if field == "gender":
            has_male = any(x in text for x in ["पुरुष", "male", "m", "पोरुष", "पुरूष"])
            has_female = any(x in text for x in ["महिला", "female", "f"])
            return has_male and has_female

        if field == "caste":
            hits = sum(
                1 for c in ["general", "obc", "sc", "st", "जनरल", "ओबीसी", "एससी", "एसटी"]
                if c in text
            )
            return hits > 1

        return False

    def is_affirmative(self, text):
        return any(x in text for x in ["हाँ", "हां", "सही", "सही है", "yes"])

    # ==================================================
    # AGENTIC LOOP (Planner → Executor → Evaluator)
    # ==================================================
    def run(self):
        self.speak("नमस्ते, मैं आपकी सरकारी योजनाएं खोजने में मदद करूँगा।")

        fields = {
            "age": "आपकी उम्र कितनी है?",
            "gender": "आपका लिंग क्या है? (महिला या पुरुष)",
            "income": "आपकी मासिक आय कितनी है?",
            "caste": "आपकी जाति क्या है?"
        }

        # ---------------- PLANNER ----------------
        for field, question in fields.items():
            while self.user_data[field] is None:
                self.speak(question)

                # -------- EXECUTOR --------
                raw = self.tool_stt()
                if not raw:
                    self.speak("मुझे आपकी आवाज़ नहीं सुनाई दी।")
                    continue

                # -------- EVALUATOR --------
                if self.is_ambiguous(raw, field):
                    self.speak("आपने एक से अधिक उत्तर दिए हैं। कृपया केवल एक उत्तर दें।")
                    continue

                parsed = self.tool_parse(raw, field)

                # -------- IMMEDIATE CONFIRMATION --------
                self.speak(f"आपने {parsed} बताया है। क्या यह सही है?")

                conf = self.tool_stt()
                if conf and self.is_affirmative(conf):
                    self.user_data[field] = parsed
                else:
                    self.speak("ठीक है, कृपया दोबारा बताइए।")

        # ---------------- FINAL ACTION ----------------
        self.speak("धन्यवाद। मैं आपके लिए योजनाओं की खोज कर रहा हूँ।")
        results = self.tool_eligibility_engine()

        if results:
            self.speak(f"आप {len(results)} योजनाओं के लिए पात्र हैं: " + ", ".join(results))
        else:
            self.speak("आपकी जानकारी के अनुसार कोई योजना नहीं मिली।")


if __name__ == "__main__":
    agent = AgenticHindiGovtAgent()
    agent.run()
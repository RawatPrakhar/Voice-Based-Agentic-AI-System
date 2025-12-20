import os
import json
import time
import sys
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
import speech_recognition as sr
from pygame import mixer
from rich.console import Console

# Force UTF-8 encoding for VS Code Terminal
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
console = Console()


class HindiGovtAgent:
    def __init__(self):
        # Conversation memory
        self.user_data = {
            "age": None,
            "gender": None,
            "income": None,
            "caste": None
        }

        # Load schemes
        try:
            with open("data/schemes.json", "r", encoding="utf-8") as f:
                self.schemes = json.load(f)
        except:
            self.schemes = []

        mixer.init()
        if not os.path.exists("temp"):
            os.makedirs("temp")

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

    def listen(self):
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

    def parse_with_llm(self, user_input, field_type):
        prompt = (
            "You are a strict data extractor.\n"
            "Return ONLY ONE value.\n\n"
            f"Input: {user_input}\n"
            f"Field: {field_type}\n\n"
            "Rules:\n"
            "- Gender: MALE or FEMALE\n"
            "- Caste: GENERAL, OBC, SC, ST\n"
            "- Age/Income: digits only\n"
            "- No explanation\n"
        )

        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0,
        )

        raw = completion.choices[0].message.content.upper()
        clean = raw.split()[0]  # TAKE ONLY FIRST TOKEN
        return clean

    # =======================
    # ✅ NEW: Ambiguity Check
    # =======================
    def is_ambiguous(self, text, field_type):
        text = text.lower()

        if field_type in ["age", "income"]:
            import re
            numbers = re.findall(r'\d[\d,]*', text)
            normalized = {n.replace(",", "") for n in numbers}
            return len(normalized) > 1


        if field_type == "gender":
            has_male = any(x in text for x in ["पुरुष", "male", "m", "पुरूष"])
            has_female = any(x in text for x in ["महिला", "female", "f"])
            return has_male and has_female

        if field_type == "caste":
            hits = 0
            for c in ["general", "obc", "sc", "st", "जनरल", "ओबीसी", "एससी", "एसटी"]:
                if c in text:
                    hits += 1
            return hits > 1

        return False

    def collect_information(self):
        self.speak(
            "नमस्ते, मैं आपकी सरकारी योजनाएं खोजने में मदद करूँगा। "
            "कृपया अपनी जानकारी दें।"
        )

        fields = {
            "age": "आपकी उम्र कितनी है?",
            "gender": "आपका लिंग क्या है? (महिला या पुरुष)",
            "income": "आपकी मासिक आय कितनी है?",
            "caste": "आपकी जाति क्या है? (जनरल, ओबीसी, एससी, एसटी)"
        }

        for key, question in fields.items():
            success = False
            while not success:
                self.speak(question)
                raw = self.listen()

                if not raw:
                    self.speak("मुझे आपकी आवाज़ नहीं सुनाई दी।")
                    continue

                # ✅ Ambiguity rejection BEFORE parsing
                if self.is_ambiguous(raw, key):
                    self.speak(
                        "आपने एक से अधिक उत्तर दिए हैं। "
                        "कृपया केवल एक स्पष्ट उत्तर दें।"
                    )
                    continue

                parsed = self.parse_with_llm(raw, key)
                if parsed:
                    self.user_data[key] = parsed
                    success = True
                else:
                    self.speak("क्षमा करें, मुझे समझ नहीं आया।")

    def verify_and_execute(self):
        gender_hi = "महिला" if self.user_data["gender"] == "FEMALE" else "पुरुष"

        summary = (
            f"आपने बताया: उम्र {self.user_data['age']}, "
            f"लिंग {gender_hi}, "
            f"आय {self.user_data['income']}, "
            f"और जाति {self.user_data['caste']}। "
            "क्या यह सही है?"
        )

        self.speak(summary)

        user_conf = self.listen()
        if user_conf and any(x in user_conf for x in ["हाँ", "सही", "सही है"]):
            self.run_tool()
        else:
            self.speak("ठीक है, कृपया फिर से जानकारी दें।")
            self.collect_information()
            self.verify_and_execute()

    def run_tool(self):
        self.speak("धन्यवाद। मैं आपके लिए सही योजनाओं की खोज कर रहा हूँ।")

        try:
            u_age = int("".join(filter(str.isdigit, self.user_data["age"])))
            u_income = int("".join(filter(str.isdigit, self.user_data["income"])))
            u_gender = self.user_data["gender"]
            u_caste = self.user_data["caste"]

            matches = []

            for s in self.schemes:
                age_ok = s["min_age"] <= u_age <= s["max_age"]
                income_ok = s["min_income"] <= u_income <= s["max_income"]
                caste_ok = u_caste in [c.upper() for c in s["caste"]]
                gender_ok = u_gender in [g.upper() for g in s["gender"]]

                if age_ok and income_ok and caste_ok and gender_ok:
                    matches.append(s["name"])

            if matches:
                self.speak(
                    f"आप {len(matches)} योजनाओं के लिए पात्र हैं: "
                    + ", ".join(matches)
                )
            else:
                self.speak(
                    "माफ कीजिये, आपकी जानकारी के अनुसार कोई योजना नहीं मिली।"
                )

        except:
            self.speak("डेटा प्रोसेस करने में तकनीकी समस्या हुई।")


if __name__ == "__main__":
    agent = HindiGovtAgent()
    agent.collect_information()
    agent.verify_and_execute()

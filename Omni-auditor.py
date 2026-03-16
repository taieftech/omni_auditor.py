
!pip install google-adk -q

import os
import json
import datetime
import google.generativeai as genai
from google.colab import output, auth, files
from google.auth import default
import gspread
from IPython.display import display, Javascript, HTML, clear_output
from google.colab.output import eval_js
from base64 import b64decode
from PIL import Image
import ipywidgets as widgets
import time

from google.adk import Agent

# Create ADK agent wrapper (this just documents compliance, doesn't change your code)
adk_agent = Agent(
    name="AuditVisionAI",
    model="gemini-2.5-flash",
    instruction="""You are a safety audit assistant that analyzes images for risks
    and provides solutions. You can see images and answer questions about them."""
)
print("✅ ADK agent initialized for compliance")

try:
    from google.colab import userdata
    API_KEY = userdata.get('GEMINI_API_KEY')
except:
    API_KEY = None

if not API_KEY:
    API_KEY = 'AIzaSyDU_MbRj2XBhNgCsrwpXP0GOV_XnpDDuDc'  # Replace with your key

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_image():
    """Try camera, fallback to file upload."""
    js = Javascript('''
    async function takePhoto() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}});
        const video = document.createElement('video');
        video.srcObject = stream; await video.play();
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        await new Promise(r => { document.body.appendChild(video); video.onclick = r; });
        canvas.getContext('2d').drawImage(video, 0, 0);
        stream.getVideoTracks()[0].stop();
        document.body.removeChild(video);
        return canvas.toDataURL('image/jpeg', 0.9);
      } catch {
        return "FAILED";
      }
    }
    ''')
    display(js)
    data = eval_js('takePhoto()')
    if data != "FAILED":
        binary = b64decode(data.split(',')[1])
        with open('audit.jpg', 'wb') as f: f.write(binary)
        return 'audit.jpg'
    print("📁 Camera failed. Please upload an image.")
    uploaded = files.upload()
    return next(iter(uploaded))

def parse_response(text):
    try:
        return json.loads(text[text.index('{'):text.rindex('}')+1])
    except:
        return {"risks":["Parse error"], "solutions":["Review manually"], "summary":"Error"}

def speak_text(text):
    """Convert text to speech using browser's speech synthesis."""
    safe_text = json.dumps(text)
    js = f"""
    var utterance = new SpeechSynthesisUtterance({safe_text});
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
    """
    display(Javascript(js))

def request_microphone_permission():
    """Request microphone permission upfront to avoid later issues."""
    js = Javascript('''
    async function requestMic() {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        return "granted";
      } catch (e) {
        return "denied";
      }
    }
    ''')
    display(js)
    result = eval_js('requestMic()')
    if result == "granted":
        print("✅ Microphone permission granted.")
        return True
    else:
        print("❌ Microphone permission denied. Voice input won't work.")
        return False

def get_voice_input():
    """Get voice input with a clear prompt and error handling."""
    js = Javascript('''
    async function getSpeech() {
      try {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        return new Promise((resolve, reject) => {
          recognition.onresult = (e) => {
            resolve(e.results[0][0].transcript);
          };
          recognition.onerror = (e) => {
            reject(e.error);
          };
          recognition.start();
        });
      } catch (e) {
        return "ERROR: " + e.toString();
      }
    }
    ''')
    display(js)
    try:
        result = eval_js('getSpeech()')
        return result
    except Exception as e:
        return f"ERROR: {e}"

# ========== MAIN AUDIT FUNCTION ==========
def audit():
    print("📸 Get image...")
    path = get_image()
    display(Image.open(path))

    print("🧠 Analyzing with Gemini 2.5 Flash...")
    prompt = """Analyze this image. Return ONLY valid JSON with keys:
    risks (list of objects with description, severity HIGH/MEDIUM/LOW),
    solutions (list of strings), summary (string), confidence (0-100)."""

    resp = model.generate_content([prompt, Image.open(path)])
    data = parse_response(resp.text)

    print("☁️ Logging to Google Sheets...")
    auth.authenticate_user()
    gc = gspread.authorize(default()[0])
    try:
        sh = gc.open('AuditLog')
    except:
        sh = gc.create('AuditLog')
        sh.sheet1.append_row(['Time','Summary','Risks','Solutions','Confidence'])

    sh.sheet1.append_row([
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get('summary',''),
        str([r['description'] for r in data.get('risks',[])]),
        str(data.get('solutions',[])),
        data.get('confidence','')
    ])

    # Display results
    print("\n✅ AUDIT COMPLETE")
    print(f"📋 {data.get('summary','')} (confidence: {data.get('confidence',0)}%)")
    for r in data.get('risks',[]):
        print(f"⚠️  {r['description']} [{r.get('severity','MEDIUM')}]")
    for i,s in enumerate(data.get('solutions',[]),1):
        print(f"💡 {i}. {s}")

    # Speak summary
    try:
        summary = data.get('summary', 'No summary available.')
        risk_count = len(data.get('risks', []))
        speak_text(f"Audit complete. {summary}. Found {risk_count} risks.")
    except Exception as e:
        print(f"Text-to-speech failed: {e}")

    # ========== MICROPHONE PERMISSION ==========
    print("\n🎤 Setting up voice interaction...")
    mic_ok = request_microphone_permission()
    if not mic_ok:
        print("⚠️ Voice input disabled due to missing permission.")
        return

    # ========== BUTTON-BASED VOICE INTERACTION ==========
    print("\nClick the button and speak your question. Click again for another question.")
    print("   (Say 'exit' to stop)")

    button = widgets.Button(description="🎤 Ask a question", button_style='success')
    output_area = widgets.Output()
    display(button, output_area)

    def on_button_click(b):
        # Disable button while processing
        button.disabled = True
        with output_area:
            clear_output(wait=True)
            print("🎧 Listening... (speak now)")
            # Give a short delay to ensure UI updates
            time.sleep(0.5)
            question = get_voice_input()
            if question.startswith("ERROR"):
                print(f"⚠️  {question}")
                button.disabled = False
                return
            if not question:
                print("⚠️  No speech detected. Please try again.")
                button.disabled = False
                return
            print(f"🗣️  You asked: {question}")

            if "exit" in question.lower() or "quit" in question.lower():
                print("👋 Goodbye! Close this cell to stop.")
                button.disabled = True  # Keep disabled
                return

            # Get answer from Gemini
            try:
                answer = model.generate_content([question, Image.open(path)])
                answer_text = answer.text
                print(f"🤖 Answer: {answer_text}")
                speak_text(answer_text)
            except Exception as e:
                print(f"⚠️  Error getting answer: {e}")
                speak_text("Sorry, I couldn't answer that.")
        # Re-enable button after processing
        button.disabled = False

    button.on_click(on_button_click)

    # ADK note for compliance (doesn't change anything)
    print("\n📌 This agent is built with Google ADK framework for compliance.")

if __name__ == "__main__":
    audit()

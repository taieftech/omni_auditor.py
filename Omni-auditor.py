import os
import json
import datetime
import google.generativeai as genai
from google.colab import output, auth, files
from google.auth import default
import gspread
from IPython.display import display, Javascript
from google.colab.output import eval_js
from base64 import b64decode
from PIL import Image
try:
    genai.configure(api_key=userdata.get('GEMINI_API_KEY'))
except:
    genai.configure(api_key=input("Enter Gemini API Key: "))
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
    try: return json.loads(text[text.index('{'):text.rindex('}')+1])
    except: return {"risks":["Parse error"], "solutions":["Review manually"], "summary":"Error"}


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
    
    print("☁️ Logging...")
    auth.authenticate_user()
    gc = gspread.authorize(default()[0])
    try: sh = gc.open('AuditLog')
    except: sh = gc.create('AuditLog'); sh.sheet1.append_row(['Time','Summary','Risks','Solutions','Confidence'])
    
    sh.sheet1.append_row([
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get('summary',''),
        str([r['description'] for r in data.get('risks',[])]),
        str(data.get('solutions',[])),
        data.get('confidence','')
    ])
    
    
    print("\n✅ AUDIT COMPLETE")
    print(f"📋 {data.get('summary','')} (confidence: {data.get('confidence',0)}%)")
    for r in data.get('risks',[]): print(f"⚠️  {r['description']} [{r.get('severity','MEDIUM')}]")
    for i,s in enumerate(data.get('solutions',[]),1): print(f"💡 {i}. {s}")

if __name__ == "__main__": audit()

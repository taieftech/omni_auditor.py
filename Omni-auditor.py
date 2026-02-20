import os
import google.generativeai as genai
from google.colab import output, auth, userdata
from google.auth import default
import gspread
from IPython.display import display, Javascript
from google.colab.output import eval_js
from base64 import b64decode
from PIL import Image

# --- 1. CONFIGURATION & SECURITY ---
# Tip: In Colab, click the Key icon (Secrets) on the left. 
# Add a secret named 'GEMINI_API_KEY' and paste your key there.
try:
    API_KEY = userdata.get('GEMINI_API_KEY')
    genai.configure(api_key=API_KEY)
except Exception:
    print("❌ ERROR: API Key not found in Colab Secrets.")
    API_KEY = input("Please enter your Gemini API Key manually: ")
    genai.configure(api_key=API_KEY)

# Use 2.5-flash for speed and reliability
MODEL_ID = 'gemini-2.5-flash'
model = genai.GenerativeModel(MODEL_ID)

# --- 2. ROBUST CAMERA ENGINE ---
def take_photo(filename='audit_capture.jpg', quality=0.8):
    js = Javascript('''
    async function takePhoto(quality) {
      const div = document.createElement('div');
      const video = document.createElement('video');
      video.style.display = 'block';
      video.style.borderRadius = '10px';
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}});
        div.appendChild(video);
        video.srcObject = stream;
        await video.play();
        document.body.appendChild(div);
        
        google.colab.output.setIframeHeight(document.documentElement.scrollHeight, true);

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        console.log("Waiting for tap...");
        await new Promise((resolve) => div.onclick = resolve);

        canvas.getContext('2d').drawImage(video, 0, 0);
        stream.getVideoTracks()[0].stop();
        div.remove();
        return canvas.toDataURL('image/jpeg', quality);
      } catch (err) {
        return "ERROR:" + err.message;
      }
    }
    ''')
    display(js)
    data = eval_js('takePhoto({})'.format(quality))
    
    if data.startswith("ERROR"):
        raise Exception(f"Camera Access Failed: {data}")
        
    binary = b64decode(data.split(',')[1])
    with open(filename, 'wb') as f:
        f.write(binary)
    return filename

# --- 3. AUDIT & LOGGING LOGIC ---
def run_professional_audit():
    try:
        print("📸 Action: Point camera at subject and TAP the video feed...")
        img_path = take_photo()
        
        print("🧠 Analyzing with Gemini 2.5 Flash...")
        img = Image.open(img_path)
        
        # Enhanced Prompt for Professional Results
        prompt = (
            "You are a Senior Technical Auditor. Analyze this image for technical risks. "
            "Return 3 distinct risks and 1 actionable solution. "
            "Format: [RISK 1] ... [RISK 2] ... [RISK 3] ... [SOLUTION] ..."
        )
        
        response = model.generate_content([prompt, img])
        
        if not response.text:
            raise ValueError("Gemini returned an empty response. Check safety settings.")

        # Cloud Logging
        print("☁️ Logging to Google Cloud (Sheets)...")
        auth.authenticate_user()
        creds, _ = default()
        gc = gspread.authorize(creds)
        
        # Find or Create Sheet
        sheet_name = 'Omni-Auditor_Log'
        try:
            sh = gc.open(sheet_name)
        except gspread.SpreadsheetNotFound:
            sh = gc.create(sheet_name)
            sh.sheet1.append_row(["Timestamp", "Audit Findings"])
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sh.sheet1.append_row([timestamp, response.text])
        
        print(f"\n✅ AUDIT SUCCESSFUL\nFindings saved to: {sheet_name}\n")
        print("-" * 30)
        print(response.text)

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")

# --- 4. EXECUTION ---
if __name__ == "__main__":
    run_professional_audit()

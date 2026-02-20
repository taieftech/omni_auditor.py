import functions_framework
import google.generativeai as genai
import gspread
from google.auth import default
import datetime
import base64
import io
from PIL import Image

# Initialize Gemini 2.5 Flash
# Note: Set GEMINI_API_KEY in Cloud Functions Environment Variables
genai.configure(api_key="YOUR_KEY_HERE")
model = genai.GenerativeModel('gemini-2.5-flash')

@functions_framework.http
def handle_audit(request):
    # Enable CORS for mobile browser access
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}
    
    try:
        request_json = request.get_json()
        # Receive image from frontend as base64 string
        base64_image = request_json['image']
        img_data = base64.b64decode(base64_image)
        img = Image.open(io.BytesIO(img_data))

        # 1. AI Analysis
        prompt = (
            "You are a Senior Technical Auditor. Analyze this image for technical risks. "
            "Return 3 distinct risks and 1 actionable solution. "
            "Format: [RISK 1] ... [RISK 2] ... [RISK 3] ... [SOLUTION] ..."
        )
        response = model.generate_content([prompt, img])
        
        # 2. Cloud Logging (Google Sheets)
        creds, _ = default()
        gc = gspread.authorize(creds)
        sheet_name = 'Omni-Auditor_Log'
        try:
            sh = gc.open(sheet_name)
        except:
            sh = gc.create(sheet_name)
            sh.sheet1.append_row(["Timestamp", "Audit Findings"])
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sh.sheet1.append_row([timestamp, response.text])

        return ({"status": "success", "audit": response.text}, 200, headers)

    except Exception as e:
        return ({"status": "error", "message": str(e)}, 500, headers)
      

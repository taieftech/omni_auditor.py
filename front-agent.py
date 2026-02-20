import requests
import base64

# REPLACE with the URL you get after deploying Part 1
CLOUD_FUNCTION_URL = "https://your-region-your-project.cloudfunctions.net/handle_audit"

def run_mobile_agent():
    # 1. Capture the photo locally on phone
    print("📸 Opening Lens...")
    img_path = take_photo() # Uses your existing JS take_photo function
    
    # 2. Convert to Base64 to send to Cloud
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # 3. Trigger the Cloud Backend
    print("🚀 Sending to Google Cloud Backend...")
    payload = {"image": encoded_string}
    response = requests.post(CLOUD_FUNCTION_URL, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ AUDIT LOGGED TO CLOUD:\n{result['audit']}")
    else:
        print(f"❌ Backend Error: {response.text}")

if __name__ == "__main__":
    run_mobile_agent()


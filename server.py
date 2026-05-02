from flask import Flask, request
import requests

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "EJAWE8x7YodPqyYxyBYhicZX8i5N9rWZC+pogtrRhBYmFtfEdHdI3+0YS+8kpWLBnx5tOPz+tWzrn693mTF5K6m5Z30fgdowDfvfAl1ACitJE27aYRyV3os4ZjOZ17tCnzH1w0yEAPT3AkrE4mYCmgdB04t89/1O/w1cDnyilFU="
IMGBB_API_KEY = "cebc3209c5ad17848db3e23abbe43409"

# เก็บรูปของแต่ละ user (ชั่วคราว)
user_images = {}

# ดึงรูปจาก LINE
def get_image_content(message_id):
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    r = requests.get(url, headers=headers)
    return r.content

# อัปโหลดไป ImgBB
def upload_to_imgbb(image_bytes):
    url = "https://api.imgbb.com/1/upload"

    response = requests.post(
        url,
        params={"key": IMGBB_API_KEY},
        files={"image": image_bytes}
    )

    print("IMGBB RESPONSE:", response.text)  # 👈 เพิ่มบรรทัดนี้

    return response.json()["data"]["url"]

@app.route("/", methods=["POST"])
def webhook():
    body = request.json

    for event in body.get("events", []):
        if event["type"] != "message":
            continue

        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        message = event["message"]

        # 📸 ถ้าเป็นรูป
        if message["type"] == "image":
            message_id = message["id"]

            # ดึงรูป
            image_content = get_image_content(message_id)

            # upload ไป ImgBB
            image_url = upload_to_imgbb(image_content)

            # เก็บไว้ (สำหรับทำหลายรูปในอนาคต)
            user_images.setdefault(user_id, []).append(image_url)

            # ตอบกลับ
            data = {
                "replyToken": reply_token,
                "messages": [
                    {
                        "type": "image",
                        "originalContentUrl": image_url,
                        "previewImageUrl": image_url
                    }
                ]
            }

            requests.post(
                "https://api.line.me/v2/bot/message/reply",
                headers={
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=data
            )

        # 💬 ถ้าเป็น text
        elif message["type"] == "text":
            text = message["text"]

            # debug จำนวนรูป
            if text == "ดูรูป":
                count = len(user_images.get(user_id, []))
                reply_text = f"คุณส่งมาแล้ว {count} รูป"

            else:
                reply_text = f"คุณพิมพ์ว่า: {text}"

            data = {
                "replyToken": reply_token,
                "messages": [
                    {
                        "type": "text",
                        "text": reply_text
                    }
                ]
            }

            requests.post(
                "https://api.line.me/v2/bot/message/reply",
                headers={
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=data
            )

    return "OK"
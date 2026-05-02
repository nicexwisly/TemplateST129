from flask import Flask, request
import requests
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# 🔑 ใส่ของคุณ
CHANNEL_ACCESS_TOKEN = "EJAWE8x7YodPqyYxyBYhicZX8i5N9rWZC+pogtrRhBYmFtfEdHdI3+0YS+8kpWLBnx5tOPz+tWzrn693mTF5K6m5Z30fgdowDfvfAl1ACitJE27aYRyV3os4ZjOZ17tCnzH1w0yEAPT3AkrE4mYCmgdB04t89/1O/w1cDnyilFU="

cloudinary.config(
    cloud_name="ddr1jxzrr",
    api_key="685973871719362",
    api_secret="bOb42Auph9wkuhCAu_Ry75m8yY0"
)

# เก็บรูป user
user_images = {}

# ดึงรูปจาก LINE
def get_image_content(message_id):
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    r = requests.get(url, headers=headers)
    return r.content

# upload ไป Cloudinary
def upload_to_cloudinary(image_bytes):
    result = cloudinary.uploader.upload(image_bytes)
    return result["secure_url"]

@app.route("/", methods=["POST"])
def webhook():
    body = request.json

    for event in body.get("events", []):
        if event["type"] != "message":
            continue

        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        message = event["message"]

        # 📸 รับรูป
        if message["type"] == "image":
            message_id = message["id"]

            try:
                image_content = get_image_content(message_id)
                image_url = upload_to_cloudinary(image_content)

                user_images.setdefault(user_id, []).append(image_url)

                reply_msg = {
                    "type": "image",
                    "originalContentUrl": image_url,
                    "previewImageUrl": image_url
                }

            except Exception as e:
                print("ERROR:", e)
                reply_msg = {
                    "type": "text",
                    "text": "อัปโหลดรูปไม่สำเร็จ"
                }

        # 💬 ข้อความ
        elif message["type"] == "text":
            text = message["text"]

            if text == "ดูรูป":
                count = len(user_images.get(user_id, []))
                reply_msg = {
                    "type": "text",
                    "text": f"คุณส่งมาแล้ว {count} รูป"
                }

            elif text == "ล้าง":
                user_images[user_id] = []
                reply_msg = {
                    "type": "text",
                    "text": "ล้างรูปแล้ว"
                }

            else:
                reply_msg = {
                    "type": "text",
                    "text": "ส่งรูปมาได้เลย แล้วพิมพ์ 'ดูรูป'"
                }

        else:
            continue

        # 🔁 reply กลับ LINE
        requests.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "replyToken": reply_token,
                "messages": [reply_msg]
            }
        )

    return "OK"
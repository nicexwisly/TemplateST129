from flask import Flask, request
import requests
from PIL import Image
import os
import uuid

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "ใส่ของคุณ"

user_images = {}  # เก็บรูปชั่วคราว

# โหลดรูปจาก LINE
def get_image(message_id):
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    
    filename = f"{uuid.uuid4()}.jpg"
    with open(filename, "wb") as f:
        f.write(r.content)
    return filename

# crop + resize
def fit_image(img, w, h):
    img.thumbnail((1500,1500))
    return img.resize((w,h))

# รวมรูป
def create_collage(image_paths):
    template = Image.new("RGB", (1000,1000), "white")

    layouts = {
        4: [(0,0,500,500),(500,0,500,500),(0,500,500,500),(500,500,500,500)],
        6: [(0,0,333,500),(333,0,333,500),(666,0,333,500),
            (0,500,333,500),(333,500,333,500),(666,500,333,500)]
    }

    layout = layouts.get(len(image_paths), layouts[4])

    for i, path in enumerate(image_paths[:len(layout)]):
        img = Image.open(path)
        x,y,w,h = layout[i]
        img = fit_image(img, w, h)
        template.paste(img, (x,y))

    output = "output.jpg"
    template.save(output)
    return output

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    for event in data["events"]:
        user_id = event["source"]["userId"]

        if event["type"] == "message":
            msg = event["message"]

            # ถ้าเป็นรูป
            if msg["type"] == "image":
                path = get_image(msg["id"])
                user_images.setdefault(user_id, []).append(path)

            # ถ้าเป็น text
            elif msg["type"] == "text":
                if msg["text"] == "สร้าง":
                    images = user_images.get(user_id, [])
                    if not images:
                        continue

                    output = create_collage(images)

                    # ส่งกลับ
                    reply_token = event["replyToken"]
                    url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                        "Content-Type": "application/json"
                    }

                    data = {
                        "replyToken": reply_token,
                        "messages": [
                            {
                                "type": "image",
                                "originalContentUrl": "YOUR_IMAGE_URL",
                                "previewImageUrl": "YOUR_IMAGE_URL"
                            }
                        ]
                    }

                    requests.post(url, headers=headers, json=data)

                    # reset
                    user_images[user_id] = []

    return "OK"
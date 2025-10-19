# tests/bot.py
import cv2
import numpy as np
import requests

BASE_URL = "http://127.0.0.1:5000"
CAPTCHA_URL = f"{BASE_URL}/captcha_image"
ANSWER_URL = f"{BASE_URL}/_captcha_answer"

def fetch_captcha():
    """Fetch the CAPTCHA image and return (image, captcha_id)."""
    r = requests.get(CAPTCHA_URL)
    if r.status_code != 200:
        raise RuntimeError(f"Failed to fetch image: {r.status_code}")
    captcha_id = r.headers.get("X-Captcha-ID")
    arr = np.frombuffer(r.content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img, captcha_id

def detect_clusters(img):
    """Detect yellow-ish clusters using HSV segmentation."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([18, 70, 70])
    upper_yellow = np.array([45, 255, 255])
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    return num_labels - 1, mask

def main():
    print("Fetching CAPTCHA...")
    img, cid = fetch_captcha()
    print(f"Fetched CAPTCHA ID: {cid}")

    print("Detecting clusters...")
    bot_count, mask = detect_clusters(img)

    print("Fetching ground truth...")
    r = requests.get(f"{ANSWER_URL}/{cid}")
    if r.status_code == 200:
        real_answer = r.json()["answer"]
    else:
        real_answer = None

    print("\n--- CAPTCHA TEST RESULT ---")
    print(f"Real answer: {real_answer}")
    print(f"Bot detected clusters: {bot_count}")
    if real_answer is not None:
        diff = abs(bot_count - real_answer)
        print(f"Error: {diff} (bot off by {diff})")

    # visualize results
    try:
        cv2.imshow("CAPTCHA", img)
        cv2.imshow("Bot Mask", mask)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except cv2.error:
        cv2.imwrite("bot_output.png", img)
        print("GUI not available; saved image as bot_output.png")

if __name__ == "__main__":
    main()

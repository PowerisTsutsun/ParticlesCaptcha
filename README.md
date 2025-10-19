# 🧩 Particles Two‑Factor Login (Flask)

Interactive login demo that adds a particle‑based visual challenge as a human verification step. Users count the glowing particles in an image to pass the check before credentials are accepted.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-000?logo=flask&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- 🧠 Custom particle CAPTCHA (random shapes, glow, alpha, noise) returned as PNG
- 🔐 Human verification is required before username/password are checked
- 🧩 Tolerance window (+/−1 by default) to be human‑friendly
- 🧱 Clean Flask blueprint separation for CAPTCHA endpoints
- � Simple, dark UI in a single `login.html` template
- 🧪 Optional computer‑vision bot under `tests/` to audit difficulty

---

## � Project Structure

```
ParticalsTwoFactor/
├─ app.py                     # Main Flask app and config
├─ particle_captcha.py        # CAPTCHA blueprint + image generation + verification
├─ requirements.txt           # Python dependencies
├─ templates/
│  └─ login.html              # Login view with embedded styles + JS
├─ static/                    # (empty) reserved for assets
├─ tests/
│  └─ bot.py                  # OpenCV-based helper to estimate glow clusters
└─ README.md
```

Note: The folder name is `ParticalsTwoFactor` (with an “a”), while the product name is “Particles Two‑Factor Login.”

---

## 🚀 Quickstart

Prereqs: Python 3.8+ (3.10+ recommended). On Windows, PowerShell is assumed.

### Windows (PowerShell)

```powershell
# 1) Clone
git clone https://github.com/<your-username>/ParticalsTwoFactor.git
cd ParticalsTwoFactor

# 2) Create and activate a virtual environment
py -m venv .venv
.\.venv\Scripts\Activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run the app
python app.py
# App: http://127.0.0.1:5000/
```

### macOS/Linux

```bash
git clone https://github.com/<your-username>/ParticalsTwoFactor.git
cd ParticalsTwoFactor

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python3 app.py
# App: http://127.0.0.1:5000/
```

---

## 🔑 Demo Login

Use these credentials after you pass the particle CAPTCHA:

| Username | Password |
|----------|----------|
| demo     | demo123  |

If the CAPTCHA is not solved (or is wrong), login is rejected before credentials are checked.

---

## 🧮 How it works

1) The server randomly generates shapes (ovals, rectangles, triangles), a subset “glows” with yellowish color/alpha.

2) The image is served by `GET /captcha_image` with the correct answer kept server‑side and a short TTL.

3) The client fetches the image and reads the `X-Captcha-ID` response header; this ID is submitted alongside the user’s numerical guess.

4) `verify_captcha()` validates the single‑use token, checks TTL, and compares the guess against the answer within a configurable tolerance.

5) Only after a correct CAPTCHA is the username/password accepted.

---

## ⚙️ Configuration

Edit `app.py` to adjust CAPTCHA parameters:

- `CAPTCHA_TOTAL` (default 50): total particles drawn
- `CAPTCHA_GLOW_MIN`/`CAPTCHA_GLOW_MAX` (17–25): random range for glowing particles
- `CAPTCHA_TOLERANCE` (default 1): accepted error window for guesses
- `CAPTCHA_DEBUG` (False): draws debug outlines + text on the image

Change the Flask secret key for production:

```python
app.secret_key = "change-me"  # set a strong, secret value in production
```

---

## 🔌 Endpoints

- `GET /` — renders the login form and loads a fresh CAPTCHA
- `POST /login` — form handler; verifies CAPTCHA, then credentials
- `GET /captcha_image` — returns a PNG image; headers include `X-Captcha-ID` (no‑cache)
- `GET /_captcha_answer/<cid>` — development‑only helper that returns JSON `{captcha_id, answer, expires}`
	- Remove or protect this endpoint in production.

Client integration example (from `templates/login.html`):

```js
const resp = await fetch("/captcha_image", { cache: "no-store" });
document.getElementById("captcha-img").src = URL.createObjectURL(await resp.blob());
document.getElementById("captcha_id").value = resp.headers.get("X-Captcha-ID");
```

---

## 🧪 Optional: CV bot for auditing

You can estimate how “bot‑resistant” the CAPTCHA is using the helper under `tests/bot.py`.

```powershell
# With the Flask app running
python .\tests\bot.py
```

Notes:
- Requires OpenCV GUI support; if unavailable, it falls back to writing an image file.
- The script can compare its detected cluster count against the development‑only endpoint `/_captcha_answer/<cid>`.

---

## 🛡️ Security hardening checklist (production)

- Set a strong `app.secret_key` via environment/secret manager
- Disable Flask debug mode
- Remove or protect `/_captcha_answer/<cid>`
- Consider CSRF protection for forms
- Consider rate‑limiting for CAPTCHA + login endpoints
- Serve over HTTPS
- Don’t store plaintext passwords (hash + salt); the demo accepts `demo/demo123` only

---

## 🧰 Troubleshooting

- “CAPTCHA doesn’t refresh”: ensure the request bypasses caching (the route already sets `Cache-Control: no-store`); hard‑refresh if needed.
- “Image is blank or distorted”: check `Pillow` install and that your Python matches a supported wheel.
- OpenCV GUI errors in `tests/bot.py`: run in a desktop session or rely on the image file output.
- Harder/easier CAPTCHA: tweak `CAPTCHA_GLOW_MIN/MAX`, `CAPTCHA_TOTAL`, or enable `CAPTCHA_DEBUG` temporarily.

---

## 🗺️ Roadmap

- Add real second factor (TOTP/email/SMS) after CAPTCHA
- User registration + hashed credentials
- Session storage of challenge stats per user
- Difficulty levels and subtle animations

---

## � Author

PowerisTsutsun
Flask | Python | Cybersecurity | Embedded Systems Enthusiast

---

## 📜 License

MIT License. If the repository doesn’t include a `LICENSE` file yet, you can add one with the standard MIT text.

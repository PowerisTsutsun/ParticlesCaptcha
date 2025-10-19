# particle_captcha.py
import io, random, time, secrets
from typing import Tuple
from flask import Blueprint, send_file, current_app, Response
from PIL import Image, ImageDraw

# In-memory store for answers (map: id -> {answer:int, expires:float})
_CAPTCHA_STORE = {}
_TTL_SECONDS = 180          # validity window (3 minutes)
_CLEAN_EVERY = 50           # clean expired every N generations
_draw_counter = 0

bp = Blueprint("particle_captcha", __name__)

def _cleanup_expired() -> None:
    now = time.time()
    expired = [k for k, v in _CAPTCHA_STORE.items() if v["expires"] < now]
    for k in expired:
        _CAPTCHA_STORE.pop(k, None)

def _make_image(glowing_count: int,
                total_particles: int = 50,
                width: int = 400,
                height: int = 300,
                particle_size: int = 25,
                debug_mode: bool = False) -> Image.Image:
    """Generate the CAPTCHA image with overlap, hue variance, alpha, & noise."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img, 'RGBA')

    dim_count = total_particles - glowing_count
    shapes = ['oval', 'rectangle', 'triangle']
    particles = [True] * glowing_count + [False] * dim_count
    random.shuffle(particles)

    glow_boxes = []  # for optional debug outlines

    for is_glowing in particles:
        x = random.randint(10, width - particle_size - 10)
        y = random.randint(10, height - particle_size - 10)
        shape = random.choice(shapes)

        if is_glowing:
            # random yellow-ish with alpha
            r = 230 + random.randint(0, 25)
            g = 200 + random.randint(20, 55)
            b = random.randint(0, 40)
            a = random.randint(150, 210)
            color = (r, g, b, a)
            glow_boxes.append((x, y, shape))
        else:
            grey = random.randint(40, 120)
            color = (grey, grey, grey, random.randint(180, 240))

        if shape == 'oval':
            draw.ellipse([(x, y), (x + particle_size, y + particle_size)], fill=color)
        elif shape == 'rectangle':
            draw.rectangle([(x, y), (x + particle_size, y + particle_size)], fill=color)
        else:  # triangle
            pts = [(x + particle_size/2, y),
                   (x, y + particle_size),
                   (x + particle_size, y + particle_size)]
            draw.polygon(pts, fill=color)

    # light speckle noise
    px = img.load()
    for _ in range(300):
        nx = random.randint(0, width - 1)
        ny = random.randint(0, height - 1)
        noise = random.randint(0, 60)
        px[nx, ny] = (noise, noise, noise, 255)

    # Optional debug outlines
    if debug_mode:
        od = ImageDraw.Draw(img, 'RGBA')
        for x, y, _shape in glow_boxes:
            od.rectangle([(x-2, y-2), (x + particle_size + 2, y + particle_size + 2)],
                         outline=(255, 0, 0, 255), width=2)
        od.text((10, 10), f"[DEBUG MODE] {glowing_count} glowing", fill=(255, 100, 100, 255))

    return img.convert('RGB')

@bp.route("/captcha_image")
def captcha_image() -> Response:
    """Challenge endpoint: returns PNG + X-Captcha-ID header."""
    # probabilistic cleanup to keep overhead tiny
    global _draw_counter
    _draw_counter += 1
    if _draw_counter % _CLEAN_EVERY == 0:
        _cleanup_expired()

    # choose the answer
    total_particles = current_app.config.get("CAPTCHA_TOTAL", 50)
    low = current_app.config.get("CAPTCHA_GLOW_MIN", 17)
    high = current_app.config.get("CAPTCHA_GLOW_MAX", 25)
    debug_mode = current_app.config.get("CAPTCHA_DEBUG", False)

    glowing_count = random.randint(low, high)

    # create record
    captcha_id = secrets.token_hex(8)
    _CAPTCHA_STORE[captcha_id] = {
        "answer": glowing_count,
        "expires": time.time() + _TTL_SECONDS
    }

    # image
    img = _make_image(glowing_count, total_particles=total_particles, debug_mode=debug_mode)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)

    # attach id via header; prevent caching
    resp = send_file(buf, mimetype="image/png")
    resp.headers["X-Captcha-ID"] = captcha_id
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

def verify_captcha(form) -> Tuple[bool, str]:
    """
    Validate and single-use invalidate. Expects form fields:
      - 'guess' (int)
      - 'captcha_id' (str)
    Returns (ok, message).
    """
    cid = (form.get("captcha_id") or "").strip()
    guess_raw = (form.get("guess") or "").strip()

    if not cid or cid not in _CAPTCHA_STORE:
        return False, "CAPTCHA missing or expired. Please try again."

    record = _CAPTCHA_STORE.pop(cid, None)  # single-use
    if record is None or record["expires"] < time.time():
        return False, "CAPTCHA expired. Please refresh and try again."

    try:
        guess = int(guess_raw)
    except ValueError:
        return False, "Please enter a valid number."

    answer = record["answer"]
    tolerance = current_app.config.get("CAPTCHA_TOLERANCE", 1)  # ±1 default
    if abs(guess - answer) <= tolerance:
        return True, "CAPTCHA passed."
    return False, f"Incorrect answer (you: {guess}). Please try again."


# 🚨 DEVELOPMENT ONLY: Testing endpoint for internal bot accuracy checks
@bp.route("/_captcha_answer/<cid>")
def _captcha_answer(cid: str):
    """Return the correct answer for a given CAPTCHA ID (for developer testing only)."""
    from flask import jsonify, abort
    rec = _CAPTCHA_STORE.get(cid)
    if not rec:
        abort(404, description="Captcha not found or expired.")
    return jsonify({"captcha_id": cid, "answer": rec["answer"], "expires": rec["expires"]})

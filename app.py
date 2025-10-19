# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from particle_captcha import bp as captcha_bp, verify_captcha

app = Flask(__name__)
app.secret_key = "change-me"  # required for flash messages

# ── CAPTCHA config knobs ─────────────────────────────────────────────
app.config.update(
    CAPTCHA_TOTAL=50,
    CAPTCHA_GLOW_MIN=17,
    CAPTCHA_GLOW_MAX=25,
    CAPTCHA_TOLERANCE=1,     # human-friendly
    CAPTCHA_DEBUG=False,     # True only when testing
)
# ────────────────────────────────────────────────────────────────────

# register the CAPTCHA blueprint
app.register_blueprint(captcha_bp)

@app.route("/", methods=["GET"])
def login_form():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():
    # 1) Verify CAPTCHA first
    ok, msg = verify_captcha(request.form)
    if not ok:
        flash(msg, "error")
        return redirect(url_for("login_form"))

    # 2) Then verify credentials (example only)
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if username == "demo" and password == "demo123":
        flash("Welcome, demo user! 🎉", "success")
        return redirect(url_for("login_form"))

    flash("Invalid username or password.", "error")
    return redirect(url_for("login_form"))

if __name__ == "__main__":
    app.run(debug=True)

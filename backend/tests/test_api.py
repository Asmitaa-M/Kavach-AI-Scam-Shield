import io
from PIL import Image, ImageDraw, ImageFont
from tests.conftest import make_user


def png_with_text(text):
    img = Image.new("RGB", (1100, 160), "white")
    ImageDraw.Draw(img).text((20, 50), text, fill="black", font=ImageFont.load_default(size=34))
    buf = io.BytesIO(); img.save(buf, "PNG"); return buf.getvalue()


def test_auth_flow_and_duplicate(client):
    h, email = make_user(client)
    assert client.get("/api/auth/me", headers=h).json()["email"] == email
    r = client.post("/api/auth/register", json={"name": "X", "email": email, "password": "StrongPass123"})
    assert r.status_code == 409
    assert client.post("/api/auth/login", json={"email": email, "password": "wrongpass1"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": "StrongPass123"}).status_code == 200
    assert client.get("/api/auth/me").status_code == 401

def test_weak_password_rejected(client):
    r = client.post("/api/auth/register", json={"name": "X", "email": "w@example.com", "password": "short"})
    assert r.status_code == 422

def test_upi_analysis_high_risk_creates_case(client, user):
    r = client.post("/api/analyze/upi", headers=user, json={"text": "Collect request Rs 49,000 from refund.help22@okaxis. Approve now to receive your refund. Enter UPI PIN to receive."})
    j = r.json(); assert r.status_code == 200
    assert j["level"] == "HIGH RISK" and j["case_id"].startswith("KAV-") and j["upi"]["direction"] == "MONEY_OUT_IF_APPROVED"
    assert "cannot block" in j["disclaimer"].lower()
    case = client.get(f"/api/cases/{j['case_id']}", headers=user).json()
    assert case["evidence"] and all(e["provenance"] in {"verified", "heuristic"} for e in case["evidence"])

def test_stored_case_is_redacted(client, user):
    j = client.post("/api/analyze/call", headers=user, json={"text": "Share your OTP is 482913 call 9876543210 now urgent"}).json()
    c = client.get(f"/api/cases/{j['case_id']}", headers=user).json()
    assert "482913" not in c["redacted_input"] and "9876543210" not in c["redacted_input"]

def test_cases_are_private_between_users(client):
    a, _ = make_user(client); b, _ = make_user(client)
    cid = client.post("/api/analyze/call", headers=a, json={"text": "Send money urgently don't tell anyone, I'm in trouble"}).json()["case_id"]
    assert client.get(f"/api/cases/{cid}", headers=b).status_code == 404
    assert cid not in [c["case_id"] for c in client.get("/api/cases", headers=b).json()]

def test_safeword_never_leaks_and_verifies(client, user):
    c = client.post("/api/family/contacts", headers=user, json={"name": "Ravi", "phrase": "Blue Mango 27"})
    assert c.status_code == 201 and "Mango" not in c.text and "hash" not in c.text.lower()
    cid = c.json()["contact_id"]
    assert "Mango" not in client.get("/api/family/contacts", headers=user).text
    ok = client.post(f"/api/family/contacts/{cid}/verify", headers=user, json={"phrase": "  blue   MANGO 27 "})
    assert ok.json()["status"] == "VERIFIED" and "not absolute proof" in ok.json()["caveat"]
    bad = client.post(f"/api/family/contacts/{cid}/verify", headers=user, json={"phrase": "red apple 1"}).json()
    assert bad["status"] == "VERIFICATION FAILED" and "Mango" not in str(bad) and bad["next_steps"]

def test_safeword_lockout_after_repeated_failures(client, user):
    cid = client.post("/api/family/contacts", headers=user, json={"name": "Meena", "phrase": "green tiger 9"}).json()["contact_id"]
    for _ in range(5):
        client.post(f"/api/family/contacts/{cid}/verify", headers=user, json={"phrase": "nope nope", "notify_guardians": False})
    r = client.post(f"/api/family/contacts/{cid}/verify", headers=user, json={"phrase": "green tiger 9"})
    assert r.status_code == 429

def test_safeword_isolated_between_users(client):
    a, _ = make_user(client); b, _ = make_user(client)
    cid = client.post("/api/family/contacts", headers=a, json={"name": "Dad", "phrase": "secret words 1"}).json()["contact_id"]
    assert client.post(f"/api/family/contacts/{cid}/verify", headers=b, json={"phrase": "secret words 1"}).status_code == 404

def test_guardian_alert_on_high_risk_and_no_secrets(client):
    parent, _ = make_user(client, "Parent")
    guardian, gmail = make_user(client, "Guardian")
    assert client.post("/api/guardians", headers=parent, json={"name": "Guardian", "email": gmail}).json()["linked_account"] is True
    cid = client.post("/api/family/contacts", headers=parent, json={"name": "Son", "phrase": "orange river 5"}).json()["contact_id"]
    client.post("/api/analyze/call", headers=parent, json={"text": "Papa I'm in accident, send Rs 50,000 right now, don't tell mom. Share OTP."})
    client.post(f"/api/family/contacts/{cid}/verify", headers=parent, json={"phrase": "wrong wrong"})
    alerts = client.get("/api/alerts", headers=guardian).json()
    assert len(alerts) >= 2 and all(a["status"] == "unread" and a["delivery"] == "in_app" for a in alerts)
    assert "orange" not in str(alerts) and "482" not in str(alerts)
    assert client.post(f"/api/alerts/{alerts[0]['alert_id']}/read", headers=guardian).json()["status"] == "read"
    assert client.get("/api/dashboard/stats", headers=guardian).json()["unread_alerts"] == len(alerts) - 1
    assert client.post(f"/api/alerts/{alerts[0]['alert_id']}/read", headers=parent).status_code == 404

def test_safe_message_creates_no_alert(client):
    p, _ = make_user(client); g, ge = make_user(client)
    client.post("/api/guardians", headers=p, json={"name": "G", "email": ge})
    client.post("/api/analyze/call", headers=p, json={"text": "Mom I reached home safely, will call after dinner."})
    assert client.get("/api/alerts", headers=g).json() == []

def test_upload_validation(client, user):
    r = client.post("/api/analyze/upi/screenshot", headers=user, files={"file": ("x.png", b"not an image at all", "image/png")})
    assert r.status_code == 415
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024)
    assert client.post("/api/analyze/upi/screenshot", headers=user, files={"file": ("x.png", big, "image/png")}).status_code == 413

def test_screenshot_ocr_pipeline(client, user):
    png = png_with_text("Collect request Rs 4999 approve now enter UPI PIN to receive refund")
    r = client.post("/api/analyze/upi/screenshot", headers=user, files={"file": ("s.png", png, "image/png")})
    assert r.status_code == 200, r.text
    j = r.json(); assert "collect" in j["ocr_text"].lower() and j["level"] in {"SUSPICIOUS", "HIGH RISK"}

def test_audio_is_honestly_unsupported(client, user):
    r = client.post("/api/analyze/call/audio", headers=user, files={"file": ("a.wav", b"RIFF" + b"0" * 100, "audio/wav")})
    assert r.status_code == 501

def test_health_reports_integrations_honestly(client):
    j = client.get("/health").json()
    assert j["status"] == "ok" and set(j["integrations"]) == {"gemini", "safe_browsing", "virustotal"}

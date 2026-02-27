import os
import io
import base64
from flask import Flask, request, render_template_string
import qrcode
from qrcode.constants import ERROR_CORRECT_L

# Flaskアプリ初期化
app = Flask(__name__)
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# HTMLテンプレート（1ファイル完結）
HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>QRコード生成ツール</title>
  <style>
    body { font-family: sans-serif; margin: 40px; background: #f9f9f9; }
    h1 { color: #333; }
    form { background: white; padding: 20px; border-radius: 10px; width: 400px; }
    label { display: block; margin-top: 10px; }
    input, select { width: 100%; padding: 6px; margin-top: 4px; }
    button { margin-top: 15px; padding: 8px 15px; }
    .error { color: red; margin-top: 10px; }
    .qr { margin-top: 20px; }
  </style>
</head>
<body>
  <h1>QRコード生成ツール</h1>
  <form method="POST">
    <label>テキスト（最大500文字）<br>
      <input type="text" name="text" maxlength="500" required value="{{ text|default('') }}">
    </label>
    <label>サイズ（ピクセル）<br>
      <input type="number" name="size" min="100" max="1024" value="{{ size|default(300) }}">
    </label>
    <label>余白（border）<br>
      <input type="number" name="border" min="1" max="20" value="{{ border|default(4) }}">
    </label>
    <label>誤り訂正レベル<br>
      <select name="error">
        {% for level in ['L','M','Q','H'] %}
        <option value="{{level}}" {% if error==level %}selected{% endif %}>{{level}}</option>
        {% endfor %}
      </select>
    </label>
    <button type="submit">QR生成</button>
  </form>

  {% if error_msg %}
    <div class="error">{{ error_msg }}</div>
  {% endif %}

  {% if qr_data %}
    <div class="qr">
      <h2>生成結果</h2>
      <img src="data:image/png;base64,{{ qr_data }}" alt="QRコード"><br>
      <a href="data:image/png;base64,{{ qr_data }}" download="qrcode.png">画像をダウンロード</a>
    </div>
  {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    qr_data = None
    error_msg = None
    text = ""
    size = 300
    border = 4
    error_level = "L"

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        try:
            size = int(request.form.get("size", 300))
            border = int(request.form.get("border", 4))
            error_level = request.form.get("error", "L").upper()
        except ValueError:
            error_msg = "数値入力に誤りがあります。"
            size, border, error_level = 300, 4, "L"

        if not text:
            error_msg = "テキストを入力してください。"
        elif len(text) > 500:
            error_msg = "テキストが長すぎます（最大500文字）。"
        elif size > 1024 or size < 100:
            error_msg = "サイズは100〜1024の範囲で指定してください。"
        else:
            try:
                correction = {
                    "L": qrcode.constants.ERROR_CORRECT_L,
                    "M": qrcode.constants.ERROR_CORRECT_M,
                    "Q": qrcode.constants.ERROR_CORRECT_Q,
                    "H": qrcode.constants.ERROR_CORRECT_H,
                }.get(error_level, ERROR_CORRECT_L)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=correction,
                    box_size=10,
                    border=border,
                )
                qr.add_data(text)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white").resize((size, size))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                qr_data = base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception as e:
                error_msg = f"QR生成エラー: {e}"

    return render_template_string(
        HTML,
        qr_data=qr_data,
        text=text,
        size=size,
        border=border,
        error=error_level,
        error_msg=error_msg,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    app.run(host=host, port=port, debug=DEBUG)

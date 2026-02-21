from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image
import os
import sqlite3

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------- Allergen Maps ----------------
allergen_map = {
    "milk": ["milk","whey","casein","milk solids","butter","lactose","milk protein"],
    "egg": ["egg","albumin","ovalbumin","egg white","egg yolk","lysozyme"],
    "soy": ["soy","soy protein","soy protein isolate","soy lecithin","soybean"],
    "peanut": ["peanut","groundnut","arachis oil","peanut butter"],
    "tree nut": ["tree nut"], # dropdown handles specific nuts
    "wheat": ["wheat","gluten","seitan","barley","rye","spelt","kamut","farro"],
    "fish": ["fish"], # dropdown handles specific fish
    "shellfish": ["shellfish"],# dropdown handles specific shellfish
    "sesame": ["sesame","sesame seeds","tahini","sesame oil"],
    "mustard": ["mustard","mustard seed","mustard powder","mustard oil"],
    "celery": ["celery","celery seed","celery root"],
    "sulphites": ["sulphite","sulfite","sulfur dioxide","e220","e221","e222","e223"],
    "lupin": ["lupin","lupin flour","lupin protein"],
    "mollusk": ["mollusk","clams","oysters","mussels","scallops"],
    "corn": ["corn","corn syrup","corn starch","maize","corn protein"],
    "chocolate": ["cocoa","chocolate","cacao","cocoa butter"],
    "yeast": ["yeast","baker's yeast","brewer's yeast"],
    "caffeine": ["caffeine","coffee","tea","cola","guarana"],
    "artificial colors": ["tartrazine","sunset yellow","allura red","food coloring"],
    "artificial preservatives": ["sodium benzoate","potassium sorbate","bht","bha"],
    "acidifiers": ["citric acid","lactic acid","acetic acid","malic acid"]
}

# Specific allergens for dropdowns
specific_allergens = {
    "tree nut": ["almond","cashew","walnut","pecan","pistachio","hazelnut","macadamia","brazil nut","pine nut"],
    "fish": ["cod", "salmon", "tuna", "anchovy", "haddock", "trout", "sardine"],
    "shellfish": ["shrimp","prawn","lobster","crab","crayfish","oyster","squid","mussels","clams","scallops"]
}

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            detected TEXT,
            risk TEXT,
            safety_percent REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTE ----------------
@app.route("/", methods=["GET","POST"])
def index():
    result = None
    detected_allergens = []
    safety_percent = 100
    total_ingredients = 0

    if request.method == "POST":
        name = request.form.get("name", "")
        severity = request.form.get("severity", "")
        selected = request.form.getlist("allergens")
        file_label = request.files.get("image")
        file_report = request.files.get("report")

        all_text = ""

        # --- Scan ingredient label ---
        if file_label and file_label.filename != "":
            path_label = os.path.join(app.config['UPLOAD_FOLDER'], file_label.filename)
            file_label.save(path_label)
            all_text += pytesseract.image_to_string(Image.open(path_label)).lower() + " "

        # --- Scan doctor's report if uploaded ---
        if file_report and file_report.filename != "":
            path_report = os.path.join(app.config['UPLOAD_FOLDER'], file_report.filename)
            file_report.save(path_report)
            all_text += pytesseract.image_to_string(Image.open(path_report)).lower() + " "

        # --- Check allergens ---
        total_ingredients = len(all_text.split())
        for allergen in selected:
            for keyword in allergen_map.get(allergen, []):
                if keyword in all_text and allergen not in detected_allergens:
                    detected_allergens.append(allergen)

        # --- Risk Calculation ---
        count = len(detected_allergens)
        if count == 0:
            result = "SAFE"
        elif count == 1:
            result = "MEDIUM"
        else:
            result = "HIGH"

        # --- Safety Percentage ---
        if total_ingredients > 0:
            safety_percent = max(0, 100 - (count / total_ingredients * 100))
        else:
            safety_percent = 100

        # --- Store in DB ---
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO scans (name, detected, risk, safety_percent) VALUES (?, ?, ?, ?)",
            (name, ",".join(detected_allergens), result, safety_percent)
        )
        conn.commit()
        conn.close()

        # Return JSON response
        return jsonify({
            "result": result,
            "detected": detected_allergens,
            "risk": result,
            "safety_percent": round(safety_percent, 2),
            "total_ingredients": total_ingredients
        })
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

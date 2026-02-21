from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image, ImageFile, ImageOps, ImageFilter
ImageFile.LOAD_TRUNCATED_IMAGES = True
import re
import difflib
import unicodedata
import os
import sqlite3

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------- Allergen Maps ----------------
allergen_map = {
    "milk": ["milk","whey","casein","milk solids","butter","lactose","milk protein"],
    "egg": ["eggs","albumin","ovalbumin","egg white","egg yolk","lysozyme"],
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
    conn = sqlite3.connect('allergens.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     name TEXT,
     allergens TEXT
    )
    ''')

    
    # Create scans table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scans (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER,
     scanned_ingredients TEXT,
     detected_allergens TEXT,
     risk_level TEXT,
     safety_score INTEGER,
     scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
init_db()


def normalize_text(s: str) -> str:
    """Normalize OCR text: unicode -> ascii, replace common OCR artifacts,
    remove non-alphanumerics, collapse spaces, and lower-case."""
    if not s:
        return ""
    # Unicode normalize and remove diacritics
    s = unicodedata.normalize('NFKD', s)
    s = s.encode('ascii', 'ignore').decode('ascii')
    s = s.lower()

    # common OCR character substitutions
    subs = {
        '|': 'l',
        '0': 'o',
        '1': 'l',
        '¢': 'c',
        '€': 'e',
        '¥': 'y',
        '§': 's',
        '“': '"',
        '”': '"',
        '‘': "'",
        '\\*': ' ',
    }
    for k, v in subs.items():
        s = s.replace(k, v)

    # remove remaining non-alphanumeric (keep spaces)
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def ocr_with_preprocess(path: str) -> str:
    
  img = Image.open(path)
  img = ImageOps.grayscale(img)
  img = ImageOps.autocontrast(img)
  txt = pytesseract.image_to_string(img,config='--oem 3 --psm 3')
  return txt.lower()

def save_scan(user_id, ingredients, detected, risk, safety):
    conn = sqlite3.connect('allergens.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO scans (user_id, scanned_ingredients, detected_allergens, risk_level, safety_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, ','.join(ingredients), ','.join(detected), risk, safety))

    conn.commit()
    conn.close()

def get_scan_history(user_id):
    conn = sqlite3.connect('allergens.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT scanned_ingredients, detected_allergens, risk_level, safety_score, scan_date
        FROM scans
        WHERE user_id=?
        ORDER BY scan_date DESC
    ''', (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows
# ---------------- ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
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
            try:
                all_text += pytesseract.image_to_string(Image.open(path_label)).lower() + " "
            except Exception:
                try:
                    img = Image.open(path_label)
                    img.load()
                    all_text += pytesseract.image_to_string(img).lower() + " "
                except Exception:
                    # if OCR fails, continue without crashing
                    pass

        # --- Scan doctor's report if uploaded ---
        if file_report and file_report.filename != "":
            path_report = os.path.join(app.config['UPLOAD_FOLDER'], file_report.filename)
            file_report.save(path_report)
            all_text += pytesseract.image_to_string(Image.open(path_report)).lower() + " "

        # --- Parse ingredients (split on commas, semicolons, newlines, or 'and') ---
        # preserve raw OCR for debug, but use normalized text for matching
        ocr_raw = all_text.strip()
        
        if ',' in ocr_raw:
            raw_parts = ocr_raw.split(',')
        else:
            raw_parts = ocr_raw.split('\n')
        ingredients_list = [p.strip() for p in raw_parts if len(p.strip()) > 1]
        total_ingredients = len(ingredients_list)

        # --- Check allergens ---
        allergens_to_check = [s.lower() for s in selected] if selected else list(allergen_map.keys())

        # Match against normalized ingredient strings and tokens with fuzzy fallback
        
        for ingredient in ingredients_list:
            clean_ing = normalize_text(ingredient)
            for allergen in allergens_to_check:
                keywords = allergen_map.get(allergen.lower(), [])
                for k in keywords:
                    k_norm = normalize_text(k)
                    if k_norm.lower() in clean_ing.lower():
                        if allergen not in detected_allergens:
                            detected_allergens.append(allergen)

                    # fuzzy match entire ingredient vs keyword
                    if len(clean_ing) >= 3:
                        ratio_whole = difflib.SequenceMatcher(None, clean_ing, k_norm).ratio()
                        if ratio_whole >= 0.75:
                            if allergen not in detected_allergens:
                                detected_allergens.append(allergen)
                                

                    # token-level fuzzy matching
                    for token in clean_ing.split():
                        if len(token) >= 3:
                            ratio = difflib.SequenceMatcher(None, token, k_norm).ratio()
                            if ratio >= 0.78:
                                if allergen not in detected_allergens:
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

        # --- Store in DB (use helper) ---
        try:
            save_scan(None, ingredients_list, detected_allergens, result, int(round(safety_percent)))
        except Exception:
            # Fallback: attempt to store minimally without crashing
            conn = sqlite3.connect('allergens.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scans (user_id, scanned_ingredients, detected_allergens, risk_level, safety_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (None, ','.join(all_text.split()), ','.join(detected_allergens), result, int(round(safety_percent))))
            conn.commit()
            conn.close()

        # Return JSON response (include OCR/debug info to help troubleshoot detection)
        return jsonify({
            "result": result,
            "detected": detected_allergens,
            "risk": result,
            "safety_percent": round(safety_percent, 2),
            "total_ingredients": total_ingredients,
            "ocr_text": all_text,
            "ingredients": ingredients_list
        })

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

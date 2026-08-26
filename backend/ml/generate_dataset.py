"""
Dataset generator for kirana shop customer intent classifier.
Covers: English, Tanglish (Tamil-English mix), spelling mistakes, all contexts.
Run: python -m backend.ml.generate_dataset
"""
import csv, random, os

# ─── All kirana shop products ────────────────────────────────────────────────
PRODUCTS = [
    # Vegetables
    "brinjal", "brinjel", "kathirikkai", "tomato", "tamato", "tamoto",
    "onion", "vengayam", "potato", "urulaikizhangu", "carrot", "beans",
    "cabbage", "cauliflower", "ladies finger", "okra", "beetroot",
    "drumstick", "murungakkai", "raw banana", "plantain", "spinach",
    "coriander", "kothamalli", "green chilli", "milagai",
    # Fruits
    "apple", "banana", "pazham", "mango", "manga", "grapes", "orange",
    "papaya", "watermelon", "guava", "pomegranate",
    # Dairy
    "milk", "paal", "curd", "thayir", "butter", "cream", "paneer",
    "cheese", "ghee", "buttermilk", "moru",
    # Grains & Dal
    "rice", "arisi", "wheat", "atta", "maida", "toor dal", "thuvaram paruppu",
    "moong dal", "chana dal", "urad dal", "rajma", "black gram",
    "idli rice", "boiled rice", "raw rice", "ponni rice", "sona masoori",
    # Oil
    "sunflower oil", "gingelly oil", "nalla ennai", "coconut oil",
    "groundnut oil", "refined oil", "olive oil",
    # Spices
    "turmeric", "manjal", "pepper", "milagu", "cumin", "jeera",
    "mustard", "kadugu", "fenugreek", "methi", "cardamom", "elachi",
    "cloves", "kirambu", "cinnamon", "pattai", "bay leaf", "salt",
    "sambar powder", "rasam powder", "chilli powder", "garam masala",
    # Packaged
    "sugar", "shakkar", "jaggery", "vellam", "tea", "tea powder",
    "coffee", "biscuit", "bread", "egg", "mutta", "noodles", "maggi",
    "pasta", "cornflakes", "oats", "semolina", "rava", "vermicelli",
    "coconut", "thenga", "tamarind", "puli",
    # Household
    "soap", "shampoo", "toothpaste", "detergent", "washing powder",
    "surf excel", "tide", "vim", "lizol", "dettol", "hand wash",
    # Snacks
    "chips", "namkeen", "murukku", "mixture", "lays", "kurkure",
]

# ─── Intent templates ────────────────────────────────────────────────────────

AVAILABILITY_TEMPLATES = [
    # Clean English
    "do you have {p}",
    "is {p} available",
    "is {p} in stock",
    "do you sell {p}",
    "got any {p}",
    "any {p} left",
    "{p} available",
    "{p} in stock",
    "have you got {p}",
    "do u have {p}",
    "is there {p}",
    "do you carry {p}",
    "can i get {p}",
    "do you keep {p}",
    "{p} stock there",
    # Spelling mistakes
    "do u hav {p}",
    "iz {p} avaliable",
    "{p} availabel",
    "do you hav {p}",
    "{p} avilable",
    "any {p} avalaible",
    "{p} stock availble",
    "is {p} availabl",
    # Tanglish (Tamil + English)
    "{p} iruka",
    "{p} irukka",
    "{p} irukkuma",
    "{p} irukka pa",
    "{p} irukkanga",
    "{p} stock iruka",
    "{p} kittaya",
    "{p} kidaikuma",
    "{p} kidaikkuma",
    "{p} vachu irukenga",
    "{p} vangalam",
    "{p} tharuveenga",
    # Mixed Tamil-English
    "{p} available ah",
    "{p} stock iruka bro",
    "do you have {p} ah",
    "{p} irukkuma sir",
    "{p} available na sollunga",
    "bro {p} iruka",
    "anna {p} iruka",
    "{p} available pa",
    "{p} stock ah",
]

PRICE_TEMPLATES = [
    # Clean English
    "what is the price of {p}",
    "how much is {p}",
    "what does {p} cost",
    "price of {p}",
    "cost of {p}",
    "rate of {p}",
    "{p} price",
    "{p} cost",
    "{p} rate",
    "how much for {p}",
    "what is {p} price",
    "tell me the price of {p}",
    "how much does {p} cost",
    "{p} price please",
    "what is the rate of {p}",
    # Spelling mistakes
    "wht is prise of {p}",
    "hw much is {p}",
    "pric of {p}",
    "wat is cost of {p}",
    "how mch for {p}",
    "{p} prise",
    "{p} proce",
    "wat is {p} rate",
    "{p} prce",
    # Tanglish
    "{p} price enna",
    "{p} evvalavu",
    "{p} evlo",
    "{p} rate enna",
    "{p} cost enna",
    "{p} vilai enna",
    "{p} vilai sollu",
    "{p} rate sollunga",
    "{p} price sollu pa",
    "{p} evlo aagum",
    "{p} eppadi iruku price",
    # Mixed
    "{p} price how much",
    "what is rate of {p} ah",
    "{p} price enna bro",
    "bro {p} evlo",
    "{p} price sollunga sir",
    "anna {p} rate enna",
    "{p} cost enna da",
    "how much {p} price ah",
]

GREETING_EXAMPLES = [
    # English
    "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
    "good night", "hi there", "hello there", "hey there", "greetings",
    "howdy", "sup", "whats up", "what's up", "yo",
    # Spelling
    "helo", "helo there", "hii", "heloo", "hai", "haai", "heyy",
    "gud morning", "gd morning", "gd evng",
    # Tamil
    "vanakkam", "vanakam", "vanakam sir", "vanakkam anna",
    "namaste", "namasthe", "namaskaram",
    # Mixed
    "hi anna", "hello bro", "hi sir", "hello sir", "hey bro",
    "good morning sir", "good morning anna", "vanakkam bro",
    "hi da", "hello pa",
]

THANKS_EXAMPLES = [
    "thanks", "thank you", "thank u", "thx", "thnks", "thnx", "ty",
    "ok thanks", "ok thank you", "ok thnks", "thanks a lot",
    "many thanks", "thanks bro", "thanks sir", "thanks anna",
    "super thanks", "ok", "okay", "k", "k thanks", "ok ok",
    # Tamil
    "nandri", "romba nandri", "thanks pa", "thanks da",
    "super", "nalla iruku", "seri", "ok seri",
    # Mixed
    "ok thanks bro", "thanks sir ok", "nandri sir", "thank you anna",
    "romba thanks sir", "super thanks bro",
]

COMPLAINT_EXAMPLES = [
    # Quality complaints
    "milk was bad", "milk quality not good", "milk was sour",
    "rice had stones in it", "rice quality poor",
    "bread was stale", "bread not fresh", "bread was hard",
    "dal was old", "oil was rancid", "eggs were rotten",
    "vegetables not fresh", "tomato was rotten", "onion was bad",
    "yesterday {p} was not good", "last time {p} quality was poor",
    # Tanglish complaints
    "paal kedaichiruku", "paal sour agiduchu", "paal nalla illai",
    "arisi kasta iruku", "bread pasi agiduchu",
    "tomato mosam agiduchu", "onion quality illai",
    "neram aachu delivery illai", "late agiduchu",
    # English complaints about quality
    "the {p} i bought was spoiled",
    "last time {p} was not fresh",
    "please give fresh items",
    "quality is going down",
    "always giving old stock",
    # Mixed
    "milk mosam sir", "rice quality illai bro", "bread fresh illai pa",
    "delivery late agiduchu", "wrong item kudutheenga",
    "tomato rotten agiduchu anna",
]

OUT_OF_SCOPE_EXAMPLES = [
    # Timings
    "what time do you open", "when do you open", "shop timing",
    "what time do you close", "are you open now", "open sunday?",
    "what are your working hours", "shop open ah", "eppo open aagum",
    "unga shop timings enna",
    # Location
    "where are you located", "what is your address", "how to reach your shop",
    "shop address sollu", "unga shop enga iruku", "directions to shop",
    # Delivery
    "do you deliver", "home delivery available", "delivery cost",
    "delivery charge", "minimum order for delivery", "delivery time",
    "delivery panreengala", "home delivery pannuveenga",
    # Contact
    "what is your phone number", "contact number", "whatsapp number",
    "call pannum number", "phone number sollu",
    # Payment
    "do you accept upi", "gpay accepted", "phonepay ok",
    "credit card accepted", "do you take card", "online payment",
    "upi teriyuma", "gpay panalam",
    # Other
    "how old is your shop", "who is the owner", "shop name",
]

BULK_ORDER_TEMPLATES = [
    "i need {qty}{unit} of {p}",
    "i want {qty}{unit} {p}",
    "give me {qty}{unit} {p}",
    "i'll take {qty}{unit} {p}",
    "order {qty}{unit} {p}",
    "book {qty}{unit} {p} for me",
    "{qty}{unit} {p} vennum",
    "{qty}{unit} {p} kavanum",
    "{qty}{unit} {p} tharuveenga",
    "{qty}{unit} {p} venum",
    "can you give {qty}{unit} {p}",
    "{p} {qty}{unit} kudungal",
    "bro {qty}{unit} {p} vennum",
    "anna {qty}{unit} {p} venam",
    "{qty}{unit} {p} pack panningla",
]

MULTIPLE_ITEMS_TEMPLATES = [
    "do you have {p1} and {p2}",
    "do you have {p1} and {p2} both",
    "{p1} and {p2} iruka",
    "{p1} and {p2} available ah",
    "i need {p1} and {p2}",
    "do you sell {p1} and {p2}",
    "{p1} and {p2} stock iruka",
    "both {p1} and {p2} iruka",
    "{p1} also {p2} also iruka",
    "{p1} avum {p2} avum iruka",
]

BULK_QTY = [
    ("1","kg"), ("2","kg"), ("5","kg"), ("10","kg"), ("500","g"), ("250","g"),
    ("1","litre"), ("2","litre"), ("500","ml"), ("1","packet"), ("2","packets"),
    ("6","pieces"), ("12","pieces"), ("1","dozen"), ("half","kg"),
]

# ─── Build dataset ────────────────────────────────────────────────────────────

rows = []

def add(text, intent):
    rows.append({"text": text.strip().lower(), "intent": intent})

# AVAILABILITY_CHECK
for tmpl in AVAILABILITY_TEMPLATES:
    for p in random.sample(PRODUCTS, min(8, len(PRODUCTS))):
        add(tmpl.format(p=p), "AVAILABILITY_CHECK")

# PRICE_ENQUIRY
for tmpl in PRICE_TEMPLATES:
    for p in random.sample(PRODUCTS, min(8, len(PRODUCTS))):
        add(tmpl.format(p=p), "PRICE_ENQUIRY")

# GREETING
for ex in GREETING_EXAMPLES:
    add(ex, "GREETING")
    # double some with punctuation
    add(ex + "!", "GREETING")
    add(ex + "?", "GREETING")

# THANKS
for ex in THANKS_EXAMPLES:
    add(ex, "THANKS")

# COMPLAINT
for ex in COMPLAINT_EXAMPLES:
    if "{p}" in ex:
        for p in random.sample(PRODUCTS[:15], 3):
            add(ex.format(p=p), "COMPLAINT")
    else:
        add(ex, "COMPLAINT")

# OUT_OF_SCOPE
for ex in OUT_OF_SCOPE_EXAMPLES:
    add(ex, "OUT_OF_SCOPE")
    add(ex + "?", "OUT_OF_SCOPE")

# BULK_ORDER
for tmpl in BULK_ORDER_TEMPLATES:
    for p in random.sample(PRODUCTS, 6):
        qty, unit = random.choice(BULK_QTY)
        add(tmpl.format(p=p, qty=qty, unit=unit), "BULK_ORDER")

# MULTIPLE_ITEMS
for tmpl in MULTIPLE_ITEMS_TEMPLATES:
    for _ in range(6):
        p1, p2 = random.sample(PRODUCTS, 2)
        add(tmpl.format(p1=p1, p2=p2), "MULTIPLE_ITEMS")

# Extra spelling mistake variants — important for robustness
extra_misspelled = [
    ("do u hav brinajl", "AVAILABILITY_CHECK"),
    ("is brinajl availabe", "AVAILABILITY_CHECK"),
    ("tometo iruka", "AVAILABILITY_CHECK"),
    ("tamoto stock ah", "AVAILABILITY_CHECK"),
    ("oneon irukka", "AVAILABILITY_CHECK"),
    ("pottato available", "AVAILABILITY_CHECK"),
    ("curd avialble", "AVAILABILITY_CHECK"),
    ("miilk iruka", "AVAILABILITY_CHECK"),
    ("egss iruka", "AVAILABILITY_CHECK"),
    ("suger available", "AVAILABILITY_CHECK"),
    ("wht is prise of tometo", "PRICE_ENQUIRY"),
    ("brinjal prise enna", "PRICE_ENQUIRY"),
    ("how mch is milk", "PRICE_ENQUIRY"),
    ("oneon rate enna", "PRICE_ENQUIRY"),
    ("pottato cost enna", "PRICE_ENQUIRY"),
    ("riice price enna", "PRICE_ENQUIRY"),
    ("suger vilai enna", "PRICE_ENQUIRY"),
    ("tamoto evlo", "PRICE_ENQUIRY"),
    ("miilk prise sollu", "PRICE_ENQUIRY"),
    ("egss rate enna", "PRICE_ENQUIRY"),
    ("helllo", "GREETING"),
    ("hiii", "GREETING"),
    ("good moorning", "GREETING"),
    ("vanakam sir", "GREETING"),
    ("thnk u", "THANKS"),
    ("thankz", "THANKS"),
    ("ok thnx", "THANKS"),
    ("mlk was bad", "COMPLAINT"),
    ("riice had stnes", "COMPLAINT"),
    ("whn do u open", "OUT_OF_SCOPE"),
    ("deliver panrengla", "OUT_OF_SCOPE"),
    ("5 kh rice vennum", "BULK_ORDER"),
    ("2 litr milk tharuveenga", "BULK_ORDER"),
    ("milk and brea iruka", "MULTIPLE_ITEMS"),
    ("tometo and onioin iruka", "MULTIPLE_ITEMS"),
]
for text, intent in extra_misspelled:
    add(text, intent)

# Shuffle
random.seed(42)
random.shuffle(rows)

# Remove duplicates
seen = set()
unique_rows = []
for r in rows:
    if r["text"] not in seen:
        seen.add(r["text"])
        unique_rows.append(r)

# Save
out_path = os.path.join(os.path.dirname(__file__), "dataset.csv")
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["text", "intent"])
    writer.writeheader()
    writer.writerows(unique_rows)

# Stats
from collections import Counter
counts = Counter(r["intent"] for r in unique_rows)
print(f"\nDataset generated: {len(unique_rows)} examples")
print("\nExamples per intent:")
for intent, count in sorted(counts.items()):
    print(f"  {intent:<22} {count:>4} examples")
print(f"\nSaved to: {out_path}")

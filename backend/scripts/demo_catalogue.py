"""Demo catalogue shared by generate_demo_images.py and seed_products.py.

These are fictional products. Images are drawn procedurally (see generate_demo_images.py),
so no copyrighted photos are involved. Replace them with your own product photos for real use.

Fields: code, name, category, material, purity, weight (g), price (INR), stone, colour,
occasion, file, variant (drawing style 0-3).
"""

# (code, name, category, material, purity, weight, price, stone, colour, occasion, file, variant)
_ROWS = [
    ("NK001", "Traditional Gold Necklace", "Necklace", "Gold", "22K", 25.5, 65000, "Ruby", "Gold", "Wedding", "necklace_001.jpg", 0),
    ("NK002", "Emerald Temple Necklace", "Necklace", "Gold", "22K", 28.0, 78000, "Emerald", "Gold", "Traditional", "necklace_002.jpg", 1),
    ("NK003", "Bridal Gold Necklace", "Necklace", "Gold", "22K", 34.2, 85000, "Ruby", "Gold", "Wedding", "necklace_003.jpg", 2),
    ("NK004", "Diamond Pendant Necklace", "Necklace", "Diamond", "18K", 12.4, 120000, "Diamond", "White", "Party", "necklace_004.jpg", 3),
    ("RG001", "Gold Solitaire Ring", "Ring", "Gold", "22K", 4.8, 32000, "Diamond", "Gold", "Engagement", "ring_001.jpg", 0),
    ("RG002", "Ruby Halo Ring", "Ring", "Gold", "18K", 5.2, 41000, "Ruby", "Gold", "Engagement", "ring_002.jpg", 1),
    ("RG003", "Silver Band Ring", "Ring", "Silver", "925", 6.0, 3500, None, "Silver", "Daily Wear", "ring_003.jpg", 3),
    ("RG004", "Diamond Three-Stone Ring", "Ring", "Diamond", "18K", 4.1, 95000, "Diamond", "White", "Engagement", "ring_004.jpg", 2),
    ("ER001", "Gold Drop Earrings", "Earrings", "Gold", "22K", 6.5, 18000, "Ruby", "Gold", "Traditional", "earring_001.jpg", 0),
    ("ER002", "Silver Hoop Earrings", "Earrings", "Silver", "925", 5.0, 2800, None, "Silver", "Daily Wear", "earring_002.jpg", 1),
    ("ER003", "Diamond Chandelier Earrings", "Earrings", "Diamond", "18K", 7.2, 88000, "Diamond", "White", "Party", "earring_003.jpg", 2),
    ("ER004", "Emerald Gold Drop Earrings", "Earrings", "Gold", "22K", 7.0, 24000, "Emerald", "Gold", "Wedding", "earring_004.jpg", 3),
    ("BR001", "Gold Link Bracelet", "Bracelet", "Gold", "22K", 14.0, 52000, None, "Gold", "Daily Wear", "bracelet_001.jpg", 0),
    ("BR002", "Silver Charm Bracelet", "Bracelet", "Silver", "925", 11.0, 4200, "Sapphire", "Silver", "Party", "bracelet_002.jpg", 1),
    ("BR003", "Diamond Tennis Bracelet", "Bracelet", "Diamond", "18K", 9.5, 135000, "Diamond", "White", "Party", "bracelet_003.jpg", 2),
    ("BR004", "Ruby Gold Bracelet", "Bracelet", "Gold", "22K", 16.5, 61000, "Ruby", "Gold", "Traditional", "bracelet_004.jpg", 3),
    ("BG001", "Traditional Gold Bangle", "Bangle", "Gold", "22K", 22.0, 58000, None, "Gold", "Traditional", "bangle_001.jpg", 0),
    ("BG002", "Silver Engraved Bangle", "Bangle", "Silver", "925", 18.0, 5200, None, "Silver", "Daily Wear", "bangle_002.jpg", 1),
    ("BG003", "Emerald Gold Bangle", "Bangle", "Gold", "22K", 26.0, 74000, "Emerald", "Gold", "Wedding", "bangle_003.jpg", 2),
    ("BG004", "Diamond Studded Bangle", "Bangle", "Diamond", "18K", 15.0, 148000, "Diamond", "White", "Party", "bangle_004.jpg", 3),
    ("PD001", "Gold Teardrop Pendant", "Pendant", "Gold", "22K", 3.6, 21000, "Ruby", "Gold", "Daily Wear", "pendant_001.jpg", 0),
    ("PD002", "Ruby Heart Pendant", "Pendant", "Gold", "18K", 3.1, 19500, "Ruby", "Gold", "Party", "pendant_002.jpg", 1),
    ("PD003", "Silver Medallion Pendant", "Pendant", "Silver", "925", 5.5, 2400, None, "Silver", "Daily Wear", "pendant_003.jpg", 2),
    ("PD004", "Diamond Solitaire Pendant", "Pendant", "Diamond", "18K", 2.4, 56000, "Diamond", "White", "Engagement", "pendant_004.jpg", 3),
]

_KEYS = ("product_code", "name", "category", "material", "purity", "weight", "price",
         "stone_type", "colour", "occasion", "image_filename", "variant")

CATALOGUE = [dict(zip(_KEYS, row)) for row in _ROWS]

for _p in CATALOGUE:
    stone = f" with {_p['stone_type'].lower()}" if _p["stone_type"] else ""
    _p["description"] = (
        f"{_p['purity']} {_p['material'].lower()} {_p['category'].lower()}{stone}, "
        f"suited to {_p['occasion'].lower()} occasions. Demo product."
    )

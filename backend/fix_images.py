import csv
import re
import os
import sys

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from catalog.models import Product, ProductImage, Category

def word_in(word, text):
    return bool(re.search(r'\b' + re.escape(word) + r'\b', text))

def any_word_in(words, text):
    return any(word_in(w, text) for w in words)

def choose_image(sku, name, cat, subcat):
    n = name.lower()
    c = cat.lower()

    # 1. SPECIAL CALLOUTS FROM USER
    # Almonds photo was shown for Cashew Nuts - WRONG!
    # Cherry Tomato showed mixed salad photo - WRONG!
    if 'cashew' in n:
        return 'photo-1573555657105-47a0bb37c3ea'  # Genuine cashew nuts
    if 'cherry tomato' in n:
        return 'photo-1587049203042-e04a3c16f4cc'  # Fresh cherry tomatoes on vine/pile

    # 2. CATEGORY: VEGETABLES
    if c == 'vegetables':
        if 'spinach' in n:
            return 'photo-1576045057995-568f588f82fb'
        if 'onion' in n:
            return 'photo-1618512496248-a07fe83aa8cb'
        if 'sweet potato' in n:
            return 'photo-1596097635121-14b63b7a0c19'
        if 'potato' in n:
            return 'photo-1518977676601-b53f82aba655'
        if 'cucumber' in n:
            return 'photo-1604977042946-1eecc30f269e'
        if 'brinjal' in n or 'eggplant' in n:
            return 'photo-1615485290382-441e4d049cb5'
        if 'capsicum' in n or 'bell pepper' in n:
            return 'photo-1563565375-f3fdfdbefa83'
        if 'cauliflower' in n:
            return 'photo-1568584711075-3d021a7c3ca3'
        if 'peas' in n:
            return 'photo-1587735243615-c03f25aaff15'
        if 'carrot' in n:
            return 'photo-1598170845058-32b9d6a5da37'
        if 'beetroot' in n:
            return 'photo-1526772662000-3f88f10405ff'
        if 'corn' in n:
            return 'photo-1551754655-cd27e38d2076'
        if 'bean' in n:
            return 'photo-1567375698348-5d9d5ae99de0'
        if 'lady finger' in n or 'okra' in n:
            return 'photo-1606851094655-b2593a9af63f'
        if 'drumstick' in n:
            return 'photo-1596797882870-8c33deeac224'
        if 'bitter gourd' in n:
            return 'photo-1617454837333-87f54c304ea2'
        if 'gourd' in n:
            return 'photo-1597362925123-77861d3fbac7'
        if 'pumpkin' in n:
            return 'photo-1506917728037-b6af01a7d403'
        if 'broccoli' in n:
            return 'photo-1584270359816-646702e50584'
        if 'zucchini' in n:
            return 'photo-1590779033100-9f60a05a013d'
        if 'coriander' in n:
            return 'photo-1608686207856-001b95cf60ca'
        if 'mint' in n:
            return 'photo-1628556270448-4d4e4148e1b1'
        if 'curry leaves' in n:
            return 'photo-1615485500704-8e990f9900f7'
        if 'tomato' in n:
            return 'photo-1546094096-0df4bcaaa337'
        return 'photo-1540420773420-3366772f4999'

    # 3. CATEGORY: FRUITS
    if c == 'fruits':
        if 'mango' in n:
            return 'photo-1553279768-865429fa0078'
        if 'banana' in n:
            return 'photo-1571771894821-ce9b6c11b08e'
        if 'orange' in n:
            return 'photo-1611080626919-7cf5a9dbab5b'
        if 'sweet lime' in n or 'lemon' in n:
            return 'photo-1590502593747-42a996133562'
        if 'black grape' in n:
            return 'photo-1537640538966-79f369143f8f'
        if 'grape' in n:
            return 'photo-1596363505729-4190a9506133'
        if 'pineapple' in n:
            return 'photo-1550258987-190a2d41a8ba'
        if 'apple' in n:
            return 'photo-1560806887-1e4cd0b6cbd6'
        if 'pomegranate' in n:
            return 'photo-1541344999736-83eca872f241'
        if 'guava' in n:
            return 'photo-1536511136777-29d81121774f'
        if 'papaya' in n:
            return 'photo-1517282009859-f000ec3b26fe'
        if 'watermelon' in n:
            return 'photo-1587049352846-4a222e784d38'
        if 'muskmelon' in n:
            return 'photo-1571575179703-4bde44fb14bc'
        if 'kiwi' in n:
            return 'photo-1518492104633-130d0cc84637'
        if 'dragon fruit' in n:
            return 'photo-1527325678964-54921661f888'
        if 'pear' in n:
            return 'photo-1615484477778-ca3b77940c25'
        if 'chikoo' in n:
            return 'photo-1589533610925-1cffc309ebaa'
        if 'coconut' in n:
            return 'photo-1544378730-8b5104b18790'
        if 'strawberry' in n:
            return 'photo-1464965911861-746a04b4bca6'
        if 'blueberry' in n:
            return 'photo-1498557850523-fd3d118b962e'
        if 'jamun' in n:
            return 'photo-1596547609652-9cf5d8d76921'
        if 'avocado' in n:
            return 'photo-1523049673857-eb18f1d7b578'
        return 'photo-1610832958506-aa56368176cf'

    # 4. CATEGORY: DAIRY & EGGS
    if c == 'dairy-eggs':
        if 'egg' in n:
            return 'photo-1506976785307-8732e854ad03'
        if 'paneer' in n:
            return 'photo-1631452180519-c014fe946bc7'
        if 'tofu' in n:
            return 'photo-1546069901-ba9599a7e63c'
        if 'cheese' in n:
            return 'photo-1618160702438-9b02ab6515c9'
        if 'butter' in n and 'buttermilk' not in n:
            return 'photo-1589985270826-4b7bb135bc9d'
        if 'ghee' in n:
            return 'photo-1628088062854-d1870b4553da'
        if 'buttermilk' in n or 'lassi' in n:
            return 'photo-1550583724-b2692b85b150'
        if 'curd' in n or 'yogurt' in n:
            return 'photo-1488477181946-6428a0291777'
        if 'cream' in n:
            return 'photo-1550583724-b2692b85b150'
        if 'milk' in n:
            return 'photo-1563636619-e9143da7973b'
        return 'photo-1550583724-b2692b85b150'

    # 5. CATEGORY: RICE & PULSES
    if c == 'rice-pulses':
        if any(k in n for k in ['brown', 'red rice', 'black rice', 'matta']):
            return 'photo-1536304993881-ff6e9eefa2a6'
        if 'masoor' in n:
            return 'photo-1585994192701-f1a505c817ea'
        if any(k in n for k in ['dal', 'chana', 'rajma', 'peas', 'pulse', 'gram', 'moong', 'urad', 'toor']):
            return 'photo-1515543237350-b3eea1ec8082'
        if any(k in n for k in ['rice', 'millet', 'wheat', 'grain', 'atta', 'flour', 'poha', 'quinoa']):
            return 'photo-1586201375761-83865001e31c'
        return 'photo-1586201375761-83865001e31c'

    # 6. CATEGORY: MEAT & SEAFOOD
    if c == 'meat-seafood':
        if 'chicken breast' in n or 'turkey breast' in n or 'duck breast' in n:
            return 'photo-1604503468506-a8da13d82791'
        if any(k in n for k in ['sausage', 'pork']):
            return 'photo-1568901346375-23c9450c58cd'
        if any(k in n for k in ['tikka', 'kebab', 'meatball', 'lollipop']):
            return 'photo-1599488615731-7e5c2823ff28'
        if any(k in n for k in ['mutton', 'lamb', 'goat', 'liver', 'keema', 'ribs']):
            return 'photo-1603048588665-791ca8aea617'
        if any(k in n for k in ['chicken', 'drumstick', 'wing', 'thigh', 'duck', 'whole chicken', 'mince']):
            return 'photo-1587593810167-a84920ea0781'
        return 'photo-1607623814075-e51df1bdc82f'

    # 7. CATEGORY: FISH & PRAWNS
    if c == 'fish-prawns':
        if any(k in n for k in ['prawn', 'shrimp', 'squid', 'crab', 'clam', 'lobster']):
            return 'photo-1565680018434-b513d5e5fd47'
        return 'photo-1519708227418-c8fd9a32b7a2'

    # 8. CATEGORY: BAKERY
    if c == 'bakery':
        if 'sourdough' in n:
            return 'photo-1509440159596-0249088772ff'
        if 'baguette' in n or 'garlic bread' in n:
            return 'photo-1589367920969-ab8e050bbb04'
        if any(k in n for k in ['croissant']):
            return 'photo-1555507036-ab1f4038808a'
        if 'muffin' in n:
            return 'photo-1586985289688-ca3cf47d3e6e'
        if 'brownie' in n:
            return 'photo-1606313564200-e75d5e30476c'
        if 'cake' in n:
            return 'photo-1578985545062-69928b1d9587'
        if any(k in n for k in ['biscuit', 'cookie', 'rusk', 'nankhatai']):
            return 'photo-1499636136210-6f4ee915583e'
        if any(k in n for k in ['bun', 'pav']):
            return 'photo-1586190848861-99aa4a171e90'
        if any(k in n for k in ['puff', 'khari']):
            return 'photo-1601050690597-df0568f70950'
        if any(k in n for k in ['pizza', 'wrap']):
            return 'photo-1513104890138-7c749659a591'
        if 'bread' in n or 'loaf' in n:
            return 'photo-1549931319-a545dcf3bc73'
        return 'photo-1509440159596-0249088772ff'

    # 9. CATEGORY: SNACKS
    if c == 'snacks':
        if 'almond' in n:
            return 'photo-1508061253366-f7da158b6d46'
        if 'pistachio' in n:
            return 'photo-1616684000067-36952fde5641'
        if 'walnut' in n:
            return 'photo-1558642452-9d2a7deb7f62'
        if 'peanut' in n or 'chana' in n:
            return 'photo-1567892328127-14e4b52cb5b6'
        if 'makhana' in n:
            return 'photo-1599488615731-7e5c2823ff28'
        if any(k in n for k in ['chip', 'wafer']):
            return 'photo-1566478989037-eec170784d0b'
        if any(k in n for k in ['ladoo', 'chikki', 'energy bite', 'trail mix', 'seed mix']):
            return 'photo-1541781774459-bb2af2f05b55'
        if any(k in n for k in ['murukku', 'pakoda', 'bhujia', 'namkeen', 'khakhra', 'puff', 'mix']):
            return 'photo-1601050690597-df0568f70950'
        return 'photo-1508061253366-f7da158b6d46'

    # 10. CATEGORY: BEVERAGES
    if c == 'beverages':
        if 'tea' in n or 'chai' in n:
            return 'photo-1544787219-7f47ccb76574'
        if 'coffee' in n:
            return 'photo-1514432324607-a09d9b4aefdd'
        if 'orange juice' in n:
            return 'photo-1611080626919-7cf5a9dbab5b'
        if 'mango juice' in n or 'aam' in n:
            return 'photo-1553279768-865429fa0078'
        if 'guava juice' in n:
            return 'photo-1536511136777-29d81121774f'
        if 'coconut' in n:
            return 'photo-1544378730-8b5104b18790'
        if 'lemonade' in n:
            return 'photo-1590502593747-42a996133562'
        if 'juice' in n:
            return 'photo-1600271886742-f049cd451bba'
        if 'buttermilk' in n:
            return 'photo-1550583724-b2692b85b150'
        return 'photo-1513558161293-cdaf765ed2fd'

    # 11. CATEGORY: COOKING OILS
    if c == 'cooking-oils':
        # All cooking oils should be shown as clean cooking oil bottles/pourers
        return 'photo-1474979266404-7eaacbcd87c5'

    # 12. CATEGORY: MASALA & SPICES
    if c == 'masala-spices':
        # All spices and powders should be clean spice powders / whole spice bowls
        return 'photo-1596040033229-a9821ebd058d'

    # 13. CATEGORY: PERSONAL CARE
    if c == 'personal-care':
        # Clean cosmetic / personal hygiene bottle
        return 'photo-1608248543803-ba4f8c70ae0b'

    # 14. CATEGORY: HOUSEHOLD ESSENTIALS
    if c == 'household-essentials':
        # Clean household cleaning supplies
        return 'photo-1585421514284-efb74c2b69ba'

    # 15. CATEGORY: BABY CARE
    if c == 'baby-care':
        if 'cereal' in n:
            return 'photo-1586201375761-83865001e31c'
        if 'apple' in n:
            return 'photo-1560806887-1e4cd0b6cbd6'
        if 'banana' in n:
            return 'photo-1571771894821-ce9b6c11b08e'
        return 'photo-1519689680058-324335c77eba'

    # 16. CATEGORY: FROZEN FOODS
    if c == 'frozen-foods':
        if 'pea' in n:
            return 'photo-1587735243615-c03f25aaff15'
        if 'corn' in n:
            return 'photo-1551754655-cd27e38d2076'
        if 'spinach' in n:
            return 'photo-1576045057995-568f588f82fb'
        if 'cauliflower' in n:
            return 'photo-1568584711075-3d021a7c3ca3'
        if 'broccoli' in n:
            return 'photo-1584270359816-646702e50584'
        if 'blueberry' in n or 'blueberries' in n:
            return 'photo-1498557850523-fd3d118b962e'
        if 'strawberry' in n or 'strawberries' in n:
            return 'photo-1464965911861-746a04b4bca6'
        if 'paneer' in n:
            return 'photo-1631452180519-c014fe946bc7'
        if 'chicken' in n or 'nugget' in n:
            return 'photo-1599488615731-7e5c2823ff28'
        if 'fries' in n or 'potato' in n or 'tikki' in n:
            return 'photo-1566478989037-eec170784d0b'
        if 'pizza' in n:
            return 'photo-1513104890138-7c749659a591'
        if any(k in n for k in ['paratha', 'parotta', 'roti']):
            return 'photo-1509440159596-0249088772ff'
        if any(k in n for k in ['samosa', 'roll', 'momo', 'curry', 'vegetable', 'bean']):
            return 'photo-1601050690597-df0568f70950'
        return 'photo-1587735243615-c03f25aaff15'

    # 17. CATEGORY: ORGANIC FOODS
    if c == 'organic-foods':
        if 'tomato' in n:
            return 'photo-1546094096-0df4bcaaa337'
        if 'spinach' in n:
            return 'photo-1576045057995-568f588f82fb'
        if 'carrot' in n:
            return 'photo-1598170845058-32b9d6a5da37'
        if 'cucumber' in n:
            return 'photo-1604977042946-1eecc30f269e'
        if 'banana' in n:
            return 'photo-1571771894821-ce9b6c11b08e'
        if 'apple' in n:
            return 'photo-1560806887-1e4cd0b6cbd6'
        if any(k in n for k in ['dal', 'lentil', 'chickpea']):
            return 'photo-1515543237350-b3eea1ec8082'
        if 'brown rice' in n:
            return 'photo-1536304993881-ff6e9eefa2a6'
        if any(k in n for k in ['rice', 'oat', 'poha', 'quinoa', 'atta', 'flour']):
            return 'photo-1586201375761-83865001e31c'
        if 'oil' in n:
            return 'photo-1474979266404-7eaacbcd87c5'
        if 'peanut butter' in n:
            return 'photo-1567892328127-14e4b52cb5b6'
        if 'tea' in n:
            return 'photo-1544787219-7f47ccb76574'
        if 'coconut' in n:
            return 'photo-1544378730-8b5104b18790'
        if any(k in n for k in ['seed', 'jaggery', 'raisin']):
            return 'photo-1541781774459-bb2af2f05b55'
        return 'photo-1540420773420-3366772f4999'

    # 18. CATEGORY: PET CARE (STRICTLY NO ANIMALS!)
    if c == 'pet-care':
        # Food & treats show clean pet food bowls or biscuits, NEVER live animals
        if any(k in n for k in ['treat', 'chew', 'biscuit']):
            return 'photo-1582798358481-d199fb7347bb'  # Pet biscuits/treats, NO animal
        if any(k in n for k in ['food', 'starter', 'flake', 'replacer', 'feed', 'bowl']):
            return 'photo-1589924691995-400dc9ecc119'  # Pet food bowl / kibble, NO animal
        if 'seed' in n or 'hay' in n:
            return 'photo-1541781774459-bb2af2f05b55'  # Seeds
        # Accessories, shampoo, brush, litter, bags: clean product packaging
        return 'photo-1585421514284-efb74c2b69ba'

    # 19. CATEGORY: HOME & KITCHEN
    if c == 'home-kitchen':
        if 'water bottle' in n:
            return 'photo-1513558161293-cdaf765ed2fd'
        return 'photo-1514228742587-6b1558fcca3d'

    # 20. CATEGORY: POOJA ESSENTIALS
    if c == 'pooja-essentials':
        if 'camphor' in n:
            return 'photo-1608571423902-eed4a5ad8108'
        if 'incense' in n or 'dhoop' in n:
            return 'photo-1506456070622-d7b102283e33'
        if 'diya' in n or 'lamp' in n:
            return 'photo-1605335198104-582775a98708'
        return 'photo-1609137144813-7d9921338f24'

    # 21. CATEGORY: STATIONERY
    if c == 'stationery':
        return 'photo-1455390582262-044cdead277a'

    return 'photo-1542838132-92c53300491e'

# Read CSV and update
csv_path = 'catalog/data/products.csv'
rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig')))
print(f"Total rows in CSV: {len(rows)}")

changed = []
for r in rows:
    sku = r['sku']
    name = r['name']
    cat = r['category']
    subcat = r['subcategory']
    old_url = r['image_url']
    photo_id = choose_image(sku, name, cat, subcat)
    new_url = f'https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=720&q=80'
    if old_url != new_url:
        changed.append((sku, name, cat, old_url, new_url))
        r['image_url'] = new_url

fieldnames = list(rows[0].keys())
with open(csv_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Updated {len(changed)} products in CSV.")

# Update MySQL database
db_updated = 0
for r in rows:
    sku = r['sku']
    new_url = r['image_url']
    product = Product.objects.filter(sku=sku).first()
    if product:
        primary_img = ProductImage.objects.filter(product=product, is_primary=True).first()
        if primary_img:
            if primary_img.image_url != new_url:
                primary_img.image_url = new_url
                primary_img.alt_text = product.name
                primary_img.save()
                db_updated += 1
        else:
            ProductImage.objects.create(product=product, image_url=new_url, alt_text=product.name, is_primary=True)
            db_updated += 1

print(f"Updated {db_updated} ProductImage records in database.")

# Update Pet Care category image in database if it has dog photo
pet_cat = Category.objects.filter(slug='pet-care').first()
if pet_cat:
    pet_cat.image_url = 'https://images.unsplash.com/photo-1589924691995-400dc9ecc119'
    pet_cat.save()
    print("Updated Pet Care category image in database (removed dog photo).")

with open('image_changes_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total products updated: {len(changed)}\n\n")
    for sku, name, cat, old, new in changed:
        f.write(f"[{sku}] ({cat}) {name}\n  Old: {old}\n  New: {new}\n\n")

print("Report saved to image_changes_report.txt")

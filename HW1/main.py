import json
from pprint import pprint

from unit_extractor import UnitExtractor


extractor = UnitExtractor()
# matn = "دیروز با مهدی رفتم ۲ متر کالباس خریدم و با هم با سرعت ۲۵ متر بر ثانیه دویدیم"
# results = extractor.run(matn)
# pprint(results)
# print()

# matn = "شهاب سنگی به جرم ۱۰ کیلوگرم به زمین برخورد کرد"
# results = extractor.run(matn)
# pprint(results)
# print()

# matn = "یک خودرو با سرعت زیاد از ما سبقت گرفت"
# results = extractor.run(matn)
# pprint(results)
# print()


# matn = "یک خودرو با طول زیاد از کنار ما رد شد"
# results = extractor.run(matn)
# pprint(results)
# print()


with open('data.json') as f:
    data = json.load(f)

for article in data:
    print(article['title'])
    print()
    results = extractor.run(article['text'])
    pprint(results)
    print('\n----------------------------\n')

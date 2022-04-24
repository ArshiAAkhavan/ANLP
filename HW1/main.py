import json
from pprint import pprint

from HW1.unit_converter import UnitConverter
from HW1.unit_extractor.output import ValidOutput
from unit_extractor.extractor import UnitExtractor


extractor = UnitExtractor()
# matn = " بنابراین روتور سه درجه آزادی چرخش دارد و محورش هم دو درجه دارد."
# results = extractor.run(matn)
# pprint(results)
# print()

# matn = "دیروز با مهدی رفتم ۲ متر کالباس خریدم و با هم با سرعت ۲۵ متر بر ثانیه دویدیم"
# results = extractor.run(matn)
# pprint(results)
# print()


# matn = "سنگ جرم ۱۱ کیلوگرم به زمین برخورد کرد"
# results = extractor.run(matn)
# pprint(results)
# print()

matn = "شهاب سنگی به جرم ۱۰ کیلوگرم به زمین برخورد کرد"
results = extractor.run(matn)
pprint(results)
print()

matn = "شهاب سنگی به تندی ۱۰ کیلوگرم به زمین برخورد کرد"
results = extractor.run(matn)
pprint(results)
print()


matn = "شهاب سنگی به تندی ۱۰ کیلومتر بر ثانیه به زمین برخورد کرد"
results = extractor.run(matn)
pprint(results)
print()

# matn = "یک خودرو با سرعت زیاد از ما سبقت گرفت"
# results = extractor.run(matn)
# pprint(results)
# print()


# matn = "یک خودرو با طول زیاد از کنار ما رد شد"
# results = extractor.run(matn)
# pprint(results)
# print()

validOutput = ValidOutput(quantity='زمان', amount=4, unit='ماه', item='برای', marker='چهار ماه برای', span=(3404, 3417))
pprint(UnitConverter().convert(validOutput))



# with open('data.json' , encoding='utf8') as f:
#     data = json.load(f)
#
# for article in data:
#     print(article['title'])
#     print()
#     results = extractor.run(article['text'])
#     pprint(results)
#     print('\n----------------------------\n')

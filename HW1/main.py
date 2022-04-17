from pprint import pprint as print
from unit_extractor import UnitExtractor

extractor = UnitExtractor()
matn = "دیروز با مهدی رفتم ۲ متر کالباس خریدم و با هم با سرعت ۲۵ متر بر ثانیه دویدیم"
results = extractor.run(matn)
print(results)
matn = "شهاب سنگی به جرم ۱۰ کیلوگرم به زمین برخورد کرد"

results = extractor.run(matn)
print(results)

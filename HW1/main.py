from parsi_io.modules.number_extractor import NumberExtractor
from pprint import pprint as print
extractor = NumberExtractor()

units=['متر', 'گرم']

matn='دیروز با مهدی رفتم ۲ گرم کالباس خریدم'

for p_target in extractor.run(matn):
    print(p_target)
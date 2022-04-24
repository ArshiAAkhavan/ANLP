import pandas as pd

from HW1.unit_extractor.extractor import UnitExtractor
from HW1.unit_extractor.output import ValidOutput


class UnitConverter:
    @staticmethod
    def convert(validOutput: ValidOutput):
        if  not validOutput.amount or not validOutput.unit:
            return []
        unit_extractor = UnitExtractor()
        quantity,qid,proper_unit = unit_extractor.get_quantity_and_proper_unit_from_unit_name(validOutput.unit)
        u_df = pd.read_csv("units.csv")
        u_df =u_df[u_df['qid']==qid]
        base_unit = u_df[u_df['id']==proper_unit]
        u_df.reset_index()
        result = []
        for index, row in u_df.iterrows():
            new_amount = float(validOutput.amount) * row['conversion_factor'] / base_unit['conversion_factor'].iloc[0]
            result.append({'unit':row['id'],'amount':new_amount})
        return result


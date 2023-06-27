import pandas as pd

file_path = 'output1.3.xlsx'

data = pd.read_excel(file_path)
data_copy = data.copy()

data_copy['ref-idv-id'].fillna('N/A', inplace=True)
data_copy['description'] = data_copy['description'].astype(str)

data_copy.loc[data_copy['mod-number'] == '0', 'total-obligated-amount'] = data_copy['obligated-amount']

grouped_data = data_copy.groupby(['award-id', 'ref-idv-id']).agg({
    'mod-number': 'count',
    'total-obligated-amount': 'last',
    'signed-date': 'first',
    'description': lambda x: ', '.join(x.unique()),
    **{col: lambda x: x.iloc[-1] for col in data.columns if col not in ['award-id', 'ref-idv-id',
                                                                        'mod-number',
                                                                        'signed-date',
                                                                        'obligated-amount',
                                                                        'total-obligated-amount',
                                                                        'has-socio-data',
                                                                        'other-government-entities',
                                                                        'educational-entities',
                                                                        'description']}
}).reset_index()

grouped_data.loc[grouped_data['ref-idv-id'] == 'N/A', 'ref-idv-id'] = ''

grouped_data.to_excel('aggregate.xlsx', index=False)

import pandas as pd
from tqdm import tqdm
from fuzzywuzzy import process, fuzz

# legacy


def normalize(s):
    return s.lower().replace('.', '').replace(',', '')


aggregate_sbir = pd.read_excel('aggregate_sbir.xlsx')
aggregate_sttr = pd.read_excel('aggregate_sttr.xlsx')
aggregate = pd.concat([aggregate_sbir, aggregate_sttr])
data = pd.read_csv('award_data.csv')
data = data[data['Company'].apply(lambda x: isinstance(x, str))]


# Create normalized versions for matching
aggregate['legal-business-name-normalized'] = aggregate['legal-business-name'].apply(normalize)
data['Company-normalized'] = data['Company'].apply(normalize)

# Create a list of unique company names
unique_companies = aggregate['legal-business-name-normalized'].unique().tolist()
# Create a dictionary to store the matches
matches = {}
threshold = 95  # Set threshold you find appropriate

# Find the matches
for company in tqdm(unique_companies):
    highest = process.extractOne(company, data['Company-normalized'], scorer=fuzz.ratio)
    # if highest[1] >= threshold:
    matches[company] = {
        'Company': data.loc[data['Company-normalized'] == highest[0], 'Company'].iloc[0],
        'legal-business-name':
            aggregate.loc[aggregate['legal-business-name-normalized'] == company, 'legal-business-name'].iloc[0],
        'fuzz_score': highest[1]
    }

# Map normalized names back to original names
matches_df = pd.DataFrame(list(matches.values()))
matches_df['legal-business-name-normalized'] = matches.keys()

# Filter the data
filtered_data = pd.merge(data, matches_df, how='inner', on='Company')

# Find the missing companies
missing_companies = aggregate[~aggregate['legal-business-name-normalized'].isin(matches.keys())]

# Prepare the missing data dataframe
missing_data = pd.DataFrame({'legal-business-name': missing_companies['legal-business-name'],
                             'Company': '',
                             'fuzz_score': '0',
                             'Agency': '',
                             'Award Year': '',
                             'Award Amount': '',
                             'Program': '',
                             'Phase': ''})
missing_data = missing_data.drop_duplicates()

# Concatenate the filtered data and the missing data
filtered_data = pd.concat([filtered_data[['legal-business-name', 'Company', 'fuzz_score', 'Agency', 'Award Year',
                                          'Award Amount', 'Program', 'Phase']],
                           missing_data])

# Write the filtered data to a CSV file
filtered_data.to_csv('filtered.csv', index=False)

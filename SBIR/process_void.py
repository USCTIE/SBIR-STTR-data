import pandas as pd
from fuzzywuzzy import process
from crawler import normalize

# Load downloaded award data from SBIR website
data = pd.read_csv('award_data.csv')
data['Company'] = data['Company'].astype(str)
original_names = {normalize(name): name for name in data['Company']}
companies = pd.Series(list(original_names.keys())).drop_duplicates()

# Load scraped SBIR data to deal with companies with void records
df = pd.read_excel('sbir.xlsx')
df_copy = df.drop(columns='FPDS_legal business name')
mask = df_copy.isnull().all(axis=1)
empty_rows = df[mask]['FPDS_legal business name']
void_companies = empty_rows.tolist()


# Function to get the top 5 matches for a given company using a new fuzzy matching algorithm
def get_top_matches(company):
    matches = process.extract(normalize(company), companies, limit=5)
    matches = [(original_names[match], score) for match, score, _ in matches]
    return matches


# Execute the script and save the matches of companies with void records to an Excel file
matched_companies = {company: get_top_matches(company) for company in void_companies}
df_matched_companies = pd.DataFrame(matched_companies).T

df_matched_companies = df_matched_companies.applymap(lambda x: x[0] if x else "")

df_matched_companies.reset_index(level=0, inplace=True)

df_matched_companies.columns = ['company', 'top1', 'top2', 'top3', 'top4', 'top5']

df_matched_companies.to_excel('void_companies.xlsx', index=False)


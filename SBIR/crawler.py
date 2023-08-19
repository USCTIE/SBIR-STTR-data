import csv
import logging
import os
import random
import time
from fuzzywuzzy import process, fuzz

import requests
from bs4 import BeautifulSoup
import pandas as pd

from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor

from openpyxl.workbook import Workbook
from tqdm import tqdm
from contract import Contract

# Define constants
BASE_URL = "https://www.sbir.gov"
TIME_OUT = 60

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')


# Function to scrape contract information from a given URL
def scrape_contract_info(url, firm, company):
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            logger.info(f"Processing url for {company}: {url}")
            contract = Contract()
            contract_resp = requests.get(BASE_URL + url, timeout=TIME_OUT)
            contract_soup = BeautifulSoup(contract_resp.text, 'html.parser')
            award_info = contract_soup.find('div', class_='award-info-wrapper')
            agency_label = award_info.find('span', class_='open-label', string='Agency:')
            year_label = award_info.find('span', class_='open-label', string='Award Year:')
            amount_label = award_info.find('span', class_='open-label', string='Amount:')
            phase_label = award_info.find('span', class_='open-label', string='Phase:')
            program_label = award_info.find('span', class_='open-label', string='Program:')
            contract_id_label = award_info.find('span', class_='open-label', string='Contract:')
            DUNS_label = award_info.find('span', class_='open-label', string='DUNS:')
            if agency_label and agency_label.find_next_sibling('span', class_='open-description'):
                agency = agency_label.find_next_sibling('span', class_='open-description').text
            else:
                agency = ""
            if year_label and year_label.find_next_sibling('span', class_='open-description'):
                award_year = year_label.find_next_sibling('span', class_='open-description').text
            else:
                award_year = ""
            if amount_label and amount_label.find_next_sibling('span', class_='open-description'):
                amount = amount_label.find_next_sibling('span', class_='open-description').text
            else:
                amount = ""
            if phase_label and phase_label.find_next_sibling('span', class_='open-description'):
                phase = phase_label.find_next_sibling('span', class_='open-description').text
            else:
                phase = ""
            if program_label and program_label.find_next_sibling('span', class_='open-description'):
                program = program_label.find_next_sibling('span', class_='open-description').text
            else:
                program = ""
            if contract_id_label and contract_id_label.find_next_sibling('span', class_='open-description'):
                contract_id = contract_id_label.find_next_sibling('span', class_='open-description').text
            else:
                contract_id = ""
            if DUNS_label and DUNS_label.find_next_sibling('span', class_='open-description'):
                duns = DUNS_label.find_next_sibling('span', class_='open-description').text
            else:
                duns = ""
            contract.set_url(BASE_URL + url)
            contract.set_business(firm)
            contract.set_company(company)
            contract.set_agency(agency)
            contract.set_award_year(award_year)
            contract.set_amount(amount)
            contract.set_phase(phase)
            contract.set_program(program)
            contract.set_conract_id(contract_id)
            contract.set_DUNS(duns)
            return contract
        except Exception as e:
            logger.error(f"An error occurred while scraping contract info for {firm} - URL: {url}: {e}")
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying... Retry count: {retry_count}")
            else:
                logger.error(f"Max retry count reached. Skipping contract - URL: {url}")
                return None


# Function to scrape contracts for a given firm
def scrape_contracts(firm, name_dict):
    if name_dict[firm] == "":
        contract = Contract()
        contract.set_business(firm)
        return [contract]
    company = name_dict[firm]
    search_query = "/sbirsearch/award/all/?firm={}".format(company.replace("&", "%20%26%20")) \
        # + "&f%5B0%5D=im_field_phase%3A105788&f%5B1%5D=im_field_program%3A105791"
    session = requests.Session()
    search_resp = session.get(BASE_URL + search_query, timeout=TIME_OUT)
    search_soup = BeautifulSoup(search_resp.text, 'html.parser')
    # logger.info(f"Search firm {firm}")
    counter_element = search_soup.find(class_='search-result-counter')
    if not counter_element:
        contract = Contract()
        contract.set_business(firm)
        contract.set_company(company)
        return [contract]
    total_results = int(counter_element.text.strip().split(' ')[-1])
    search_results = search_soup.find_all('li', class_='search-result')
    urls = [result.find('a')['href'] for result in search_results
            if result.find('div', class_='search-result-sub-title').find('span').text[5:] == company]

    for i in range(1, -(-total_results // 10)):
        search_query += "&page={}".format(i)
        search_resp = session.get(BASE_URL + search_query, timeout=TIME_OUT)
        search_soup = BeautifulSoup(search_resp.text, 'html.parser')
        search_results = search_soup.find_all('li', class_='search-result')
        urls += [result.find('a')['href'] for result in search_results
                 if result.find('div', class_='search-result-sub-title').find('span').text[5:] == company]

    contracts = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrape_contract_info, url, firm, company) for url in urls]
        # for future in tqdm(as_completed(futures), total=len(futures), desc='Scraping contracts for {}'.format(firm)):
        for future in as_completed(futures):
            contract = future.result()
            if contract is not None:
                contracts.append(contract)
            # time.sleep(random.uniform(1, 3))

    # time.sleep(random.uniform(1, 3))

    return contracts


# Function to crawl and scrape contracts for multiple firms
def crawl(firms, name_dict):
    all_contracts = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrape_contracts, firm, name_dict) for firm in firms]
        for future in tqdm(as_completed(futures), total=len(futures), ncols=120):
            contracts = future.result()
            all_contracts.extend(contracts)
            # time.sleep(random.uniform(1, 3))
        executor.shutdown(wait=True)
    return all_contracts


# Function to read business name data from FPDS system
def read_businesses(file_paths=None):
    if file_paths is None:
        file_paths = ['aggregate_sbir.xlsx', 'aggregate_sttr.xlsx']
    aggregate_sbir = pd.read_excel(file_paths[0])
    aggregate_sttr = pd.read_excel(file_paths[1])
    aggregate = pd.concat([aggregate_sbir, aggregate_sttr])
    return aggregate[['legal-business-name', 'city', 'state']].drop_duplicates()


# Helper function to normalize strings
def normalize(s):
    return s.lower().replace('.', '').replace(',', '')


# Function to find the best match for a given firm in the data
def find_match(firm, data):
    normal_firm = normalize(firm)
    highest = process.extractOne(normal_firm, data['Company-normalized'], scorer=fuzz.ratio)
    matched_row = data[data['Company-normalized'] == highest[0]]
    company = matched_row['Company'].values[0]
    city = matched_row['City'].values[0]
    state = matched_row['State'].values[0]
    return firm, company, city, state, highest[1]


# Helper function to unpack parameters and find a match
def unpack_and_find_match(params):
    return find_match(*params)


# Function to read company name data from SBIR system and perform fuzzy matching
def read_companies(file_path='award_data.csv', fuzz_match='fuzz_match.csv'):
    if os.path.exists(fuzz_match):
        if os.path.exists('manual_record.xlsx'):
            update_fuzz_match()
        df = pd.read_csv(fuzz_match).fillna("")
        firms = df['FPDS_legal_business_name'].unique().tolist()
        firm_company_dict = df.set_index('FPDS_legal_business_name')['search_keyword'].to_dict()
        return firms, firm_company_dict
    firms_df = read_businesses()
    firms = firms_df['legal-business-name'].values
    data = pd.read_csv(file_path)
    data = data[data['Company'].apply(lambda x: isinstance(x, str))]
    data['Company-normalized'] = data['Company'].apply(normalize)

    # Prepare data for find_match function
    match_data = [(firm, data[['Company', 'Company-normalized', 'City', 'State']]) for firm in firms]

    with ProcessPoolExecutor() as executor:
        results = list(tqdm(executor.map(unpack_and_find_match, match_data), total=len(firms)))

    df = pd.DataFrame(results, columns=['FPDS_legal_business_name', 'SBIR_company', 'SBIR_city', 'SBIR_state',
                                        'fuzz_score'])
    firms_df = firms_df.rename(columns={'legal-business-name': 'FPDS_legal_business_name', 'city': 'FPDS_city',
                                        'state': 'FPDS_state'})
    df = pd.merge(firms_df, df, on='FPDS_legal_business_name')
    df = df[['FPDS_legal_business_name', 'SBIR_company', 'FPDS_city', 'FPDS_state', 'SBIR_city', 'SBIR_state',
             'fuzz_score']]
    df['search_keyword'] = ''
    df.loc[(df['fuzz_score'] > 95) | (
            (df['fuzz_score'] > 70) & (df['FPDS_city'].str.lower() == df['SBIR_city'].str.lower())
            & (df['FPDS_state'] == df['SBIR_state'])), 'search_keyword'] = df[
        'SBIR_company']
    df.to_csv('fuzz_match.csv', index=False)
    firms = df['FPDS_legal_business_name'].unique().tolist()
    firm_company_dict = df.set_index('FPDS_legal_business_name')['SBIR_company'].to_dict()
    if os.path.exists('manual_record.xlsx'):
        update_fuzz_match()
    return firms, firm_company_dict


# Function to update the fuzzy match data with manual records
def update_fuzz_match(fuzz_match='fuzz_match.csv', manual='manual_record.xlsx'):
    manual = pd.read_excel(manual, 'Manual')
    fuzz_match = pd.read_csv(fuzz_match)
    map_dict = manual.set_index('FPDS_legal_business_name')['SBIR_company'].to_dict()
    fuzz_match.loc[fuzz_match['FPDS_legal_business_name'].isin(map_dict.keys()), 'search_keyword'] = \
        fuzz_match['FPDS_legal_business_name'].map(map_dict)
    fuzz_match.to_csv('fuzz_match.csv', index=False)


# Function to write contracts to a CSV file
def write_csv(contracts, csv_file_path='sbir_phase_i.csv'):
    """
    Write contracts to a CSV file.
    :param csv_file_path:
    :param contracts:
    :return: output.csv
    """
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['business', 'year', 'agency', 'url'])

        # Write the header row
        writer.writeheader()

        # Write the contract data
        for contract in contracts:
            writer.writerow(vars(contract))

    print('CSV file has been generated.')


# Function to write contracts to an Excel file
def write_xlsx(contracts, xlsx_file_path='sbir.xlsx'):
    """
    Write contracts to an Excel file.
    :param xlsx_file_path:
    :param contracts:
    :return: output.xlsx
    """
    wb = Workbook()
    sheet = wb.active

    # Define the header row
    header = ['FPDS_legal business name', 'SBIR_company', 'year', 'agency', 'amount', 'program', 'phase', 'url',
              'contract ID', 'DUNS']
    sheet.append(header)

    # Write the contract data
    for contract in contracts:
        contract_data = []
        for field in header:
            if field == 'year':
                field = 'award_year'
            if field == 'FPDS_legal business name':
                field = 'legal_business_name'
            if field == 'SBIR_company':
                field = 'company'
            if field == 'contract ID':
                field = 'contract_id'
            value = getattr(contract, field)
            contract_data.append(value)
        sheet.append(contract_data)

    # Save the workbook to an XLSX file
    wb.save(xlsx_file_path)

    print('XLSX file has been generated.')


# Function to process special cases in the contracts
def process_specials(contracts='sbir.xlsx', award_data='award_data.csv'):
    df_contracts = pd.read_excel(contracts)
    df_award_data = pd.read_csv(award_data)

    filtered_df = df_contracts[(df_contracts['SBIR_company'].notna()) & (df_contracts['year'].isna())]
    indices_to_drop = filtered_df.index
    df_contracts.drop(indices_to_drop, inplace=True)

    for _, row in tqdm(filtered_df.iterrows(), total=filtered_df.shape[0]):
        matching_rows = df_award_data[df_award_data['Company'] == row['SBIR_company']]
        for _, matching_row in matching_rows.iterrows():
            new_row = pd.DataFrame({
                'FPDS_legal business name': [row['FPDS_legal business name']],
                'SBIR_company': [row['SBIR_company']],
                'year': [matching_row['Award Year']],
                'agency': [matching_row['Agency']],
                'amount': [matching_row['Award Amount']],
                'program': [matching_row['Program']],
                'phase': [matching_row['Phase']],
                'url': "",
                'contract ID': [matching_row['Contract']],
                'DUNS': [matching_row['Duns']],
            })

            df_contracts = pd.concat([df_contracts, new_row], ignore_index=True)

    df_contracts.to_excel(contracts, index=False)


if __name__ == '__main__':
    businesses, companies = read_companies()
    res = crawl(businesses, companies)
    contract_companies = set(contract.company for contract in res)
    missing_firms = [firm for firm in businesses if companies.get(firm) not in contract_companies]
    if missing_firms:
        missing_companies = {companies.get(firm) for firm in missing_firms}
        res = [contract for contract in res
               if contract.legal_business_name not in missing_companies]
        print(f'Retrying for {len(missing_firms)} missing firms.')
        res += crawl(missing_firms, companies)
    write_xlsx(res)
    print('total contracts: ' + str(len(res)))
    process_specials()

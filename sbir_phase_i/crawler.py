import csv
import logging
import random
import time

import requests
from bs4 import BeautifulSoup
import pandas as pd

from concurrent.futures import ThreadPoolExecutor, as_completed

from openpyxl.workbook import Workbook
from tqdm import tqdm
from sbir_phase_i.contract import Contract

BASE_URL = "https://www.sbir.gov"
TIME_OUT = 60

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')


def scrape_contract_info(url, firm):
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            logger.info(f"Processing url for {firm}: {url}")
            contract = Contract()
            contract_resp = requests.get(BASE_URL + url, timeout=TIME_OUT)
            contract_soup = BeautifulSoup(contract_resp.text, 'html.parser')
            award_info = contract_soup.find('div', class_='award-info-wrapper')
            agency_label = award_info.find('span', class_='open-label', string='Agency:')
            year_label = award_info.find('span', class_='open-label', string='Award Year:')
            if agency_label and agency_label.find_next_sibling('span', class_='open-description'):
                agency = agency_label.find_next_sibling('span', class_='open-description').text
            else:
                agency = ""
            if year_label and year_label.find_next_sibling('span', class_='open-description'):
                award_year = year_label.find_next_sibling('span', class_='open-description').text
            else:
                award_year = ""
            contract.set_url(BASE_URL + url)
            contract.set_business(firm)
            contract.set_agency(agency)
            contract.set_award_year(award_year)
            return contract
        except Exception as e:
            logger.error(f"An error occurred while scraping contract info for {firm} - URL: {url}: {e}")
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying... Retry count: {retry_count}")
            else:
                logger.error(f"Max retry count reached. Skipping contract - URL: {url}")
                return None


def scrape_contracts(firm):
    search_query = "/sbirsearch/award/all/?firm={}" \
                   "&f%5B0%5D=im_field_phase%3A105788&f%5B1%5D=im_field_program%3A105791".format(firm)
    session = requests.Session()
    search_resp = session.get(BASE_URL + search_query, timeout=TIME_OUT)
    search_soup = BeautifulSoup(search_resp.text, 'html.parser')
    # logger.info(f"Search firm {firm}")
    counter_element = search_soup.find(class_='search-result-counter')
    if not counter_element:
        contract = Contract()
        contract.set_business(firm)
        return [contract]
    total_results = int(counter_element.text.strip().split(' ')[-1])
    search_results = search_soup.find_all('li', class_='search-result')
    urls = [result.find('a')['href'] for result in search_results]

    for i in range(1, -(-total_results // 10)):
        search_query += "&page={}".format(i)
        search_resp = session.get(BASE_URL + search_query, timeout=TIME_OUT)
        search_soup = BeautifulSoup(search_resp.text, 'html.parser')
        search_results = search_soup.find_all('li', class_='search-result')
        urls += [result.find('a')['href'] for result in search_results]

    contracts = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrape_contract_info, url, firm) for url in urls]
        # for future in tqdm(as_completed(futures), total=len(futures), desc='Scraping contracts for {}'.format(firm)):
        for future in as_completed(futures):
            contract = future.result()
            if contract is not None:
                contracts.append(contract)
            # time.sleep(random.uniform(1, 3))

    # time.sleep(random.uniform(1, 3))

    return contracts


def crawl(firms):
    all_contracts = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrape_contracts, firm) for firm in firms]
        for future in tqdm(as_completed(futures), total=len(futures), ncols=120):
            contracts = future.result()
            all_contracts.extend(contracts)
            # time.sleep(random.uniform(1, 3))
        executor.shutdown(wait=True)
    return all_contracts


def read_businesses(file_path='aggregate.xlsx'):
    data = pd.read_excel(file_path)
    firms = data['legal-business-name'].unique()
    firms = [name.replace("&", "%20%26%20") for name in firms]
    firms.remove('SYS')
    return firms


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


def write_xlsx(contracts, xlsx_file_path='sbir_phase_i.xlsx'):
    """
    Write contracts to an Excel file.
    :param xlsx_file_path:
    :param contracts:
    :return: output.xlsx
    """
    wb = Workbook()
    sheet = wb.active

    # Define the header row
    header = ['business', 'year', 'agency', 'url']
    sheet.append(header)

    # Write the contract data
    for contract in contracts:
        contract_data = []
        for field in header:
            if field == 'year':
                field = 'award_year'
            value = getattr(contract, field)
            contract_data.append(value)
        sheet.append(contract_data)

    # Save the workbook to an XLSX file
    wb.save(xlsx_file_path)

    print('XLSX file has been generated.')


if __name__ == '__main__':
    companies = read_businesses()
    res = crawl(companies)
    write_xlsx(res)
    print('total contracts: ' + str(len(res)))

import re

from bs4 import BeautifulSoup
import requests
from contract import Contract
import concurrent.futures
from multiprocessing import Pool
from tqdm import tqdm
import csv
import logging
from openpyxl import Workbook
from collections import defaultdict
from line_profiler import LineProfiler
import time
from requests.exceptions import ReadTimeout

# set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')

# total count placeholder
TOTAL_COUNT = 90

BASE_URL = "https://www.fpds.gov"

# output paths
csv_file_path = "output.csv"
xlsx_file_path = "output.xlsx"

# required fields
fieldnames = ['url', 'solicitation_id', 'mod_number', 'award_id', 'ref_idv_id', 'award_type', 'obligated_amount',
              'total_obligated_amount', 'signed_date', 'contracting_office_id', 'contracting_office',
              'funding_request_id', 'funding_request', 'legal_business_name', 'DBAN', 'city', 'state',
              'unique_entity_id', 'has_socio_data', 'business_type', 'socio_data', 'line_of_business',
              'relationship_with_government', 'other_government_entities', 'organization_factors',
              'educational_entities', 'certifications', 'description']

# set up retry
retry_attempts = 3
retry_delay = 5


def get_award_id(soup):
    award_id_tag = soup.find('input', {'id': 'PIID'})
    if award_id_tag:
        award_id = award_id_tag['value']
        return award_id
    return ""


def get_idv_id(soup):
    idv_id_tag = soup.find('input', {'id': 'idvPIID'})
    if idv_id_tag:
        idv_id = idv_id_tag['value']
        return idv_id
    return ""


def get_award_type(soup):
    award_type_tag = soup.find('td', {'id': 'displayAwardType'})
    if award_type_tag:
        award_type = award_type_tag.text
        return award_type
    return ""


def get_solicitation_id(soup):
    solicitation_tag = soup.find('input', {'id': 'solicitationID'})
    if solicitation_tag:
        solicitation_id = solicitation_tag['value']
        return solicitation_id
    return ""


def get_mod_num(soup):
    mod_tag = soup.find('input', {'id': 'modNumber'})
    if mod_tag:
        mod_number = mod_tag['value']
        return mod_number
    return ""


def get_obligated_amount(soup):
    obligated_amount_tag = soup.find('input', {'id': 'obligatedAmount'})
    if obligated_amount_tag:
        obligated_amount = obligated_amount_tag['value']
        return obligated_amount
    return ""


def get_total_obligated_amount(soup):
    total_obligated_amount_tag = soup.find('input', {'id': 'totalObligatedAmount'})
    if total_obligated_amount_tag and 'value' in total_obligated_amount_tag.attrs:
        total_obligated_amount = total_obligated_amount_tag['value']
        return total_obligated_amount
    return "$0.00"


def get_signed_date(soup):
    signed_date_tag = soup.find('input', {'id': 'signedDate'})
    if signed_date_tag:
        signed_date = signed_date_tag['value']
        return signed_date
    return ""


def get_contracting_office_id(soup):
    contracting_office_id_tag = soup.find('input', {'id': 'contractingOfficeAgencyID'})
    if contracting_office_id_tag:
        contracting_office_id = contracting_office_id_tag['value']
        return contracting_office_id
    return ""


def get_contracting_office(soup):
    contracting_office_tag = soup.find('input', {'id': 'contractingOfficeAgencyName'})
    if contracting_office_tag:
        contracting_office = contracting_office_tag['value']
        return contracting_office
    return ""


def get_funding_request_id(soup):
    funding_request_id_tag = soup.find('input', {'id': 'fundingRequestingAgencyID'})
    if funding_request_id_tag:
        funding_request_id = funding_request_id_tag['value']
        return funding_request_id
    return ""


def get_funding_request(soup):
    funding_request_tag = soup.find('input', {'id': 'fundingRequestingAgencyName'})
    if funding_request_tag:
        funding_request = funding_request_tag['value']
        return funding_request
    return ""


def get_legal_business_name(soup):
    vendor_name_tag = soup.find('input', {'id': 'vendorName'})
    if vendor_name_tag:
        vendor_name = vendor_name_tag['value']
        return vendor_name
    return ""


def get_DBAN(soup):
    DBAN_tag = soup.find('input', {'id': 'vendorDoingAsBusinessName'})
    if DBAN_tag:
        DBAN_name = DBAN_tag['value']
        return DBAN_name
    return ""


def get_city(soup):
    city_tag = soup.find('input', {'id': 'vendorCity'})
    if city_tag:
        city_name = city_tag['value']
        return city_name
    return ""


def get_state(soup):
    state_tag = soup.find('input', {'id': 'vendorState'})
    if state_tag:
        state_code = state_tag['value']
        return state_code
    return ""


def get_unique_entity_id(soup):
    UEI_tag = soup.find('input', {'id': 'UEINumber'})
    if UEI_tag:
        UEI_number = UEI_tag['value']
        return UEI_number
    return ""


def get_checked_categories(tr):
    # for contracts after 2010, the page uses checkbox for various categories
    categories = []
    checkboxes = tr.find_all('input', {'type': 'checkbox'})
    for checkbox in checkboxes:
        category_name = checkbox.find_next('td').text.strip()
        is_checked = checkbox.get('checked') == 'true'
        if is_checked:
            categories.append(category_name)
    return ",".join(categories)


def get_business_type(soup):
    business_type_tr = soup.find('tr', id='busTypestr')
    return get_checked_categories(business_type_tr)


def get_socio_data(soup, has_socio_data):
    categories = []
    # for contracts before 2010
    if has_socio_data:
        sentinal = soup.find('tr', id='ccrVersion')
        if sentinal:
            tr = sentinal.find_next_sibling('tr')
            td = tr.find_all('td')[0]
            socio_data_td = td.findNext('td').find_next_sibling('td')
            checkboxes = socio_data_td.find_all('input', {'type': 'checkbox'})
            for checkbox in checkboxes:
                category_name = checkbox.find_next('td').get_text(strip=True)
                is_checked = checkbox.get('checked') == 'true'
                if is_checked:
                    categories.append(category_name)
    # for contracts after 2010
    else:
        socio_data_tr = soup.find('tr', id='sociotr')
        checkboxes = socio_data_tr.find_all('input', {'type': 'checkbox'})
        for checkbox in checkboxes:
            category_name = checkbox.find_next('td').text.strip()
            is_checked = checkbox.get('checked') == 'true'
            if is_checked:
                categories.append(category_name)
    return ",".join(categories)


def get_line_of_business(soup):
    line_of_business_tr = soup.find('tr', id='lobtr')
    return get_checked_categories(line_of_business_tr)


def get_relationship_with_government(soup):
    relationship_with_government_tr = soup.find('tr', id='relWithFedGovtr')
    return get_checked_categories(relationship_with_government_tr)


def get_other_government_entities(soup):
    other_government_entities_tr = soup.find('tr', id='otherGovEnttr')
    return get_checked_categories(other_government_entities_tr)


def get_organization_factors(soup):
    organization_factors_tr = soup.find('tr', id='orgFactorstr')
    return get_checked_categories(organization_factors_tr)


def get_educational_entities(soup):
    educational_entities_tr = soup.find('tr', id='eduEnttr')
    return get_checked_categories(educational_entities_tr)


def get_certifications(soup):
    certifications_tr = soup.find('tr', id='certtr')
    return get_checked_categories(certifications_tr)


def get_description(soup):
    textarea = soup.find('textarea', {'id': 'descriptionOfContractRequirement'})
    if textarea:
        description = textarea.text.strip()
        return description
    return ""


def process_contract(link):
    """
    Process a contract given its URL and retrieve the contract information.
    Generate a BeautifulSoup object and calls get_{fieldname}().

    :param link: URL of the contract
    :return: Contract object containing the contract information
    """
    for attempt in range(retry_attempts):
        try:
            contract = Contract()
            contract.set_url(link)
            # logger.info(f"Processing link under url: {link}")
            contract_res = requests.get(link, timeout=60)
            contract_soup = BeautifulSoup(contract_res.text, 'html.parser')

            contract.set_award_id(get_award_id(contract_soup))
            contract.set_ref_idv_id(get_idv_id(contract_soup))
            contract.set_award_type(get_award_type(contract_soup))

            contract.set_solicidation_id(get_solicitation_id(contract_soup))
            contract.set_mod_number(get_mod_num(contract_soup))

            contract.set_obligated_amount(get_obligated_amount(contract_soup))
            contract.set_total_obligated_amount(get_total_obligated_amount(contract_soup))
            contract.set_signed_date(get_signed_date(contract_soup))

            contract.set_contracting_office_id(get_contracting_office_id(contract_soup))
            contract.set_contracting_office(get_contracting_office(contract_soup))

            contract.set_funding_request_id(get_funding_request_id(contract_soup))
            contract.set_funding_request(get_funding_request(contract_soup))

            contract.set_legal_business_name(get_legal_business_name(contract_soup))
            contract.set_DBAN(get_DBAN(contract_soup))

            contract.set_city(get_city(contract_soup))
            contract.set_state(get_state(contract_soup))

            contract.set_unique_entity_id(get_unique_entity_id(contract_soup))

            socio_data_tag = contract_soup.find('tr', {'id': 'vendorDetails'})
            if socio_data_tag and 'style' in socio_data_tag.attrs:
                if 'display:none' in socio_data_tag['style']:
                    contract.toggle_has_socio_data()

            if not contract.has_socio_data:
                contract.set_business_type(get_business_type(contract_soup))
                contract.set_line_of_business(get_line_of_business(contract_soup))
                contract.set_relationship_with_government(get_relationship_with_government(contract_soup))
                contract.set_other_government_entities(get_other_government_entities(contract_soup))
                contract.set_organization_factors(get_organization_factors(contract_soup))
                contract.set_educational_entities(get_educational_entities(contract_soup))
                contract.set_certifications(get_certifications(contract_soup))
            contract.set_socio_data(get_socio_data(contract_soup, contract.has_socio_data))

            contract.set_description(get_description(contract_soup))

            # if not contract.award_id:
            #     raise ValueError("Empty award ID.")

            return contract

        except requests.exceptions.RequestException as exception:
            print(f"An error occurred while processing contract from {link}: {exception}")
            time.sleep(retry_delay)
            print(f"Request timed out. Retrying... (Attempt {attempt + 1}/{retry_attempts})")

        # except ValueError as exception:
        #     print(f"An error occurred while processing contract from {link}: {exception}")
        #     time.sleep(retry_delay)
        #     print(f"Empty value. Retrying... (Attempt {attempt + 1}/{retry_attempts})")

        except Exception as exception:
            print(f"An unexpected error occurred while processing contract from {link}: {exception}")
            time.sleep(retry_delay)
            print(f"Unexpected error. Retrying... (Attempt {attempt + 1}/{retry_attempts})")

    return None


# @profile
def get_contract_info_for_30(url):
    """
    Process all contracts on one page by calling process_contract().

    :param url: URL of a contract list page
    :return: List of Contract objects
    """
    # logger.info(f"Processing url: {url}")
    for attempt in range(retry_attempts):
        try:
            # Retrieve the target url links for the 30 contracts
            session = requests.Session()
            search_res = session.get(url, timeout=60)
            search_soup = BeautifulSoup(search_res.text, 'html.parser')
            view_tags = search_soup.find_all('a', {'title': 'View'})
            hrefs = [a['href'] for a in view_tags]
            links = []
            for href in hrefs:
                start_index = href.index("('/") + 2
                end_index = href.index("')")
                query = href[start_index:end_index]
                links.append(BASE_URL + query)

            contracts = []
            retry_links = []
            # Parse the required fields in contract detail
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(process_contract, links)
                for result in results:
                    if result.award_id:
                        contracts.append(result)
                    else:
                        retry_links.append(result.url)

            retry_contracts = []
            while retry_links:
                link = retry_links.pop()
                logger.info(f"Empty value. Retrying for: {link}")
                retry_contract = process_contract(link)
                if retry_contract.award_id:
                    retry_contracts.append(retry_contract)
                else:
                    retry_contracts.append(link)

            contracts += retry_contracts

            return contracts

        except requests.exceptions.RequestException as exception:
            print(f"An error occurred while processing batch from {url}: {exception}")
            time.sleep(retry_delay)
            print(f"Request timed out. Retrying... (Attempt {attempt + 1}/{retry_attempts})")

        except Exception as exception:
            print(f"An unexpected error occurred while processing batch from {url}: {exception}")
            time.sleep(retry_delay)
            print(f"Unexpected error. Retrying... (Attempt {attempt + 1}/{retry_attempts})")

    return []


def process_page_for_award_id(url):
    """
    Process a page to extract award IDs and IDV IDs.

    :param url: URL of the page to process
    :return: Set of award IDs and dictionary of IDV IDs mapped to award IDs
    """
    award_ids = set()
    idv_ids = defaultdict(set)
    session = requests.Session()
    search_res = session.get(url, timeout=60)
    soup = BeautifulSoup(search_res.text, 'html.parser')
    tables = soup.find_all('table', class_=['resultbox1', 'resultbox2'])
    for table in tables:
        award_id_tag = table.find('a', title=lambda value: value and 'Click here to drill down by Award ID' in value)
        award_id = award_id_tag.text.strip()
        referenced_idv_tag = table.find('a', title=lambda value: value and 'Click here to drill down by Referenced IDV' in value)
        referenced_idv = referenced_idv_tag.text.strip()
        award_ids.add(award_id)
        if referenced_idv:
            idv_ids[award_id].add(referenced_idv)
    return award_ids, idv_ids


def get_award_ids():
    """
    Retrieve the target set of award IDs and IDV IDs.

    :return: Set of award IDs and dictionary of IDV IDs mapped to award IDs
    """
    award_ids = set()
    idv_ids = defaultdict(set)
    search_query = "/ezsearch/search.do?indexName=awardfull&templateName=1.5.3&s=FPDS.GOV&q=sbir+phase+iii"
    resp = requests.get(BASE_URL + search_query, timeout=60)
    start_page = BeautifulSoup(resp.text, 'html.parser')
    total_tag = start_page.find('b', string='30').find_next_sibling('b')
    total = int(total_tag.text)
    # total = 0
    urls = [BASE_URL + search_query + "&start=" + str(i * 30) for i in range(total // 30 + 1)]
    logger.info(f"Searching for award ids")
    with concurrent.futures.ThreadPoolExecutor() as executor, tqdm(total=len(urls), ncols=120) as pbar:
        results = executor.map(process_page_for_award_id, urls)
        for result in results:
            result_award_ids, result_idv_ids = result
            award_ids.update(result_award_ids)
            for award_id, idvs in result_idv_ids.items():
                idv_ids[award_id].update(idvs)
            pbar.update(1)
    return award_ids, idv_ids


def process_award_id(award_id, idv_ids):
    """
    Process an award ID and its associated IDV IDs to generate URLs for contract processing.

    :param award_id: Award ID to process
    :param idv_ids: Dictionary of IDV IDs mapped to the award ID
    :return: List of URLs to process
    """
    urls = []
    queries = []
    search = "/ezsearch/fpdsportal?indexName=awardfull&templateName=1.5.3&s=FPDS.GOV&q=PIID%3A%22{}%22".format(award_id)
    if not idv_ids[award_id]:
        queries.append(search)
    while idv_ids[award_id]:
        idv_id = idv_ids[award_id].pop()
        queries.append(search + "+REF_IDV_PIID%3A%22{}%22".format(idv_id))
    for query in queries:
        resp = requests.get(BASE_URL + query, timeout=60)
        start_page = BeautifulSoup(resp.text, 'html.parser')
        page_num_tag = start_page.find_all('span', class_='results_heading')[1]
        total_page_tag = page_num_tag.find_all('b')[-1]
        total = int(total_page_tag.text)
        urls += [BASE_URL + query + "&start=" + str(i * 30) for i in range(total // 30 + 1)]
    # if len(urls) > 50:
    #     print("{}: {}, link: {}".format(award_id, len(urls), BASE_URL + search_query))
    return urls


def get_target_urls():
    """
    Retrieve the target URLs for contract processing.

    :return: List of target URLs
    """
    award_ids, idv_ids = get_award_ids()
    # award_ids.add("0060")
    urls = []
    logger.info(f"Generating urls")
    with concurrent.futures.ThreadPoolExecutor() as executor, tqdm(total=len(award_ids), ncols=160) as pbar:
        future_to_url = {executor.submit(process_award_id, award_id, idv_ids): award_id for award_id in award_ids}
        for future in concurrent.futures.as_completed(future_to_url):
            award_id = future_to_url[future]
            try:
                urls.extend(future.result())
            except Exception as exception:
                print(f"Error processing award ID {award_id}: {exception}")
            pbar.update(1)
    return urls


def thread_crawl():
    """
    Perform threaded crawling to retrieve contract information.

    Note: Speed depends on network and core number. Usually finishes in 2-3 hours.

    :return: List of Contract objects
    """
    urls = get_target_urls()
    contracts = []
    logger.info(f"Processing url for contract info")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks for each URL
        future_contracts = [executor.submit(get_contract_info_for_30, url) for url in urls]

        # Retrieve the completed contracts with progress bar
        with tqdm(total=len(future_contracts), ncols=200) as pbar:
            for future in concurrent.futures.as_completed(future_contracts):
                contracts += future.result()
                pbar.update(1)

    # for contract in contracts:
    #     print(contract)
    print('total contracts: ' + str(len(contracts)))
    return contracts


def process_crawl():
    """
    Legacy function. Please use thread_crawl instead.

    Note: process pool performs well on small sample, while thread pool is significantly better on large data.
    """
    search_query = "/ezsearch/search.do?indexName=awardfull&templateName=1.5.3&s=FPDS.GOV&q=sbir+phase+iii"
    # Loop over all search results
    urls = [BASE_URL + search_query + "&start=" + str(i * 30) for i in range(TOTAL_COUNT // 30 + 1)]
    contracts = []
    pool = Pool(processes=8)
    future_contracts = pool.starmap(get_contract_info_for_30, [(url,) for url in urls])

    for result in future_contracts:
        contracts += result

    print('total contracts: ' + str(len(contracts)))
    return contracts


def write_csv(contracts):
    """
    Write contracts to a CSV file.
    :param contracts:
    :return: output.csv
    """
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

        # Write the contract data
        for contract in contracts:
            writer.writerow(vars(contract))

    print('CSV file has been generated.')


def write_xlsx(contracts):
    """
    Write contracts to an Excel file.
    :param contracts:
    :return: output.xlsx
    """
    wb = Workbook()
    sheet = wb.active

    # Define the header row
    header = [field.replace('_', '-') for field in fieldnames]
    sheet.append(header)

    # Write the contract data
    for contract in contracts:
        contract_data = []
        for field in fieldnames:
            value = getattr(contract, field)
            if field == "description":
                sanitized_value = re.sub(r'[\\/*?:\[\]]', '', str(value))
                contract_data.append(sanitized_value)
            else:
                contract_data.append(value)
        sheet.append(contract_data)

    # Save the workbook to an XLSX file
    wb.save(xlsx_file_path)

    print('XLSX file has been generated.')


def test():
    """
    Legacy function.
    """
    search_query = "/ezsearch/search.do?indexName=awardfull&templateName=1.5.3&s=FPDS.GOV&q=sbir+phase+iii"
    # Loop over all search results
    urls = [BASE_URL + search_query + "&start=" + str(i * 30) for i in range(TOTAL_COUNT // 30 + 1)]
    count = 0
    for url in urls:
        count += 1
        print(count)
        get_contract_info_for_30(url)


if __name__ == "__main__":
    # print(get_target_urls())
    output = thread_crawl()
    try:
        write_xlsx(output)
    except Exception as e:
        print(f"Error occurred while writing to XLSX: {e}")
        print("Attempting to write to CSV instead...")
        try:
            write_csv(output)
        except Exception as e:
            print(f"Error occurred while writing to CSV: {e}")
            print("Both XLSX and CSV write operations failed.")
    # write(process_crawl())
    # test()

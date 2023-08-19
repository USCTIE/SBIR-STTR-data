# SBIR/STTR data project
This project is designed to retrieve and process contract data from a government procurement website. It
used to retrieve information related to SBIR/STTR phase III data from the FPDS website and now also includes functionality to fetch phase I and II data from the SBIR website.


## Directory Structure
- FPDS: Contains codebase related to data retrieval and processing from fpds.gov.
  - `crawler.py`: Script for crawling FPDS data.
  - `contract.py`: Object for processing FPDS contract data.
  - `aggregate.py`: Script for aggregating the output results.
  - `output_sbir.xlsx`: Search results for SBIR phase III.
  - `output_sttr.xlsx`: Search results for STTR phase III.
  - `aggregate_sbir.xlsx`: Aggregated results for SBIR phase III.
  - `aggregate_sttr.xlsx`: Aggregated results for STTR phase III.
- SBIR: Contains codebase related to data retrieval and processing from sbir.gov.
  - `process_void.py`: Script for processing companies with void records in SBIR.
  - `crawler.py`: Script for crawling SBIR data. 
  - `contract.py`: Object for processing SBIR contract data. 
  - `filter.py`: Legacy script for company names matching.
  - `fuzz_match.csv`: Fuzzy match results for company names and search key to use in search in sbir.gov
  - `void_companies.xlsx`: Top 5 candidates for companies with void records in SBIR.
  - `manual_record.xlsx`: Manual matching records for company names.
  - `sbir.xlsx`: Final results for SBIR/STTR phase I & II contracts data.



## Workflow

1. Retrieve SBIR/STTR phase III contracts from fpds.gov
- Retrieves award IDs and corresponding IDVs (Indefinite Delivery Vehicles) from the government procurement website (`fpds.gov`).
- Generates URLs for contract details based on the retrieved award IDs and IDVs.
- Follow these URLs to generate detail pages for each contract.
- Retrieves and processes contract details for each page.
- Supports nested multithreaded processing for improved performance.
- Exports the processed contract data to CSV or XLSX files.

2. Find match company names in `sbir.gov` corresponding to the business name in `fpds.gov` (This is where large manual work is needed)
- Use different fuzz algorithms to capture most accurate results
- Keep top 5 candidates for void companies
- Manual go over the rest companies, find out their history of acquisition, merge, name change, etc.

3. Retrieve corresponding phase I & II contract data from sbir.gov
- Utilizes the matched company names from the previous step to search for contracts on the SBIR website. 
- Generates search queries based on the matched company names to retrieve relevant contract data. 
- Uses nested multi-threaded crawling to efficiently navigate through the SBIR website and extract contract details. 
- Exports the consolidated contract data to CSV or XLSX files.


## Prerequisites

Before running the project, make sure you have the following prerequisites:

- Python 3.8 or higher
- Required Python packages (specified in `requirements.txt`)
- It is very much recommended to use a virtual environment (follow `Setup`)

## Setup

1. Clone the repository:

    `git clone https://github.com/USCTIE/SBIR-STTR-data.git`
2. Navigate to the project directory:

    `cd SBIR-STTR-data`
3. Set up a virtual environment to isolate project dependencies:

    `python -m venv env`
4. Activate the virtual environment:

    For Windows:
    
    `env\Scripts\activate`

    For macOS and Linux:

    `source env/bin/activate`
5. Install the required dependencies:

    `pip install -r requirements.txt`

## Usage
To run the project, Navigate to the desired directory (`FPDS` or `SBIR`) and run the respective crawler script:

`python crawler.py`

The project will retrieve the contract data, process it, and generate CSV or XLSX files with the extracted information.
Execution speed really depends on the network condition and the number of available cores. In most situations it will complete in 1-2 hours.

## Data Dictionary for FPDS Data

- `award_id`: The unique identifier for each contract, agreement or order.
- `ref_idv_id`: When reporting orders under Indefinite Delivery Vehicles (IDV) such as a GWAC, IDC, FSS, BOA, or BPA, report the Procurement Instrument Identifier (Contract Number or Agreement Number) of the IDV. For the initial load of a BPA under a FSS, this is the FSS contract number. Note: BOAs and BPAs are with industry and not with other Federal Agencies.
**Some old contracts use this as the unique identifier, such for `award_id` 0001**.
- `award_type`: The type of award being entered by this transaction. Types of awards include Purchase Orders (PO), Delivery Orders (DO), BPA Calls and Definitive Contracts.
- `solicitation_id`: Identifier used to link transactions in FPDS-NG to solicitation information.
- `mod_number`: An identifier issued by an agency that uniquely identifies one modification for one contract, agreement, order, etc.
- `obligated_amount`: The amount that is obligated or de-obligated for this modification.
- `total_obligated_amount`: The **latest** total amount obligated for the contract.
- `signed_date`: The date that a mutually binding agreement was reached. The date signed by the Contracting Officer or the Contractor, whichever is later.
- `contracting_office_id`: The agency supplied code of the contracting office that executes the transaction.
- `contracting_office`: The name of the contracting office.
- `funding_request_id`: The FIPS Pub. 95 code for the agency that provided the preponderance of the funds obligated by this transaction.
- `funding_request`: The name of the funding request agency.
- `legal_business_name`: The legal name of the business associated with the contract.
- `DBAN`: The Doing Business As Name (DBAN) for the business.
- `city`: The city where the contractor is located.
- `state`: The state where the contractor is located.
- `unique_entity_id`: The unique identifier for the contractor entity.
- `has_socio_data`: Indicates if socio-economic data is displayed independently. **Usually contracts before 2009 does that.**
- `business_type`: The type of business.
- `line_of_business`: The line of business associated with the contract.
- `relationship_with_government`: The relationship of the business with the government.
- `other_government_entities`: Other government entities associated with the contract.
- `organization_factors`: Factors related to the organization.
- `educational_entities`: Educational entities associated with the contract.
- `certifications`: Certifications held by the business.
- `socio_data`: Socio-economic data associated with the contract.
- `description`: A brief description of the contract or award.


## Data Dictionary for SBIR Data
- `FPDS_legal_business_name`: The legal name of the business associated with the award. (From fpds.gov)
- `SBIR_company`: The official name of the company receiving the award. (From sbir.gov)
- `year`: The year in which the award was granted.
- `agency`: The federal agency that granted the award.
- `amount`: The monetary value of the award.
- `program`: The specific SBIR/STTR program under which the award was granted.
- `phase`: The phase of the SBIR/STTR program (I or II).
- `url`: The URL pointing to the detailed page of the specific award on the SBIR website.
- `contract ID`: The unique contract identifier associated with the award.
- `DUNS`: The Data Universal Numbering System identifier for the business.


## Contact

For any inquiries or feedback, feel free to reach out to us:

- Vincent Zhu - zhuwenxu@usc.edu

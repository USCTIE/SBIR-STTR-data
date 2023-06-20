# SBIR-phase-iii-data
This project is designed to retrieve and process contract data from a government procurement website. It extracts contract information, such as solicitation IDs, vendor details, funding requests, and more, for a specific search query related to SBIR phase III contracts.

## Workflow

- Retrieves award IDs and corresponding IDVs (Indefinite Delivery Vehicles) from the government procurement website (`fpds.gov`).
- Generates URLs for contract details based on the retrieved award IDs and IDVs.
- Follow these URLs to generate detail pages for each contract.
- Retrieves and processes contract details for each page.
- Supports nested multithreaded processing for improved performance.
- Exports the processed contract data to CSV or XLSX files.


## Prerequisites

Before running the project, make sure you have the following prerequisites:

- Python 3.8 or higher
- Required Python packages (specified in `requirements.txt`)
- It is very much recommended to use a virtual environment (follow `Setup`)

## Setup

1. Clone the repository:

    `git clone https://github.com/USCTIE/SBIR-phase-iii-data.git`
2. Navigate to the project directory:

    `cd SBIR-phase-iii-data`
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
To run the project, execute the following command:

`python crawler.py`

The project will retrieve the contract data, process it, and generate CSV or XLSX files with the extracted information.
Execution speed really depends on the network condition and the number of available cores. In most situations it will complete in 1-2 hours.

## Data Dictionary

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

## Contact

For any inquiries or feedback, feel free to reach out to us:

- Vincent Zhu - zhuwenxu@usc.edu
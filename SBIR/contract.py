class Contract:
    def __init__(self):
        self.legal_business_name = ""
        self.company = ""
        self.award_year = ""
        self.agency = ""
        self.amount = ""
        self.phase = ""
        self.program = ""
        self.url = ""
        self.contract_id = ""
        self.DUNS = ""

    def __str__(self):
        return f"ContractInfo: {vars(self)}"

    def set_business(self, business):
        self.legal_business_name = business

    def set_company(self, company):
        self.company = company

    def set_award_year(self, award_year):
        self.award_year = award_year

    def set_agency(self, agency):
        self.agency = agency

    def set_amount(self, amount):
        self.amount = amount

    def set_phase(self, phase):
        self.phase = phase

    def set_program(self, program):
        self.program = program

    def set_url(self, url):
        self.url = url

    def set_conract_id(self, contract_id):
        self.contract_id = contract_id

    def set_DUNS(self, duns):
        self.DUNS = duns

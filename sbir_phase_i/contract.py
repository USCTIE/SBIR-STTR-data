class Contract:
    def __init__(self):
        self.business = ""
        self.award_year = ""
        self.agency = ""
        self.url = ""

    def __str__(self):
        return f"ContractInfo: {vars(self)}"

    def set_business(self, business):
        self.business = business

    def set_award_year(self, award_year):
        self.award_year = award_year

    def set_agency(self, agency):
        self.agency = agency

    def set_url(self, url):
        self.url = url

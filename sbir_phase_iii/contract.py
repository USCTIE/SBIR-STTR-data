class Contract:
    def __init__(self):
        self.url = ""
        self.award_id = ""
        self.ref_idv_id = ""
        self.award_type = ""
        self.solicitation_id = ""
        self.mod_number = ""
        self.obligated_amount = ""
        self.total_obligated_amount = ""
        self.signed_date = ""
        self.contracting_office_id = ""
        self.contracting_office = ""
        self.funding_request_id = ""
        self.funding_request = ""
        self.legal_business_name = ""
        self.DBAN = ""
        self.city = ""
        self.state = ""
        self.unique_entity_id = ""
        self.has_socio_data = True
        self.business_type = ""
        self.socio_data = ""
        self.line_of_business = ""
        self.relationship_with_government = ""
        self.other_government_entities = ""
        self.organization_factors = ""
        self.educational_entities = ""
        self.certifications = ""
        self.description = ""

    def __str__(self):
        return f"ContractInfo: {vars(self)}"

    def set_url(self, url):
        self.url = url

    def set_award_id(self, award_id):
        self.award_id = award_id

    def set_ref_idv_id(self, idv_id):
        self.ref_idv_id = idv_id

    def set_award_type(self, award_type):
        self.award_type = award_type

    def set_solicidation_id(self, solicidation_id):
        self.solicitation_id = solicidation_id

    def set_mod_number(self, mod_number):
        self.mod_number = mod_number

    def set_obligated_amount(self, obligated_amount):
        self.obligated_amount = obligated_amount

    def set_total_obligated_amount(self, total_obligated_amount):
        self.total_obligated_amount = total_obligated_amount

    def set_signed_date(self, signed_date):
        self.signed_date = signed_date

    def set_contracting_office_id(self, contracting_office_id):
        self.contracting_office_id = contracting_office_id

    def set_contracting_office(self, contracting_office):
        self.contracting_office = contracting_office

    def set_funding_request_id(self, funding_request_id):
        self.funding_request_id = funding_request_id

    def set_funding_request(self, funding_request):
        self.funding_request = funding_request

    def set_legal_business_name(self, vendor_name):
        self.legal_business_name = vendor_name

    def set_DBAN(self, dban):
        self.DBAN = dban

    def set_city(self, city):
        self.city = city

    def set_state(self, state):
        self.state = state

    def set_unique_entity_id(self, unique_entity_id):
        self.unique_entity_id = unique_entity_id

    def toggle_has_socio_data(self):
        self.has_socio_data = not self.has_socio_data

    def set_business_type(self, business_type):
        self.business_type = business_type

    def set_socio_data(self, socio_data):
        self.socio_data = socio_data

    def set_line_of_business(self, line_of_business):
        self.line_of_business = line_of_business

    def set_relationship_with_government(self, relationship_with_government):
        self.relationship_with_government = relationship_with_government

    def set_other_government_entities(self, other_government_entities):
        self.other_government_entities = other_government_entities

    def set_organization_factors(self, organization_factors):
        self.organization_factors = organization_factors

    def set_educational_entities(self, educational_entities):
        self.educational_entities = educational_entities

    def set_certifications(self, certifications):
        self.certifications = certifications

    def set_description(self, description):
        self.description = description

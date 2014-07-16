
from mongoengine import *
import models
from datetime import datetime
import logging
import os
import json
import csv
from collections import Counter
import numpy as np
import re

#Just some global varbs. 
favicon_path = '/static/img/favicon.ico'
companyType = ['Public', 'Private', 'Nonprofit']
companyFunction = ['Consumer Research and/or Marketing', 'Consumer Services', 'Data Management and Analysis', 'Financial/Investment Services', 'Information for Consumers']
criticalDataTypes = ['Federal Open Data', 'State Open Data', 'City/Local Open Data', 'Private/Proprietary Data Sources']
revenueSource = ['Advertising', 'Data Management and Analytic Services', 'Database Licensing', 'Lead Generation To Other Businesses', 'Philanthropy', 'Software Licensing', 'Subscriptions', 'User Fees for Web or Mobile Access']
sectors = ['Agriculture', 'Arts, Entertainment and Recreation' 'Crime', 'Education', 'Energy', 'Environmental', 'Finance', 'Geospatial data/mapping', 'Health and Healthcare', 'Housing/Real Estate', 'Manufacturing', 'Nutrition', 'Scientific Research', 'Social Assistance', 'Trade', 'Transportation', 'Telecom', 'Weather']
datatypes = ['Federal Open Data', 'State Open Data', 'City/Local Open Data']
categories = ['Business & Legal Services', 'Data/Technology', 'Education', 'Energy', 'Environment & Weather', 'Finance & Investment', 'Food & Agriculture', 'Geospatial/Mapping', 'Governance', 'Healthcare', 'Housing/Real Estate', 'Insurance', 'Lifestyle & Consumer', 'Research & Consulting', 'Scientific Research', 'Transportation']
states ={ "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KA": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico"}
stateListAbbrev = { 
            "us": [ "", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KA", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "PR"],
            "ca": ["", "AB", "BC", "MB", "NB", "NL", "NT", "NS", "NU", "ON", "PE", "QC", "SK", "YT"]
            }
stateList = {
            "us": ["(Select State)", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "Puerto Rico"],
            "ca": ["(Select Province/Territory)", "Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Northwest Territories", "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Yukon"]
            }
agency_types = ['Federal','State','City/County','University/Institution']
available_countries = ["int", "us", "ca"]
country_keys = { "int":"United States", "us":"United States", "ca":"Canada", "United States":"us", "Canada":"ca"}


class Validators(object):
	def check_for_duplicates(self, companyName):
		#check if companyName exists:
		try: 
			c = models.Company.objects.get(prettyName=re.sub(r'([^\s\w])+', '', companyName).replace(" ", "-").title())
			response = { "error": "This company has already been submitted. Email opendata500@thegovlab.org for questions." }
		except:
			response = 'true'
		return response

class Tools(object):
    def re_do_filters(self, country):
        companies = models.Company.objects(country=country)
        for c in companies:
            filters = []
            filters.append(self.prettify(c.companyCategory))
            filters.append(c.state)
            for a in c.agencies:
                filters.append(a.prettyName)
            if c.submittedSurvey:
                filters.append("survey-company")
            c.filters = filters
            c.save()
        logging.info("Filters Redone.")

    def prettify(self, name):
        return re.sub(r'([^\s\w])+', '', name).replace(" ", "-")


class StatsGenerator(object):
    def get_total_companies(self, country):
        return models.Stats.objects.get(country=country).totalCompanies
    
    def get_total_companies_web(self, country):
        return models.Stats.objects.get(country=country).totalCompaniesWeb
    
    def get_total_companies_surveys(self, country):
        return models.Stats.objects.get(country=country).totalCompaniesSurvey

    def get_total_displayed_companies(self, country):
        return models.Stats.objects.get(country=country).totalCompaniesDisplayed

    def get_total_agencies(self, country):
        return models.Stats.objects.get(country=country).totalAgencies

    def update_total_agencies(self, country):
        s = models.Stats.objects.get(country=country)
        s.totalAgencies = models.Agency.objects(country=country).count()
        s.save()

    def update_totals_companies(self, country):
        s = models.Stats.objects.get(country=country)
        s.totalCompanies = models.Company.objects(country=country).count()
        s.totalCompaniesWeb = models.Company.objects(Q(submittedThroughWebsite = True) & Q(country=country)).count()
        s.totalCompaniesSurvey = models.Company.objects(Q(submittedSurvey = True) & Q(country=country)).count()
        s.totalCompaniesDisplayed = models.Company.objects(Q(displayed=True) & Q(country=country)).count()
        s.save()
    
    def increase_individual_state_count(self, state, country):
        stats = models.Stats.objects.get(country=country)
        for s in stats.states:
            if s.abbrev == state:
                s.count = s.count + 1
        stats.save()

    def decrease_individual_state_count(self, state, country):
        stats = models.Stats.objects.get(country=country)
        for s in stats.states:
            if s.abbrev == state:
                s.count = s.count - 1
        stats.save()

    def update_all_state_counts(self, country):
        stats = models.Stats.objects.get(country=country)
        companies  = models.Company.objects(Q(display=True) & Q(country=country))
        stateCount = []
        for c in companies:
            stateCount.append(c.state)
        stats.states = []
        for i in range(1, len(stateList[country])):
            s = models.States(
                name = stateList[country][i],
                abbrev = stateListAbbrev[country][i],
                count = stateCount.count(stateListAbbrev[country][i]))
            stats.states.append(s)
        stats.save()

    def refresh_stats(self, country):
        stats = models.Stats.objects.get(country=country)
        stats.totalCompanies = models.Company.objects(country=country).count()
        stats.totalCompaniesWeb = models.Company.objects(Q(submittedThroughWebsite = True) & Q(country=country)).count()
        stats.totalCompaniesSurvey = models.Company.objects(Q(submittedSurvey = True) & Q(country=country)).count()
        stats.totalCompaniesDisplayed = models.Company.objects(Q(display=True) & Q(country=country)).count()
        companies  = models.Company.objects(Q(display=True) & Q(country=country))
        stateCount = []
        for c in companies:
            stateCount.append(c.state)
        stats.states = []
        for i in range(1, len(stateList[country])):
            s = models.States(
                name = stateList[country][i],
                abbrev = stateListAbbrev[country][i],
                count = stateCount.count(stateListAbbrev[country][i]))
            stats.states.append(s)
        stats.lastUpdate = datetime.now()
        stats.save()


class FileGenerator(object):
    def generate_company_json(self, country):
        #------COMPANIES JSON---------
        companies = models.Company.objects(Q(display=True) & Q(country=country))
        companiesJSON = []
        for c in companies:
            agencies = []
            for a in c.agencies:
                datasets_agency = []
                for d in a.datasets:
                    if c == d.usedBy:
                        ds = {
                            "datasetName":d.datasetName,
                            "datasetURL":d.datasetURL,
                            "rating":d.rating
                        }
                        datasets_agency.append(ds)
                subagencies = []
                for s in a.subagencies:
                    if c in s.usedBy:
                        datasets_subagency = []
                        for d in s.datasets:
                            if c == d.usedBy:
                                ds = {
                                    "datasetName":d.datasetName,
                                    "datasetURL":d.datasetURL,
                                    "rating":d.rating
                                }
                                datasets_subagency.append(ds)
                        sub = {
                            "name":s.name,
                            "abbrev":s.abbrev,
                            "url":s.url,
                            "datasets":datasets_subagency
                        }
                        subagencies.append(sub)
                ag = {
                    "name": a.name,
                    "abbrev":a.abbrev,
                    "prettyName":a.prettyName,
                    "url": a.url,
                    "type":a.dataType,
                    "datasets":datasets_agency,
                    "subagencies":subagencies
                }
                agencies.append(ag)
            try:
                subagencies
            except Exception, e:
                logging.info("No Subagencies: " + str(e))
                subagencies = []
            company = {
                "company_name_id": c.prettyName,
                "companyName": c.companyName,
                "url": c.url,
                "city": c.city,
                "state": c.state,
                "zipCode": c.zipCode,
                "ceoFirstName": c.ceo.firstName,
                "ceoLastName": c.ceo.lastName,
                "yearFounded": c.yearFounded,
                "fte": c.fte,
                "companyType": c.companyType,
                "companyCategory": c.companyCategory,
                "revenueSource": c.revenueSource,
                "description": c.description,
                "descriptionShort": c.descriptionShort,
                "agencies":agencies,
                "subagencies":subagencies
            }
            companiesJSON.append(company)
        with open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + '_OD500_Companies.json', 'w') as outfile:
            json.dump(companiesJSON, outfile)
        logging.info("Company JSON File Done!")
    def generate_agency_json(self, country):
        #--------------JSON OF AGENCIES------------
        agencies = models.Agency.objects(country=country)
        agenciesJSON = []
        for a in agencies:
            #--------DATASETS AT AGENCY LEVEL------
            datasets_agency = []
            for d in a.datasets:
                ds = {
                    "datasetName":d.datasetName,
                    "datasetURL":d.datasetURL,
                    "rating":d.rating,
                    "usedBy":d.usedBy.prettyName
                }
                datasets_agency.append(ds)
            #--------SUBAGENCIES------
            subagencies = []
            for s in a.subagencies:
                datasets_subagency = []
                for d in s.datasets:
                    #logging.info(d.datasetName)
                    ds = {
                        "datasetName":d.datasetName,
                        "datasetURL":d.datasetURL,
                        "rating":d.rating,
                        "usedBy": d.usedBy.prettyName
                    }
                    datasets_subagency.append(ds)
                usedBy = []
                for u in s.usedBy:
                    usedBy.append(u.prettyName)
                sub = {
                    "name":s.name,
                    "abbrev":s.abbrev,
                    "url":s.url,
                    "datasets":datasets_subagency,
                    "usedBy":usedBy
                }
                subagencies.append(sub)
            #--------SUBAGENCIES------
            usedBy = []
            for u in a.usedBy:
                usedBy.append(u.prettyName)
            ag = {
                "name": a.name,
                "abbrev":a.abbrev,
                "prettyName":a.prettyName,
                "url": a.url,
                "type":a.dataType,
                "datasets":datasets_agency,
                "subagencies":subagencies,
                "usedBy":usedBy
            }
            agenciesJSON.append(ag)
        with open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + '_OD500_Agencies.json', 'w') as outfile:
            json.dump(agenciesJSON, outfile)
        logging.info("Agency JSON File Done!")
    def generate_company_csv(self, country):
        #---CSV OF ALL COMPANIES----
        companies = models.Company.objects(Q(display=True) & Q(country=country))
        csvwriter = csv.writer(open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + "_OD500_Companies.csv", "w"))
        csvwriter.writerow([
            'company_name_id',
            'company_name',
            'url',
            'city',
            'state',
            'zip_code',
            'ceo_first_name',
            'ceo_last_name',
            'year_founded',
            'full_time_employees',
            'company_type',
            'company_category',
            'revenue_source',
            'description',
            'description_short',
            'financial_info',
            'sourceCount'
            ])
        for c in companies:
            newrow = [
                c.prettyName,
                c.companyName,
                c.url,
                c.city,
                c.state,
                c.zipCode,
                c.ceo.firstName,
                c.ceo.lastName,
                c.yearFounded,
                c.fte,
                c.companyType,
                c.companyCategory,
                ', '.join(c.revenueSource),
                c.description,
                c.descriptionShort,
                c.financialInfo,
                c.sourceCount 
            ]
            for i in range(len(newrow)):  # For every value in our newrow
                if hasattr(newrow[i], 'encode'):
                    newrow[i] = newrow[i].encode('utf8')
            csvwriter.writerow(newrow)
        logging.info("Company CSV File Done!")
    def generate_company_all_csv(self, country):
        #---CSV OF ALL COMPANIES----
        companies = models.Company.objects(country=country)
        csvwriter = csv.writer(open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + "_OD500_Companies_All.csv", "w"))
        csvwriter.writerow([
            'company_name_id',
            'company_name',
            'url',
            'city',
            'state',
            'zip_code',
            'contact_first_name',
            'contact_last_name',
            'contact_email',
            'ceo_first_name',
            'ceo_last_name',
            'year_founded',
            'full_time_employees',
            'company_type',
            'company_category',
            'revenue_source',
            'description',
            'description_short',
            'financial_info',
            'source_count',
            'data_comments',
            'dataset_wishlist',
            'confidentiality',
            'ts',
            'survey_submitted',
            'vetted',
            'locked',
            'vettedByCompany',
            'display',
            'notes'
            ])
        for c in companies:
            newrow = [
                c.prettyName,
                c.companyName,
                c.url,
                c.city,
                c.state,
                c.zipCode,
                c.contact.firstName,
                c.contact.lastName,
                c.contact.email,
                c.ceo.firstName,
                c.ceo.lastName,
                c.yearFounded,
                c.fte,
                c.companyType,
                c.companyCategory,
                ', '.join(c.revenueSource),
                c.description,
                c.descriptionShort,
                c.financialInfo,
                c.sourceCount,
                c.dataComments,
                c.datasetWishList,
                c.confidentiality,
                c.ts,
                c.submittedSurvey,
                c.vetted,
                c.locked,
                c.vettedByCompany,
                c.display,
                c.notes
            ]
            for i in range(len(newrow)):  # For every value in our newrow
                if hasattr(newrow[i], 'encode'):
                    newrow[i] = newrow[i].encode('utf8')
            csvwriter.writerow(newrow)
        logging.info("All Companies CSV File Done!")

    def generate_agency_csv(self, country):
        companies = models.Company.objects(Q(country=country) & Q(display=True))
        agencies = models.Agency.objects(country=country)
        csvwriter = csv.writer(open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + "_OD500_Agencies.csv", "w"))
        csvwriter.writerow([
            'agency_name',
            'agency_abbrev',
            'agency_type',
            'subagency_name',
            'subagency_abbrev',
            'url',
            'used_by',
            'used_by_category',
            'dataset_name',
            'dataset_url'
            ])
        index_of_companies = {}
        for c in companies:
            index_of_companies[str(c.id)] = [c.companyName, c.companyCategory]
        AD = []
        SD = []
        S = []
        for a in agencies:
            for d in a.datasets:
                if d.usedBy.display:
                    newrow = [
                        a.name, 
                        a.abbrev, 
                        a.dataType, 
                        "General", 
                        "", 
                        a.url, 
                        index_of_companies[str(d.usedBy.id)][0],
                        index_of_companies[str(d.usedBy.id)][1],
                        d.datasetName,
                        d.datasetURL
                    ]
                    AD.append(str(d.usedBy.companyName + "|"+ a.name))
                    #write csv row here
                    for i in range(len(newrow)):  # For every value in our newrow
                        if hasattr(newrow[i], 'encode'):
                            newrow[i] = newrow[i].encode('utf8')
                    csvwriter.writerow(newrow)
            for s in a.subagencies:
                for d in s.datasets:
                    if d.usedBy.display:
                        newrow = [
                            a.name, 
                            a.abbrev, 
                            a.dataType, 
                            s.name, 
                            s.abbrev, 
                            s.url, 
                            index_of_companies[str(d.usedBy.id)][0],
                            index_of_companies[str(d.usedBy.id)][1],
                            d.datasetName,
                            d.datasetURL
                        ]
                        SD.append(str(d.usedBy.companyName + "|"+ s.name))
                        SD.append(str(d.usedBy.companyName + "|"+ a.name))
                        #write csv row here
                        for i in range(len(newrow)):  # For every value in our newrow
                            if hasattr(newrow[i], 'encode'):
                                newrow[i] = newrow[i].encode('utf8')
                        csvwriter.writerow(newrow)
                for c in s.usedBy:
                    if str(c.companyName + "|"+s.name) not in SD and c.display:
                        newrow = [
                            a.name, 
                            a.abbrev, 
                            a.dataType, 
                            s.name, 
                            s.abbrev, 
                            s.url, 
                            index_of_companies[str(c.id)][0],
                            index_of_companies[str(c.id)][1],
                            "",
                            ""
                        ]
                        S.append(str(c.companyName + "|"+a.name))
                        #write csv row
                        for i in range(len(newrow)):  # For every value in our newrow
                            if hasattr(newrow[i], 'encode'):
                                newrow[i] = newrow[i].encode('utf8')
                        csvwriter.writerow(newrow)
            for c in a.usedBy:
                if str(c.companyName + "|"+a.name) not in SD+AD+S and c.display:
                    newrow = [
                            a.name, 
                            a.abbrev, 
                            a.dataType, 
                            "General", 
                            "", 
                            a.url, 
                            index_of_companies[str(c.id)][0],
                            index_of_companies[str(c.id)][1],
                            "",
                            ""
                        ]
                    #companies_accounted_for.append(d.usedBy)
                    #write csv row
                    for i in range(len(newrow)):  # For every value in our newrow
                        if hasattr(newrow[i], 'encode'):
                            newrow[i] = newrow[i].encode('utf8')
                    csvwriter.writerow(newrow)
        #done, wrap up csv
        logging.info("Agency CSV File Done!")


    def generate_sankey_json(self, country):
        #get qualifying agencies
        agencies = models.Agency.objects(Q(usedBy__not__size=0) & Q(source__not__exact="web") & Q(dataType="Federal")).order_by('name') #federal agencies from official list that are used by a company
        #going to just make a list of all the category-agency combos
        cats = [] #list of used categories
        cats_agency_combo = []
        for a in agencies:
            for c in a.usedBy:
                if c.display:
                    if c.companyCategory in categories: #exclude "Other" Categories, and only displayed companies
                        cats_agency_combo.append(c.companyCategory+"|"+a.name)
                        cats.append(c.companyCategory)
        count = list(Counter(cats_agency_combo).items()) #count repeat combos
        #make dictionary
        cat_v_agencies = {"nodes": [], "links": []}
        #make node list
        cat_agency_list = [] #keep track of category agency list, we're going to need their indeces. 
        for c in categories: #Add categories to node list
            if c in cats: #only add category if used
                cat_v_agencies['nodes'].append({"name":c})
                cat_agency_list.append(c)
        for a in agencies: #add agency names to node list
            used = False
            for c in a.usedBy:
                if c.display:
                    used = True
            if used:
                cat_v_agencies['nodes'].append({"name":a.name})
                cat_agency_list.append(a.name)
        #make the links
        for c in count:
            link = {"source":cat_agency_list.index(c[0].split('|')[0]), "target":cat_agency_list.index(c[0].split('|')[1]), "value":c[1]} #make a link
            cat_v_agencies['links'].append(link)
        for n in cat_v_agencies['nodes']: #Abbreviate Department
            n['name'] = n['name'].replace('Department', 'Dept.')
            n['name'] = n['name'].replace('Administration', 'Admin.')
            n['name'] = n['name'].replace('United States', 'US')
            n['name'] = n['name'].replace('National', "Nat'l")
        with open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + '_sankey.json', 'w') as outfile:
            json.dump(cat_v_agencies, outfile)

    def generate_chord_chart_files(self, country):
        agencies = models.Agency.objects(Q(usedBy__not__size=0) & Q(source__not__exact="web") & Q(dataType="Federal") & Q(country="us")).order_by('name')
        #get agencies that are used
        used_agencies_categories = []
        for a in agencies:
            if a.usedBy and a.source == "dataGov":
                used_agencies_categories.append(a.name)
        #Keep track of # of categories
        num_agencies = len(used_agencies_categories)
        #get categories that are actually used from agencies that are used
        for a in agencies:
            if a.usedBy and a.source == "dataGov":
                for c in a.usedBy:
                    if c.companyCategory in categories and c.companyCategory not in used_agencies_categories:
                        used_agencies_categories.append(c.companyCategory)
        #logging.info(used_agencies_categories)
        name_key = {}
        key_name = {}
        for i, name in enumerate(used_agencies_categories):
            name_key[name] = i
            key_name[str(i)] = name
        #Make matrix
        l = len(name_key)
        matrix = np.matrix([[0]*l]*l)
        #populate matrix
        for a in agencies:
            if a.source == "dataGov":
                for c in a.usedBy:
                    if c.companyCategory in categories: 
                        matrix[name_key[c.companyCategory], name_key[a.name]] += 1
                        matrix[name_key[a.name], name_key[c.companyCategory]] += 1
        #make json
        matrix = matrix.tolist()
        data = {"matrix":matrix, "names":key_name, "num_agencies":num_agencies}
        #abbreviate some stuff
        for key in data['names']:
            data['names'][key] = data['names'][key].replace('Department', 'Dept.')
            data['names'][key] = data['names'][key].replace('Administration', 'Admin.')
            data['names'][key] = data['names'][key].replace('United States', 'US')
            data['names'][key] = data['names'][key].replace('U.S.', 'US')
            data['names'][key] = data['names'][key].replace('National', "Nat'l")
            data['names'][key] = data['names'][key].replace('Federal', "Fed.")
            data['names'][key] = data['names'][key].replace('Commission', "Com.")
            data['names'][key] = data['names'][key].replace('International', "Int'l")
            data['names'][key] = data['names'][key].replace('Development', "Dev.")
            data['names'][key] = data['names'][key].replace('Corporation', "Corp.")
            data['names'][key] = data['names'][key].replace('Institute', "Inst.")
            data['names'][key] = data['names'][key].replace('Administrative', "Admin.")
            data['names'][key] = data['names'][key].replace(' and ', " & ")
            data['names'][key] = data['names'][key].replace('Financial', "Fin.")
            data['names'][key] = data['names'][key].replace('Protection', "Prot.")
            data['names'][key] = data['names'][key].replace('Environmental', "Env.")
        #save to file
        with open(os.path.join(os.path.dirname(__file__), 'static') + '/files/' + country + '_matrix.json', 'w') as outfile:
            json.dump(data, outfile)
        logging.info("Chord Chart File Done!")

    def generate_visit_csv(self, country):
        #---CSV OF ALL COMPANIES----
        visits = models.Visit.objects()
        csvwriter = csv.writer(open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + "_OD500_Visits.csv", "w"))
        csvwriter.writerow([
            'ts',
            'referer',
            'page',
            'user_agent',
            'ip'
            ])
        for v in visits:
            newrow = [
                v.ts,
                v.r,
                v.p,
                v.ua,
                v.ip
            ]
            for i in range(len(newrow)):  # For every value in our newrow
                if hasattr(newrow[i], 'encode'):
                    newrow[i] = newrow[i].encode('utf8')
            csvwriter.writerow(newrow)
        logging.info("Visit CSV File Done!")

    def generate_agency_list(self, country):
        agencies = models.Agency.objects(Q(country=country) & Q(source__not__exact="web"))
        agency_list = []
        for a in agencies:
            label = [a.name, " (", a.abbrev, ")"]
            agency = {
                "label": ''.join(filter(None, label)),
                "a": a.name,
                "aa": a.abbrev,
                "s": "",
                "ss": ""
            }
            agency_list.append(agency)
            if a.subagencies:
                for s in a.subagencies:
                    label = [a.name, " (", a.abbrev, ")", " - ", s.name, " (", s.abbrev, ")"]
                    agency = {
                        "label": ''.join(filter(None, label)),
                        "a": a.name,
                        "aa": a.abbrev,
                        "s": s.name,
                        "ss": s.abbrev
                    }
                    agency_list.append(agency)
        with open(os.path.join(os.path.dirname(__file__), 'static') + "/files/" + country + '_Agency_List.json', 'w') as outfile:
            json.dump(agency_list, outfile)
        logging.info("Agency List Done!")





















import time
from datetime import datetime
import json
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
import argparse
import configparser
import csv

'''
Scraper using selenium-wire (https://pypi.org/project/selenium-wire/) to
acess all bank statements from Guiabolso and output transactions
along with respective categories to CSV file
'''

def parseRequest():
    '''
    Flters and parses statement requests, generating a dict of categories and list of dicts with each transaction
    Uses global browser objects
    '''
    api_requests = [request for request in browser.requests if 'v2/events' in str(request)]
    statements = []
    category_types = []
    firstTransaction = ''
    for request in api_requests:
        
        # body is returned as Bytes, so need to decode to str and from Str to Dict
        req_body = json.loads(request.body.decode('UTF-8'))
        if (req_body['name'] == 'users:summary:month'):
            resp_body = json.loads(request.response.body.decode('UTF-8'))
            try:
                if (resp_body.get('payload', {}).get('userMonthHistory', {}).get('statements') != None):
                    statements += resp_body['payload']['userMonthHistory']['statements']
                if (resp_body.get('payload', {}).get('rawData', {}).get('categoryTypes') != None):
                    category_types = resp_body.get('payload', {}).get('rawData', {}).get('categoryTypes')
                if (resp_body.get('payload', {}).get('rawData', {}).get('firstTransaction') != None):
                    firstTransaction = resp_body.get('payload', {}).get('rawData', {}).get('firstTransaction')
            except AttributeError:
                continue

    firstTransaction = time.strptime(firstTransaction, '%d/%m/%Y')
    categories = {}
    for category_type in category_types:
        for category in category_type['categories']:
            categories.update({category['id']: category['name']})

    return statements, categories, firstTransaction


def GetStatement(monthly_statements, categories):
    '''
    Extracts transactions and respective category, returns merged list from all accounts
    '''
    merged_monthly_statement = []
    for statement in monthly_statements:
        for transaction in statement['transactions']:
            item = {}
            item.update({'statement_name': statement['name']})
            item.update({'statement_type': statement['statementType']})
            item.update({'statement_id': statement['id']})
            item.update({'id': transaction['id']})
            item.update({'label': transaction['label']})
            item.update({'categoryId': transaction['categoryId']})
            item.update({'categoryName': categories[transaction['categoryId']]})
            item.update({'value': round(float(transaction['value']), 2)})
            item.update({'date': (time.strftime('%d/%m/%Y', time.gmtime(transaction['date'] / 1000)))})
            item.update({'currency': transaction['currency']})
            item.update({'exchangeValue': transaction['exchangeValue']})
            item.update({'duplicated': transaction['duplicated']})
            merged_monthly_statement.append(item)

    return merged_monthly_statement


def MonthSelector():
    '''
    Loops through each month available at the statement screen
    Menu rendered dynamically an only shows after clicking on central menu
    call request parser, statement parser and returns final list of transactins
    '''
    menu = browser.find_element_by_class_name('MonthSelectMenuRoot')
    menu.find_element_by_tag_name('button').click()
    qty_months = len(menu.find_elements_by_tag_name('li'))
    
    # close menu before starting the loop
    browser.find_element_by_id('root').click()
    final_statement = []
    i = 0
    while (i < qty_months):
        menu = browser.find_element_by_class_name('MonthSelectMenuRoot')
        menu.find_element_by_tag_name('button').send_keys(Keys.ENTER)
        months = menu.find_elements_by_tag_name('li')
        months[i].send_keys(Keys.ENTER)
        browser.get(extrato)
        time.sleep(5)
        month_statement, transaction_categories, firstTransaction = parseRequest()
        final_statement += GetStatement(month_statement, transaction_categories)
        del browser.requests
        browser.get(home)
        time.sleep(5)
        i += 1
    return final_statement


def write_output(export_data, file_name):
    with open(file_name, 'w', newline='') as file:
        if (len(export_data) > 0):
            fields = list(export_data[0].keys())
            output = csv.DictWriter(file, fieldnames=fields)
            output.writeheader()
            for row in export_data:
                output.writerow(row)
        else:
            print('no statement to write')


if __name__ == '__main__':
    # Selenium wire cannot handle self-signed SSL certificates, skipping the check. 
    # Ref https://github.com/wkeeling/selenium-wire/issues/55
    options = {'verify_ssl': False, 'suppress_connection_errors': False, 'disable_encoding': True}

    config = configparser.RawConfigParser()
    config.read('urls.cfg')
    urls = dict(config.items('URLs'))
    login = urls['login']
    extrato = urls['extrato']
    home = urls['home']
    
    browser = webdriver.Chrome(seleniumwire_options=options)
    browser.scopes = ['.*guiabolso.*']

    parser = argparse.ArgumentParser()
    parser.add_argument("-username")
    parser.add_argument("-password")
    parser.add_argument("-output_file_name")
    args = parser.parse_args()
    username = args.username
    pwd = args.password
    output_file_name = args.output_file_name

    browser.get(login)
    time.sleep(5)
    browser.find_element_by_name("email").send_keys(username)
    browser.find_element_by_name("password").send_keys(pwd + Keys.ENTER)
    
    # Need to manually pass ReCaptcha
    breakpoint()
    time.sleep(5)
    
    # Completion of execution closes proxy and prevents further connections. Sleeping to allow for requests to be captured
    time.sleep(5)
    all_transactions = MonthSelector()
    tuple_transactions = set(tuple(transaction.items()) for transaction in all_transactions)
    export_statement = [dict(transaction) for transaction in tuple_transactions]
    write_output(export_data=export_statement, file_name=output_file_name)

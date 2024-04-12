import time
import csv
import json
from io import StringIO
import urllib
import datetime
import requests

SID_ENDPOINT_URL = "https://www.lhv.ee/auth/ibank/mid"
PORTFOLIO_REPORT_URL = "https://www.lhv.ee/portfolio/reports_cur.cfm?newframe=1"
ACCOUNTS_URL = "https://www.lhv.ee/b/accounts"

nickname_input = input("Enter the username: ")
code_input = input("Enter the mobile number: ")
user_payload = {"nickname": nickname_input, "phoneNumber": code_input}
auth_cookie = {}

default_headers = {

}


def make_http_request(
    url,
    data=None,
    json=None,
    headers=None,
    params={},
    cookies={},
    method="GET",
):
    try:
        make_request_response = requests.request(
            method=method,
            url=url,
            json=json,
            data=data,
            params={"redirectUrl": "", **params},
            cookies=cookies,
            headers=headers,
            timeout=5
        )

        # Raise an exception for 4xx and 5xx status codes
        make_request_response.raise_for_status()
        return make_request_response
    except requests.exceptions.RequestException as error:
        print("Error:", error)
        print("Body:", error.response.text)
        return None


def make_login_request():
    response = make_http_request(
        url=SID_ENDPOINT_URL,
        json=user_payload,
        method="POST"
    )

    body = response.json()
    verification_code = body["verificationCode"]
    print(f"PIN1: {verification_code}")

    return {
        "CLIENT_ID": response.cookies.get("CLIENT_ID"),
        "JSESSIONID": response.cookies.get("JSESSIONID")
    }


def loop_auth_callback_request():
    is_authenticated = False

    while not is_authenticated:
        response = make_http_request(
            url=SID_ENDPOINT_URL,
            json=user_payload,
            cookies=auth_cookie,
            method="PUT"
        )

        body = response.content.decode('utf-8')
        is_authenticated = "AUTHENTICATED" in body

        if not is_authenticated:
            # Await spamming API
            time.sleep(3)

    # Return new auth_cookie
    return {
        **auth_cookie,
        "JSESSIONID": response.cookies.get("JSESSIONID")
    }


def get_user_accounts():
    response = make_http_request(
        url=ACCOUNTS_URL,
        cookies=auth_cookie,
        method="GET"
    )

    return response.json()


def select_portfolio(accounts):
    account_names = []
    account_portfolio_ids = []

    for account in accounts:
        account_portfolio_ids.append(account['accountId'])
        account_names.append(account['name'])

    print("\nSelect an account:")

    for idx, account_name in enumerate(account_names, start=1):
        # Print options
        print(f"{idx}. {account_name}")

    choice = None
    while choice is None:
        try:
            choice = int(input("Enter the number of your choice: "))

            if 1 <= choice <= len(account_names):
                index = choice - 1
                print(f"You selected: {account_names[index]}")
            else:
                print(f"Invalid choice: {choice}. Please enter a valid index.")
                choice = None
        except ValueError:
            print("Invalid input.")

    return [account_names[index], account_portfolio_ids[index]]


def get_portfolio_report(portfolio_id, type="csv"):
    date_end = datetime.datetime.now()
    date_start = date_end - datetime.timedelta(days=30)

    body = urllib.parse.urlencode({
        "i_no_filters": "2",
        "i_del_filters": "",
        "i_hide_filters": "1",
        "i_report_type": type,
        "i_bdoc": "",
        "i_show_report": "1",
        "i_portfolio_id": portfolio_id,
        "i_card_id": "",
        "i_sort_order_asc": "0",
        "i_date_type": "inv",
        "i_portfolio_card": "",
        "i_date_start": date_start.strftime('%d.%m.%Y'),
        "i_date_end": date_end,
        "i_currency_id": "",
        "i_filter_1": "any",
        "i_filter_val_1": ""
    })

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    return make_http_request(
        url=PORTFOLIO_REPORT_URL,
        cookies=auth_cookie,
        method="POST",
        data=body,
        headers=headers
    )


def parse_portfolio_report_csv(response):
    csv_data_text = response.text
    csv_data_io = StringIO(csv_data_text)

# Convert the CSV text into a format that the CSV reader can work with
    json_report = {"payments": []}
    csv_reader = csv.reader(csv_data_io, delimiter=',')

    # Skip the first row (header row)
    next(csv_reader)

    for row in csv_reader:
        # print("ROW: ", row)
        [
            account_no,
            document_no,
            date,
            sender_or_reciever_acc,
            sender_or_reciever_name,
            sender_bank_code,
            empty,
            debit_or_credit,
            amount,
            reference_number,
            archiving_code,
            description,
            fee,
            currency,
            personal_or_registry_code,
            bank_bic,
            debator_name,
            transaction_reference,
            account_service_reference
        ] = row

        json_report["payments"].append({
            "AccountNo": account_no,
            "DocumentNo": document_no,
            "Date": date,
            "Account": sender_or_reciever_acc,
            "Name": sender_or_reciever_name,
            "BankCode": sender_bank_code,
            "Credit": debit_or_credit == "C",
            "Amount": amount,
            "ReferenceNo": reference_number,
            "ArchivingCode": archiving_code,
            "Description": description,
            "Fee": fee,
            "Currency": currency,
            "PersonalCode": personal_or_registry_code,
            "BIC": bank_bic,
            "DebatorName": debator_name,
            "Reference": transaction_reference,
            "AccountServiceReference": account_service_reference
        })

    csv_data_io.close()

    return json_report


def store_json_to_file(json_data, account_name):
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H%M%S")
    formatted_account_name = account_name.lower().replace(" ", "_")
    filename = f"lhv_payments_{formatted_account_name}_{formatted_time}.json"

    with open(filename, "w") as json_file:
        json.dump(json_data, json_file, indent=2)
        print(f"Storing payments to file {filename} successful")


auth_cookie = make_login_request()
auth_cookie = loop_auth_callback_request()
accounts = get_user_accounts()
[account_name, portfolio_id] = select_portfolio(accounts)
portfolio_response = get_portfolio_report(portfolio_id)
json_data = parse_portfolio_report_csv(portfolio_response)
store_json_to_file(json_data, account_name)

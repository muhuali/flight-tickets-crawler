# coding=utf-8

from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import unicodedata
from datetime import datetime,timedelta
from pyvirtualdisplay import Display


START_LINK = "https://www.google.com/flights?hl=en#flt="
END_LINK = "c:USD;e:1;sd:1;t:f;tt:o"
DATE_MAP = {"周一":"2020-07-27",
            "周二":"2020-07-28",
            "周三":"2020-07-29",
            "周四":"2020-07-30",
            "周五":"2020-07-31",
            "周六":"2020-08-01",
            "周日":"2020-08-02"}

def find_flight(start_date,from_place,to_place):
    driver = webdriver.Chrome(executable_path='/Users/kangw/Desktop/splinter_chromeDriver/chromedriver')
    driver.get('https://www.google.com/flights?hl=en#flt=SFO.PVG.2020-08-04;c:USD;e:1;sd:1;t:f;tt:o')
    wait = WebDriverWait(driver, 20)
    wait.until(EC.visibility_of_element_located((By.XPATH, '//span[contains(text(), "One way")]')))


def find_flight_by_link(airline_infos):
    # Required on Linux
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-extensions')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    display = Display(visible=0, size=(800, 800))
    display.start()
    service_log_path = "{}/chromedriver.log".format("data")
    service_args = ['--verbose']

    driver = webdriver.Chrome('/usr/bin/chromedriver',
        service_args=service_args,
        service_log_path=service_log_path,
        chrome_options=options)

    airline_result_with_price = {}
    airline_result_without_price = []
    # Search the airline in the next two months
    for airline in airline_infos:
        for i in range(0, 7):
            for date in airline["date"]:
                new_date = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=(7*i))
                new_date_str = datetime.strftime(new_date, "%Y-%m-%d")
                link = "%s.%s.%s;a:%s;" %(airline["from_place"], airline["to_place"],new_date_str, airline["airline"])
                final_link = START_LINK + link + END_LINK
                driver.get(final_link)
                sleep(0.3)

                flight_price = store_flight_search_result(driver)
                if flight_price == "1":
                    airline_result_without_price.append(final_link + '\n')
                    airline_result_without_price.append(airline["airline_number"] + '\n')
                elif flight_price != "0":
                    airline_result_with_price['from_place'] = airline['from_place']
                    airline_result_with_price['to_place'] = airline['to_place']
                    airline_result_with_price['airline_info'] = airline["full_airline_info"]
                    airline_result_with_price['date'] = new_date_str
                    airline_result_with_price['price'] = flight_price
                    airline_result_with_price['link'] = final_link
        print("Done with airline " + airline['airline_number'])


    driver.quit()
    with open("data/airlines_after_process_without_price.txt", "w") as f:
        for r in airline_result_without_price:
            f.write(r)

    with open("data/airlines_after_process_with_price.txt", "w") as d:
        for r in airline_result_with_price:
            d.write(r)
        d.write('\n' + str(datetime.now()))


def store_flight_search_result(driver):
    try:
        flight_result_indicator = driver.find_element_by_xpath('//*[@id="gws-flights-results__other_flights_heading"]')
        try:
           price_result_indicator =  driver.find_element_by_xpath('//div[text() = "Price unavailable"]')
           return "1"
        except Exception:
            # Find the ticket price
            price_result = driver.find_element_by_xpath('//div[@class="flt-subhead1 gws-flights-results__price gws-flights-results__cheapest-price"]')
            return price_result.text
    except Exception:
        return "0"


def read_file(filename):
    f = open(filename)
    raw_data = f.readlines()
    f.close()

    # Process raw data
    result = []
    for line in raw_data[1:]:
        one_airline_info = {}

        if line.startswith("#"):
            continue

        splits = [e for e in line.split(",")]
        # 纽约 (JFK)
        one_airline_info["from_place"] = re.search(r'\(.*\)', splits[2]).group()[1:-1]
        # 上海 (PVG)
        one_airline_info["to_place"] = re.search(r'\(.*\)', splits[3]).group()[1:-1]
        # 达美 (DL)
        one_airline_info["airline"] = re.search(r'\(.*\)', splits[4]).group()[1:-1]
        one_airline_info["full_airline_info"] = splits[4]
        # MU588 / MU587
        one_airline_info["airline_number"] = splits[5].split('/')[0].strip()
        # 周三 / 周二
        one_airline_info["date"] = process_date(splits[6])

        result.append(one_airline_info)
    return result


def process_date(text):
    text = text.strip().split("/")[0].split("和")
    date_result = []
    for date_str in text:
        date_result.append(DATE_MAP[date_str.strip()])
    return date_result


#result = read_file("data/airlines.csv")
result = read_file("data/test_airlines.csv")
find_flight_by_link(result)

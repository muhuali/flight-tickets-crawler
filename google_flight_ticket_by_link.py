# coding=utf-8

from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
from datetime import datetime,timedelta
import json

START_LINK = "https://www.google.com/flights?hl=en#flt="
END_LINK = "c:USD;e:1;sd:1;t:f;tt:o"
WEEK_DAYS = ("周一".decode('utf-8'),
             "周二".decode('utf-8'),
             "周三".decode('utf-8'),
             "周四".decode('utf-8'),
             "周五".decode('utf-8'),
             "周六".decode('utf-8'),
             "周日".decode('utf-8'))
DEFAULT_DATE_MAP = {"周一".decode('utf-8'):"2020-07-27",
            "周二".decode('utf-8'):"2020-07-28",
            "周三".decode('utf-8'):"2020-07-29",
            "周四".decode('utf-8'):"2020-07-30",
            "周五".decode('utf-8'):"2020-07-31",
            "周六".decode('utf-8'):"2020-08-01",
            "周日".decode('utf-8'):"2020-08-02"}

def find_flight(start_date,from_place,to_place):
    driver = webdriver.Chrome(executable_path='/Users/kangw/Desktop/splinter_chromeDriver/chromedriver')
    driver.get('https://www.google.com/flights?hl=en#flt=SFO.PVG.2020-08-04;c:USD;e:1;sd:1;t:f;tt:o')
    wait = WebDriverWait(driver, 20)
    wait.until(EC.visibility_of_element_located((By.XPATH, '//span[contains(text(), "One way")]')))

# Update the default date map
def update_date_map():
    current_date = datetime.today()
    for i in range(0, 7):
        next_date = current_date + timedelta(days=i)
        # weekday() returns 0, 1....6
        next_week_day = WEEK_DAYS[next_date.weekday()]
        DEFAULT_DATE_MAP[next_week_day] = datetime.strftime(next_date, "%Y-%m-%d")

def find_flight_by_link(airline_infos, driver=None):
    options = webdriver.ChromeOptions()
    # Bypass OS security model
    # options.add_argument('--no-sandbox')
    # options.add_argument('--headless')
    # applicable to windows os only
    # options.add_argument('--disable-gpu')
    # # overcome limited resource problems
    # options.add_argument('--disable-dev-shm-usage')
    # # open Browser in maximized mode
    # options.add_argument('--disable-extensions')
    # # options.add_argument('--start-maximized')
    # options.add_argument('--window-size=1920,1080') # Set to be max when used in headless
    # options.add_argument('--remote-debugging-port=9222')
    # options.add_argument('--shm-size=2g')
    # options.add_experimental_option('useAutomationExtension', False)

    if not driver:
        driver = webdriver.Chrome(
                executable_path='/Users/kangw/Desktop/splinter_chromeDriver/chromedriver',chrome_options=options)

    airline_result_with_price = []
    airline_result_without_price = []

    # Search the airline in the next two months
    for i in range(0, 2):
        for airline in airline_infos:
            for date in airline["date"]:
                new_date = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=(7*i))
                # Check if the time is in the past
                if new_date < datetime.now():
                    continue
                new_date_str = datetime.strftime(new_date, "%Y-%m-%d")
                link = "%s.%s.%s;a:%s;" %(airline["from_place"], airline["to_place"],new_date_str, airline["airline"])
                final_link = START_LINK + link + END_LINK
                driver.get(final_link)
                sleep(0.3)

                flight_price = store_flight_search_result(driver, airline)
                if flight_price == "1":
                    airline_result_without_price.append(final_link + '\n')
                    airline_result_without_price.append(airline["airline_number"] + '\n')
                elif flight_price != "0":
                    per_airline_result_with_price = {}
                    per_airline_result_with_price['from'] = airline['from_place']
                    per_airline_result_with_price['to'] = airline['to_place']
                    per_airline_result_with_price['info'] = airline["full_airline_info"]
                    per_airline_result_with_price['date'] = new_date_str
                    per_airline_result_with_price['price'] = flight_price
                    per_airline_result_with_price['link'] = final_link
                    airline_result_with_price.append(per_airline_result_with_price)

    driver.quit()
    with open("data/airlines_after_process_without_price.txt", "w") as f:
        for r in airline_result_without_price:
            f.write(str(r))

    with open("data/airlines_after_process_with_price.txt", "w") as d:
        for r in airline_result_with_price:
            d.write(json.dumps(r) + '\n')
        d.write('\n#' + str(datetime.now()))


def store_flight_search_result(driver, airline):
    try:
        flight_result_indicator = driver.find_element_by_xpath('//*[@id="gws-flights-results__other_flights_heading"]')
        try:
           price_result_indicator =  driver.find_element_by_xpath('//div[text() = "Price unavailable"]')
           return "1"
        except Exception:
            # CA390 / CA391 -> 390
            flight_number = re.findall(r'\d+', airline["airline_number"])[0]
            # Check if the flight number is the same.
            flight_number_element = driver.find_element_by_xpath("//span[text() = '" + flight_number + "']")
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

        splits = [e.decode('utf-8') for e in line.split(",")]
        # 纽约 (JFK)
        one_airline_info["from_place"] = re.search(r'\(.*\)', splits[2]).group()[1:-1]
        # 上海 (PVG)
        one_airline_info["to_place"] = re.search(r'\(.*\)', splits[3]).group()[1:-1]
        # 达美 (DL)
        one_airline_info["airline"] = re.search(r'\(.*\)', splits[4]).group()[1:-1]
        one_airline_info["full_airline_info"] = splits[4]
        # MU588 / MU587
        one_airline_info["airline_number"] = splits[5]
        # 周三 / 周二
        one_airline_info["date"] = process_date(splits[6])
        result.append(one_airline_info)
    return result


def process_date(text):
    update_date_map()
    text = text.strip().split("/")[0].split("和".decode('utf-8'))
    date_result = []
    for date_str in text:
        date_result.append(DEFAULT_DATE_MAP[date_str.strip()])
    return date_result


def crawl_us_ticket():
    # driver = webdriver.Chrome(executable_path='/Users/kangw/Desktop/splinter_chromeDriver/chromedriver')
    while True:
        result = read_file("/Users/kangw/Desktop/splinter_chromeDriver/src/data/airlines.csv")
        find_flight_by_link(result)
        sleep(120)

crawl_us_ticket()
# result = read_file("/Users/kangw/Desktop/splinter_chromeDriver/src/data/airlines.csv")
# result = read_file("/Users/kangw/Desktop/splinter_chromeDriver/src/data/test_airlines.csv")
# find_flight_by_link(result)
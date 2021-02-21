from bs4 import BeautifulSoup as soup
from time import sleep
from selenium import webdriver
import sys
import datetime
from datetime import timedelta
import pandas as pd


class Driver:
    """
    path: Web driver path, eg: Chrome, Firefox
    options: list of web driver options
    """

    def __init__(self, path, options):
        self.path = path
        self.options = options
        self.driver_options = webdriver.ChromeOptions()
        for option in self.options:
            self.driver_options.add_argument(option)
        self.driver = webdriver.Chrome(path, options=self.driver_options)

    def click_button_xpath(self, tag_value):
        """Clicks the element found with xpath"""
        self.driver.find_elements_by_xpath(tag_value)[0].click()

    def get_element_list(self, tag_value):
        """Get a list of elements from an xpath"""
        return self.driver.find_elements_by_xpath(tag_value)

    def execute_script(self, code, element):
        """Execute script"""
        return self.driver.execute_script(code, element)

    def current_url(self):
        return self.driver.current_url

    def page_source(self):
        return self.driver.page_source

    def back(self):
        return self.driver.back()

    def close(self):
        return self.driver.close()


class SearchFilter:
    """
    dep: Departure airport
    arr: Arrival airport
    fly_date: Fly date as datetime type.
    """

    def __init__(self, dep, arr, fly_date):
        self.dep = dep
        self.arr = arr
        self.fly_date = fly_date


def search_flights(driver, search_filter):
    """Searches google flights for one-way flights based on the departure, arrival airports and travel date"""
    url = "https://www.google.com/flights?hl=en#flt={}.{}.{};c:USD;e:1;sd:1;t".format(search_filter.dep,
                                                                                      search_filter.arr,
                                                                                      search_filter.fly_date.\
                                                                                      strftime("%Y-%m-%d"))
    print(url)
    driver.driver.get(url)

    driver.driver.maximize_window()
    sleep(4)
    driver.click_button_xpath("//div[@class='VfPpkd-RLmnJb']")
    driver.click_button_xpath("//li[@role='option' and @data-value=2 and @class='uT1UOd']")
    driver.click_button_xpath("//span[@class='bEfgkb']")
    sleep(1)
    page_source = driver.page_source()
    page_soup = soup(page_source, "html.parser")
    return page_soup


class Scraper:
    def __init__(self, driver: Driver, search_filter: SearchFilter):
        self.driver = driver
        self.search_filter = search_filter

    def scrape(self):
        # driver.set_page_load_timeout(10)
        self.driver.driver.implicitly_wait(10)

        page_soup = search_flights(self.driver, self.search_filter)
        # find data (departure time, arrival time, airlines, flight duration, number of stops and price) in the
        # unexpanded div
        flight_results_unexpanded = page_soup.findAll("div", {"class": "OgQvJf nKlB3b"})
        print('Total Flights = {}'.format(len(flight_results_unexpanded)))
        # search_results is a dictionary to store flight info
        search_results = {}

        # get the list of all the toggles so that they can be expanded
        toggles = self.driver.get_element_list("//div[@class='xKbyce']")
        print(len(toggles))
        # expand all the toggles first
        for x in range(len(toggles)):
            self.driver.execute_script("arguments[0].click();", toggles[x])
        print(len(toggles))
        # get page source of the full page to get layover info, and cabin class
        print(type(self.driver.page_source))
        print(type(self.driver.driver.page_source))
        page_source = self.driver.page_source()
        page_soup = soup(page_source, "html.parser")

        url = []
        for x in range(len(toggles)):
            select_flight_buttons = self.driver.get_element_list("//button[@aria-label='Select flight']")
            # the following logic is in place to avoid clicking a non-clickable button
            i = x
            for _ in iter(int, 1):
                try:
                    self.driver.execute_script("arguments[0].click();", select_flight_buttons[i])
                    break
                except Exception as e:
                    # to refine and make sure it does not always throw an exception, add MAX_RETRIES to avoid highly
                    # unlikely infinite loop
                    i = i + 1
                    if i == len(select_flight_buttons):
                        sys.exit('{}: Retries to click Select flight button exhausted after {} retries '.format(e, i))
                    continue
            url.append(self.driver.current_url())
            if x == len(toggles) - 1:
                break
            print('Breakout {}'.format(x))
            self.driver.back()
            sleep(3)
            toggle_url = self.driver.get_element_list("//div[@class='xKbyce']")
            if len(toggles) != len(toggle_url):
                print('Number of flights changed from {} to {} during scraping. Re-firing'.format(len(toggles),
                                                                                                  len(
                                                                                                      toggle_url)))
                self.driver.close()
                self.scrape()
            self.driver.execute_script("arguments[0].click();", toggle_url[x + 1])
        self.driver.close()

        i = 0
        for flight_result in flight_results_unexpanded:
            search_results[i] = {}
            search_results[i]['DEP'] = \
                flight_result.findAll('span', {'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                    2].text
            search_results[i]['ARR'] = \
                flight_result.findAll('span', {'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                    3].text
            search_results[i]['BRAND'] = flight_result.findAll('div', {'class': 'TQqf0e sSHqwe tPgKwe ogfYpf'})[
                0].span.text
            if flight_result.findAll('span', {'class': 'pIgMWd ogfYpf'})[0].text == 'Nonstop':
                search_results[i]['STOPS'] = 0
            else:
                search_results[i]['STOPS'] = int(
                    flight_result.findAll('span', {'class': 'pIgMWd ogfYpf'})[0].text.split(' ')[0])

            if len(flight_result.findAll('div', {'class': 'BVAVmf I11szd POX3ye'})) == 0:
                search_results[i]['PRICE'] = 'NA'
            else:
                search_results[i]['PRICE'] = \
                    flight_result.findAll('div', {'class': 'BVAVmf I11szd POX3ye'})[0].findAll('div')[
                        1].span.text

            search_results[i]['TRIP_DURATION'] = flight_result.findAll('div', {'class': 'gvkrdb AdWm1c tPgKwe ogfYpf'})[
                0].text
            search_results[i]['DEP_DATE'] = self.search_filter.fly_date
            search_results[i]['DEP_TIME'] = \
                flight_result.findAll('span', {'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                    0].text
            search_results[i]['ARR_TIME'] = \
                flight_result.findAll('span', {'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                    1].text
            layovers = []
            for j in range(search_results[i]['STOPS']):
                layovers.append(
                    page_soup.findAll('div', {'class': 'yJwmMb'})[i].findAll('div', {'class': 'tvtJdb eoY5cb y52p7d'})[j].text.replace('layover', 'at '))
            cabin_class = \
                page_soup.findAll('div', {'class': 'MX5RWe sSHqwe y52p7d'})[i].findAll('span', {'class': 'Xsgmwe'})[
                    2].text
            search_results[i]['LAYOVER'] = ' , '.join(layovers)
            search_results[i]['CABIN_CLASS'] = cabin_class
            i = i + 1

        df = pd.DataFrame(search_results)
        df = df.T
        land_date = [self.search_filter.fly_date] * len(flight_results_unexpanded)
        add_days_to_dep_date = list(df.ARR_TIME.str.split('+').str[1].fillna(value=0).astype(int))
        for x in range(len(add_days_to_dep_date)):
            land_date[x] = land_date[x] + timedelta(days=add_days_to_dep_date[x])

        df['ARR_DATE'] = land_date
        df['ARR_TIME'] = df.ARR_TIME.str.split('+').str[0]
        df['URL'] = url
        # to dump the flight results in csv, uncomment below line
        # df.to_csv('GoogleFlights.csv', sep=',')
        return df


def main():
    # user inputs
    web_driver_path = '/Users/khugel01/Downloads/chromedriver'
    driver_options = ['--ignore-certificate-errors',
                      '--incognito',
                      '--headless'
                      ]
    departure_airport = 'DAL'
    arrival_airport = 'SFO'
    fly_date = datetime.datetime(2021, 3, 10)

    # execution starts
    driver = Driver(web_driver_path, driver_options)
    search_filter = SearchFilter(departure_airport, arrival_airport, fly_date)
    scraper = Scraper(driver, search_filter)
    scraper.scrape()


main()

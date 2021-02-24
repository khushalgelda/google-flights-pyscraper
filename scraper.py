from bs4 import BeautifulSoup as soup
from time import sleep
from selenium import webdriver
# from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
import sys
import datetime
from datetime import timedelta
import pandas as pd


class Driver:
    """
    path: Web driver path, eg: Chrome, Firefox
    options: list of web driver options
    This creates a webdriver object with options.
    """

    def __init__(self, path, options=()):
        self.path = path
        self.options = options
        self.driver_options = webdriver.ChromeOptions()
        for option in self.options:
            self.driver_options.add_argument(option)
        self.driver = webdriver.Chrome(path, options=self.driver_options)

    def click_button_xpath(self, tag_value):
        """Finds the element using xpath. If found, clicks it."""
        button = self.driver.find_elements_by_xpath(tag_value)
        if len(button) > 0:
            self.driver.execute_script("arguments[0].click();", button[0])

    def get_element_list(self, tag_value):
        """Get a list of elements from an xpath"""
        return self.driver.find_elements_by_xpath(tag_value)

    def execute_script(self, code, element):
        """Executes script"""
        return self.driver.execute_script(code, element)

    def current_url(self):
        """Gets current URL"""
        return self.driver.current_url

    def page_source(self):
        """Gets page source"""
        return self.driver.page_source

    def back(self):
        """Takes the driver 1 page back"""
        return self.driver.back()

    def close(self):
        """closes the driver"""
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
    """Searches one-way google flights based on the departure-arrival airports and departure date"""
    url = "https://www.google.com/flights?hl=en#flt={}.{}.{};c:USD;e:1;sd:1;t".format(search_filter.dep,
                                                                                      search_filter.arr,
                                                                                      search_filter.fly_date.
                                                                                      strftime("%Y-%m-%d"))
    print('Searching for flights from {} to {} for {}'.format(search_filter.dep, search_filter.arr, search_filter.
                                                              fly_date.strftime("%Y-%m-%d")))
    driver.driver.get(url)
    driver.driver.maximize_window()
    sleep(2)

    # Checks if there are no results in the search. If 0 results, returns None.
    try:
        driver.find_elements_by_xpath("//p[contains(text(),'no results')]")
        return None
    except:
        pass

    # Dropdown buttons can be directly clicked without opening.
    # driver.click_button_xpath("//div[@class='VfPpkd-RLmnJb']")
    driver.click_button_xpath("//li[@role='option' and @data-value=2 and @class='uT1UOd']")
    driver.click_button_xpath("//span[@class='bEfgkb']")
    # driver.click_button_xpath("//span[text()='Sort by:']")
    driver.click_button_xpath("//li[@role='option' and @data-value=2 and @class='uT1UOd' and text()='Price']")
    sleep(2)

    page_source = driver.page_source()
    page_soup = soup(page_source, "html.parser")
    return page_soup


def get_flight_info(flight_results_unexpanded, flight_count, fly_date, page_soup):
    print('Extracting all information about available flights')
    i = 0
    search_results = {}

    # Expanded_elements is used to extract layover, cabin_class, brand information
    expanded_elements = page_soup.findAll('div', {'class': 'yJwmMb'})

    # Info needs to be extracted only for 'flight_count' number of flights.
    for flight_result in flight_results_unexpanded[0:flight_count]:
        search_results[i] = {}
        search_results[i]['DEP'] = \
            flight_result.findAll('div', {'class': 'Ak5kof'})[0].findAll('span', {
                'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                0].text

        search_results[i]['ARR'] = \
            flight_result.findAll('div', {'class': 'Ak5kof'})[0].findAll('span', {
                'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                1].text

        if flight_result.findAll('span', {'class': 'pIgMWd ogfYpf'})[0].text == 'Nonstop':
            search_results[i]['STOPS'] = 0
        else:
            search_results[i]['STOPS'] = int(
                flight_result.findAll('span', {'class': 'pIgMWd ogfYpf'})[0].text.split(' ')[0])

        if len(flight_result.findAll('div', {'class': 'BVAVmf I11szd POX3ye'})) == 0:
            search_results[i]['PRICE'] = float('NaN')
        else:
            search_results[i]['PRICE'] = float(
                flight_result.findAll('div', {'class': 'BVAVmf I11szd POX3ye'})[0].findAll('span', {'role': 'text'})[
                    0].text.replace(',', '')[1:])

        search_results[i]['TRIP_DURATION'] = flight_result.findAll('div', {'class': 'gvkrdb AdWm1c tPgKwe ogfYpf'})[
            0].text

        search_results[i]['DEP_DATE'] = fly_date

        search_results[i]['DEP_TIME'] = \
            flight_result.findAll('span', {'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                0].text

        search_results[i]['ARR_TIME'] = \
            flight_result.findAll('span', {'class': 'CrAOse-hSRGPd CrAOse-hSRGPd-TGB85e-cOuCgd hide-focus-ring'})[
                1].text

        layovers = []
        cabin_classes = []
        brands = []
        # If 0 stops, then no layover is possible.
        if search_results[i]['STOPS'] == 0:
            cabin_classes.append(
                expanded_elements[i].findAll('div', {'class': 'MX5RWe sSHqwe y52p7d'})[0].findAll('span',
                                                                                                  {'class': 'Xsgmwe'})[
                    2].text)
            brands.append(
                expanded_elements[i].findAll('div', {'class': 'MX5RWe sSHqwe y52p7d'})[0].findAll('span',
                                                                                                  {'class': 'Xsgmwe'})[
                    0].text)
        else:
            # Goes into each flight info, and iterates over each stop to get info for each leg of flight.
            for j in range(search_results[i]['STOPS'] + 1):
                if j < search_results[i]['STOPS']:
                    layovers.append(
                        expanded_elements[i].findAll('div', {'class': 'tvtJdb eoY5cb y52p7d'})[j].text.replace(
                            'layover', 'at '))
                cabin_classes.append(
                    expanded_elements[i].findAll('div', {'class': 'MX5RWe sSHqwe y52p7d'})[j].findAll('span', {
                        'class': 'Xsgmwe'})[2].text)
                brands.append(
                    expanded_elements[i].findAll('div', {'class': 'MX5RWe sSHqwe y52p7d'})[j].findAll('span', {
                        'class': 'Xsgmwe'})[0].text)

        search_results[i]['LAYOVER'] = ' , '.join(layovers)
        search_results[i]['CABIN_CLASS'] = ' , '.join(cabin_classes)
        search_results[i]['BRANDS'] = ' , '.join(brands)

        i = i + 1
    return search_results


def create_dataframe(dep, arr, search_results, result_count, fly_date, urls):
    print('Creating DataFrame')
    df = pd.DataFrame(search_results)
    df = df.T

    # Takes extra day information from ARR_TIME and adds it to fly_date to get land_date
    land_date = [fly_date] * result_count
    add_days_to_dep_date = list(df.ARR_TIME.str.split('+').str[1].fillna(value=0).astype(int))
    for x in range(len(add_days_to_dep_date)):
        land_date[x] = land_date[x] + timedelta(days=add_days_to_dep_date[x])

    df['ARR_DATE'] = land_date
    df['ARR_TIME'] = df.ARR_TIME.str.split('+').str[0]
    df['URL'] = urls
    # to dump the flight results in csv, uncomment below line
    # create_csv(df, dep, arr)

    return df.sort_values('PRICE')


def create_csv(df, dep, arr):
    # to dump the flight results in csv, uncomment below line
    df.to_csv('Flights_{}_{}.csv'.format(dep, arr), sep=',')


class Scraper:
    def __init__(self, driver: Driver, search_filter: SearchFilter):
        self.driver = driver
        self.search_filter = search_filter

    def scrape(self, max_flights_to_scrape):
        # self.driver.driver.implicitly_wait(10)

        page_soup_unexpanded = search_flights(self.driver, self.search_filter)
        if page_soup_unexpanded is None:
            print('No flights found')
            return None

        # Gets 'departure time, arrival time, airlines, flight duration, number of stops and price' from this
        # unexpanded div
        flight_results_unexpanded = page_soup_unexpanded.findAll("div", {"class": "OgQvJf nKlB3b"})
        print('Total available flights = {}'.format(len(flight_results_unexpanded)))

        # Gets the list of all the toggles so that they can be expanded
        toggles = self.driver.get_element_list("//div[@class='xKbyce']")

        # No toggles mean no flight was found. Decides number of flights to be scraped.
        if len(toggles) == 0:
            print('No flights found')
            return None
        else:
            if max_flights_to_scrape <= len(toggles):
                flights_to_scrape = max_flights_to_scrape
            else:
                flights_to_scrape = len(toggles)

        # Expand all the toggles first
        for x in range(flights_to_scrape):
            self.driver.execute_script("arguments[0].click();", toggles[x])

        # get page source of the full page to get layover info, and cabin class
        page_source = self.driver.page_source()
        page_soup = soup(page_source, "html.parser")

        # Search_results is a dictionary to store flight info
        search_results = get_flight_info(flight_results_unexpanded, flights_to_scrape, self.search_filter.fly_date,
                                         page_soup)

        print('Extracting URLs for all available flights')
        urls = []
        for x in range(flights_to_scrape):
            # Select_flight_buttons have to be searched everytime because the elements go stale when 'back' happens.
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

            urls.append(self.driver.current_url())
            if x == flights_to_scrape - 1:
                break
            self.driver.back()

            sleep(1)
            toggle_url = self.driver.get_element_list("//div[@class='xKbyce']")
            # try:
            #     a = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable("//div[@class='xKbyce']"[0]))
            #     a.click()
            # except TimeoutException:
            #     pass

            # If number of updated toggle buttons is not same as original toggle buttons, it implies flight result
            # has changed.
            if len(toggles) != len(toggle_url):
                print('Number of flights changed from {} to {} during scraping. Re-firing'.format(len(toggles),
                                                                                                  len(
                                                                                                      toggle_url)))
                df = self.scrape(max_flights_to_scrape)
                return df
            self.driver.execute_script("arguments[0].click();", toggle_url[x + 1])

        return create_dataframe(self.search_filter.dep, self.search_filter.arr, search_results, flights_to_scrape, self.search_filter.fly_date, urls)


def main():
    # User inputs
    web_driver_path = '/Users/khugel01/Downloads/chromedriver'
    driver_options = ('--ignore-certificate-errors',
                      '--incognito',
                      '--headless'
                      )
    departure_airport = 'ORD'
    arrival_airport = ['ATL', 'PSE', 'ORD', 'SFO']
    # arrival_airport = (
    #     "ATL",
    #     "LAX",
    #     "ORD",
    #     "DFW",
    #     "DEN",
    #     "JFK",
    #     "SFO",
    #     "SEA",
    #     "LAS",
    #     "MCO",
    #     "CLT",
    #     "EWR",
    #     "PHX",
    #     "IAH",
    #     "MIA",
    #     "BOS",
    #     "MSP",
    #     "DTW",
    #     "FLL",
    #     "PHL",
    #     "LGA",
    #     "BWI",
    #     "SLC",
    #     "SAN",
    #     "IAD",
    #     "DCA",
    #     "TPA",
    #     "MDW",
    #     "HNL",
    #     "PDX",
    #     "BNA",
    #     "AUS",
    #     "DAL",
    #     "STL",
    #     "SJC",
    #     "HOU",
    #     "RDU",
    #     "MSY",
    #     "OAK",
    #     "SMF",
    #     "MCI",
    #     "SNA",
    #     "RSW",
    #     "SAT",
    #     "CLE",
    #     "PIT",
    #     "IND",
    #     "SJU",
    #     "CVG",
    #     "CMH",
    #     "OGG",
    #     "JAX",
    #     "PBI",
    #     "MKE",
    #     "BDL",
    #     "BUR",
    #     "ONT",
    #     "ANC",
    #     "ABQ",
    #     "BUF",
    #     "OMA",
    #     "CHS",
    #     "MEM",
    #     "RIC",
    #     "RNO",
    #     "OKC",
    #     "BOI",
    #     "SDF",
    #     "ORF",
    #     "PVD",
    #     "GEG",
    #     "KOA",
    #     "TUS",
    #     "GRR",
    #     "LGB",
    #     "ELP",
    #     "LIH",
    #     "SFB",
    #     "BHM",
    #     "TUL",
    #     "ALB",
    #     "SAV",
    #     "DSM",
    #     "PSP",
    #     "MYR",
    #     "GSP",
    #     "ROC",
    #     "SYR",
    #     "TYS",
    #     "GUM",
    #     "MSN",
    #     "PIE",
    #     "PNS",
    #     "PWM",
    #     "LIT",
    #     "GSO",
    #     "SRQ",
    #     "FAT",
    #     "XNA",
    #     "IWA",
    #     "HPN",
    #     "ICT",
    #     "MHT",
    #     "DAY",
    #     "COS",
    #     "PGD",
    #     "VPS",
    #     "AVL",
    #     "BZN",
    #     "ISP",
    #     "MDT",
    #     "LEX",
    #     "HSV",
    #     "BTV",
    #     "MAF",
    #     "CID",
    #     "CAE",
    #     "ECP",
    #     "EUG",
    #     "STT",
    #     "SGF",
    #     "ITO",
    #     "FSD",
    #     "FAI",
    #     "CHA",
    #     "JAN",
    #     "ILM",
    #     "MFR",
    #     "ACY",
    #     "LBB",
    #     "SBA",
    #     "EYW",
    #     "RDM",
    #     "FAR",
    #     "BIL",
    #     "TTN",
    #     "MSO",
    #     "JAC",
    #     "PSC",
    #     "ABE",
    #     "SBN",
    #     "TLH",
    #     "MFE",
    #     "CAK",
    #     "FWA",
    #     "JNU",
    #     "BTR",
    #     "PAE",
    #     "CHO",
    #     "ATW",
    #     "GPT",
    #     "BQN",
    #     "ROA",
    #     "GPI",
    #     "MLI",
    #     "GSN",
    #     "AMA",
    #     "GRB",
    #     "RAP",
    #     "PIA",
    #     "DAB",
    #     "HRL",
    #     "BLI",
    #     "AGS",
    #     "MOB",
    #     "CRP",
    #     "SHV",
    #     "BGR",
    #     "BIS",
    #     "ASE",
    #     "FNT",
    #     "AVP",
    #     "TVC",
    #     "GNV",
    #     "SWF",
    #     "SBP",
    #     "LFT",
    #     "GJT",
    #     "EVV",
    #     "MLB",
    #     "STS",
    #     "MRY",
    #     "CRW",
    #     "STX",
    #     "TRI",
    #     "FAY",
    #     "PHF",
    #     "BMI",
    #     "DRO",
    #     "MGM",
    #     "UNV",
    #     "GCN",
    #     "EGE",
    #     "RST",
    #     "JQF",
    #     "GRK",
    #     "GTF",
    #     "IDA",
    #     "LAN",
    #     "LNK",
    #     "MOT",
    #     "OAJ",
    #     "BVU",
    #     "BET",
    #     "LBE",
    #     "MTJ",
    #     "ELM",
    #     "DLH",
    #     "LCK",
    #     "BLV",
    #     "AZO",
    #     "SAF",
    #     "AEX",
    #     "CWA",
    #     "KTN",
    #     "ACK",
    #     "MBS",
    #     "BFL",
    #     "COU",
    #     "BRO",
    #     "PBG",
    #     "TOL",
    #     "IAG",
    #     "FLG",
    #     "HLN",
    #     "GFK",
    #     "RFD",
    #     "MLU",
    #     "EWN",
    #     "HXD",
    #     "PVU",
    #     "ITH",
    #     "HTS",
    #     "ERI",
    #     "HDN",
    #     "CMI",
    #     "PSE",
    #     "SGU",
    #     "SCK",
    #     "NYL",
    #     "CPR"
    # )
    fly_date = datetime.datetime(2021, 3, 10)

    # Execution starts

    driver = Driver(web_driver_path, driver_options)
    i = 1
    for a in arrival_airport:
        print('query #{}'.format(i))
        search_filter = SearchFilter(departure_airport, a, fly_date)
        scraper = Scraper(driver, search_filter)

        # If any random exception occurs, it will re-try scraping 1 more time before exiting.
        for rerun_count in range(2):
            try:
                scraper.scrape(7)
                break
            except Exception as e:
                # In case some random exception occurs, scraper will make 1 more attempt.
                if rerun_count == 1:
                    sys.exit('Retry failed after an exception occurred')
                continue
        i = i + 1
    driver.close()


main()

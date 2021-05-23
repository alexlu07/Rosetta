from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import time

opt = Options()
# opt.add_argument("headless")
opt.add_experimental_option("prefs", { \
    "profile.default_content_setting_values.media_stream_mic": 2,
    "profile.default_content_setting_values.media_stream_camera": 2,
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.notifications": 2
  })

class RosettaBot:
    browser = webdriver.Chrome(options=opt)
    wait = WebDriverWait(browser, 500)
    swait = WebDriverWait(browser, 1)

    def __init__(self, activities):
        print("Bot Initialized")
        self.browser.get("https://clever.com/oauth/authorize?channel=clever-portal&client_id=48ce2b70f34e2b069a79&confirmed=true&district_id=5aba967e5dba5a00013851df&redirect_uri=https%3A%2F%2Fstatic.rosettastoneclassroom.com%2Fclever%2Fauth%2FESP&response_type=code")
        print("Login link reached")

        self.login()

        self.start(activities)

    def login(self):
        self.get_element("//a[@class='flexbox items--center AuthMethod--container']").click()

        with open(".school.txt") as f:
            e = f.readline().strip()
            p = f.readline().strip()

        print("Entering email and password")
        self.get_element("//input[@id='identifierId']").send_keys(e + Keys.RETURN)
        self.get_element("//input[@name='password']").send_keys(p + Keys.RETURN)


        self.get_element("//*[@id='community_launch_link']/a").click()
        print("Successfully logged into Rosetta Stone")
        time.sleep(5)

    def start(self, activities):
        for activity in activities:
            print("Navigating activity")
            self.navigate(activity)
            print("Finished navigating")

            self.loop()
            time.sleep(500)

    def loop(self):
        # find out how many activities
        activities = 36
        print("Found number of activities")
        for i in range(activities):
            self.solve()

    def solve(self):
        print("Solving")
        pronunciation = True
        while True:
            print("\tDetecting type of problem")
            button = self.wait.until(EC.any_of(
                EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='GlobalVisibilityButton']/div")),
                EC.element_to_be_clickable((By.XPATH, "//button[@data-qa='next_button']"))))
            if button.get_attribute("data-qa") == "next_button":
                if pronunciation:
                    print("\tProblem is Pronunciation")
                print("\tMoving to next problem")
                button.click()
                return
            else:
                pronunciation = False
                try:
                    bar = self.swait.until(EC.any_of(
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='CueComponentWrapperActChoice']")),
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='CuesComponentWrapperCueChoice']"))))
                    if bar.get_attribute("data-qa") == "CueComponentWrapperActChoice":
                        print("\tProblem is Bar")
                        if self.solve_bar():
                            return
                    elif bar.get_attribute("data-qa") == "CuesComponentWrapperCueChoice":
                        print("\tProblem is TopBar")
                        self.solve_topbar()
                except:
                    print("\tProblem is Dropdown")
                    self.solve_dropdown()

    def solve_bar(self):
        skip = self.get_element("//div[@data-qa='skip']")
        try:
            print("\tProblem is text")
            text = self.get_element("//span[@data-qa='CueText-0']", w=self.swait).text
            print(f"\t\tFound text: {text}")

            hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
            hide.click()
            print("\t\tShowing answers")

            choices = self.get_element("//span[contains(@data-qa, 'ActText')]", multiple=True)
            idx = None
            for i, c in enumerate(choices):
                if c.text == text:
                    idx = i+1
            print("\t\tAnswers found")
            hide.click()

            print("\t\tClicking correct answer")
            self.get_element(f"(//div[contains(@data-qa, 'ActComponent')])[{idx}]").click()

            return False
        except Exception as e:
            print("\tProblem is sound - Skipping")
            skip.click()
            return True

    def solve_topbar(self):
        skip = self.get_element("//div[@data-qa='skip']")
        skip.click()

    def solve_dropdown(self):
        skip = self.get_element("//div[@data-qa='skip']")
        skip.click()

    def navigate(self, activity):
        self.browser.get("https://totale.rosettastone.com/units")
        path = f"//div[@data-qa='UnitItem-{activity[0]}']"
        while True:
            try:
                self.get_element(path).click()
                break
            except:
                pass

        self.get_element(f"//div[@data-qa='lesson-number-{activity[1]}']").click()
        self.get_element("//div[@data-qa='path-badge']/div[@class='css-1etijt1']/button", True)[activity[2]].click()

        self.get_element("//button[@data-qa='PromptButton' and @class='css-epcrq8']").click()

    def get_element(self, path, multiple=False, w=wait):
        w.until(EC.element_to_be_clickable((By.XPATH, path)))
        if multiple:
            return self.browser.find_elements(By.XPATH, path)
        else:
            return self.browser.find_element(By.XPATH, path)

a = [[5, 0, 0], [5, 1, 2]]
RosettaBot(a)

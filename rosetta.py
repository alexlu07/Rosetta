from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import psutil
import os
import subprocess
import time
import re
import collections

from gtts import gTTS
from pydub import AudioSegment

from pygame._sdl2 import get_num_audio_devices, get_audio_device_name #Get playback device names
import pygame

os.system("pactl unload-module module-null-sink")
os.system("pactl load-module module-null-sink sink_name=MicOutput sink_properties=device.description='Virtual_Microphone_Output'")

pygame.mixer.init() #Initialize the mixer, this will allow the next command to work
audios = [get_audio_device_name(x, 0).decode() for x in range(get_num_audio_devices(0))] #Returns playback devices
print(audios)
virtual_mic = ""
for a in audios:
    if 'Virtual_Microphone' in a: virtual_mic = a
print(virtual_mic)
pygame.mixer.quit()

pygame.mixer.init(devicename=virtual_mic)


opt = Options()
# opt.add_argument("headless")
opt.add_experimental_option("prefs", {
    "profile.default_content_setting_values.media_stream_mic": 1,
    "profile.default_content_setting_values.media_stream_camera": 2,
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.notifications": 2
  })

class RosettaBot:
    browser = webdriver.Chrome(options=opt)
    pid = browser.service.process.pid
    wait = WebDriverWait(browser, 500)
    swait = WebDriverWait(browser, 1)
    didMicSetup = False

    def __init__(self, activities, language):
        print("Bot Initialized")
        self.language = language

        self.browser.get("https://clever.com/oauth/authorize?channel=clever-portal&client_id=48ce2b70f34e2b069a79&confirmed=true&district_id=5aba967e5dba5a00013851df&redirect_uri=https%3A%2F%2Fstatic.rosettastoneclassroom.com%2Fclever%2Fauth%2FESP&response_type=code")
        print("Login link reached")

        self.login()

        self.start(activities)

    def login(self):
        self.get_element("//a[@class='flexbox items--center AuthMethod--container']").click()

        with open('.school.txt') as f:
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
            time.sleep(1)

    def solve(self):
        print("Solving")
        pronunciation = True

        while True:
            print("\tDetecting type of problem")
            button = self.wait.until(EC.any_of(
                EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='GlobalVisibilityButton']/div")),
                EC.element_to_be_clickable((By.XPATH, "//button[@data-qa='next_button']"))
            ))


            # if pronunciation
            if button.get_attribute("data-qa") == "next_button":
                button.click()
                return
            else:
                try:
                    ele = self.swait.until(EC.any_of(
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='CueComponentWrapperActChoice']")),
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='CuesComponentWrapperCueChoice']")),
                        EC.element_to_be_clickable((By.XPATH, "//span[@data-qa='SkipActButton-true']")),
                        EC.element_to_be_clickable((By.XPATH, "//button[@data-qa='next_button']"))
                    ))
                    if ele.get_attribute("data-qa") == "next_button":
                        ele.click()
                        return
                    elif ele.get_attribute("data-qa") == "CueComponentWrapperActChoice":
                        print("\tProblem is Bar")
                        if self.solve_bar():
                            return
                    elif ele.get_attribute("data-qa") == "CuesComponentWrapperCueChoice":
                        print("\tProblem is TopBar")
                        if self.solve_topbar():
                            return
                    elif ele.get_attribute("data-qa") == "SkipActButton-true":
                        print("\tProblem is Pronunciation")
                        if self.solve_speaking():
                            return
                except:
                    print("\tProblem is Dropdown")
                    self.solve_dropdown()
                    return

    def solve_speaking(self):
        el = self.get_element("//span[@data-qa='SkipActButton-true']")

        parent = el.find_element(By.XPATH, '..')
        num = parent.get_attribute('data-qa')[-1]

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()


        words = self.get_element(f"//span[@data-qa='ActText-{num}']").get_attribute('innerHTML')

        hide.click()
        sound = gTTS(text=words, lang=language, slow=False)
        sound.save("sample.mp3")

        audio = AudioSegment.from_mp3("sample.mp3")
        audio.export("sample.wav", format="wav")

        self.get_element('//div[@data-qa="SREEchoBox"]')
        time.sleep(0.5)

        self.play_through_mic("sample.wav")
        time.sleep(5)

    def solve_bar(self):
        skip = self.get_element("//div[@data-qa='skip']")
        try:
            # print("\tProblem is text")
            text = self.get_element("//span[@data-qa='CueText-0']", w=self.swait).text
            # print(f"\t\tFound text: {text}")

            hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
            hide.click()
            # print("\t\tShowing answers")

            choices = self.get_element("//span[contains(@data-qa, 'ActText')]", multiple=True)
            idx = None
            for i, c in enumerate(choices):
                if c.text == text:
                    idx = i+1
            # print("\t\tAnswers found")
            hide.click()

            # print("\t\tClicking correct answer")
            self.get_element(f"(//div[contains(@data-qa, 'ActComponent')])[{idx}]").click()
            time.sleep(1)

            return False
        except Exception as e:
            # print("\tProblem is sound - Skipping")
            skip.click()
            return True

    def solve_topbar(self):
        skip = self.get_element("//div[@data-qa='skip']")
        acts = [i.get_attribute("class") for i in self.get_element("//div[@data-qa='ActHeaderWrapperSoundTextContainer']", multiple=True)]

        idx_class = collections.Counter(acts).most_common()[-1][0]

        question_idx = acts.index(idx_class)


        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()


        text = self.get_element(f"//span[@data-qa='ActText-{question_idx}']").text

        hide.click()

        choices = self.get_element("//span[contains(@data-qa, 'CueText')]", multiple=True)
        for c in choices:
                if c.text == text:
                    c.click()
                    return False


        skip.click()

    def solve_dropdown(self):
        skip = self.get_element("//div[@data-qa='skip']")
        skip.click()

    def mic_setup(self):
        didMicSetup = True

        outputs = subprocess.check_output("pactl list sources short", shell=True).decode("utf-8")
        for line in outputs.split("\n"):
            if "MicOutput" in line:
                self.vmic_id = re.search("(\d+).*", line).group(1)
                break

        # pygame.mixer.music.load("12345.wav")

        self.get_element("//button[@data-qa='ContinueButton']").click()
        self.get_element('//span[@data-qa="mic_calibration_please_say"]')
        time.sleep(0.5)

        self.play_through_mic("12345.wav")

        self.get_element("//button[@data-qa='ContinueButton']").click()

    def play_through_mic(self, path):
        source_outputs = subprocess.check_output("pactl list source-outputs", shell=True).decode("utf-8")
        output_id = None
        source = None
        # print(source_outputs)
        for line in source_outputs.split("\n"):
            line = line.strip()
            if "Source Output #" in line:
                output_id = line[15:]
            elif "Source: " in line:
                source = line[8:]
            elif "application.process.id = " in line:
                if psutil.Process(int(line[26:-1])).parent().ppid() == self.pid:
                    break
        else:
            raise Exception("Source-output not found")

        # print(output_id, self.vmic_id)
        os.system(f"pactl move-source-output {output_id} {self.vmic_id}")

        sound = pygame.mixer.Sound(path)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.delay(100)


        os.system(f"pactl move-source-output {output_id} {source}")


    def navigate(self, activity):
        self.browser.get("https://totale.rosettastone.com/units")
        path = f"//div[@data-qa='UnitItem-{activity[0]}']"
        while True:
            try:
                self.get_element(path).click()
                break
            except:
                pass
        time.sleep(2)
        self.get_element(f"//div[@data-qa='lesson-number-{activity[1]}']").click()
        self.get_element("//div[@data-qa='path-badge']/div[@class='css-1etijt1']/button", True)[activity[2]].click()
        if not self.didMicSetup:
            self.get_element("//select[@data-qa='MicList']")
            self.mic_setup()
        else:
            pass
            # self.get_element("//button[@data-qa='PromptButton' and @class='css-epcrq8']").click()

    def get_element(self, path, multiple=False, w=wait):
        w.until(EC.element_to_be_clickable((By.XPATH, path)))
        if multiple:
            return self.browser.find_elements(By.XPATH, path)
        else:
            return self.browser.find_element(By.XPATH, path)

a = [[5, 0, 0], [5, 1, 2]]
language = 'es'

RosettaBot(a, language)

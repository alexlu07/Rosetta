LINUX = True

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

if LINUX:
    import psutil
    from pydub import AudioSegment
import os
import subprocess
import time
import re
import collections

from gtts import gTTS
import speech_recognition as sr
import Levenshtein

from pygame._sdl2 import get_num_audio_devices, get_audio_device_name #Get playback device names
import pygame
from pygame import mixer



if LINUX:
    print('USING LINUX')
    os.system("pactl unload-module module-null-sink")
    os.system("pactl load-module module-null-sink sink_name=MicOutput sink_properties=device.description='Virtual_Microphone_Output'")
    os.system("pactl load-module module-null-sink sink_name=MicInput sink_properties=device.description='Virtual_Microphone_Input'")

    pygame.mixer.init() #Initialize the mixer, this will allow the next command to work
    audios = [get_audio_device_name(x, 0).decode() for x in range(get_num_audio_devices(0))] #Returns playback devices
    print(audios)
    virtual_mic = ""
    for a in audios:
        if 'Virtual_Microphone_Output' in a: virtual_mic = a
    print(virtual_mic)
    pygame.mixer.quit()

    pygame.mixer.init(devicename=virtual_mic)

else:
    print("MACOS OR WINDOWS")
    mixer.init() #Initialize the mixer, this will allow the next command to work
    audios = [get_audio_device_name(x, 0).decode() for x in range(get_num_audio_devices(0))] #Returns playback devices
    print(audios)
    vb = ""
    for a in audios:
        if 'VB' in a: vb = a
    print(vb)
    mixer.quit()
    mixer.init(devicename=vb)



opt = Options()
# opt.add_argument("headless")
opt.add_experimental_option("prefs", {
    "profile.default_content_setting_values.media_stream_mic": 1,
    "profile.default_content_setting_values.media_stream_camera": 2,
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.notifications": 2
})

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

class RosettaBot:
    browser = webdriver.Chrome(options=opt)
    pid = browser.service.process.pid
    wait = WebDriverWait(browser, 500)
    swait = WebDriverWait(browser, 1)
    varwait = lambda self, sec: WebDriverWait(self.browser, sec)
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

        if LINUX:
            with open('.school.txt') as f:
                e = f.readline().strip()
                p = f.readline().strip()
        else:
            with open(os.path.join(__location__, 'school.txt')) as f:
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

            if button.get_attribute("data-qa") == "next_button":
                button.click()
                return
            else:

                ele = self.wait.until(EC.any_of(
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='CueComponentWrapperActChoice']")),
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-qa='CuesComponentWrapperCueChoice']")),
                        EC.element_to_be_clickable((By.XPATH, "//span[@data-qa='SkipActButton-true']")),
                        EC.element_to_be_clickable((By.XPATH, "//button[@data-qa='next_button']")),
                        EC.element_to_be_clickable((By.XPATH, "//span[starts-with(@data-qa, 'ActTileChoice')]"))
                    ))

                print("DATA-QA", ele.get_attribute("data-qa"))

                if ele.get_attribute("data-qa") == "next_button":
                    ele.click()

                elif ele.get_attribute("data-qa") == "CueComponentWrapperActChoice":
                    print("\tProblem is Bar")
                    self.solve_bar()

                elif ele.get_attribute("data-qa") == "CuesComponentWrapperCueChoice":
                    print("\tProblem is TopBar")
                    self.solve_topbar()

                elif ele.get_attribute("data-qa") == "SkipActButton-true":
                    print("\tProblem is Pronunciation")
                    self.solve_speaking()

                elif "ActTileChoice" in ele.get_attribute("data-qa"):
                    print("\tProblem is dropdown")
                    self.solve_dropdown()

    def solve_speaking(self):
        el = self.get_element("//span[@data-qa='SkipActButton-true']")
        num = el.find_element(By.XPATH, "..").get_attribute('data-qa')[-1]

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()

        words = self.get_element(f"//span[@data-qa='ActText-{num}']").get_attribute('innerHTML')

        hide.click()
        sound = gTTS(text=words, lang=language, slow=False)

        if LINUX:
            sound.save("sample.mp3")

            audio = AudioSegment.from_mp3("sample.mp3")
            audio.export("sample.wav", format="wav")

            self.get_element('//div[@data-qa="SREEchoBox"]')
            time.sleep(0.5)

            self.play_through_mic("sample.wav")

        else:
            path = os.path.join(__location__, "sample.mp3")
            sound.save(path)

            mixer.music.load(path)
            self.get_element('//div[@data-qa="SREEchoBox"]')
            time.sleep(0.5)
            mixer.music.play()

        time.sleep(5)

    def solve_bar(self):
        skip = self.get_element("//div[@data-qa='skip']")

        text = None
        try:
            text = self.get_element("//span[@data-qa='CueText-0']", w=self.swait).text
        except:
            self.get_element("//span[contains(@data-qa, 'RSIcon-audioPause')]")
            print("LISTENING")

            self.solve_listening_bar()
            return

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()

        choices = self.get_element("//span[contains(@data-qa, 'ActText')]", multiple=True)
        idx = None
        for i, c in enumerate(choices):
            if c.text == text:
                idx = i+1
        hide.click()

        self.get_element(f"(//div[contains(@data-qa, 'ActComponent')])[{idx}]").click()
        time.sleep(1)

        return

    def solve_listening_bar(self):
        text = self.listen()
        print(text)

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()

        choices = self.get_element("//span[contains(@data-qa, 'ActText')]", multiple=True)
        idx = [None, float("inf")]
        for i, c in enumerate(choices):
            dist = Levenshtein.distance(c.text, text)
            print(dist, i, c.text)
            if dist < idx[1]:
                idx = [i+1, dist]
        hide.click()

        print(idx)
        self.get_element(f"(//div[contains(@data-qa, 'ActComponent')])[{idx[0]}]").click()
        time.sleep(1)

        return

    def listen(self):
        if LINUX:
            sink_inputs = subprocess.check_output("pactl list sink-inputs", shell=True).decode("utf-8")
            # print(sink_inputs)
            input_id = []
            sink = []
            # print(source_outputs)
            found = False
            for line in sink_inputs.split("\n"):
                line = line.strip()
                if "Sink Input #" in line:
                    i = line[12:]
                elif "Sink: " in line:
                    s = line[6:]
                elif "application.process.id = " in line:
                    # print(self.pid, psutil.Process(int(line[26:-1])).parent().ppid())
                    if psutil.Process(int(line[26:-1])).parent().ppid() == self.pid:
                        input_id.append(i)
                        sink.append(s)
                        found = True
            if not found:
                raise Exception("Sink-input not found")

            # print(output_id, self.vmic_id)
            for i in input_id:
                # print(i, self.vmicin_id)
                os.system(f"pactl move-sink-input {i} {self.vmicinsink_id}")

            r = sr.Recognizer()
            mic = sr.Microphone()
            self.get_element("//span[contains(@data-qa, 'RSIcon-audio-')]")
            with mic as mic_source:
                source_outputs = subprocess.check_output("pactl list source-outputs", shell=True).decode("utf-8")
                # print(source_outputs)
                output_id = None
                source = None
                for line in source_outputs.split("\n"):
                    line = line.strip()
                    if "Source Output #" in line:
                        output_id = line[15:]
                    elif "Source: " in line:
                        source = line[8:]
                    elif "application.process.id = " in line:
                        # print(os.getpid(), int(line[26:-1]))
                        if int(line[26:-1]) == os.getpid():
                            # print(output_id, self.vmicinsource_id)
                            os.system(f"pactl move-source-output {output_id} {self.vmicinsource_id}")
                            break
                else:
                    raise Exception("Source-output not found")

                self.get_element("//span[contains(@data-qa, 'RSIcon-audio-')]").click()
                audio = r.listen(mic_source)

                # print("a")
                os.system(f"pactl move-source-output {output_id} {source}")

            for i, s in zip(input_id, sink):
                os.system(f"pactl move-sink-input {i} {s}")

            return r.recognize_google(audio, language="es")

    def solve_topbar(self):

        isImage = False

        skip = self.get_element("//div[@data-qa='skip']")

        acts = [i.get_attribute("class") for i in self.get_element("//div[@data-qa='ActHeaderWrapperSoundTextContainer']", multiple=True)]

        idx_class = collections.Counter(acts).most_common()[-1][0]

        question_idx = acts.index(idx_class)

        self.get_element("//div[@data-qa='CuesComponentWrapperCueChoice']")
        time.sleep(1)
        try:
            self.browser.find_element(By.XPATH, "//div[@data-qa='ImageComponentWrap']")
            isImage = True
            print("ITS AN IMAGE")
        except:
            print("not image")

        if isImage:
            return self.solve_image_topbar()

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()

        text = self.get_element(f"//span[@data-qa='ActText-{question_idx}']").text

        hide.click()

        for c in self.get_element("//span[contains(@data-qa, 'CueText')]", multiple=True):
            if c.text == text:
                c.click()
                return False


        skip.click()
    def solve_image_topbar(self):
        print('solving image topbar')

        question_idx = 0

        components = self.get_element("//div[contains(@data-qa, 'ActComponent')]", multiple=True)
        for i, el in enumerate(components):
            try:
                el.find_element(By.TAG_NAME, 'img')
            except:
                question_idx = i
                break

        print('box #' + str(question_idx))

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()

        box = self.get_element(f"//div[@data-qa='ActComponent-{question_idx}']")
        img = box.find_element(By.TAG_NAME, 'img')
        src = img.get_attribute('src')

        hide.click()

        choices = self.get_element('//div[@data-qa="ImageComponentWrap"]', multiple=True)
        for c in choices:
            if c.find_element(By.TAG_NAME, 'img').get_attribute('src') == src:
                c.click()
                return False

        skip = self.get_element("//div[@data-qa='skip']")
        skip.click()

    def solve_dropdown(self):
        # get which word it's looking for
        wordsBefore = 0
        options = self.get_element("//span[starts-with(@data-qa, 'ActTileChoice')]")
        opscontainer = options.find_element(By.XPATH, '..').find_element(By.XPATH, '..')
        words = opscontainer.find_element(By.XPATH, '..')
        allWords = words.find_elements(By.XPATH, './*')
        print('allwords length:', len(allWords))
        for word in allWords:
            if word == opscontainer:
                break
            text = word.find_element(By.TAG_NAME, 'span').text.strip()
            if len(text) > 0:
                wordsBefore += 1
                print(text)

        card = words.find_element(By.XPATH, '..').find_element(By.XPATH, '..')

        num = card.get_attribute('data-qa').split('-')[1]

        print('wordsbefore:', wordsBefore)

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()

        text = self.get_element(f"//span[@data-qa='ActText-{num}']").text
        wordToFind = text.split(' ')[wordsBefore]
        wordToFind = re.sub(r'\W+', '', wordToFind)

        print('word to find:', wordToFind)

        hide = self.get_element("//div[@data-qa='GlobalVisibilityButton']")
        hide.click()

        opscontainer = self.get_element("//span[starts-with(@data-qa, 'ActTileChoice')]").find_element(By.XPATH, '..').find_element(By.XPATH, '..')

        options = opscontainer.find_elements(By.XPATH, './*')
        for op in options:
            text = op.find_element(By.TAG_NAME, 'span').text
            print(text)
            if text == wordToFind:
                op.click()
                return False

    def mic_setup(self):

        if LINUX:
            inputs = subprocess.check_output("pactl list sinks short", shell=True).decode("utf-8")
            for line in inputs.split("\n"):
                if "MicInput" in line:
                    self.vmicinsink_id = re.search("(\d+).*", line).group(1)

            outputs = subprocess.check_output("pactl list sources short", shell=True).decode("utf-8")
            for line in outputs.split("\n"):
                if "MicOutput" in line:
                    self.vmicout_id = re.search("(\d+).*", line).group(1)
                if "MicInput" in line:
                    self.vmicinsource_id = re.search("(\d+).*", line).group(1)

            # pygame.mixer.music.load("12345.wav")

            self.get_element("//button[@data-qa='ContinueButton']").click()
            self.get_element('//span[@data-qa="mic_calibration_please_say"]')
            time.sleep(0.5)

            self.play_through_mic("12345.wav")

            self.get_element("//button[@data-qa='ContinueButton']").click()

        else:
            mixer.music.load(os.path.join(__location__, '12345.mp3'))

            micList = self.get_element('//select[@data-qa="MicList"]')
            micList.click()

            options = [x for x in micList.find_elements(By.TAG_NAME, "option")]
            for i in options:
                if 'VB' in i.get_attribute("value"):
                    i.click()
                    break

            time.sleep(2)
            self.get_element('//button[@data-qa="ContinueButton"]').click()
            self.get_element('//span[@data-qa="mic_calibration_please_say"]')
            time.sleep(0.5)
            mixer.music.play()
            time.sleep(5)
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
        os.system(f"pactl move-source-output {output_id} {self.vmicout_id}")

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

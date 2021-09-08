import json, ctypes, asyncio, logging, sys
from pyppeteer import launch

logging.disable(logging.CRITICAL)

class CreateVCC:
    def __init__(self, username, password, amount):
        self.amount = amount
        self.created = 0
        self.user = username
        self.pw = password
        ctypes.windll.kernel32.SetConsoleTitleW(f"Citi VCC Generator ~ By @dzintt | Progress: {self.created}/{self.amount}")
        asyncio.run(self.initBrowser())
    
    async def initBrowser(self):

        self.browser = await launch({'headless': False , 'defaultViewport': None}, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False, logLevel=0, autoClose=False, executablePath=chromePath)

        page = await self.browser.pages()
        page = page[0]
        await page.goto("https://online.citi.com/US/ag/repcard/van2", {'waitUntil':'networkidle2'})
        await sendKeys(page, '//*[@id="username"]', self.user, 10000)
        await asyncio.sleep(0.5)
        await sendKeys(page, '//*[@id="password"]', self.pw, 10000)
        await asyncio.sleep(0.5)
        await click(page, '//*[@id="signInBtn"]', 10000)

        url = await page.evaluate("window.location.href")
        while not url.startswith("https://online.citi.com/US/ag/repcard/van2"):
            await page.waitForNavigation({'waitUntil':'load', 'timeout': 0})
            url = await page.evaluate("window.location.href")

        queue = asyncio.Queue()

        for _ in range(self.amount):
            await queue.put("https://online.citi.com/US/ag/repcard/van2/vangeneratestart")

        tasks = []
        for _ in range(1):
            tasks.append(asyncio.create_task(self.create(queue)))

        await queue.join()

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

    async def create(self, queue):
        while True:
            isEmpty = queue.empty()
            if not isEmpty:
                data = await queue.get()
                print(f"Starting Create ({self.created+1})")

                taskPage = await self.browser.newPage()
                await taskPage.goto(data, {'waitUntil':'networkidle0'})
                print(f"Creating Card... ({self.created+1})")

                await click(taskPage, '//*[@id="radio2-1-input"]', 10000)
                await click(taskPage, '//*[@class="btn btn-primary default"]', 10000)
                await asyncio.sleep(1)
                await taskPage.evaluate('document.getElementById("setTimeTo2").click()')
                await click(taskPage, '//*[@id="van-get-started"]', 10000)

                url = await taskPage.evaluate("window.location.href")
                while "finalvangenerate" not in url:
                    await taskPage.waitForNavigation({'waitUntil':'load', 'timeout': 0})
                    url = await taskPage.evaluate("window.location.href")
                
                cardNum = await taskPage.evaluate('document.getElementsByClassName("cust-labl1")[0].textContent')
                cvv = await taskPage.evaluate('document.getElementsByClassName("cust-labl1")[2].textContent')
                exp = await taskPage.evaluate('document.getElementsByClassName("cust-labl1")[1].textContent')

                save(f"{cardNum.replace(' ', '')} {cvv} {exp}")

                self.created += 1

                print(f"Created Card ({self.created})")

                ctypes.windll.kernel32.SetConsoleTitleW(f"Citi VCC Generator ~ By @dzintt | Progress: {self.created}/{self.amount}")
                await taskPage.close()
            else:
                break

        print(f"Task Finished")
        await queue.task_done()

class DeleteVCC:
    def __init__(self, username, password):
        self.deleted = 0
        self.user = username
        self.pw = password
        ctypes.windll.kernel32.SetConsoleTitleW(f"Citi VCC Generator ~ By @dzintt | Deleting VCC's ({self.deleted})")
        asyncio.run(self.initBrowser())
    
    async def initBrowser(self):
        self.browser = await launch({'args': ['--window-size=1600,1000'], 'headless': False , 'defaultViewport': None}, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False, logLevel=0, autoClose=False, executablePath=chromePath)

        page = await self.browser.pages()
        page = page[0]

        await page.goto("https://online.citi.com/US/ag/repcard/van2", {'waitUntil':'networkidle2'})
        await sendKeys(page, '//*[@id="username"]', self.user, 10000)
        await asyncio.sleep(0.5)
        await sendKeys(page, '//*[@id="password"]', self.pw, 10000)
        await asyncio.sleep(0.5)
        await click(page, '//*[@id="signInBtn"]', 10000)

        url = await page.evaluate("window.location.href")
        while not url.startswith("https://online.citi.com/US/ag/repcard/van2"):
            await page.waitForNavigation({'waitUntil':'load', 'timeout': 0})
            url = await page.evaluate("window.location.href")

        await asyncio.sleep(2)

        if "dashboard" in await page.evaluate("window.location.href"):
            while True:
                try:
                    await page.waitForXPath('//*[@datatarget="#deactivateModal"]', {"timeout": 5000}):
                    await click(page, '//*[@datatarget="#deactivateModal"]', 2222)
                    await click(page, '//*[@class="btn btn-primary"]', 2222)
                    self.deleted += 1
                    print(f"Deleted VCC ({self.deleted})")
                    ctypes.windll.kernel32.SetConsoleTitleW(f"Citi VCC Generator ~ By @dzintt | Deleting VCC's ({self.deleted})")
                    await page.reload({"waitUntil": "load"})
                except:
                    print("No VCC's Available to Delete")
                    await page.close()
                    await self.browser.close()
        else:
            print("No VCC's Available to Delete")

async def click(page, xpath, time):
    page.waitForXPath(xpath, timeout=time)
    result = await page.Jx(xpath)
    await result[0].click()

async def sendKeys(page, xpath, text, time):
    page.waitForXPath(xpath, timeout=time)
    result = await page.Jx(xpath)
    await result[0].type(text)

def save(text):
    f = open("./output.txt", "a")
    f.write(text + "\n")
    f.close()

def getSettings():
    global username, password, chromePath
    settings = json.load(open("./settings.json"))
    username = settings["username"]
    password = settings["password"]
    chromePath = settings["chrome_path"]

def main():
    ctypes.windll.kernel32.SetConsoleTitleW(f"Citi VCC Generator ~ By @dzintt | Progress: N/A")
    mode = int(input("Do you want to create or delete VCC's? (1/2) "))
    getSettings()
    if mode == 1:
        amount = int(input("How many VCC's do you want to create? "))
        CreateVCC(username, password, amount)
        input("Completed. Press ENTER to exit.")
        sys.exit()
    elif mode == 2:
        DeleteVCC(username, password)
        input("Completed. Press ENTER to exit.")
        sys.exit()
    else:
        print("Option does not exist")
        
if __name__ == '__main__':
    main()

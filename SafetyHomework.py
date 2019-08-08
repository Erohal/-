import argparse
import json
import re
from http import cookiejar
from urllib import parse, request

specialID = None
accountArray = None


class AutomaticSpecialGetter:
    def __init__(self):
        pass

    def getSpecial(self):
        workURLList = "https://file.safetree.com.cn/webapi.zhejiang/jt/MyHomeWork.html?grade=11&classroom=532913125&cityid=330600&r=8652551&host=1shaoxing.xueanquan.com"
        workListPattern = "https://huodong.xueanquan.com/.*?html"
        workURLSearch = re.compile(workListPattern)
        workSearcher = workURLSearch.findall(
            request.urlopen(workURLList).read().decode("utf-8"))
        if(workSearcher != None):
            specialURL = workSearcher[0]
        specialPattern = re.compile('<body data-specialId =".*?">')
        specialIDSearcher = specialPattern.search(
            request.urlopen(specialURL).read().decode("utf-8"))
        if (specialIDSearcher != None):
            specialID = specialIDSearcher.group()[23:-2]
        else:
            print(r"Can't get special automaticly,please input the special with -s")
            exit()
        return specialID


class AccountControler:
    def __init__(self, accountFile='account.json'):
        self.m_accountFile = accountFile

    def loadAccount(self):
        accountFile = open(self.m_accountFile)
        accountText = accountFile.read()
        accountJson = json.loads(accountText)
        return accountJson


class HomeWorkDeployer:
    loginURL = "https://zhejianglogin.xueanquan.com/LoginHandler.ashx?jsoncallback=login&userName={}&password={}&checkcode=&type=login&loginType=1"
    signURL = "https://huodongapi.xueanquan.com/p/zhejiang/Topic/topic/platformapi/api/v1/records/sign"
    finishURL = "https://huodongapi.xueanquan.com/p/zhejiang/Topic/topic/platformapi/api/v1/records/finish-status?specialId={}"

    def __init__(self, account, password):
        self.m_account = account
        self.m_password = password

    def login(self):
        self.cookie = cookiejar.CookieJar()
        cookieHandle = request.HTTPCookieProcessor(self.cookie)
        opener = request.build_opener(cookieHandle)
        self.loginMsg = opener.open(HomeWorkDeployer.loginURL.format(
            self.m_account, self.m_password)).read().decode("utf-8")[6:-2]
        self.loginFlag = False
        loginFlagPattern = re.compile(r"ret:\w")
        loginFlagRet = loginFlagPattern.search(self.loginMsg)
        if(loginFlagRet != None and loginFlagRet.group() == "ret:1"):
            self.loginFlag = True
        return self.loginFlag

    def doSign(self, special, step):
        postData = {"specialId": special, "step": step}
        cookieHandle = request.HTTPCookieProcessor(self.cookie)
        opener = request.build_opener(cookieHandle)
        postData = parse.urlencode(postData).encode("utf-8")
        self.signMsg = opener.open(
            HomeWorkDeployer.signURL, postData).read().decode("utf-8")

    def finishStatus(self, special):
        cookieHandle = request.HTTPCookieProcessor(self.cookie)
        opener = request.build_opener(cookieHandle)
        self.finishMsg = opener.open(HomeWorkDeployer.finishURL.format(
            special)).read().decode("utf-8")
        return self.finishMsg

    def getLoginMsg(self):
        return self.loginMsg

    def getSignMsg(self):
        return self.signMsg


class PersonParser:
    def __init__(self, information):
        self.infoMsg = information
        self.namePattern = re.compile(r"TrueName:'.*?'")
        self.schoolNamePattern = re.compile(r"SchoolName:'.*?'")
        self.privincePattern = re.compile(r"PrvName:'.*?'")
        self.cityNamePattern = re.compile(r"CityName:'.*?'")
        self.countryNamePattern = re.compile(r"CountryName:'.*?'")

    def prase(self):
        self.name = self.namePattern.search(self.infoMsg).group()[10:-1]
        self.schoolName = self.schoolNamePattern.search(
            self.infoMsg).group()[12:-1]
        self.privince = self.privincePattern.search(self.infoMsg).group()[9:-1]
        self.cityName = self.cityNamePattern.search(
            self.infoMsg).group()[10:-1]
        self.countryName = self.countryNamePattern.search(self.infoMsg).group()[
            13:-1]

    def getName(self):
        return self.name

    def getSchoolName(self):
        return self.schoolName

    def getPrivince(self):
        return self.privince

    def getCityName(self):
        return self.cityName

    def getCountryName(self):
        return self.countryName


class SignParser:
    def __init__(self, signInfo):
        self.signInfo = signInfo

    def parse(self):
        self.msgJson = json.loads(self.signInfo)

    def getStatus(self):
        return self.msgJson["result"]

    def getMsg(self):
        return self.msgJson["msg"]


def main():
    errorLoginCounter = 0
    errorAccountSet = set()

    accountArray = AccountControler().loadAccount()
    counterForPerson = 1
    for account in accountArray:
        password = accountArray[account]
        person = HomeWorkDeployer(account, password)
        isLogin = person.login()
        if(isLogin):
            personParser = PersonParser(person.getLoginMsg())
            personParser.prase()
            person.doSign(specialID, 1)
            signParserStep1 = SignParser(person.getSignMsg())
            person.doSign(specialID, 2)
            signParserStep2 = SignParser(person.getSignMsg())
            msgT = "[{}]{}{}{}:{} {} {}"
            signParserStep1.parse()
            signParserStep2.parse()
            if(signParserStep1.getStatus() and signParserStep2.getStatus()):
                msgT = msgT.format(
                    counterForPerson,
                    personParser.getPrivince(),
                    personParser.getCityName(),
                    personParser.getSchoolName(),
                    personParser.getName(),
                    "SignSuccess",
                    "SurveySuccess")
                print(msgT)
            else:
                msgT = msgT.format(
                    counterForPerson,
                    personParser.getPrivince(),
                    personParser.getCityName(),
                    personParser.getSchoolName(),
                    personParser.getName(),
                    signParserStep1.getMsg(),
                    signParserStep2.getMsg())
                print(msgT)
        else:
            errorLoginCounter += 1
            errorAccountSet.add(account)
        counterForPerson += 1
    print("--------------------------------------------------")
    if errorLoginCounter > 1:
        counterRows = 1
        for account in errorAccountSet:
            if ((counterRows-1) % 4 == 0):
                print('')
            print("[{}]:{}  ".format(counterRows, account), end='')
            counterRows += 1
        print('')
        print("--------------------------------------------------")
        print("Login failed", errorLoginCounter,
              "times,please check the password above.")
    else:
        print("All accounts have completed,press any key to quit")


if __name__ == "__main__":
    argParer_m = argparse.ArgumentParser()
    argParer_m.add_argument("-s", "--special", type=int,
                            help="Please input the special")
    args = argParer_m.parse_args()
    if (args.special != None):
        specialID = args.special
    else:
        x = input("请输入specialId(留空则自动判断):")
        if(x != ""):
            specialID = x
        else:
            automaticSpecialGetter = AutomaticSpecialGetter()
            specialID = automaticSpecialGetter.getSpecial()
            print("Successfully get the special:", specialID)
    main()
    input()

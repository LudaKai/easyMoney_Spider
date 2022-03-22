from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import time
import pandas as pd
import os


# 添加无头headlesss
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
# browser = webdriver.Chrome(chrome_options=chrome_options)

headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
     'Cookie': 'qgqp_b_id=27b2a8733d0607c3368f4a0d66f2e386; cowCookie=true; st_si=81563261598286; st_pvi=68836185486248; st_sp=2021-12-13 14:09:27; st_inirUrl=https://www.baidu.com/link; st_sn=1; st_psi=20211216233449693-113300300812-3855123952; st_asi=delete; intellpositionL=1215.35px; intellpositionT=455px; arp_scroll_position=0',
    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    'accept-language': "zh-CN,zh;q=0.8",
    'cache-control': "no-cache",
    'cookie': "miid=165455699654368GLfgXOlF-KOKx",
    'upgrade-insecure-requests': "1",
     }

desired_capabilities = DesiredCapabilities.PHANTOMJS.copy()
for key,value in headers.items():
    desired_capabilities['phantomjs.page.customHeaders.{}'.format(key)] = value

browser = webdriver.PhantomJS(desired_capabilities=desired_capabilities) # 会报警高提示，建议chrome添加无头
browser.maximize_window()  # 最大化窗口
wait = WebDriverWait(browser, 10)


def index_page(page):
    try:
        print('正在爬取第： %s 页' % page)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody")))
        # 判断是否是第1页，如果大于1就输入跳转，否则等待加载完成。
        if page > 1:
            # 确定页数输入框
            input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#gotopageindex')))
            input.click()
            input.clear()
            input.send_keys(page)
            submit = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '.gotopage >form>input[class="btn"]')))
            submit.click()
            time.sleep(4)
        # 确认成功跳转到输入框中的指定页
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '.active'), str(page)))
        # x=browser.find_element_by_css_selector(".active").text
        # print("跳转到：",x)
    except Exception:
        print("跳转页面出错")
        return None


def parse_table():
    #提取表格数据
    element = browser.find_element_by_css_selector('tbody')
    # print(element)
    # 提取表格内容td
    td_content = element.find_elements_by_tag_name("td")
    lst = []
    for td in td_content:
        lst.append(td.text)

    # 确定表格列数
    col = len(element.find_elements_by_css_selector('tr:nth-child(1) td'))
    # 通过定位一行td的数量，可获得表格的列数，然后将list拆分为对应列数的子list
    lst = [lst[i:i + col] for i in range(0, len(lst), col)]

    # 原网页中打开"详细"链接，可以查看更详细的数据，这里我们把url提取出来，方便后期查看
    lst_link = []
    links = element.find_elements_by_css_selector('a.red')
    for link in links:
        url = link.get_attribute('href')
        lst_link.append(url)

    lst_link = pd.Series(lst_link)
    # list转为dataframe
    df_table = pd.DataFrame(lst)
    # 添加url列
    df_table['url'] = lst_link

    # print(df_table.head())
    return df_table


# 写入文件
def write_to_file(df_table, category):
    # # 设置文件保存在table文件夹下
    df_table.to_csv('./table/{}.csv' .format(category), mode='a',
                    encoding='utf_8_sig', index=0, header=0)


# 设置表格获取时间、类型
def set_table():
    print('*' * 80)
    print('\t\t\t\t东方财富网报表下载')
    print('--------------')

    # 1 设置财务报表获取时期
    year = int(float(input('请输入要查询的年份(四位数2007-2021)：\n')))
    # int表示取整，里面加float是因为输入的是str，直接int会报错，float则不会
    while (year < 2007 or year > 2021):
        year = int(float(input('年份数值输入错误，请重新输入：\n')))

    quarter = int(float(input('请输入小写数字季度(1:1季报，2-年中报，3：3季报，4-年报)：\n')))
    while (quarter < 1 or quarter > 4):
        quarter = int(float(input('季度数值输入错误，请重新输入：\n')))

    quarter = '{:02d}'.format(quarter * 3)
    # quarter = '%02d' %(int(month)*3)
    date = '{}{}' .format(year, quarter)
    # print(date) 测试日期 ok

    # 2 设置财务报表种类
    tables = int(
        input('请输入查询的报表种类对应的数字(1-业绩报表；2-业绩快报表：3-业绩预告表；4-预约披露时间表；5-资产负债表；6-利润表；7-现金流量表): \n'))

    dict_tables = {1: '业绩报表', 2: '业绩快报表', 3: '业绩预告表',
                   4: '预约披露时间表', 5: '资产负债表', 6: '利润表', 7: '现金流量表'}
    dict = {1: 'yjbb', 2: 'yjkb/13', 3: 'yjyg',
            4: 'yysj', 5: 'zcfz', 6: 'lrb', 7: 'xjll'}
    category = dict[tables]

    # 3 设置url
    url = 'http://data.eastmoney.com/{}/{}/{}.html' .format(
        'bbsj', date, category)

    # # 4 选择爬取页数范围
    start_page = int(input('请输入下载起始页数：\n'))
    nums = input('请输入要下载的页数，（若需下载全部则按回车）：\n')
    print('*' * 80)

    # 确定网页中的最后一页
    browser.get(url)
    # 确定最后一页页数不直接用数字而是采用定位，因为不同时间段的页码会不一样
    try:
        page = browser.find_element_by_css_selector("div[class='pagerbox'] > a:nth-child(7)")  # next节点后面的a节点

    except:
        page = 15
    # else:
    #     print('没有找到该节点')

    end_page = int(page.text)

    if nums.isdigit():
        end_page = start_page + int(nums)
    elif nums == '':
        end_page = end_page
    else:
        print('页数输入错误')

    # 输入准备下载表格类型
    print('准备下载:{}-{}' .format(date, dict_tables[tables]))
    print(url)

    yield{
        'url': url,
        'category': dict_tables[tables],
        'start_page': start_page,
        'end_page': end_page
    }


def main(category, page):
    try:
        index_page(page)
        # parse_table() #测试print
        df_table = parse_table()
        write_to_file(df_table, category)
        print('第 %s 页抓取完成' % page)
        print('--------------')
    except Exception:
        print('网页爬取失败，请检查网页中表格内容是否存在')

# 单进程
if __name__ == '__main__':

    for i in set_table():
        category = i.get('category')
        start_page = i.get('start_page')
        end_page = i.get('end_page')

    for page in range(start_page, end_page):
        # for page in range(44,pageall+1): # 如果下载中断，可以尝试手动更改网页继续下载
        main(category, page)
    print('全部抓取完成')

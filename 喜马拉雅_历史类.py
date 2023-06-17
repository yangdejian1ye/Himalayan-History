from concurrent.futures import ThreadPoolExecutor
import requests
from lxml import etree
import numpy as np
import pandas as pd
import time
#提取历史类下的数据，如二级页面url
def History(page):
    url = "https://www.ximalaya.com/revision/category/v2/albums?pageNum={}&pageSize=100&sort=1&categoryId=9".format(str(page))
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    # print(data["data"]["albums"])
    return data["data"]["albums"]

#对二级页面数据进行提取
def Secondary_page(Secondary_url):
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }
    response = requests.get(Secondary_url, headers=headers)
    response.encoding = "utf-8"
    html1 = etree.HTML(response.text)
    # 听过次数
    number_times = html1.xpath('//*[@id="award"]/main/div[1]/div[2]/div[1]/div[1]/div[2]/div[2]/div[2]/span/text()')[-1]
    #声音集数
    Episodes = html1.xpath('//*[@id="anchor_sound_list"]/div[1]/a/span/text()')[1]
    #评论数量
    try:
        Number_comments = html1.xpath('//*[@id="anchor_sound_list"]/div[1]/span/span/text()')[1]
    except:
        Number_comments = 0
    # 详细简介
    Detailed_Introduction = html1.xpath('//*[@id="award"]/main/div[1]/div[2]/div[1]/div[1]/div[3]/article//text()')
    Detailed_Introduction = ' '.join(Detailed_Introduction)
    # print(url,Detailed_Introduction)
    return [number_times,Episodes,Number_comments,Detailed_Introduction]

if __name__ == '__main__':
    data_list = []
    start = round(time.time())
    #获取一级页面数据，利用线程池对数据进行爬取
    with ThreadPoolExecutor(5) as p:
        for page in range(1,31):    #经简单检验，能查看历史类下的3000条数据
            future1 = p.submit(History,page)
            res_data = future1.result()
            # print(res_data)
            for res in res_data:
                #获取 作者名称,标题,ID,简介
                try:
                    res_list = [res["albumUserNickName"],res["albumTitle"],res["albumId"],res["intro"]]
                except:
                    res_list = [res["albumUserNickName"], res["albumTitle"], res["albumId"], ""]
                #二级页面url
                Secondary_url = "https://www.ximalaya.com"+res["albumUrl"]
                res_list.append(Secondary_url)
                #图片链接
                picture_url = "https://imagev2.xmcdn.com/"+ res["albumCoverPath"]
                res_list.append(picture_url)

                data_list.append(res_list)
    #爬取二级页面数据
    with ThreadPoolExecutor(15) as p:
        for i in range(len(data_list)):
            future2 = p.submit(Secondary_page, data_list[i][-2])
            Secondary_data = future2.result()
            # print(Secondary_data)
            for sec_data in Secondary_data:
                data_list[i].append(sec_data)

    title = ["作者名称", "标题", "ID", "简介", "二级页面url", "图片链接", "听过次数", "声音集数", "评论数量", "详细简介"]
    # 将数据处理后存入 excel 表格
    data_list = np.array(data_list).transpose()
    dict2 = {}
    for i in range(len(data_list)):
        dict2[title[i]] = data_list[i]
    data = pd.DataFrame(dict2)
    data.to_excel('喜马拉雅_历史类_数据.xlsx', index=False)
    # print(data_list)
    end = round(time.time())
    # 计算爬取耗费的时间
    print("爬取时间:",(end-start)/60,"分")
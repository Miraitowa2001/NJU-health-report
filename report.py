from njupass import NjuUiaAuth
import json
import time
import datetime
from pytz import timezone
from urllib.parse import urlencode

URL_JKDK_LIST = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do'
URL_JKDK_APPLY = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do'
URL_JDKD_INDEX = 'http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.html'


def get_zjhs_time(method='YESTERDAY'):
    """获取最近核酸时间"""
    today = datetime.datetime.now(timezone('Asia/Shanghai'))
    yesterday = today + datetime.timedelta(-1)
    if method == 'YESTERDAY':
        return yesterday.strftime("%Y-%m-%d %-H")


def apply(curr_location, logger, auth: NjuUiaAuth, covidTestMethod='YESTERDAY', force=False):
    """
    完成一次健康打卡
    :param `covidTestMethod`: 最近核酸时间的方案
    :param `force`: 是否在今日已经打卡的前提下强制打卡
    """
    for _ in range(10):
        logger.info('尝试获取打卡列表信息...')
        r = auth.session.get(URL_JKDK_LIST)
        if r.status_code != 200:
            logger.error('获取失败，一分钟后再次尝试...')
            time.sleep(60)
            continue

        dk_info = json.loads(r.text)['data'][0]

        has_applied = dk_info['TBZT'] == "1"
        wid = dk_info['WID']
        param = {
            'WID': wid,
            'IS_TWZC': 1,  # 是否体温正常
            'CURR_LOCATION': curr_location,  # 位置
            'ZJHSJCSJ': get_zjhs_time(covidTestMethod),  # 最近核酸检测时间
            'JRSKMYS': 1,  # 今日苏康码颜色
            'IS_HAS_JKQK': 1,  # 健康情况
            'JZRJRSKMYS': 1,  # 居住人今日苏康码颜色
            'SFZJLN': 1
        }
        headers = {
            'referer': URL_JDKD_INDEX,  # required since 2022/4/20
            "X-Requested-With": "com.wisedu.cpdaily.nju",
        }
        url = URL_JKDK_APPLY + '?' + urlencode(param)

        if not has_applied or force:
            logger.info('正在打卡')
            auth.session.get(url, headers=headers)

            force = False
            time.sleep(1)

        else:
            logger.info('今日已打卡！')
            return True

    logger.error("打卡失败，请尝试手动打卡")
    return False

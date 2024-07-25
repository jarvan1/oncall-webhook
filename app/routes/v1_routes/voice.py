import hashlib

from fastapi import APIRouter, HTTPException, Request
import base64
import requests
import time
import uuid
import hmac
from pydantic import BaseModel
import logging
# from typing import List, Optional
from .ldap_info import LDAPClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
endpoint_name = "huawei_voice"

base_url = 'https://rtccall.cn-north-1.myhuaweicloud.cn:443'  # APP接入地址,购买服务时下发,请替换为实际值
appKey = 'app key'  # 语音通知应用的appKey,购买服务时下发,请替换为实际值
appSecret = 'app secret'  # 语音通知应用的appSecret,购买服务时下发,请替换为实际值


class VoiceNotificationRequest(BaseModel):
    userID: str
    eventID: str


def buildAKSKHeader(appKey, appSecret):
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ')  # Created
    nonce = str(uuid.uuid4()).replace('-', '')  # Nonce
    # digist = hmac.new(appSecret.encode(), (nonce + now).encode(), digestmod=sha256).digest()
    digist = hmac.new(appSecret.encode(), (nonce + now).encode(), hashlib.sha256).digest()
    digestBase64 = base64.b64encode(digist).decode()  # PasswordDigest
    return 'UsernameToken Username="{}",PasswordDigest="{}",Nonce="{}",Created="{}"'.format(appKey, digestBase64, nonce,
                                                                                            now)


def voiceNotifyAPI(displayNbr, calleeNbr, playInfoList):
    if len(displayNbr) < 1 or len(calleeNbr) < 1 or playInfoList is None:
        return

    apiUri = '/rest/httpsessions/callnotify/v2.0'  # v1.0 or v2.0
    requestUrl = base_url + apiUri

    header = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Authorization': 'AKSK realm="SDP",profile="UsernameToken",type="Appkey"',
        'X-AKSK': buildAKSKHeader(appKey, appSecret)
    }

    jsonData = {
        # 必填参数
        'displayNbr': displayNbr,  # 主叫用户手机终端的来电显示号码。
        'calleeNbr': calleeNbr,  # 发起呼叫时所拨打的被叫号码。
        'playInfoList': playInfoList  # 播放信息列表，最大支持5个，每个播放信息携带的参数都可以不相同。
        # 选填参数
        #         'statusUrl': '', #设置SP接收状态上报的URL,要求使用BASE64编码
        #         'feeUrl': '', #设置SP接收话单上报的URL,要求使用BASE64编码
        #         'returnIdlePort': 'false', #指示是否需要返回平台空闲呼叫端口数量
        #         'userData': 'customerId123' #设置用户的附属信息
    }

    try:
        r = requests.post(requestUrl, json=jsonData, headers=header, verify=False)
        return r.text
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=e.read().decode('utf-8'))


def getPlayInfoList(templateId, templateParas):
    playInfoList = [{
        'templateId': templateId,
        'templateParas': templateParas
        #         'collectInd': 0, #是否进行收号
        #         'replayAfterCollection': 'false', #设置是否在收号后重新播放notifyVoice或templateId指定的放音
        #         'collectContentTriggerReplaying': '1' #设置触发重新放音的收号内容
    }]
    return playInfoList


@router.post("/webhook/voice")
async def webhookVoice(request: Request):
    ldap_client = LDAPClient("ldaps://ldap.example:636", "cn=admin,dc=ldap,dc=example,dc=com",
                             "example.com") # replace your ldap info

    request_data = await request.json()
    logger.info(f"Received request with data: {request_data}")

    alertname = request_data['alert_payload']['alerts'][0]['labels']['alertname']
    usernames = [user['username'] for user in request_data['users_to_be_notified']]
    results = []

    for username in usernames:
        user_info = ldap_client.search_user(username)
        if user_info:
            user_mobile_list = user_info.get("attributes").get("mobile")
            # print(user_mobile_list)
            user_mobile = user_mobile_list[0].decode('utf-8').replace('-', '').strip()
            print(user_mobile)

            displayNbr = "+86123456789"    # voice call number
            playInfoList = getPlayInfoList('voice call template ID', [time.strftime('%H:%M'), alertname])   # replace your template ID
            result = voiceNotifyAPI(displayNbr, user_mobile, playInfoList)
            logger.info(f"[{time.strftime('%H:%M')}] firing: {alertname}, notify: {username}, mobile: {user_mobile}")
            results.append(result)
        else:
            raise HTTPException(status_code=404, detail="User not found")
    if results:
        return {"status": "success", "data": results}
    else:
        raise HTTPException(status_code=500, detail="No notifications were sent")

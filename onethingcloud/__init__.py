import json
import requests
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import urllib3

from . import config, utils

urllib3.disable_warnings()


class OneThingCloudClient:
    __request_handler = requests.session()

    __method_post = 'POST'
    __method_get = 'GET'

    __username = ''
    __password = ''
    __user_info = {}
    __device = False
    __turn_server_1 = False
    __turn_server_2 = False

    __task_info = {'recycleNum': '0', 'serverFailNum': '0', 'sync': '0', 'tasks': [], 'dlNum': '0', 'completeNum': '0'}

    __scheduler = BackgroundScheduler()

    def __init__(self, username, password):
        # self.__request_handler.headers = {
        #     'User-Agent': "Mozilla/5.0",
        #     "cache-control": "no-cache"
        # }
        self.__request_handler.verify = False

        # 初始化
        self.__init()
        logging.info('OneThingCloud client init begin.')

        # 登陆
        self.__username = username
        self.__password = password
        self.__login(username, password)
        logging.info('OneThingCloud account login ok.')

        # 启动定时器 检查session
        self.__scheduler.add_job(self.__check_session, 'interval', seconds=10, id='JOB_CHECK_SESSION')

        # 获取peer信息
        self.__init_peer_info()
        logging.info('OneThingCloud get device info ok.')

        # 启动定时器 获取peer信息
        self.__scheduler.add_job(self.__init_peer_info, 'interval', seconds=60, id='JOB_INIT_PEER_INFO')

        # 获取turn server信息
        self.__init_turn_server_info()
        logging.info('OneThingCloud get turn server info ok.')

        # 启动定时器 获取任务列信息
        self.__scheduler.add_job(self.__init_task_info, 'interval', seconds=10, id='JOB_INIT_TASK_LIST')

        # 启动定时器
        self.__scheduler.start()
        logging.info('OneThingCloud client init ok.')

    def close(self):
        # 销毁
        self.__scheduler.shutdown(wait=False)
        logging.info('OneThingCloud client close ok.')

    def __send_json(self, url, json_data=''):
        """
        发送json数据
        :param url:
        :param json_data:
        :return:
        """
        self.__request_handler.headers = {
            'User-Agent': "Mozilla/5.0",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=utf-8"
        }
        result = self.__request_handler.post(url, json_data)
        if result.status_code == 200:
            return result.json()
        else:
            raise Exception('ERR:%s,MSG:%s' % (result.status_code, 'request send failed.'))

    def __send(self, url, method, params=''):
        """
        发送请求
        :param url:
        :param method:
        :param params:
        :return:
        """
        self.__request_handler.headers = {
            'User-Agent': "Mozilla/5.0",
            "cache-control": "no-cache"
        }
        if self.__method_get == method:
            result = self.__request_handler.get(url)
        else:
            result = self.__request_handler.post(url, params)
        if result.status_code == 200:
            return result.json()
        else:
            raise Exception('ERR:%s,MSG:%s' % (result.status_code, 'request send failed.'))

    def __init(self):
        """
        初始化
        :return:
        """
        params = [{"act": config.ACT, "app_version": config.APP_VERSION, "os_version": config.OS_VERSION,
                   "peerid": config.PEER_ID, "tabid": config.TAB_ID, "time": str(int(time.time()))}]
        str_params = json.dumps(params)
        res = self.__send(config.URL_INIT, self.__method_post, str_params)
        logging.debug('init\nparams:%s\nresult:%s' % (params, res))
        if res['code'] == 0:
            logging.info('onethingcloud client init ok.')
        else:
            raise Exception('ERR:%s,MSG:%s' % ('1', 'client init failed.'))

    def __login(self, username, password):
        """
        登陆
        :param username:
        :param password:
        :return:
        """
        pwd = utils.get_pwd(password)
        params = utils.get_body(account_type=config.ACCOUNT_TYPE, peerid=config.PEER_ID, phone=username,
                                phone_area=config.PHONE_AREA, product_id=config.PRODUCT_ID, pwd=pwd)
        res = self.__send(config.URL_LOGIN, self.__method_post, params)
        logging.debug('login\nparams:%s\nresult:%s' % (params, res))
        i_ret = res['iRet']
        if i_ret == 0:
            self.__user_info = res['data']
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['iRet'], res['sMsg']))

    def __check_session(self):
        """
        检查session
        :return:
        """
        params = utils.get_body(peerid=config.PEER_ID, product_id=config.PRODUCT_ID,
                                protocol_version=config.PROTOCOL_VERSION, sessionid=self.__user_info['sessionid'],
                                userid=self.__user_info['userid'])
        res = self.__send(config.URL_CHECK_SESSION, self.__method_post, params)
        logging.debug('check_session\nparams:%s\nresult:%s' % (params, res))
        i_ret = res['iRet']
        if i_ret != 0:
            # 如果检查失败重新登陆下
            self.__login(self.__username, self.__password)

    def __init_peer_info(self):
        """
        获取设备信息
        :return:
        """
        params = utils.get_params(dict(appversion=config.APP_VERSION, ct='5', v='8'), self.__user_info['sessionid'],
                                  True)
        res = self.__send(config.URL_LIST_PEER + params, self.__method_get)
        logging.debug('init_peer_info\nparams:%s\nresult:%s' % (params, res))
        rtn = res['rtn']
        if rtn == 0:
            devices = res['result'][1]['devices']
            device_size = len(devices)
            if device_size > 0:
                self.__device = devices[0]
        else:
            raise Exception('ERR:%s,MSG:%s' % (rtn, res['msg']))

    def __init_turn_server_info(self):
        """
        获取内网穿透地址
        :return:
        """
        if not self.__device:
            logging.error("device info not init or device offline.")
            return None

        device_sn = self.__device['device_sn']
        params = utils.get_params(dict(appversion=config.APP_VERSION, ct='5', sn=device_sn, v='3'),
                                  self.__user_info['sessionid'],
                                  True)
        res = self.__send(config.URL_GET_TURN_SERVER + params, self.__method_get)
        logging.debug('init_turn_server_info1\nparams:%s\nresult:%s' % (params, res))
        rtn = res['rtn']
        if rtn == 0:
            self.__turn_server_1 = res['turn_server_addr']
        else:
            raise Exception('ERR:%s,MSG:%s' % (rtn, res['msg']))

        res2 = self.__send(config.URL_GET_TURN_SERVER + params, self.__method_get)
        logging.debug('init_turn_server_info2\nparams:%s\nresult:%s' % (params, res))
        rtn2 = res2['rtn']
        if rtn2 == 0:
            self.__turn_server_2 = res2['turn_server_addr']
        else:
            raise Exception('ERR:%s,MSG:%s' % (rtn2, res2['msg']))

    def __init_task_info(self):
        """
        初始化任务信息
        :return:
        """
        pid = self.__device['peerid']
        params = utils.get_params_no_sign(dict(v='2', pid=pid, ct='31', ct_ver=config.APP_VERSION, pos='0',
                                               number='0', type='4', needUrl='0'))
        res = self.__send(config.URL_CONTROL_REMOTE_LIST + params, self.__method_get)
        logging.debug('init_task_info\nparams:%s\nresult:%s' % (params, res))
        rtn = res['rtn']
        if rtn == 0:
            self.__task_info['recycleNum'] = res['recycleNum']
            self.__task_info['serverFailNum'] = res['serverFailNum']
            self.__task_info['sync'] = res['sync']
            self.__task_info['dlNum'] = res['dlNum']
            self.__task_info['completeNum'] = res['completeNum']
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['rtn'], res['msg']))

    def get_user_info(self):
        """
        获取登陆用户信息
        :return:
        """
        return self.__user_info

    def get_device_info(self):
        """
        获取设备信息
        :return:
        """
        return self.__device

    def get_turn_server_info(self):
        """
        获取内网穿透服务信息
        :return:
        """
        return self.__turn_server_1, self.__turn_server_2

    def get_task_info(self):
        """
        获取任务信息
        :return:
        """
        return self.__task_info

    def get_cloud_task_list(self):
        """
        获取云添加任务列表
        :return:
        """
        pid = self.__device['peerid']
        params = utils.get_body(v='2', pid=pid, ct='31', ct_ver=config.APP_VERSION, pos='0',
                                number='0', type='4', needUrl='100')
        res = self.__send(config.URL_CONTROL_REMOTE_LIST, self.__method_post, params)
        logging.debug('get_cloud_task_list\nparams:%s\nresult:%s' % (params, res))
        rtn = res['rtn']
        if rtn == 0:
            self.__task_info['tasks'] = res['tasks']
            return self.__task_info
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['rtn'], res['msg']))

    def del_cloud_task(self, task_id, task_state, task_type, delete_file=False, recycle_task=False):
        """
        删除任务
        :param task_id:
        :param task_state:
        :param task_type:
        :param delete_file:
        :param recycle_task:
        :return:
        """
        pid = self.__device['peerid']
        tasks = task_id + '_' + task_state + '_' + task_type

        params = utils.get_params_no_sign(
            dict(pid=pid, ct='31', clientType='PC-onethingcloud', ct_ver=config.APP_VERSION, v='1',
                 tasks=tasks, deleteFile=str(delete_file).lower(), recycleTask=str(recycle_task).lower()))
        res = self.__send(config.URL_CONTROL_REMOTE_DEL + params, self.__method_get)
        logging.debug('del_cloud_task\nparams:%s\nresult:%s' % (params, res))
        rtn = res['rtn']
        if rtn == 0:
            self.__task_info['tasks'] = []
            return self.__task_info
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['rtn'], res['msg']))

    def url_resolve(self, url):
        """
        磁力链接解析
        :param url:
        :return:
        """
        pid = self.__device['peerid']
        url_params = 'v=2&pid=' + pid + '&ct=31&ct_ver=' + config.APP_VERSION
        json_params = json.dumps({'url': url})
        res = self.__send_json(config.URL_CONTROL_REMOTE_URL_RESOLVE + url_params, json_params)
        logging.debug('url_resolve\nparams:%s\nresult:%s' % (json_params, res))
        rtn = res['rtn']
        if rtn == 0:
            if res['taskInfo']['name'] == '' or res['taskInfo']['size'] == '0':
                raise Exception('ERR:-1,MSG:url resolve failed,please try again.')
            return res['taskInfo']
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['rtn'], res['msg']))

    def create_batch_task(self, url, file_size, name, task_type, bt_sub=None):
        """
        创建下载任务
        :param url:
        :param file_size:
        :param name:
        :param task_type:
        :param bt_sub:
        :return:
        """
        if bt_sub is None:
            bt_sub = []
        pid = self.__device['peerid']
        url_params = 'v=2&pid=' + pid + '&ct=31&ct_ver=' + config.APP_VERSION
        json_params = json.dumps({
            'path': '/media/sda/onethingcloud/tddownload',
            'tasks': [{
                'btSub': bt_sub,
                'cid': '',
                'filesize': file_size,
                'gcid': '',
                'localfile': '',
                'name': name,
                'ref_url': '',
                'type': task_type,
                'url': url
            }]
        })
        res = self.__send_json(config.URL_CONTROL_REMOTE_CREATE_BATCH_TASK + url_params, json_params)
        logging.debug('create_batch_task\nparams:%s\nresult:%s' % (json_params, res))
        rtn = res['rtn']
        if rtn == 0:
            return res['tasks']
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['rtn'], res['msg']))

    def pause_task(self, task_id, task_state, task_type):
        """
        暂停任务
        :param task_id:
        :param task_state:
        :param task_type:
        :return:
        """
        pid = self.__device['peerid']
        tasks = task_id + '_' + task_state + '_' + task_type

        params = utils.get_params_no_sign(
            dict(pid=pid, ct='31', clientType='PC-onecloud', ct_ver=config.APP_VERSION, v='1', tasks=tasks))
        res = self.__send(config.URL_CONTROL_REMOTE_PAUSE + params, self.__method_get)
        logging.debug('del_cloud_task\nparams:%s\nresult:%s' % (params, res))
        rtn = res['rtn']
        if rtn == 0:
            return True
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['rtn'], res['msg']))

    def start_task(self, task_id, task_state, task_type):
        """
        开始任务
        :param task_id:
        :param task_state:
        :param task_type:
        :return:
        """
        pid = self.__device['peerid']
        tasks = task_id + '_' + task_state + '_' + task_type

        params = utils.get_params_no_sign(
            dict(pid=pid, ct='31', clientType='PC-onecloud', ct_ver=config.APP_VERSION, v='1', tasks=tasks))
        res = self.__send(config.URL_CONTROL_REMOTE_START + params, self.__method_get)
        logging.debug('del_cloud_task\nparams:%s\nresult:%s' % (params, res))
        rtn = res['rtn']
        if rtn == 0:
            return True
        else:
            raise Exception('ERR:%s,MSG:%s' % (res['rtn'], res['msg']))

    def create_download_task(self, url):
        """
        创建下载任务(内部解析地址并创建下载任务)
        :param url:
        :return:
        """
        task_info = self.url_resolve(url)
        task_url = task_info['url']
        # 1 普通下载文件 ftp http 电驴 2 磁力链接 bt 迅雷链接
        task_type = task_info['type']
        task_name = task_info['name']
        task_file_size = task_info['size']
        bt_sub = []
        if task_type == 2:
            for sub in task_info['subList']:
                bt_sub.append(sub['id'])
        return self.create_batch_task(task_url, task_file_size, task_name, task_type, bt_sub)

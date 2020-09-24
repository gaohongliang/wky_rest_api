APP_VERSION = '1.4.5.112'
PEER_ID = 'A6B186B2630BDAE0641F78858136A65D'
ACT = 'tab_show'
OS_VERSION = 'Windows 10'
TAB_ID = 'all'

ACCOUNT_TYPE = '4'
PHONE_AREA = '86'
PRODUCT_ID = '0'
PROTOCOL_VERSION = '1'

# 系统初始化调用
URL_INIT = 'http://xyajs.data.p2cdn.com/o_onecloud_pc_cycle'
URL_ACCOUNT_BASE = 'http://account.onethingpcs.com'
URL_LOGIN = '%s/user/login?appversion=%s' % (URL_ACCOUNT_BASE, APP_VERSION)
URL_CHECK_SESSION = '%s/user/check-session?appversion=%s' % (URL_ACCOUNT_BASE, APP_VERSION)

URL_CONTROL_BASE = 'https://control.onethingpcs.com'
URL_LIST_PEER = '%s/listPeer?' % URL_CONTROL_BASE
URL_GET_TURN_SERVER = '%s/getturnserver?' % URL_CONTROL_BASE

URL_CONTROL_REMOTE_BASE = 'https://control-remotedl.onethingpcs.com'
URL_CONTROL_REMOTE_LIST = '%s/list?' % URL_CONTROL_REMOTE_BASE
URL_CONTROL_REMOTE_DEL = '%s/del?' % URL_CONTROL_REMOTE_BASE
URL_CONTROL_REMOTE_URL_RESOLVE = '%s/urlResolve?' % URL_CONTROL_REMOTE_BASE
URL_CONTROL_REMOTE_CREATE_BATCH_TASK = '%s/createBatchTask?' % URL_CONTROL_REMOTE_BASE

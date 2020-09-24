import hashlib


def md5(s):
    """
    字符串转md5
    :param s:
    :return:
    """
    return hashlib.md5(s.encode('utf-8')).hexdigest().lower()


def get_pwd(password):
    """
    获取pwd值（密码MD5后加密再取MD5值）
    :param password:
    :return:
    """
    s = md5(password)
    s = s[0:2] + s[8] + s[3:8] + s[2] + s[9:17] + s[27] + s[18:27] + s[17] + s[28:]
    return md5(s)


def get_sign(body, key=''):
    """
    获取sign值
    :param body:
    :param key:
    :return:
    """
    m = []
    while len(body) != 0:
        v = body.popitem()
        m.append(v[0] + '=' + v[1])
    m.sort()
    t = 0
    s = ''
    while t != len(m):
        s = s + m[t] + '&'
        t = t + 1
    sign_input = s + 'key=' + key
    sign = md5(sign_input)
    return sign


def get_body(**kwargs):
    result = {}
    sign_key = ''
    for key in kwargs.keys():
        if key == 'sessionid':
            sign_key = kwargs[key]
        result[key] = kwargs[key]
    sign = get_sign(result, sign_key)
    for key in kwargs.keys():
        result[key] = kwargs[key]
    result['sign'] = sign
    return result


def get_params(data, session_id, is_get=False):
    temp = []
    result = {}
    for key in data.keys():
        if key == "pwd":
            temp.append(key + "=" + get_pwd(data["pwd"]))
            result[key] = get_pwd(data[key])
        else:
            temp.append(key + "=" + data[key])
            result[key] = data[key]
    sign = get_sign(result, session_id)
    g_str = '&'.join(temp)
    if g_str:
        g_str += "&"
    key = "key=" + session_id
    e_str = g_str + key + "&"

    return e_str + "sign=" + sign if not is_get else g_str + "sign=" + sign


def get_params_no_sign(data):
    temp = []
    result = {}
    for key in data.keys():
        temp.append(key + "=" + data[key])
        result[key] = data[key]
    return '&'.join(temp)

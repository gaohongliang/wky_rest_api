from flask import Flask, request, jsonify, make_response
from config import const
import onethingcloud

app = Flask(__name__)
client = onethingcloud.Client(const.OTC_USERNAME, const.OTC_PASSWORD)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'code': '404', 'msg': 'api not found'}), 404)


@app.errorhandler(500)
def server_err(error):
    return make_response(jsonify({'code': '500', 'msg': 'system error,%s' % error.original_exception.args[0]}), 500)


def resp(data=None):
    return jsonify({'code': '0', 'msg': 'success', 'data': data})


@app.route('/')
def index():
    return jsonify({'code': '0000', 'msg': 'OneThingCloud API'})


@app.route('/userInfo', methods=['GET'])
def get_user_info():
    return resp(client.get_user_info())


@app.route('/deviceInfo', methods=['GET'])
def get_device_info():
    return resp(client.get_device_info())


@app.route('/taskInfo', methods=['GET'])
def get_task_info():
    return resp(client.get_task_info())


@app.route('/taskList', methods=['GET'])
def get_task_list():
    return resp(client.get_cloud_task_list())


@app.route('/urlResolve', methods=['POST'])
def url_resolve():
    url = request.form.get('url')
    return resp(client.url_resolve(url))


@app.route('/taskCreate', methods=['POST'])
def create_task():
    url = request.form.get('url')
    client.create_download_task(url)
    return resp()


@app.route('/taskDel', methods=['POST'])
def del_task():
    task_id = request.form.get('id')
    task_state = request.form.get('state')
    task_type = request.form.get('type')
    delete_file = True if request.form.get('delete_file') == '1' else False
    client.del_cloud_task(task_id, task_state, task_type, delete_file, False)
    return resp()


@app.route('/taskStart', methods=['POST'])
def start_task():
    task_id = request.form.get('id')
    task_state = request.form.get('state')
    task_type = request.form.get('type')
    client.start_task(task_id, task_state, task_type)
    return resp()


@app.route('/taskPause', methods=['POST'])
def pause_task():
    task_id = request.form.get('id')
    task_state = request.form.get('state')
    task_type = request.form.get('type')
    client.pause_task(task_id, task_state, task_type)
    return resp()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=const.GLOBAL_PORT, debug=False)
    client.close()

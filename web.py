from flask import Flask, url_for, render_template, request, redirect, send_from_directory, make_response, jsonify, Response
from rasa_core.agent import Agent
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_core.utils import EndpointConfig
from rasa_core.trackers import DialogueStateTracker, EventVerbosity
from rasa_core.channels import CollectingOutputChannel

app = Flask(__name__)
app.jinja_env.auto_reload = True
interpreter = RasaNLUInterpreter(r'C:/Users/YCKJ1509/Desktop/sx_demo/models/current/nlu')
action_endpoint = EndpointConfig(url="http://localhost:5055/webhook")
agent = Agent.load(r'C:/Users/YCKJ1509/Desktop/sx_demo/models/dialogue', interpreter=interpreter, action_endpoint=action_endpoint)
dialogue_hist = {}


@app.route('/', methods=['GET', 'POST'])
def parse():
    # test_html = os.path.join(app.config['HTML_FOLDER'], 'train.html')
    if request.method == 'POST':
        user_id = ''
        if 'user_id' in request.form.keys():
            print(request.form)
            user_id = request.form['user_id']
        if len(user_id) < 1:
            return render_template('homepage.html')
        # return render_template('table_example.html', output_message=[], user_id=user_id)
        '''
        if 'form_name' in request.form.keys():
            if request.form['form_name'] == 'form_dev':
                return redirect(url_for('conversation_dev', user_id=user_id))
        '''

        return redirect(url_for('conversation', user_id=user_id))
    if request.method == 'GET':
        return render_template('homepage.html')


@app.route('/conversations/<user_id>', methods=['GET', 'POST'])
def conversation(user_id):
    # test_html = os.path.join(app.config['HTML_FOLDER'], 'train.html')
    if request.method == 'POST':
        output_message = ''
        #print("{}: {}".format('request form', request.form))
        if 'restart_dialogue'in request.form.keys():
            # print("{}: {}".format('restart', request.form))
            dialogue_hist[user_id] = ['Bot: 您好，欢迎使用快乐肥宅点餐系统！']
            output_message = dialogue_hist[user_id]
            out = CollectingOutputChannel()
            # print(output_message)
            #agent.execute_action(user_id, 'action_restart', out, 'Keras Policy', 1.0)
            if user_id in agent.tracker_store.store.keys():
                agent.tracker_store.store.pop(user_id)
        elif 'input_message' in request.form.keys():
            #print("{}: {}".format('input_message', request.form))
            input_message = request.form['input_message']
            #print("{}: {}".format(input_message, type(input_message)))
            response_message = agent.handle_text(input_message, sender_id=user_id)
            if user_id not in dialogue_hist.keys():
                dialogue_hist[user_id] = []
            dialogue_hist[user_id].append('You: ' + input_message)
            for i in range(len(response_message)):
                if i == 0:
                    dialogue_hist[user_id].append('Bot: ' + response_message[i]['text'])
                else:
                    dialogue_hist[user_id].append('     ' + response_message[i]['text'])
            #print(response_message)
            output_message = dialogue_hist[user_id]
        else:
            # 对应于未开发完的post请求
            if user_id not in dialogue_hist.keys():
                dialogue_hist[user_id] = []
                dialogue_hist[user_id].append('Bot: 您好，欢迎使用快乐肥宅点餐系统！')
            output_message = dialogue_hist[user_id]
        return render_template('conversation.html', output_message=output_message, user_id=user_id)
    if request.method == 'GET':
        # print(request.form)
        if user_id not in dialogue_hist.keys():
            dialogue_hist[user_id] = []
            dialogue_hist[user_id].append('Bot: 您好，欢迎使用快乐肥宅点餐系统！')
        output_message = dialogue_hist[user_id]
        return render_template('conversation.html', output_message=output_message, user_id=user_id)


if __name__ == '__main__':
    # app.run(host='127.0.0.1', port=9250, threaded=True, debug=True)
    app.run(host='0.0.0.0', port=9360, threaded=True, debug=True)

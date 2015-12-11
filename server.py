import json
from flask import Flask, request, send_file

import ascribe


app = Flask(__name__)


def render_and_send_certificate(data):
    pdf_file = ascribe.render_certificate(data)
    response = send_file(pdf_file,
                         attachment_filename='certificate.pdf',
                         mimetype='application/pdf')
    response.headers.add('content-length', str(pdf_file.getbuffer().nbytes))
    return response


@app.route('/', methods=['POST'])
def certificate():
    print(request)
    print(request.form)
    json_data = request.form['data']
    data = json.loads(json_data)
    print(data)
    try:
        return render_and_send_certificate(data)
    except Exception as e:
        print(e)
        pass


@app.route('/', methods=['GET'])
def test():
    try:
        return render_and_send_certificate(ascribe.data_test)
    except Exception as e:
        print('Error: ' + str(e))
        pass


if __name__ == "__main__":
    # render_certificate(data_test, to_file=True)
    app.run(debug=True)

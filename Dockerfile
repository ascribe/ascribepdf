FROM python:3.5

RUN apt-get update && apt-get -y install vim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements /usr/src/app/requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/dev.txt

COPY . /usr/src/app/

EXPOSE 5000

CMD ['python', 'ascribe.py']

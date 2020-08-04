FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# get git, clone freesound-python client and install
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git
RUN git clone https://github.com/MTG/freesound-python.git ./freesound-python
WORKDIR /usr/src/app/freesound-python
RUN python ./setup.py install

WORKDIR /usr/src/app

ENV FREESOUND_API_KEY=MnelmAPvmNPZimzberjC1szm84N14Oz2NqXu1WDj FLASK_ENV=production

COPY . .

EXPOSE 8080

CMD [ "python", "app.py"]
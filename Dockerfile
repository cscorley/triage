FROM python:2.7 

RUN apt-get update -y && apt-get install -y libatlas-base-dev gfortran cython 
ADD . /app
RUN pip install -r /app/requirements.txt
RUN pip install --editable /app

WORKDIR /app

CMD cdi -vv --model lda --experiment feature_location --source release --name bookkeeper --version v4.3.0 --optimize
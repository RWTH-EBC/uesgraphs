FROM python:3

WORKDIR /home/docker/python/uesgraphs

# By copying over requirements first, we make sure that Docker will cache
# our installed requirements rather than reinstall them on every build
COPY requirements.txt /home/docker/python/uesgraphs/requirements.txt
RUN pip install -r requirements.txt

# Now copy in our code, and run it
WORKDIR /home/docker/python/uesgraphs
COPY . /home/docker/python/uesgraphs

RUN pip install -e .



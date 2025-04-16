FROM apache/airflow:2.10.5
#ADD requirements.txt .
#RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt

# Start from the official Apache Airflow image
#FROM apache/airflow:2.10.5-python3.11

# Copy your requirements.txt into the image
COPY requirements.txt /

# Install the Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt

FROM apache/spark:3.5.0

USER root

COPY wheels/ /tmp/wheels/
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels \
    numpy pandas scipy && \
    rm -rf /tmp/wheels

COPY *.jar /opt/spark/jars/
RUN chmod 644 /opt/spark/jars/*.jar

USER 185
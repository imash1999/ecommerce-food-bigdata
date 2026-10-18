FROM flink:1.17-java11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY lib/*.jar /opt/flink/lib/
COPY postgresql-42.6.0.jar /opt/flink/lib/postgresql-42.6.0.jar
COPY submit.sql /opt/flink/submit.sql
COPY submit-and-watch.sh /opt/flink/submit-and-watch.sh
RUN chmod +x /opt/flink/submit-and-watch.sh

CMD ["/opt/flink/submit-and-watch.sh"]

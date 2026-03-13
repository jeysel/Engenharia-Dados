FROM python:3.12-slim

RUN pip install --no-cache-dir \
    dbt-postgres==1.* \
    dbt-bigquery==1.*

WORKDIR /dbt

ENTRYPOINT ["dbt"]

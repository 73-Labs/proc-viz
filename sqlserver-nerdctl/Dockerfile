FROM mcr.microsoft.com/mssql/server:2022-latest
USER root
RUN mkdir -p /scripts
COPY init.sql /scripts/
COPY entrypoint.sh /scripts/
RUN chmod +x /scripts/entrypoint.sh && sed -i 's/\r$//' /scripts/entrypoint.sh
ENTRYPOINT ["/scripts/entrypoint.sh"]

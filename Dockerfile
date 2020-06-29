FROM python:3.7
WORKDIR /app
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD badwords.csv badwords.csv
ENV BADWORDS_CSV_FILE badwords.csv

ADD userreport.template userreport.template
ENV USER_REPORT_TEMPLATE_FILE userreport.template

ADD bot.py bot.py
ENTRYPOINT [ "python", "bot.py" ]

import logging as log
import collections
import jinja2
import praw
import uuid
import sys
import re
import os

log.basicConfig(level=log.DEBUG, stream=sys.stdout)

log.info("setting up reddit connection. Expected required credentials in env")
reddit = praw.Reddit(
    user_agent=uuid.uuid4().hex,
    client_id=os.environ["PRAW_CLIENT_ID"],
    client_secret=os.environ["PRAW_CLIENT_SECRET"],
    username=os.environ["REDDIT_USERNAME"],
    password=os.environ["REDDIT_PASSWORD"],
)
log.debug("testing reddit connection with simple get...")
assert reddit.get("/"), "failed to get front page for unknown reason"
log.info("finished configuring reddit connection")

badword_csv_file = os.environ["BADWORD_CSV_FILE"]
log.info(f"loading badword regexes from {badword_csv_file}")
with open(badword_csv_file) as f:
    bad_word_regexes = {
        name: re.compile(regex)
        for name, regex in map(lambda x: x.strip().split(","), f)
    }
log.info(f"finished loading badwords regexes: {bad_word_regexes}")

user_report_template = os.environ["USER_REPORT_TEMPLATE_FILE"]
log.info(f"loading jinja template into memory from {user_report_template}")
with open(user_report_template) as f:
    user_report_template = jinja2.Template(f.read())
log.info("finished loading jinja tmeplate into memory")


def process_mentions():
    for mention in reddit.inbox.mentions(limit=25):
        log.info(f"processing mention: {mention}")
        user = mention.parent().author
        log.info(f"requested user to investigate: {user}")
        mention.delete()
        report = investigate_user(user)
        print(report)


def investigate_user(user):
    report = UserReport(user)
    for comment in user.comments.hot(limit=10000):
        report.total_comments += 1
        report.total_words = len(comment.body.split(" "))
        for bad_word, regex in bad_word_regexes.items():
            found_bad_words = regex.findall(comment.body)
            report.total_bad_words += len(found_bad_words)
            report.bad_words[bad_word] += len(found_bad_words)
    return report


class UserReport:
    def __init__(self, user):
        self.user = user
        self.total_words = 0
        self.total_comments = 0
        self.total_bad_words = 0
        self.bad_words = collections.Counter()

    def __str__(self):
        return user_report_template.render(
            user_name=self.user.name,
            total_words=self.total_words,
            total_comments=self.total_comments,
            total_bad_words=self.total_bad_words,
            bad_words=self.bad_words,
        )

    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    process_mentions()

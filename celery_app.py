from celery import Celery
import os

os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")

app = Celery("prismy_ultimate")
app.config_from_object("celery_config")
app.autodiscover_tasks(["src.celery_tasks"])

if __name__ == "__main__":
    app.start()

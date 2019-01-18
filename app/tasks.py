from celery.signals import task_postrun

from app.ComicDownloader import ComicDownloader
from app import celery, db
from app.models import Comic, Chapter, Content


@celery.task
def echo(comic_id):
    comic = Comic.query.get(comic_id)
    print(comic.title)


@celery.task(bind=True)
def do_grab(self, comic_id):
    # comic = Comic.query.get(comic_id)
    STATE = ['pending...', 'running...', 'finished!']

    chapter = Chapter.query.filter_by(comic=comic_id).all()
    total = len(chapter)
    if total == 0:
        return
    self.update_state(state='PROGRESS', meta={'total': total, 'now': 0})
    task = ComicDownloader()
    now_pointer = 1
    for cp in chapter:
        task_res = task.download(cp.src, comic_id, cp.id)
        cnt = 1
        for done in task_res:
            if done:
                c = Content(cp.id, '/static/comic/{}/{}/{}.jpg.jpg'.format(comic_id, cp.id, cnt))
                db.session.add(c)
            cnt += 1
        cp.ok = True
        db.session.commit()
        self.update_state(state='PROGRESS', meta={'total': total, 'now': now_pointer})
        now_pointer += 1


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()

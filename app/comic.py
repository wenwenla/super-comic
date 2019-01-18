from flask import Blueprint, render_template, request, redirect, url_for, session

from app import db
from app.models import Comic, Chapter, Content, TaskStatus
from app.tasks import echo, do_grab

bp = Blueprint('comic', __name__)


@bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@bp.route('/list')
@bp.route('/list/<int:index>')
def list_(index=1):
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
    paginate = Comic.query.order_by(Comic.id).paginate(index, per_page=20, error_out=False)
    return render_template('comic-list.html', paginate=paginate)


@bp.route('/search')
def search():
    key = request.args['key']
    result = Comic.query.filter(Comic.title.like('%{}%'.format(key))).limit(20).all()
    return render_template('comic-result.html', result=result)


@bp.route('/show')
@bp.route('/show/<int:index>')
def show(index=1):
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
    comic = Comic.query.get(index)
    if not comic:
        return render_template('404.html')
    chapter = Chapter.query.filter_by(comic=comic.id).all()
    return render_template('comic-show.html', comic=comic, chapter=chapter)


@bp.route('/read/chapter_<int:chapter>')
@bp.route('/read/chapter_<int:chapter>/pic_<int:content>')
def read(chapter, content=None):
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
    if not content:
        pic = Content.query.filter_by(chapter=chapter).order_by(Content.id).first()
        if pic is not None:
            content = pic.id
    else:
        pic = Content.query.get(content)
    if pic is None:
        return render_template('404.html')
    nxt = Content.query.get(content + 1)
    pre = Content.query.get(content - 1)

    if pre is None or pre.chapter != chapter:
        pre = None
    if nxt is None or nxt.chapter != chapter:
        nxt = None
    return render_template('comic-read.html', pic=pic, nxt=nxt, pre=pre)


@bp.route('/task/<int:comic_id>')
def grab(comic_id):
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
    task = do_grab.apply_async(args=(comic_id,))
    comic = Comic.query.get(comic_id)
    if comic is None:
        return render_template('404.html')
    db.session.add(TaskStatus(task.id, comic.title))
    db.session.commit()
    return redirect(url_for('comic.tasks'))


@bp.route('/task/list')
@bp.route('/task/list/<int:index>')
def tasks(index=1):
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))

    def get_result(task_id):
        task = do_grab.AsyncResult(task_id)
        if task.state == 'SUCCESS':
            result = {
                'state': 'SUCCESS',
                'status': '100%'
            }
        elif task.state == 'PENDING':
            result = {
                'state': 'PENDING',
                'status': '0'
            }
        elif task.state != 'FAILURE':
            result = {
                'state': task.state,
                'status': '{:.2f}%'.format(task.info.get('now', 0) / task.info.get('total', 999) * 100),
            }
        else:
            result = {
                'state': 'FAILURE',
                'status': str(task.info)
            }
        return result

    task_queue = TaskStatus.query.order_by(TaskStatus.start_time.desc()).paginate(index, per_page=10, error_out=False)
    info = []
    for item in task_queue.items:
        info.append(get_result(item.task_id))
    return render_template('task-queue.html', info=zip(task_queue.items, info), queue=task_queue)
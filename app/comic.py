from flask import Blueprint, render_template, request, redirect, url_for, session

from app import db
from app.models import Comic, Chapter, Content, TaskStatus, History
from app.tasks import echo, do_grab

bp = Blueprint('comic', __name__)


@bp.route('/')
def _():
    return redirect(url_for('comic.list_'))


@bp.route('/list')
@bp.route('/list/<int:index>')
def list_(index=1):
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
    paginate = Comic.query.order_by(Comic.id).paginate(index, per_page=20, error_out=False)
    return render_template('comic-list.html', paginate=paginate)


@bp.route('/search')
def search():
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
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

    user_id = session['user_id']

    chapter_obj = Chapter.query.get(chapter)

    if chapter_obj is None:
        return render_template('404.html')

    comic = Comic.query.get(chapter_obj.comic)
    if comic is None:
        return render_template('404.html')

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

    history_obj = History.query.get((user_id, comic.id))
    if history_obj is None:
        db.session.add(History(user_id, comic.id, chapter, content))
    else:
        history_obj.update(chapter, content)

    db.session.commit()
    nxt_content = None
    nxt_chapter = None
    if pre is None or pre.chapter != chapter:
        pre = None
    if nxt is None or nxt.chapter != chapter:
        nxt_content = nxt
        nxt = None
    if nxt_content is not None:
        nxt_chapter = Chapter.query.get(nxt_content.chapter)
        if nxt_chapter.comic != comic.id:
            nxt_content = None
            nxt_chapter = None

    return render_template('comic-read.html', pic=pic, nxt=nxt, pre=pre, comic=comic, chapter=chapter_obj,
                           nxt_chapter=nxt_chapter, nxt_content=nxt_content)


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


@bp.route('/history')
@bp.route('/history/<int:index>')
def history(index=1):
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    history_list = History.query.filter_by(user=user_id)\
        .order_by(History.time.desc()).paginate(index, per_page=10, error_out=False)
    result = []
    for item in history_list.items:
        result.append({
            'history': item,
            'comic': Comic.query.get(item.comic),
            'chapter': Chapter.query.get(item.chapter)
        })
    return render_template('comic-history.html', history=history_list, result=result)


@bp.route('/log')
def log():
    if session.get('user_id', None) is None:
        return redirect(url_for('auth.login'))
    return render_template("log.html")

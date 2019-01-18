import datetime
import json
import os

import click
from flask.cli import with_appcontext
from app import db
from downloader import IntroPageParser


class Comic(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(128), nullable=False)
    cover = db.Column(db.String(64), nullable=False)
    src = db.Column(db.String(64), nullable=False)
    intro = db.Column(db.String(256), default='还没有写介绍~')

    def __init__(self, title, cover, src):
        self.title = title
        self.cover = cover
        self.src = src

    def __repr__(self):
        return self.title


class Chapter(db.Model):

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    comic = db.Column(db.Integer, db.ForeignKey('comic.id'), nullable=False)
    src = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    ok = db.Column(db.Boolean, default=False)

    def __init__(self, comic, src, name):
        self.comic = comic
        self.src = src
        self.name = name

    def __repr__(self):
        return self.name


class Content(db.Model):

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    chapter = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    url = db.Column(db.String(64), nullable=False)

    def __init__(self, chapter, url):
        self.chapter = chapter
        self.url = url

    def __repr__(self):
        return self.url


class User(db.Model):

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password


class TaskStatus(db.Model):

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    task_id = db.Column(db.String(64), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    name = db.Column(db.String(128), nullable=False)

    def __init__(self, task_id, name):
        self.task_id = task_id
        self.name = name


def init_comic():
    rt, _, f = next(os.walk('static/list'))
    cnt = 1
    path = os.path.join('static/list', 'out.txt')
    with open(path, 'rb') as f_in:
        data = json.loads(f_in.read().decode('utf8'))
    for d in data:
        item = Comic(d['title'], '/static/cover/{}.jpg'.format(cnt), d['href'])
        cnt += 1
        db.session.add(item)
    db.session.commit()


def init_chapter():
    rt, _, f = next(os.walk('static/intro'))
    f.sort(key=lambda x: int(x[:-5]))
    cnt = 1
    parser = IntroPageParser()
    for file in f:
        path = os.path.join(rt, file)
        with open(path, 'rb') as html:
            page = html.read().decode('utf8')
        parser.set_content(page)
        result = parser.parse()
        comic = Comic.query.get(cnt)
        comic.intro = result['intro']
        # db.session.commit()

        for chapter in result['chapter']:
            cp = Chapter(comic.id, 'https://www.manhuagui.com' + chapter['url'], chapter['name'])
            db.session.add(cp)
        # db.session.commit()
        if cnt % 1000 == 0:
            print('{} ok!'.format(cnt))
            db.session.commit()
        cnt += 1
    db.session.commit()


def init_content():
    con = Content.query.all()
    for c in con:
        if c.url[-4:] == 'webp':
            c.url = c.url[:-4] + 'jpg'
    db.session.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    # db.drop_all()
    db.create_all()
    # init_comic()
    # init_chapter()
    # init_content()
    click.echo('init-db-ok')

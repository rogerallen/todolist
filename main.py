import cherrypy
from jinja2 import Environment, FileSystemLoader
import json
from datetime import datetime
import os
import Cookie

env = Environment(loader=FileSystemLoader('.'))

# from stackoverflow
class IDSingleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(IDSingleton, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance
    def __init__(self):
        self.id = 1000
    def getId(self):
        rid = self.id
        self.id += 1
        return str(rid)
ID = IDSingleton()

# FIXME add persistence 
g_todolist = []
class TodoList(object):
    def __init__(self):
        self.timestamp = datetime.now()
        self.key = ID.getId()

# FIXME add persistence 
g_todos = []
class Todos(object):
    def __init__(self,key,order,content,done):
        self.id       = ID.getId()
        self.key      = key
        self.order    = order
        self.content  = content
        self.done     = done

    def toDict(self):
        todo = {
            'id'      : self.id, 
            'order'   : self.order,
            'content' : self.content,
            'done'    : self.done
            }
        return todo

class MainHandler(object):
    exposed = True
    def GET(self):
        if cherrypy.request.cookie.get('todos', None) == None:
            g_todolist.append(TodoList())
            cookie = cherrypy.response.cookie
            cookie['todos'] = g_todolist[-1].key
            cookie['todos']['expires'] = datetime(2014, 1, 1).strftime('%a, %d %b %Y %H:%M:%S')
            cookie['todos']['path'] = '/'
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        tmpl = env.get_template('index.html')
        return tmpl.render(salutation='Hello', target='World')

class RESTfulHandler(object):
    exposed = True
    def GET(self):
        key = cherrypy.request.cookie['todos'].value
        todos = []
        for todo in g_todos:
            if todo.key == key:
                todos.append(todo.toDict())
        todos = json.dumps(todos)
        return todos

    def POST(self):
        key = cherrypy.request.cookie['todos'].value
        todo = json.loads(cherrypy.request.body.read())
        todo = Todos(key     = key,
                     order   = todo['order'],
                     content = todo['content'],
                     done    = todo['done'])
        g_todos.append(todo)
        todo = json.dumps(todo.toDict())
        return todo

    def PUT(self, uid):
        key = cherrypy.request.cookie['todos'].value
        todo = None
        global g_todos
        for t in g_todos:
            if t.id == uid:
                todo = t
                break
        if todo and todo.key == key:
            tmp = json.loads(cherrypy.request.body.read())
            todo.content = tmp['content']
            todo.done    = tmp['done']
            todo = json.dumps(todo.toDict())
            return todo
        else:
            raise cherrypy.HTTPError(403)

    def DELETE(self, uid):
        key = cherrypy.request.cookie['todos'].value
        todo = None
        global g_todos
        for (i,t) in enumerate(g_todos):
            if t.id == uid:
                todo = t
                break
        if todo and todo.key == key:
            g_todos = g_todos[:i] + g_todos[i+1:]
        else:
            raise cherrypy.HTTPError(403)
        
root = MainHandler()
root.todos = RESTfulHandler()

conf = {
    'global': {
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 8888,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__))
        },
    '/': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        },
    '/css': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'css'
        },
    '/js': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'js'
        },
    '/img': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'img'
        },
}

cherrypy.quickstart(root, '/', conf)

__all__ = ['dumps', 'C', 'U', 'Buf', 'S', 'Call', 'Function', 'HtmlBuf', 'Line',
    'LinkBuf', 'ScriptLink', 'CssLink', 'Script', 'Style', 'New', 'OnReady', 
    'Quote', 'Var', 'Snippet']

import os
try:
    import json as JSON
except:
    import simplejson as JSON

TAB = 4
SIMPLE_IDEN = True

class ComplexEncoder(JSON.JSONEncoder):
    def __init__(self, classes=[], **kwargs):
        JSON.JSONEncoder.__init__(self, **kwargs)
        if not isinstance(classes, (tuple, list)):
            self.classes = [classes]
        else:
            self.classes = list(classes)
        
    def _iterencode_default(self, o, markers=None):
        if callable(o):
            return o()
        newobj = self.default(o)
        return self._iterencode(newobj, markers)
    
def dumps(obj):
    return JSON.dumps(obj, cls=ComplexEncoder)

class B(object):
    def __init__(self, value=None):
        self.value = value
        self.parent = None
        
    def __str__(self):
        return self.value
    
    def __call__(self):
        return self.__str__()
    
class C(B):
    def __call__(self):
        return self.value
    
class U(B):
    def __str__(self):
        return '"' + self.value + '"'
    
    def __call__(self):
        return self.__str__()
    
def S(value, tab=0):
    if isinstance(value, dict):
        s = []
        length = len(value)
        s.insert(0, '{')
        for i, j in enumerate(value.items()):
            k, v = j
            if i != length-1:
                ending = ','
            else:
                ending = ''
            if SIMPLE_IDEN and k.isalpha() and k not in ['class']:
                s.append((tab+TAB) * ' ' + '%s: %s%s' % (k, S(v, tab+TAB), ending))
            else:
                s.append((tab+TAB) * ' ' + '%s: %s%s' % (S(k, tab+TAB), S(v, tab+TAB), ending))
        s.append(tab*' ' + '}')
        return '\n'.join(s)
    elif isinstance(value, (tuple, list)):
        s = []
        s.append('[')
        length = len(value)
        for i, k in enumerate(value):
            if i != length-1:
                ending = ','
            else:
                ending = ''
            s.append((tab+TAB) * ' ' + '%s%s' % (S(k, tab+TAB), ending))
        s.append(tab*' ' + ']')
        return '\n'.join(s)
    elif isinstance(value, C):
        return str(value)
    else:
        return dumps(value)

class Var(B):
    def __init__(self, name, value=None):
        B.__init__(self, value)
        self.name = name
        
    def __str__(self):
        return 'var %s = %s;' % (self.name, self.value)
    
    def __call__(self):
        return self.name
    
    def __getattr__(self, name):
        return self.call(name)
    
    def call(self, name):
        def r(*args):
            if self.parent:
                self.parent<<'%s.%s(%s);' % (self.name, name, ','.join(map(S, args)))
        return r

class Call(B):
    def __init__(self, name, *args):
        B.__init__(self)
        self.name = name
        self.args = args
        
    def __str__(self):
        return '%s(%s);' % (self.name, ','.join(map(S, self.args)))
    
class New(B):
    def __init__(self, value, *kwargs):
        B.__init__(self, value)
        self.kwargs = kwargs
    
    def __str__(self):
        args = []
        for i in self.kwargs:
            if i is None:
                continue
            if isinstance(i, Var):
                args.append(i.name)
            else:
                args.append(S(i))
        return 'new %s(%s)' % (self.value, ','.join(args))
    
class Line(B):
    def __str__(self):
        v = str(self.value).strip()
        if not v.endswith(';'):
            return "%s;" % v
        else:
            return "%s" % v

class CssLink(B):
    def __init__(self, value=None, static_suffix=''):
        B.__init__(self, value)
        self.static_suffix = static_suffix
        self.link = os.path.join(self.static_suffix, self.value)

    def __str__(self):
        return '<link rel="stylesheet" type="text/css" href="%s"/>' % self.link
    
class CssHeaderCodeSnippet(B):
    def __init__(self, value=None, static_suffix=''):
        B.__init__(self, value)
        self.static_suffix = static_suffix
    
    def __str__(self):
        return self.value % {'static_suffix': self.static_suffix}
    
class ScriptLink(B):
    def __init__(self, value=None, static_suffix=''):
        B.__init__(self, value)
        self.static_suffix = static_suffix
        self.link = os.path.join(self.static_suffix, self.value)

    def __str__(self):
        return '<script type="text/javascript" src="%s"></script>' % self.link
        
class Buf(B):
    def __init__(self):
        B.__init__(self)
        self.buf = []
    
    def __lshift__(self, obj):
        if not obj:
            return None
        if isinstance(obj, (tuple, list)):
            self.buf.extend(obj)
        else:
            self.buf.append(obj)
            obj = [obj]
        for o in obj:
            if isinstance(o, B):
                o.parent = self
        return obj[0]
        
    def __str__(self):
        return self.render()
        
    def render(self):
        return '\n'.join([str(x) for x in self.buf])
    
class LinkBuf(Buf):
    def render(self):
        s = []
        for x in self.buf:
            t = str(x)
            if t not in s:
                s.append(t)
        return '\n'.join(s)
        
class Quote(Buf):
    def __init__(self, begin='', end=''):
        Buf.__init__(self)
        self.begin = begin
        self.end = end
        
    def render(self):
        s = [self.begin]
        s.append(Buf.render(self))
        s.append(self.end)
        return '\n'.join(s)
        
class Function(Quote):
    def __init__(self, name='', args=[], content=''):
        Quote.__init__(self, 'function ' + name + '(%s){', '}')
        self.args = args
        self.buf.append(content)
        
    def render(self):
        if self.args:
            s = [self.begin % ','.join(self.args)]
        else:
            s = [self.begin % '']
        s.append(Buf.render(self))
        s.append(self.end)
        return '\n'.join(s)
    
class Script(Quote):
    def __init__(self):
        Quote.__init__(self, '<script type="text/javascript">', '</script>')
    
    def render(self):
        content = Buf.render(self)
        if content:
            s = [self.begin]
            s.append(content)
            s.append(self.end)
            return '\n'.join(s)
        else:
            return ''
    
class Style(Script):
    def __init__(self):
        Quote.__init__(self, '<style type="text/css">', '</style>')
    
if __name__ == '__main__':
    ds = Var('ds', New('Ext.data.JsonStore', {
        'url': '/Address/default/ajax_all/',
        'root': "rows",
        'fields': ['name', 'telphone']
    }))
    

    print ds
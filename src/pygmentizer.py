from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.lexers._mapping import LEXERS
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from google.appengine.ext import db

class LangStats(db.Model):
    lang = db.StringProperty(required=True)
    count = db.IntegerProperty()

def _count_usage(lang):
    if not lang:
        return
    s = LangStats.get_or_insert(lang, lang=lang, count=0)
    s.count += 1
    s.put()

_formatter = HtmlFormatter(linenos=True)

def _pygmentize(code, lang=""):
    if lang:
        try:
            lexer = get_lexer_by_name(lang)
            _count_usage(lexer.name)
        except ClassNotFound:
            return 'Wrong language "%s". Note: language code is case-sensitive.' % lang, 'text/plain', 500
    else:
        lexer = guess_lexer(code)
    try:        
        res = highlight(code, lexer, _formatter)
    except Exception, e:
        return 'Error pygmentizing the code. %s' % e, 'text/plain', 500
    return res, 'text/html', 200



class MainPage(webapp.RequestHandler):

    def get(self):
        path = "index.html"
        rs = LangStats.all()
        stats = []
        for r in rs:
            stats.append((r.lang, r.count))
        self.response.out.write(template.render(path, 
                                                {'stats': stats,}))
        
    def post(self):
        lang = self.request.get('lang')
        code = self.request.get('code')
        
        res, type, status = _pygmentize(code, lang)
        self.response.headers['Content-Type'] = type
        if status != 200:
            self.response.set_status(status)
        
        self.response.out.write(res)

            
class LanguagesPage(webapp.RequestHandler):
    
    def get(self):
        path = "langs.html"
        langs = [(l[1], l[2]) for l in LEXERS.values()]
        langs.sort(key=lambda x: x[0].lower())
        self.response.out.write(template.render(path, 
                                                {'langs': langs}))

class TestPage(webapp.RequestHandler):
    def get(self):
        path = "test.html"
        self.response.out.write(template.render(path, {}))

application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/test', TestPage),
    ('/languages', LanguagesPage),
  ], 
  debug=False)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

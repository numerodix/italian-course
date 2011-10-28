#!/usr/bin/env python

from collections import OrderedDict
import glob
import os
import re
import sys
from optparse import OptionParser


def get_body(fp):
    content = open(fp).read()
    m = re.search('(?is)<body>(.*)</body>', content)
    content = m.group(1)
    content = content.strip()
    return content

def get_string(rx, s):
    t = ''
    m = re.search(rx, s)
    if m:
        t = m.group(1)
        t = t.strip()
    return t

def unbreak(pre=None, post=None):
    def f(match):
        if match:
            s = match.group(1)
            s = re.sub('\n', ' ', s)
            s = re.sub(' {2,}', ' ', s)
            if pre:
                s = pre + s
            if post:
                s = s + post
            return s
        raise Exception()
    return f

def break_before_bracket(exclude_rxs=None):
    def f(match):
        if match:
            s = match.group(1)
            if not any(map(lambda rx: re.match(rx, s), exclude_rxs)):
                def do_sub(m):
                    br = ''
                    if m.group(2).strip() and m.group(3):
                        br = '<br>'
                    return '%s%s%s%s%s' % (m.group(1), m.group(2), br, m.group(3) or '', m.group(4))
                s = re.sub('(?is)(<li>)(.*?)(\[.*?\])?(</li>)', do_sub, s)
        return s
    return f

def post_markdown(fp):
    content = open(fp).read()

    # ~~bad~~  =>  <del>bad</del>
    content = re.sub('(?is)~~(.*?)~~', '<del>\g<1></del>', content)

    open(fp, 'w').write(content)

def post_markdown_lezione(fp):
    content = open(fp).read()

    # break before literal bracket in some sections
    exclude_rxs = [
        '(?is)<h1>Theory.*?</h1>',
        '(?is)<h1>Notes</h1>',
    ]
    content = re.sub('(?is)(<h1>.*?</h1>.*?)(?=(?:<h1>|</body>))',
                     break_before_bracket(exclude_rxs), content)

    # ()  =>  <sup>(1)</sup>
    i = 0; s = content; t = ''
    while True:
        i += 1
        (t, subcount) = re.subn('(?is)\(\)', '<sup>(%s)</sup>' % i, s, 1)
        s = t
        if subcount == 0:
            break
    content = t

    # [Hi]  =>  <em>[Hi]</em>
    content = re.sub('(?is)(\[.*?\])', '<em>\g<1></em>', content)

    open(fp, 'w').write(content)

def html_to_bbcode(content):
    # multiline
    content = re.sub('(?is)<ol>(.*?)</ol>\n?', '[list=1]\g<1>[/list]', content)
    content = re.sub('(?is)<ul>(.*?)</ul>\n?', '[list]\g<1>[/list]', content)

    # inline
    content = re.sub('(?is)<h1>(.*?)</h1>', unbreak('[b]', '[/b]'), content)

    content = re.sub('(?is)<li>(.*?)</li>', unbreak('[*]', ''), content)

    content = re.sub('(?is)<strong>(.*?)</strong>', unbreak('[b]', '[/b]'), content)
    content = re.sub('(?is)<em>(.*?)</em>', unbreak('[i]', '[/i]'), content)
    content = re.sub('(?is)<sup>(.*?)</sup>', unbreak('[sup]', '[/sup]'), content)

    content = re.sub('(?is)<p>(.*?)</p>', unbreak('', ''), content)

    content = re.sub('(?is)<a\s+href="(.*?)"\s*>(.*?)</a>', '[b][url=\g<1>]\g<2>[/url][/b]', content)

    # linebreak before literal translation
    content = re.sub('<br>', '\n', content)

    return content

def html_to_wiki(content):
    def sub_ol(m):
        content = m.group(1)
        content = re.sub('(?is)<li>(.*?)</li>', unbreak('# ', ''), content)
        return content

    def sub_ul(m):
        content = m.group(1)
        content = re.sub('(?is)<li>(.*?)</li>', unbreak('* ', ''), content)
        return content

    # multiline
    content = re.sub('(?is)\n?<ol>(.*?)</ol>\n?', sub_ol, content)
    content = re.sub('(?is)\n?<ul>(.*?)</ul>\n?', sub_ul, content)

    # inline
    content = re.sub('(?is)<h1>(.*?)</h1>', unbreak('== ', ' =='), content)

    content = re.sub('(?is)<li>(.*?)</li>', unbreak('* ', ''), content)

    content = re.sub('(?is)<strong>(.*?)</strong>', unbreak("'''", "'''"), content)
    content = re.sub('(?is)<em>(.*?)</em>', unbreak("''", "''"), content)

    content = re.sub('(?is)<p>(.*?)</p>', unbreak('', ''), content)

    content = re.sub('(?is)<a\s+href="(.*?)"\s*>(.*?)</a>', '[[\g<1>|\g<2>]]', content)

    return content


def convert_bbcode(fp, video_url):
    content = get_body(fp)

    content = html_to_bbcode(content)

    # add video
    if video_url:
        content = "[video]%s[/video]\n\n" % video_url + content

    sys.stdout.write(content+'\n')

def convert_wiki(fp, video_url):
    content = get_body(fp)

    content = html_to_wiki(content)

    # add video
    if video_url:
        content = "== Audio ==\n\nListen to the '''[%s %s]'''\n\n" % (video_url, 'audio') + content

    sys.stdout.write(content+'\n')

def convert_youtube(fp, lesson_url):
    content = get_body(fp)

    m = re.search('(?is)(<h1>.*?</h1>.*?)<h1>', content)
    content = m.group(1)

    # multiline
    content = re.sub('\n?(?is)<ol>(.*?)</ol>\n?', '\g<1>', content)
    content = re.sub('\n?(?is)<ul>(.*?)</ul>\n?', '\g<1>', content)

    # inline
    content = re.sub('(?is)<h1>(.*?)</h1>', unbreak('', ''), content)

    content = re.sub('(?is)<li>(.*?)</li>', unbreak('', ''), content)

    content = re.sub('(?is)<strong>(.*?)</strong>', unbreak('', ''), content)
    content = re.sub('(?is)<em>(.*?)</em>', unbreak('', ''), content)
    content = re.sub('(?is)<sup>.*?</sup>', '', content)

    content = re.sub('(?is)<p>(.*?)</p>', unbreak('', ''), content)

    # add lesson link
    content += "Lesson: %s" % lesson_url
    content += "\n\nItalian course for Juventini: %s" % 'http://italiancourseforjuventini.wikia.com'

    sys.stdout.write(content+'\n')

def extract_for_grouping(fp):
    content = get_body(fp)

    title = get_string('(?is)<title>(.*)</title>', open(fp).read())
    content = "\n<div class='file'>%s</div>\n\n" % title + content

    sys.stdout.write(content+'\n')

def create_index(path, bbcode=False, wiki=False):
    metadir = os.path.join(path, '.meta')

    urls_bbcode = open(os.path.join(metadir, 'published_forum')).readlines()
    urls_bbcode = map(lambda u: u.strip(), urls_bbcode)

    urls_ex = open(os.path.join(metadir, 'published_forum_ex')).readlines()

    urls_wiki = open(os.path.join(metadir, 'published_wiki')).readlines()
    urls_wiki = map(lambda u: u.strip(), urls_wiki)

    def get_theory(files):
        dct = OrderedDict()
        for fp in files:
            content = get_body(fp)
            items = re.findall('<h1>(Theory: .*?)</h1>', content)
            dct[fp] = items
        return dct

    up_to = 23  # intro + 22 lessons
    files = sorted(glob.glob('ICFJ[0-9][0-9]*.html'))[:up_to]

    titles = map(lambda fp: re.sub('ICFJ(.*)\.html', '\g<1>', fp), files)
    titles = map(lambda fp: re.sub('_', ' ', fp), titles)

    theory = get_theory(files)

    html = ''
    for item in zip(files, titles, urls_bbcode, urls_ex, urls_wiki):
        fp, title, url_bbcode, url_ex, url_wiki = item
        ex_url = ''

        url = url_bbcode
        if wiki:
            url = url_wiki

        if bbcode and url_ex.strip():
            ex_url = ' | <a href="%s">Exercises</a>' % url_ex

        theo = theory.get(fp)
        theory_html = ''
        if theo:
            theory_html = '\n<br>' + '\n<br>'.join(theo)
        html += '<li><a href="%s">%s</a>%s%s</li>\n' % (url, title, ex_url, theory_html)
    html = '<ul>\n%s</ul>' % html
    html = '<h1>Index</h1>\n' + html

    if bbcode:
        content = html_to_bbcode(html)+'\n'
    elif wiki:
        content = html_to_wiki(html)

    sys.stdout.write(content)


if __name__ == '__main__':
    usage = "Usage:  %s [options] file.html" % sys.argv[0]
    parser = OptionParser(usage=usage)
    parser.add_option("--pm", help="Post markdown",
                      dest="post_markdown", action="store_true")
    parser.add_option("--pm-lezione", help="Post markdown lezioni flavor",
                      dest="post_markdown_lezione", action="store_true")
    parser.add_option("--eg", help="Extract for grouping",
                      dest="extract_for_grouping", action="store_true")
    parser.add_option("-b", help="Output bbcode",
                      dest="bbcode", action="store_true")
    parser.add_option("-w", help="Output wiki code",
                      dest="wiki", action="store_true")
    parser.add_option("-y", help="Output youtube description",
                      dest="youtube", action="store_true")

    parser.add_option("--idx", help="Output index",
                      dest="index", action="store_true")
    (options, args) = parser.parse_args()

    try:
        fp = args[0]
    except IndexError:
        parser.print_help()
        sys.exit(2)

    if options.post_markdown:
        post_markdown(fp)
    elif options.index:
        create_index(fp, bbcode=options.bbcode, wiki=options.wiki)
    elif options.post_markdown_lezione:
        post_markdown_lezione(fp)
    elif options.extract_for_grouping:
        extract_for_grouping(fp)
    elif options.bbcode:
        video_url = args[1]
        convert_bbcode(fp, video_url)
    elif options.wiki:
        video_url = args[1]
        convert_wiki(fp, video_url)
    elif options.youtube:
        lesson_url = args[1]
        convert_youtube(fp, lesson_url)
    else:
        parser.print_help()
        sys.exit(1)

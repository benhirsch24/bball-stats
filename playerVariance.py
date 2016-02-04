from bs4 import BeautifulSoup
import urllib2
import collections
import os
import numpy

def not_dnp(idee):
    return idee != 'pgl_basic.0'

def parseSeasonTable(logs):
    data = logs.tbody
    scores = []
    season_score = 0

    points_idx = 0
    for th in logs.thead.tr.find_all('th'):
        if th.string == 'PTS':
            break;
        else:
            points_idx += 1

    for tr in data.find_all('tr', id=not_dnp):
        if 'thead' in tr['class']:
            continue
        cells = tr.find_all('td')
        score = int(cells[points_idx].string)
        scores.append(score)
        season_score += score
    return (scores, season_score)

def parseGameLogs(tag):
    list_nodes = tag.ul.find_all('li')
    url = 'http://www.basketball-reference.com'
    seasons = collections.OrderedDict()
    for list_node in list_nodes:
        season_url = url + list_node.a['href']
        season_name = season_url.split('/')[-2]
        season_filename = season_name + '.html'
        if not os.path.isfile(season_filename):
            with open(season_filename, 'w') as f:
                contents = urllib2.urlopen(season_url).read()
                f.write(contents)
        with open(season_filename) as f:
            seasoned_soup = BeautifulSoup(f.read(), 'html.parser')
            print 'Parsing ' + season_name
            season_scores = parseSeasonTable(seasoned_soup.find(id='pgl_basic'))
            seasons[season_name] = season_scores
    scores = []
    for year, (all_scores, total_score) in seasons.iteritems():
        print '%s: %d' % (year, total_score)
        scores += all_scores
    print scores
    nscores = numpy.array(scores)
    stddev = nscores.std()
    mean = nscores.mean()
    above = nscores[nscores > (mean + stddev)].size
    below = nscores[nscores < (mean - stddev)].size
    total = nscores.size
    print 'Std dev: %f' % stddev
    print 'Mean: %f' % mean
    print 'Num above std dev: %d, num below: %d' % (above, below)
    print 'Total games: %d' % total

def game_logs_filter(tag):
    if tag.span is not None:
        if len(tag.span.contents) > 0 and tag.span.contents[0] == 'Game Logs':
            return True
    return False

if __name__ == '__main__':
    #content = urllib2.urlopen('http://www.basketball-reference.com/players/b/bryanko01.html').read()
    with open('kobe.html') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')

        page_content = soup.find(id='page_content')
        game_logs = page_content.find(class_='clearfix').find(class_='menu').find_all(game_logs_filter)
        if len(game_logs) > 0:
            parseGameLogs(game_logs[0])

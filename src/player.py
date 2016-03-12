from bs4 import BeautifulSoup
import urllib2
import collections
import os
import csv
import numpy

def nba_aba_top_50_parser(html):
    bs = BeautifulSoup(html, "html.parser")
    nba_aba_table = bs.find(id='page_content').table.tr.contents[1].div.table
    for row in nba_aba_table.find_all('tr'):
        if row.th:
            continue

        url = 'http://www.basketball-reference.com/' + row.find_all('td')[1].a['href']
        yield url

def player_file_list_parser(fi):
    with open(fi, 'r') as f:
        for player_file in f:
            if player_file[-1] == '\n':
                yield player_file[:-1]
            else:
                yield player_file

def player_file_iterator(uri):
    if uri.startswith('http://'):
        pieces = uri.split('/')
        print pieces[-1]
        if os.path.isfile(pieces[-1]):
            with open(pieces[-1], 'r') as f:
                for player_file in f:
                    if player_file[-1] == '\n':
                        yield player_file[:-1]
                    else:
                        yield player_file
        else:
            with open(pieces[-1], 'w') as f:
                html = urllib2.urlopen(uri).read()
                for url in nba_aba_top_50_parser(html):
                    f.write(url)
                    f.write('\n')
                    yield url
    else:
        for fi in player_file_list_parser(uri):
            yield fi

class Player:
    def __init__(self, player_page, input_dir='', output_dir=''):
        self.seasons    = collections.OrderedDict()
        self.name       = ''
        self.input_dir  = input_dir
        self.output_dir = output_dir
        self.scores     = []
        self.stddev     = 0
        self.mean       = 0
        self.above      = 0
        self.below      = 0
        self.cent_above = 0
        self.cent_below = 0
        self.total      = 0

        self.player_name = player_page[:-5].split('/')[-1]
        print 'Player_name = ' + self.player_name
        player_file = input_dir + self.player_name + '.html'
        player_csv  = input_dir + self.player_name + '.csv'
        html = None
        if not os.path.isfile(player_file):
            html = urllib2.urlopen(player_page).read()
            with open(player_file, 'w') as f:
                f.write(html)

        if not os.path.isfile(player_file):
            raise RuntimeError('Error: ' + player_file + 'does not exist')

        if html is None:
            with open(player_file, 'r') as f:
                html = f.read()

        if html is None:
            raise RuntimeError('Error: ' + player_file + 'does not exist')

        if os.path.isfile(player_csv):
            print 'Loading from CSV'
            self.load_csv(player_csv)
            self.compute_scores()
        else:
            soup = BeautifulSoup(html, 'html.parser')
            self.parse_player_page(soup)
            self.save_csv(player_csv)

    def save_csv(self, csv_file):
        if os.path.isfile(csv_file):
            os.remove(csv_file)
        with open(csv_file, 'a') as f:
            f.write(self.name)
            f.write('\n')
            for (season, (scores, score)) in self.seasons.iteritems():
                f.write(str(season))
                f.write(',')
                f.write(','.join([str(s) for s in scores]))
                f.write('\n')


    def load_csv(self, csv_file):
        with open(csv_file, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            self.name = reader.next()[0]
            for row in reader:
                if row[0] == 'aba':
                    continue

                if row[1] != '':
                    scores = [int(c) for c in row[1:]]
                    if self.name == 'Tracy McGrady':
                        print 'TMac'
                    if len(scores) > 0:
                        self.seasons[int(row[0])] = (scores, sum(scores))
                        self.scores += scores

    def parse_player_page(self, soup):
        def game_logs_filter(tag):
            if tag.span is not None:
                if len(tag.span.contents) > 0 and tag.span.contents[0] == 'Game Logs':
                    return True
            return False

        self.name = soup.find(id='info_box').h1.string
        page_content = soup.find(id='page_content')
        game_logs = page_content.find(class_='clearfix').find(class_='menu').find_all(game_logs_filter)
        if len(game_logs) > 0:
            self.parse_game_logs(game_logs[0])

    def parse_game_logs(self, tag):
        list_nodes = tag.ul.find_all('li')
        url = 'http://www.basketball-reference.com'
        for list_node in list_nodes:
            if list_node.a is None:
                continue

            season_url = url + list_node.a['href']
            season_name = season_url.split('/')[-2]
            season_filename = self.input_dir + self.player_name + '_' + season_name + '.html'
            if season_filename == self.input_dir + 'mitchmi01_1990.html':
                continue

            contents = None
            if not os.path.isfile(season_filename):
                with open(season_filename, 'w') as f:
                    print 'Pulling ' + season_url
                    contents = urllib2.urlopen(season_url).read()
                    f.write(contents)

            if contents is None:
                with open(season_filename) as f:
                    contents = f.read()

            seasoned_soup = BeautifulSoup(contents, 'html.parser')
            print 'Parsing ' + season_name
            season_scores = self.parse_season_table(seasoned_soup.find(id='pgl_basic'))
            self.seasons[season_name] = season_scores

        scores = []
        for year, (all_scores, total_score) in self.seasons.iteritems():
            print '%s: %d' % (year, total_score)
            self.scores += all_scores

        self.compute_scores()

    def compute_scores(self):
        if len(self.scores) > 0:
            nscores = numpy.array(self.scores)
            self.stddev = nscores.std()
            self.mean = nscores.mean()
            self.total = nscores.size
            self.above = nscores[nscores > (self.mean + self.stddev)].size
            self.below = nscores[nscores < (self.mean - self.stddev)].size
            self.cent_above = float(self.above) / self.total
            self.cent_below = float(self.below) / self.total

    def parse_season_table(self, logs):
        def not_dnp(idee):
            return idee != 'pgl_basic.0'

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
            points = cells[points_idx].string
            if points is None:
                continue

            score = int(points)
            scores.append(score)
            season_score += score
        return (scores, season_score)

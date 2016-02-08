from bs4 import BeautifulSoup
import urllib2
import collections
import os
import csv
import numpy

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
                scores = [int(c) for c in row[1:]]
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
            season_url = url + list_node.a['href']
            season_name = season_url.split('/')[-2]
            season_filename = self.input_dir + self.player_name + '_' + season_name + '.html'

            contents = None
            if not os.path.isfile(season_filename):
                with open(season_filename, 'w') as f:
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
        nscores = numpy.array(self.scores)
        self.stddev = nscores.std()
        self.mean = nscores.mean()
        self.above = nscores[nscores > (self.mean + self.stddev)].size
        self.below = nscores[nscores < (self.mean - self.stddev)].size
        self.total = nscores.size

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
            score = int(cells[points_idx].string)
            scores.append(score)
            season_score += score
        return (scores, season_score)

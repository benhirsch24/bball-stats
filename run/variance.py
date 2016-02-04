from bs4 import BeautifulSoup
import player
import sys
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find variance in scoring in a player.')
    parser.add_argument('-p', default='http://www.basketball-reference.com/players/b/bryanko01.html')
    parser.add_argument('-i', default='input/')
    parser.add_argument('-o', default='data/')
    args = parser.parse_args()

    try:
        player = player.Player(args.p, args.i, args.o)
    except RuntimeError as e:
        print e

    print player.name
    print 'Std dev: %f' % player.stddev
    print 'Mean: %f' % player.mean
    print 'Num above std dev: %d, num below: %d' % (player.above, player.below)
    print 'Total games: %d' % player.total

from bs4 import BeautifulSoup
import player as pl
import sys
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find variance in scoring in a player.')
    parser.add_argument('-p', default='players.txt')
    parser.add_argument('-i', default='input/')
    parser.add_argument('-o', default='data/')
    args = parser.parse_args()

    with open(args.p, 'r') as f:
        for player_file in f:
            if player_file[-1] == '\n':
                player_file = player_file[:-1]

            try:
                player = pl.Player(player_file, args.i, args.o)
            except RuntimeError as e:
                print e

            print player.name
            print '============='
            print 'Std dev: %f, Mean: %f' % (player.stddev, player.mean)
            print 'Num above std dev: %d, num below: %d' % (player.above, player.below)
            perabove = player.above / float(player.total)
            perbelow = player.below / float(player.total)
            print 'Percent above std dev: %f, percent below: %f' % (perabove, perbelow)
            print 'Total games: %d' % player.total
            print '\n'

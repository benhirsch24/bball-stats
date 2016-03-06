from bs4 import BeautifulSoup
import player as pl
import sys
import argparse
import matplotlib.pyplot as plt

players = []

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
            print 'Std dev: %f, Mean: %f' % (player.stddev, player.mean)
            print 'Num above std dev: %d, num below: %d' % (player.above, player.below)
            print 'Percent above std dev: %f, percent below: %f' % (player.cent_above, player.cent_below)
            print 'Total games: %d\n' % player.total

            players.append(player)

    # plot players and efficiencies
    x_axis = [p.cent_above for p in players]
    y_axis = [p.cent_below for p in players]

    min_x, max_x = min(x_axis), max(x_axis)
    min_y, max_y = min(y_axis), max(y_axis)

    x_mid = (max_x + min_x) / 2
    y_mid = (max_y + min_y) / 2

    fig = plt.figure()
    ax = fig.add_subplot(111)

    plt.plot(x_axis, y_axis, 'ro')
    plt.gca().invert_yaxis()
    for p in players:
        ax.annotate('%s (%.2f, %.2f)' % (p.name, p.mean, p.stddev), xy = (p.cent_above, p.cent_below))
    plt.axvline(x_mid)
    plt.axhspan(y_mid, y_mid)
    plt.show()

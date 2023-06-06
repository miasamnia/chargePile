import time
import requests

match = open('matches/' + str(int(time.time())), 'w')
match.write('shenmicainiao'+'\n'+'cher_l')

# info = requests.get('https://mcsrranked.com/api/users/shenmicainiao')
# print(info.json())
# ldbd = open('data/leaderboard', 'r')
# text = ldbd.readlines()
# print(text)
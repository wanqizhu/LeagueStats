# /usr/bin/python3
# usage: script.py ChampionName EnemyChampionName
# get new key at https://developer.riotgames.com/
from riotwatcher import RiotWatcher
import json
import sys
import time
import math
from requests import HTTPError


class ChampNotFoundException(Exception):
    pass

def print_match_info(last_match, champion, enemy_champion):
    champ_id = champion_name_to_id_map[champion]
    enemy_champ_id = champion_name_to_id_map[enemy_champion]
    myself = None
    enemy = None

    for player in last_match['participants']:
        if player['championId'] == champ_id:
            myself = player

        elif player['championId'] == enemy_champ_id:
            enemy = player

    if not myself:
        # print("Your champion {} not found".format(champion))
        raise ChampNotFoundException

    game_duration = last_match['gameDuration'] / 60.0

    farm = myself['stats']['totalMinionsKilled'] + myself['stats']['neutralMinionsKilled']
    cs_per_min = farm / game_duration
    if enemy:
        farm_delta = (farm - enemy['stats']['totalMinionsKilled']
                          - enemy['stats']['neutralMinionsKilled'])
    else:
        # farm_delta = 99999 # undefined
        # print("Enemy champion {} not found".format(enemy_champion))
        raise ChampNotFoundException

    k, d, a = myself['stats']['kills'], myself['stats']['deaths'], myself['stats']['assists']
    gold = myself['stats']['goldEarned']
    gpm = gold / game_duration

    # print(json.dumps(last_match, indent=4, sort_keys=True))

    farm_at_10 = 10*myself['timeline']['creepsPerMinDeltas']["0-10"]
    farm_at_20 = farm_at_10 + 10*myself['timeline']['creepsPerMinDeltas']["10-20"]
    farm_diff_at_10 = 10*myself['timeline']['csDiffPerMinDeltas']["0-10"]
    farm_diff_at_20 = farm_diff_at_10 + 10*myself['timeline']['csDiffPerMinDeltas']["10-20"]

    # maybe also print out farm_remaining (20-30 and 30-end)

    # myself['timeline']['goldPerMinDeltas']

    print("\n\nmatch-id: {} {} {} v. {}\n".format(last_match['gameId'],
        time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(last_match['gameCreation']/1000)),
        champion, enemy_champion))

    print('cs/min\tgpm\tcs@10\tcsd@10\tcs@20\tcsd@20\tk\td\ta\tcs\tgold\tgame-length')
    print('%.2f\t%.2f\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.2f\n'

        % (cs_per_min, gpm, farm_at_10, 
        farm_diff_at_10, farm_at_20, farm_diff_at_20, k, d, a, farm, gold, game_duration))






def fetch_latest_game_stats(champion, enemy_champion, game_index=-1):

    recent_matches = watcher.match.matchlist_by_account_recent(
        my_region, me['accountId'])

    if game_index > -1:
        last_match = watcher.match.by_id(
            my_region, recent_matches['matches'][game_index]['gameId'])

        print_match_info(last_match, champion, enemy_champion)
    else:
        for ind in range(20):
            try:
                last_match = watcher.match.by_id(
                    my_region, recent_matches['matches'][ind]['gameId'])

                print_match_info(last_match, champion, enemy_champion)
            except ChampNotFoundException:
                print(".")
                continue
            break


    # print(json.dumps(last_match, indent=4, sort_keys=True))


   



try:
    watcher = RiotWatcher(open('riot-api-key.txt', 'r').read())

    my_region = 'na1'

    me = watcher.summoner.by_name(my_region, 'iqiq')
    

    champ_data = watcher.static_data.champions(
                                my_region)['data'].items()

    champion_name_to_id_map = {key: value['id']
                               for key, value in champ_data}



    champion = sys.argv[1]
    enemy_champion = sys.argv[2]
    if len(sys.argv) > 3:
        game_index = int(sys.argv[3])
    else:
        game_index = -1
    fetch_latest_game_stats(champion, enemy_champion, game_index)



except HTTPError as err:
    if err.response.status_code == 429:
        fetch_latest_game_stats(champion, enemy_champion)
        # print('We should retry in {} seconds.'.format(err.headers['Retry-After']))
        # print('this retry-after is handled by default by the RiotWatcher library')
        # print('future requests wait until the retry-after time passes')
    elif err.response.status_code == 404:
        print('Summoner with that ridiculous name not found.')
    else:
        raise


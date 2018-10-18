from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.forms.models import model_to_dict
from requests_oauthlib import OAuth2Session
from .models import Emblem, Objective, Player
import os, time, zipfile, sqlite3, json, requests

authorization_base_url = 'https://www.bungie.net/en/OAuth/Authorize'
token_url = 'https://www.bungie.net/Platform/App/OAuth/token/'
baseApiUrl = 'https://www.bungie.net/Platform'
apiKey = os.environ.get('API_KEY')
credentials = {'client_id': '22228', 'client_secret': os.environ.get('CLIENT_SECRET')}
module_dir = os.path.dirname(__file__)
platforms = {1: 'xbl', 2: 'psn', 4: 'pc'}

def update_db(db_path, version):
    r = requests.get('https://www.bungie.net/' + db_path)
    if r.status_code == 200:
        with open(os.path.join(module_dir, 'destinydb.zip'), 'wb') as f:
            f.write(r.content)
        zip_ref = zipfile.ZipFile(os.path.join(module_dir, 'destinydb.zip'), 'r')
        zip_ref.extractall(module_dir)
        zip_ref.close()
        try:
            os.remove(os.path.join(module_dir, 'destinydb.zip'))
        except OSError:
            pass
        os.rename(os.path.join(module_dir, os.path.basename(db_path)), os.path.join(module_dir, 'destinydb.sqlite'))

        Objective.objects.all().delete()
        Emblem.objects.all().delete()
        plugs_record = {}
        conn = sqlite3.connect(os.path.join(module_dir, 'destinydb.sqlite'))

        #k = conn.cursor()
        #k.execute("SELECT json FROM DestinyVendorDefinition WHERE json LIKE '%\"vendorIdentifier\":\"VAULT_KIOSK\"%'")
        #item_list = json.loads(k.fetchone()[0])['itemList']

        e = conn.cursor()
        e.execute("SELECT json FROM DestinyInventoryItemDefinition WHERE json LIKE '%\"itemTypeDisplayName\":\"Emblem\"%'")
        for row in e:
            emblem_json = json.loads(row[0])
            if (emblem_json['displayProperties']['name'] != 'Default Emblem'):
                #item_in_list = next((item for item in item_list if item['itemHash'] == emblem_json['hash']), None)
                emblem = Emblem(
                    item_hash = emblem_json['hash'],
                    name = emblem_json['displayProperties']['name'],
                    description = emblem_json['displayProperties']['description'],
                    tier = emblem_json['inventory']['tierTypeName'],
                    icon = emblem_json['displayProperties']['icon'],
                    secondary_icon = emblem_json.get('secondaryIcon'),
                )
                if ('collectibleHash' in emblem_json):
                    emblem.collectible_hash = emblem_json['collectibleHash']
                #if (item_in_list):
                #    emblem.index = item_in_list['vendorItemIndex']
                if ('sockets' in emblem_json):
                    plugs_record[emblem_json['hash']] = []
                    for socket in emblem_json['sockets']['socketEntries']:
                        plugs_record[emblem_json['hash']].extend(p['plugItemHash'] for p in socket['reusablePlugItems'])
                if ('emblemObjectiveHash' in emblem_json):
                    objective_hash = emblem_json['emblemObjectiveHash']
                    o = conn.cursor()
                    o.execute("SELECT json FROM DestinyObjectiveDefinition WHERE json LIKE ?", ('%\"hash\":'+str(objective_hash)+'%',))
                    obj = o.fetchone()
                    obj_json = json.loads(obj[0])
                    objective = Objective(
                        item_hash = objective_hash,
                        description = obj_json['displayProperties']['description'],
                        progress_description = obj_json['progressDescription']
                    )
                    objective.save()
                    emblem.main_objective = objective
                emblem.save()
                if ('objectives' in emblem_json):
                    for objective_hash in emblem_json['objectives']['objectiveHashes']:
                        o = conn.cursor()
                        o.execute("SELECT json FROM DestinyObjectiveDefinition WHERE json LIKE ?", ('%\"hash\":'+str(objective_hash)+'%',))
                        obj = o.fetchone()
                        obj_json = json.loads(obj[0])
                        objective = Objective(
                            item_hash = objective_hash,
                            description = obj_json['displayProperties']['description'],
                            progress_description = obj_json['progressDescription'],
                            main_emblem = emblem
                        )
                        objective.save()
        for main_id, plug_ids in plugs_record.items():
            for plug in Emblem.objects.filter(pk__in=plug_ids):
                plug.main_emblem = Emblem.objects.get(pk=main_id)
                plug.save()
        with open(os.path.join(module_dir, 'lastupdated.json'), 'w') as outfile:
            json.dump({'version': version, 'date': time.time()}, outfile)
        try:
            os.remove(os.path.join(module_dir, 'destinydb.sqlite'))
        except OSError:
            pass

def check_and_update():
    with open(os.path.join(module_dir, 'lastupdated.json'), 'r') as f:
        last_updated = json.load(f)
        r = requests.get(baseApiUrl + '/Destiny2/Manifest/', headers={'x-api-key': apiKey})
        manifest = r.json()['Response']
        version = manifest['version']
        db_path = manifest['mobileWorldContentPaths']['en']
        if (version != last_updated['version']):
            update_db(db_path, version)

def emblem_data():
    data = {'emblems': {}}
    emblems = Emblem.objects.all()
    for emblem in emblems:
        if (emblem.main_emblem == None):
            data['emblems'][emblem.pk] = model_to_dict(emblem)
            if (emblem.main_objective != None):
                data['emblems'][emblem.pk]['main_objective'] = emblem.main_objective
            else:
                del data['emblems'][emblem.pk]['main_objective']
    for emblem in emblems:
        if (emblem.main_emblem != None):
            if ('variants' not in data['emblems'][emblem.main_emblem.pk]):
                data['emblems'][emblem.main_emblem.pk]['variants'] = {}
            data['emblems'][emblem.main_emblem.pk]['variants'][emblem.pk] = model_to_dict(emblem)
        if (emblem.objective_set.count() > 0):
            data['emblems'][emblem.pk]['objectives'] = emblem.objective_set.all()
        if (emblem.objective_set.count() > 1):
            data['emblems'][emblem.pk]['sub_objectives'] = emblem.sub_objectives
    return data['emblems']

def index(request):
    check_and_update()
    return render(request, 'destiny_emblems/index.html', {'emblems': emblem_data()})

def token_saver(request, token):
    request.session['oauth_token'] = token

def search_player(request, player_id):
    bungie = OAuth2Session(credentials['client_id'], state=request.session.get('oauth_state'),
        token=request.session.get('oauth_token'), auto_refresh_url=token_url,
        auto_refresh_kwargs=credentials, token_updater=(lambda token: token_saver(request, token)))
    headers = {'x-api-key': apiKey}
    s = bungie.get(baseApiUrl + '/Destiny2/SearchDestinyPlayer/-1/' + player_id + '/', headers=headers)

    players = s.json()['Response']
    for player in players:
        player['membershipType'] = platforms[player['membershipType']]

    if (len(players) > 1):
        return render(request, 'destiny_emblems/choose_player.html', {'players': players})
    elif (len(players) == 1):
        platform = players[0]['membershipType']
    else:
        raise Http404("Player not found")

    return redirect('destiny_emblems:player', platform=platform, player_id=player_id)

def player(request, platform, player_id):
    if (request.method == "POST"):
        return save_player(request, platform, player_id)

    player_info = emblems = {}
    debug = ''

    membership_type = next(p[0] for p in platforms.items() if p[1] == platform)

    check_and_update()
    bungie = OAuth2Session(credentials['client_id'], state=request.session.get('oauth_state'),
        token=request.session.get('oauth_token'), auto_refresh_url=token_url,
        auto_refresh_kwargs=credentials, token_updater=(lambda token: token_saver(request, token)))
    headers = {'x-api-key': apiKey}

    s = bungie.get(baseApiUrl + '/Destiny2/SearchDestinyPlayer/' + str(membership_type) + '/' + player_id + '/', headers=headers)

    players = s.json()['Response']

    membership_id = players[0]['membershipId']
    p = bungie.get(baseApiUrl + '/Destiny2/' + str(membership_type) + '/Profile/' + str(membership_id) + '/?components=100,200,201,301,800', headers=headers)
    if ('Response' in p.json()):
        response = p.json()['Response']

        player_info['player_id'] = response['profile']['data']['userInfo']['displayName']

        characters = response['characters']['data']
        last_played = '2000-01-00T00:00:00Z'
        player_info['characters'] = []
        for hash, character in characters.items():
            player_info['characters'].append(hash)
            if character['dateLastPlayed'] > last_played:
                last_played = character['dateLastPlayed']
                player_info['active_character'] = character

        p = bungie.get(baseApiUrl + '/GroupV2/User/' + str(membership_type) + '/' + str(membership_id) + '/0/1/', headers=headers)
        clans = p.json()['Response']['results']
        if len(clans) > 0:
            player_info['clan_name'] = clans[0]['group']['name']

        emblems = emblem_data()

        objectives = response['itemComponents']['objectives']['data']
        for hash, objectives_data in objectives.items():
            if 'flavorObjective' in objectives_data:
                emblem = next(
                    (emblem for hash, emblem in emblems.items() \
                        if 'main_objective' in emblem \
                        and emblem['main_objective'].item_hash == objectives_data['flavorObjective']['objectiveHash']
                    ),
                    None)
                if (emblem):
                    emblem['progress'] = objectives_data['flavorObjective']['progress']
        collectibles = response['profileCollectibles']['data']['collectibles']
        for collectible_hash, collectible_data in collectibles.items():
            emblem = next((emblem for hash, emblem in emblems.items() if str(emblem['collectible_hash']) == collectible_hash), None)
            if (emblem):
                if (collectible_data['state'] % 2 == 0):
                    emblem['available'] = True

        for character in player_info['characters']:
            collectibles = response['characterCollectibles']['data'][character]['collectibles']
            for collectible_hash, collectible_data in collectibles.items():
                emblem = next((emblem for hash, emblem in emblems.items() if str(emblem['collectible_hash']) == collectible_hash), None)
                if (emblem):
                    if (collectible_data['state'] % 2 == 0):
                        emblem['available'] = True


    try:
        player_obj = Player.objects.get(membership_type=membership_type, membership_id=membership_id)
    except Player.DoesNotExist:
        player_obj = None

    return render(request, 'destiny_emblems/player.html', {'debug': debug, 'player_info': player_info, 'emblems': emblems, 'player_obj': player_obj})

def save_player(request, platform, player_id):
    status = 401
    response = {}
    destiny_user = request.session.get('destiny_user')
    if (destiny_user):
        if (player_id == destiny_user['display_name'] and platform == platforms[destiny_user['membership_type']]):
            Player.objects.get_or_create(
                membership_type = destiny_user['membership_type'],
                membership_id = destiny_user['membership_id'],
                defaults = {'player_data': json.loads(request.body)['playerData']}
            )
            status = 200
            response = {}
    return HttpResponse(json.dumps(response), content_type='application/json', status=status)

def auth(request):
    bungie = OAuth2Session(credentials['client_id'])
    authorization_url, state = bungie.authorization_url(authorization_base_url)
    request.session['oauth_state'] = state
    return redirect(authorization_url)

def auth_callback(request):
    bungie = OAuth2Session(credentials['client_id'], state = request.session.get('oauth_state'))
    token = bungie.fetch_token(token_url, client_secret=credentials['client_secret'], authorization_response=request.build_absolute_uri())
    request.session['oauth_token'] = token

    headers = {'x-api-key': apiKey}
    s = bungie.get(baseApiUrl + '/User/GetMembershipsById/' + token['membership_id'] + '/-1/' , headers=headers)

    membership = s.json()['Response']['destinyMemberships'][0]
    request.session['destiny_user'] = {
        'display_name': membership['displayName'],
        'membership_type': membership['membershipType'],
        'membership_id': membership['membershipId']
    }

    return redirect('destiny_emblems:player', platform=platforms[membership['membershipType']], player_id=membership['displayName'])

def logout(request):
    request.session.clear()
    return redirect('destiny_emblems:index')

def profile(request):
    bungie = OAuth2Session(credentials['client_id'], state = request.session.get('oauth_state'))
    headers = {'x-api-key': apiKey, 'Authorization': 'Bearer ' + request.session.get('oauth_token')['access_token']}
    r1 = bungie.get(baseApiUrl + '/User/GetMembershipsForCurrentUser/', headers=headers)
    membershipType = 2
    membershipId = '4611686018461991702'
    r2 = bungie.get(baseApiUrl + '/Destiny2/2/Profile/4611686018461991702/?components=100,102,200,201,204,205,300,307,305,500', headers=headers)
    return render(request, 'destiny_emblems/player.html', {'r1': json.dumps(r1.json(), indent=3), 'r2': json.dumps(r2.json(), indent=3)})

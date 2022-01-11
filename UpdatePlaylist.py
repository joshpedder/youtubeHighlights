# -*- coding: utf-8 -*-

# Sample Python code for youtube.playlistItems.insert
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/guides/code_samples#python

import os
import time
from datetime import datetime, timedelta
import json
import schedule

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

def authenticate():
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "Secret_file_key.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    return youtube

def SearchVideos(keyWord,keyChannelId, mustContain, youtubeAuth):

    # Calc todays date minus 1 week and prepare iso format for API query
    my_time = datetime.now() - timedelta(10)
    isotime = my_time.isoformat()
    iso_size = len(isotime)
    isoUpdated = isotime[:iso_size - 7]
    isoUpdated2 = isoUpdated + "Z"

    # --------------------------------------
    # Search for latest videos
    listRequest = youtubeAuth.search().list(
        part="snippet",
        channelId=keyChannelId,
        maxResults=50,
        publishedAfter=isoUpdated2,
        q=keyWord
    )
    listResponse = listRequest.execute()

    dictLen = len(listResponse['items'])
    i = 0
    searchArray = []

    while i < dictLen:
        substring = mustContain
        
        iteritem = listResponse['items'][i]['snippet']['title']
        if substring in iteritem:
            searchArray.append(listResponse['items'][i]['id']['videoId'])
        i += 1
        print(f'This is the search array: {searchArray}')

    return searchArray

def playlistReader(keyPlaylistId,youtubeAuth):
# --------------------------------------
    # list contents on playlist
    playlistItemsRequest = youtubeAuth.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=50,
        playlistId=keyPlaylistId
    )
    playlistItemsResponse = playlistItemsRequest.execute()

    print(playlistItemsResponse)

    arrayLen = len(playlistItemsResponse['items'])
    i = 0

    # print(playlistItemsResponse['nextPageToken'])
# ------------------------------------------
    # Iterate through playlist and populates videos toBeRemoved array
    playlistItemIdArray = []
    toBeRemoved = []
    playlistIdVideoIdDict = {}

    while i < arrayLen:
        playlistItemIdArray.append(playlistItemsResponse['items'][i]['snippet']['resourceId']['videoId'])
        playlistIdVideoIdDict[playlistItemsResponse['items'][i]['id']] = playlistItemsResponse['items'][i]['snippet']['resourceId']['videoId']

        isodate = datetime.fromisoformat((playlistItemsResponse['items'][i]['contentDetails']['videoPublishedAt'])[:-1])
        current = datetime.now()
        final = (isodate - current).total_seconds()
        if final < -604800:
            toBeRemoved.append(playlistItemsResponse['items'][i]['id'])
        print(f'to be removed: {toBeRemoved}')
        i += 1

# NEXT PAGE TOKEN
    while 'nextPageToken' in playlistItemsResponse:
        playlistItemsRequest = youtubeAuth.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=50,
            playlistId="PLpf3D7uUm9XfQJnVRMiF877TbsHqPREsi",
            pageToken=playlistItemsResponse['nextPageToken']
        )
        playlistItemsResponse = playlistItemsRequest.execute()

        print('using next page token now')
        print(playlistItemsResponse)

        arrayLen = len(playlistItemsResponse['items'])
        i = 0

        while i < arrayLen:
            playlistItemIdArray.append(playlistItemsResponse['items'][i]['snippet']['resourceId']['videoId'])
            playlistIdVideoIdDict[playlistItemsResponse['items'][i]['id']] = playlistItemsResponse['items'][i]['snippet']['resourceId']['videoId']

            isodate = datetime.fromisoformat((playlistItemsResponse['items'][i]['contentDetails']['videoPublishedAt'])[:-1])
            current = datetime.now()
            final = (isodate - current).total_seconds()
            if final < -604800:
                toBeRemoved.append(playlistItemsResponse['items'][i]['id'])
            print(f'to be removed: {toBeRemoved}')
            i += 1

    return playlistItemIdArray, toBeRemoved, playlistIdVideoIdDict


def deleteOldVideos(toBeRemoved, youtubeAuth):
# ------------------------------------------
    # Post delete request based on toBeRemoved array
    for x in toBeRemoved:
        removeRequest = youtubeAuth.playlistItems().delete(
            id=x
        )
        removeRequest.execute()
        print(f'Following items have been removed: {x}')
    # print(f'This is the current playlist items: {playlistItemIdArray}')


def addNewVideos(searchArray,playlistItemIdArray,keyPlaylistId,youtubeAuth):
# --------------------------------------
    # Identify what items to be added are not currently in the playlist
    PlaylistIdsToAddArray = []
    for a in searchArray:
        count = 0
        for b in playlistItemIdArray:
            if a == b:
                print(f'{a} matches {b} : Item not to be added')
                count += 1
        if count == 0:
            PlaylistIdsToAddArray.append(a)
    print(f'This the the playlist items to be added : {PlaylistIdsToAddArray}')


    for ids in PlaylistIdsToAddArray:
        print(ids)
# --------------------------------------
    # Sent post request to update the playlist with the new items
    for ids in PlaylistIdsToAddArray:
        request = youtubeAuth.playlistItems().insert(
            part="snippet",
            body={
            "snippet": {
                "playlistId": keyPlaylistId,
                "position": 0,
                "resourceId": {
                "kind": "youtube#video",
                "videoId": ids
                }
            }
            }
        )
        response = request.execute()
        print(f'Video with if {ids} added to playlist Football')

    return playlistItemIdArray

def deleteDuplicates(playlistIdVideoIdDict,youtubeAuth):
    duplicateArray = []
    print(playlistIdVideoIdDict)
    for k,v in playlistIdVideoIdDict.items():
        x = 0
        for k2,v2 in playlistIdVideoIdDict.items():
            if k == k2:
                x = x + 1
            if x > 1:
                duplicateArray.append(k)
                break
        
        for x in duplicateArray:
            request = youtubeAuth.playlistItems().delete(
                id=x
            )
            response = request.execute()
    

def main():

    configJSON = {
    'items': 
        [
            # Football
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Europa League Highlights',
            'channelId' : 'UC4i_9WvfPRTuRWEaWyfKuFw',
            'channelName' : 'BT Sport',
            'playlistName' : 'Football',
            'playlistId' : 'PLpf3D7uUm9XfQJnVRMiF877TbsHqPREsi',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Champions League Highlights',
            'channelId' : 'UC4i_9WvfPRTuRWEaWyfKuFw',
            'channelName' : 'BT Sport',
            'playlistName' : 'Football',
            'playlistId' : 'PLpf3D7uUm9XfQJnVRMiF877TbsHqPREsi',
            },
                        {
            'searchWord' : 'Highlights',
            'mustInclude' : 'FA Cup highlights',
            'channelId' : 'UCW6-BQWFA70Dyyc7ZpZ9Xlg',
            'channelName' : 'BBC Sport',
            'playlistName' : 'Football',
            'playlistId' : 'PLpf3D7uUm9XfQJnVRMiF877TbsHqPREsi',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Premier League Highlights',
            'channelId' : 'UC4i_9WvfPRTuRWEaWyfKuFw',
            'channelName' : 'BT Sport',
            'playlistName' : 'Football',
            'playlistId' : 'PLpf3D7uUm9XfQJnVRMiF877TbsHqPREsi',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'EPL Highlights',
            'channelId' : 'UCNAf1k0yIjyGu3k9BwAg3lg',
            'channelName' : 'Sky Sports Football',
            'playlistName' : 'Football',
            'playlistId' : 'PLpf3D7uUm9XfQJnVRMiF877TbsHqPREsi',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Premier League Highlights',
            'channelId' : 'UCNAf1k0yIjyGu3k9BwAg3lg',
            'channelName' : 'Sky Sports Football',
            'playlistName' : 'Football',
            'playlistId' : 'PLpf3D7uUm9XfQJnVRMiF877TbsHqPREsi',
            },
            # Racing
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Highlights',
            'channelId' : 'UCB_qr75-ydFVKSF9Dmo6izg',
            'channelName' : 'Formula 1',
            'playlistName' : 'Racing',
            'playlistId' : 'PLpf3D7uUm9XdOgabnYA7x7vva1wEtJt9r',
            },
            # American Sports
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Full Game Highlights',
            'channelId' : 'UCYIYXiOsgAsZr0Xvapplz5w',
            'channelName' : 'NFL Hightlights',
            'playlistName' : 'American Sports',
            'playlistId' : 'PLpf3D7uUm9Xexsd_X32gfVrALyRrnyJuy',
            },            
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Full Game Highlights',
            'channelId' : 'UC6yGoFvjKmRAlBfglOxNCGQ',
            'channelName' : 'Hooper Highlights',
            'playlistName' : 'American Sports',
            'playlistId' : 'PLpf3D7uUm9Xexsd_X32gfVrALyRrnyJuy',
            },            
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'NHL Highlights',
            'channelId' : 'UCqFMzb-4AUf6WAIbl132QKA',
            'channelName' : 'MLB',
            'playlistName' : 'American Sports',
            'playlistId' : 'PLpf3D7uUm9Xexsd_X32gfVrALyRrnyJuy',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Highlights',
            'channelId' : 'UCoLrcjPV5PbUrUyXq5mjc_A',
            'channelName' : 'MLB',
            'playlistName' : 'American Sports',
            'playlistId' : 'PLpf3D7uUm9Xexsd_X32gfVrALyRrnyJuy',
            },
            # Other Sports
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Masters',
            'channelId' : 'UCa98aY7eenHS_YhehF-vuEQ',
            'channelName' : 'Sky Sports Golf',
            'playlistName' : 'Other Sports',
            'playlistId' : 'PLpf3D7uUm9Xe0HYGqm2hUt0W_FPslD0KS',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Ryder',
            'channelId' : 'UCa98aY7eenHS_YhehF-vuEQ',
            'channelName' : 'Sky Sports Golf',
            'playlistName' : 'Other Sports',
            'playlistId' : 'PLpf3D7uUm9Xe0HYGqm2hUt0W_FPslD0KS',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Highlights',
            'channelId' : 'UCL5bAcVfbxSAs-UM5f5ncWg',
            'channelName' : 'Guinness Six Nations',
            'playlistName' : 'Other Sports',
            'playlistId' : 'PLpf3D7uUm9Xe0HYGqm2hUt0W_FPslD0KS',
            },
            {
            'searchWord' : 'Highlights',
            'mustInclude' : 'Highlights',
            'channelId' : 'UChuLeaTGRcfzo0UjL-2qSbQ',
            'channelName' : 'World Surf League',
            'playlistName' : 'Other Sports',
            'playlistId' : 'PLpf3D7uUm9Xe0HYGqm2hUt0W_FPslD0KS',
            },
        ]
    }

    youtube=authenticate()

    def initalise():
        for i in configJSON['items']:
            searchArray=SearchVideos(i['searchWord'], i['channelId'],i['mustInclude'],youtube)
            playlistReaderReturn = playlistReader(i['playlistId'],youtube)
            playlistItemIdArray = playlistReaderReturn[0]
            toBeRemoved = playlistReaderReturn[1]
            playlistIdVideoIdDict = playlistReaderReturn[2]
            deleteOldVideos(toBeRemoved,youtube)
            addNewVideos(searchArray,playlistItemIdArray,i['playlistId'],youtube)
            deleteDuplicates(playlistIdVideoIdDict,youtube)

    schedule.every().day.at("21:15").do(initalise)

    while True:
        schedule.run_pending()
        time.sleep(1)



if __name__ == "__main__":
    main()

# Updates
#   - Add to github
#   - put on raspi linked to github
#   - specify intro or outro length to be removed
#   - Import config from a JSON file
#   - Create frontend to update whats in the config JSON
#   - Create email news letter to update on start of sport conpetitions
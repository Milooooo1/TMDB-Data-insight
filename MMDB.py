# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 20:12:03 2021

@author: Milo
"""

from datetime import date
import math
import requests
import json

class MMDB:
    
    def __init__(self, excelDF, movieData, API_KEY, fileSaveDir):
        '''
        Parameters
        ----------
        excelDF : xlsx
            Excel Document with a row "Year of release"
        movieData : json
            json file in which the movie data is present or needs to be stored. 

        '''
        self.excelDF = excelDF
        self.movieData = movieData
        self.API_KEY = API_KEY
        self.fileSaveDir = fileSaveDir
        self.missing_data = []
        self.actorDict    = dict()
        self.actorNumDict = dict()
        self.genreNumDict = dict()
        self.directorData = dict()
        self.directorDict = dict()
        self.moviesByYear = dict()
        
    def update(self):
        '''
        Goes through the excel document, searches for every movie and adds it data to the json file
        Movie titles must be the exact titles (spaces and capital letters don't matter)
        '''
        for index, row in self.excelDF.iterrows():
            search = (str(row['Movie Title']))
            if (search + " " + str(row['Year of release'])) in self.movieData.keys():
                #Data already known in json file
                pass
            else:
                #No data known, get it from the API and add it to the json file
                url = "https://api.themoviedb.org/3/search/movie?api_key=" + str(self.API_KEY) + "&query=" + search               
                response = requests.request("GET", url)
        
                results = response.json()
                
                #Find Movie ID
                movie_id = 500 #500 (fight club) as a place holder
                found = False
                for result in results['results']:
                    if search.lower().replace(" ", "") == result['title'].lower().replace(" ", ""):
                        movie_id = result['id']
                        res = result
                        found = True
                        break
                if found == False:
                    print("No movie data found for: " + str(search))
                    self.missing_data.append(search)
                    continue
        
                #Get all the movie details
                url = "https://api.themoviedb.org/3/movie/" + str(movie_id) + "?api_key=" + str(self.API_KEY)+"&append_to_response=credits"
                response = requests.request("GET", url)
                cast_results = response.json()
        
        
                #Filter results 
                res = cast_results
                res.pop('adult')
                res.pop('backdrop_path')
                res.pop('belongs_to_collection')
                res.pop('homepage')
                res.pop('overview')
                res.pop('poster_path')
                res.pop('production_companies')
                res.pop('production_countries')
                res.pop('spoken_languages')
                res.pop('status')
                res.pop('video')
                res.pop('vote_count')
                
                for i, member in enumerate(res['credits']['crew']):
                    if member['job'] == "Director":
                        res['director'] = res['credits']['crew'][i]
                del(res['credits']['crew'])
                
                self.movieData[search + " "  + str(row['Year of release'])] = res
                print("NEW data added for movie: " + str(search))
            
        self.saveData()
                
    def saveData(self):
        '''
        Save all the data to json files
        '''
        with open(str(self.fileSaveDir) + '\\movie_data.json', 'w') as outfile:
            json.dump(self.movieData, outfile)
        with open(str(self.fileSaveDir) + '\\actors_sorted.json', 'w') as outfile:
            json.dump(self.actorNumDict, outfile)
            print("Data Saved")
    
    
    def sortDict(self, dictToSort):
        sorted_dict = {}
        sorted_keys = sorted(dictToSort, key=dictToSort.get)
        
        for w in sorted_keys:
            sorted_dict[w] = dictToSort[w]
            
        return sorted_dict
    
    
    def getActorData(self):
        self.actorDict = {}
        self.actorNumDict = {}
        for movie in self.movieData.keys():
            for actor in self.movieData[movie]['credits']['cast']:
                if actor['name'] in self.actorDict.keys():
                    self.actorNumDict[actor['name']] = self.actorNumDict[actor['name']] + 1
                    self.actorDict[actor['name']]['movies'].append(self.movieData[movie]['title'])
                    self.actorDict[actor['name']]['characters'].append(actor['character'])
                else:
                    self.actorNumDict[actor['name']] = 1
                    self.actorDict[actor['name']]    = { 'id'         : actor['id'], 
                                                         'movies'     : [self.movieData[movie]['title']], 
                                                         'characters' : [actor['character']]}
        
        sorted_dict = {}
        sorted_keys = sorted(self.actorNumDict, key=self.actorNumDict.get)
        
        for w in sorted_keys:
            sorted_dict[w] = self.actorNumDict[w]
            
        self.actorNumDict = sorted_dict
        
        return self.actorNumDict, self.actorDict
    
    
    def getActorSpecificData(self, actorName):
        self.getActorData()
        
        try:
            return self.actorDict[actorName], len(self.actorDict[actorName]['movies'])
        except Exception:
            return "Couldn't find any data on actor: " + str(actorName) 
    
    
    def getGenreData(self):
        for movie in self.movieData.keys():
            for genre in self.movieData[movie]['genres']:
                if genre['name'] in self.genreNumDict.keys():
                    self.genreNumDict[genre['name']] += 1
                else:
                    self.genreNumDict[genre['name']] = 1
        
        sorted_dict = {}
        sorted_keys = sorted(self.genreNumDict, key=self.genreNumDict.get)
        
        for w in sorted_keys:
            sorted_dict[w] = self.genreNumDict[w]
            
        self.genreNumDict = sorted_dict
        
        
        return self.genreNumDict
    
    
    def getTotalWatchtime(self):
        self.totalWatchTime = 0
        self.totalMovies = 0
        for index, row in self.excelDF.iterrows():
            search = (str(row['Movie Title'])) + " " + (str(row['Year of release']))
            try:
                multiplier = (int(row['Times Watched']))
            except Exception:
                multiplier = 1
            
            self.totalMovies += multiplier
            try:
                self.totalWatchTime += (self.movieData[search]['runtime'] * multiplier)
            except Exception:
                self.totalWatchTime += 0
        
        return self.totalWatchTime, self.totalMovies, index


    def getDirectorData(self):
        self.directorData, self.directorDict = {}
        for movie in self.movieData.keys():
            try:
                if self.movieData[movie]['director']['name'] in self.directorData.keys():
                    self.directorData[self.movieData[movie]['director']['name']] += 1
                    self.directorDict[self.movieData[movie]['director']['name']]['movies'].append(movie)
                    self.directorDict[self.movieData[movie]['director']['name']]['num'] += 1
                else:
                    self.directorData[self.movieData[movie]['director']['name']] = 1
                    self.directorDict[self.movieData[movie]['director']['name']] = {'movies' : [movie]}
                    self.directorDict[self.movieData[movie]['director']['name']]['num'] = 1
            except Exception:
                print("No Director found for movie: " + str(movie))

        sorted_dict = {}
        sorted_keys = sorted(self.directorData, key=self.directorData.get)
        
        for w in sorted_keys:
            sorted_dict[w] = self.directorData[w]
            
        self.directorData = sorted_dict

        return self.directorData, self.directorDict 

    def getNumMoviesByYear(self):
        self.moviesByYear = {}
        for movie in self.movieData.keys():
            if self.movieData[movie]['release_date'][:4] in self.moviesByYear.keys():
                self.moviesByYear[self.movieData[movie]['release_date'][:4]] += 1
            else:
                self.moviesByYear[self.movieData[movie]['release_date'][:4]] = 1
        
        self.moviesByYear = self.sortDict(self.moviesByYear)
        
        return self.moviesByYear                     
    
    def searchActor(self, actor):
        url = "https://api.themoviedb.org/3/search/person?api_key=" + str(self.API_KEY) + "&query=" + actor               
        response = requests.request("GET", url)
        actor_results = response.json()
        found = False
        for result in actor_results['results']:
            if result['name'].replace(" ", "").lower() == actor.replace(" ", "").lower() and result['known_for_department'] == "Acting":
                actorID = result['id']
                found = True
            else:
                continue        
        
        if found == False:
            print("Nothing found for actor: " + actor)
            return
        
        url = "https://api.themoviedb.org/3/person/" + str(actorID) + "?api_key=" + str(self.API_KEY) +"&append_to_response=movie_credits"
        response = requests.request("GET", url)
        actor_results = response.json()
        
        
        today = date.today()
        birthday = date(int(actor_results['birthday'][:4]), int(actor_results['birthday'][5:7]), int(actor_results['birthday'][8:10]))
        age = today - birthday
        
        print("Actor: " + actor_results['name'])
        print(str(actor_results['name']) + " is " + str(math.floor(age.days / 365)) + " years old")
        
        watched        = []
        not_watched    = []
        to_be_released = []
        
        for movie in actor_results['movie_credits']['cast']:
            try:
                search = str(movie['title'] + " " + movie['release_date'][:4])                
                if not (movie['release_date'] == ""):
                    not_watched.append(search)
                    
            except:
                to_be_released.append(movie['title'])
                continue
            
        watched = self.getActorSpecificData(actor_results['name'])[0]['movies']
        for i in range(len(watched)):
            for j in range(len(not_watched)):
                if not_watched[j].lower().replace(" ", "") == watched[i].lower().replace(" ", ""):
                    not_watched.pop(j)
                else:
                    continue
        
        print("You've watched: " + str(len(watched)) + " movies starring " + str(actor_results['name']))
        
        print()    
        print("All the movies you've watched starring: " + str(actor_results['name']))
        for i in range(len(watched)):
            print(watched[i])
        
        print()
        print("All the movies you have not watched starring: " + str(actor_results['name']))
        for i in range(len(not_watched)):
            line_new = f"{not_watched[i][:-4]:<70}{not_watched[i][-4:]:>30}"
            print(line_new)
        
        print()
        print(str(actor_results['name']) + " is playing in the following movies that are yet to be released:")
        for i in range(len(to_be_released)):
            print(to_be_released[i])
        
    
'''
Possible Additions:
    My scoring average difference
    Total amount of money spent on the movies I watched
    Add support for queries about anything, also movies I haven't watched
'''
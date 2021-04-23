# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 20:12:03 2021

@author: Milo
"""

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
                url = "https://api.themoviedb.org/3/movie/" + str(movie_id) + "?api_key= " + str(self.API_KEY)+"&append_to_response=credits"
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
                    
    
'''
Possible Additions:
    My scoring average difference
    Total amount of money spent on the movies I watched
    Most watched directors
    Start the automation of graphs and word clouds
'''

# in a new environment we have to do a pip install httplib2, pip install uritemplate, pip install oauth2client

import httplib2 
import pprint
import sys
import json
import csv
import requests
import urllib2
import urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from oauth2client.tools import argparser

# Enter your Google Developer Project number
PROJECT_NUMBER = '288816571005'
PROJECT_ID = 'gitarchiveproj'
FLOW = flow_from_clientsecrets('/Users/USEREN/Dropbox/HEC/Summer Project/GoogleAPIKeys/client_secrets.json',
                               scope='https://www.googleapis.com/auth/bigquery')
NULL = 0
REPOLIST_CSV = '/Users/USEREN/Dropbox/HEC/Summer Project/Data/RepoList2014.csv'

def query_gitarchive(query_command):
# Define a storage object which can be accessed by multiple processes or threads.
  storage = Storage('bigquery_credentials.dat')
  credentials = storage.get()

  flags = argparser.parse_args(args=[])
# flags is a bunch of parameters necessary for run_flow(). The contents of flags are : 
# Namespace(auth_host_name='localhost', auth_host_port=[8080, 8090], logging_level='ERROR', noauth_local_webserver=False)
 
  if credentials is None or credentials.invalid:

#The run() function is called from your application and runs through all the steps to obtain credentials.
#It takes a Flow argument and attempts to open an authorization server page in the user's default web browser. The server asksthe user to grant your application access to the user's data.      
#Args: flow: Flow, an OAuth 2.0 Flow to step through. storage: Storage, a Storage to store the credential in.flags: argparse.ArgumentParser, the command-line flags.
      
      credentials = run_flow(FLOW, storage,flags) #Storage is the object where the credentials retruned will be stored 
      print "credentials invalid"

# class httplib2.Http([cache=None][, timeout=None]) The class that represents a client HTTP interface. The cache parameter is either the name of a directory to be used as a flat file cache, or it must an object that implements the required caching interface. The timeout parameter is the socket level timeout. 
  http = httplib2.Http()
  http = credentials.authorize(http)
#Use the authorize() function of the Credentials class to apply necessary credential headers to all requests made by an httplib2.Http instance:
#Before you can make requests, you first need to initialize an instance of the Google Compute Engine service using the API client library's build method: 
  
  bigquery_service = build('bigquery', 'v2', http=http)

  try:
    query_request = bigquery_service.jobs()
    query_data = {
    'query': (query_command)
    }

    query_response = query_request.query(projectId= PROJECT_ID,body=query_data).execute()
    return query_response


  except HttpError as err:
    print 'Error in query:', pprint.pprint(err.content)
    return NULL
    
  except AccessTokenRefreshError:
    print ("Credentials have been revoked or expired, please re-run"
           "the application to re-authorize")
    return NULL

def get_repo(search_url):
   
    r = requests.get(search_url, auth=('randomeshwar', 'rand276eshwar'))
    print r.status_code
    print r.headers['X-RateLimit-Remaining']
        
    if r.status_code == 200 :
        json_values = r.json()
        search_count = json_values['total_count']
        print 'Total search result count =', search_count
        i=0

#Capture the important fields of the repositories in CSV format
        with open(REPOLIST_CSV, 'wb') as git_repo:
            while i<search_count :
                items_values = json_values['items'][i]
                repo_licence = 'LicenceName'
                license_url = items_values['url']+'/license'
                
                parsed_url = urlparse.urlparse(license_url) # check if the url schema is correct
                
                if bool(parsed_url.scheme) == 0 : 
                    repo_licence = 'URL_Error'
                   
                else:
                    r = requests.get(license_url, auth=('km-poonacha', 'rand276eshwar'))
            #       print r.status_code
            #       print r.headers['content-type']
            #       print r.headers['X-RateLimit-Limit']
                    print r.headers['X-RateLimit-Remaining']
#print items_values['id'], items_values['name'], items_values['created_at']
                    if r.status_code == 200 :
                        values = r.json()
                        repo_licence = str(values['license']['name'])
                    elif r.status_code == 404 : 
                        repo_licence = str("Not Found")
                    else: 
                        repo_licence = str("Unknown Error")
                        
                git_archive_write = csv.writer(git_repo)
            
                git_archive_write.writerow([items_values['id'],
                                            items_values['name'],
                                            items_values['owner']['login'],
                                            items_values['language'],
                                            items_values['created_at'],
                                            items_values['pushed_at'],
                                            items_values['stargazers_count'],
                                            items_values['watchers_count'],
                                            items_values['open_issues'],
                                            items_values['forks_count'],
                                            items_values['url'],
                                            repo_licence])
                i=i+1
                
    else : return 0

  
  
        
def main():
  
# the search url for running the GitHub search and finding the relevant repos 
  search_url = "https://api.github.com/search/repositories?q=created:2014-01-01..2015-01-01%20stars:%3E15000%20fork:false%20forks:%3E1%20&sort=stars&order=asc"
# Search GitHUb and get the list of repos. The repos are filled into a CSV (RepoList2014.csv)
  return_code = get_repo(search_url)
# If error in search return from main  
  if return_code == 0:
      print "Error running the search and getting the repos. Returning from main()"
      return 
   
# Read the repo list
  with open(REPOLIST_CSV, 'rb') as repolist_read:
    repolist_data = csv.reader(repolist_read) 
  
    for row in repolist_data:        
        repo_name = row[1]
        repo_owner = row[2]
        print repo_name,repo_owner
# Let the repodetails be the first line of the CSV       
        with open('/Users/USEREN/Dropbox/HEC/Summer Project/Data/EventList2014.csv', 'ab' ) as csv_append:
          event_append = csv.writer(csv_append)
          event_append.writerow(row) 

# the query to be executed on BigQuery database   
          query = "SELECT  actor, type, repository_created_at, repository_owner, repository_pushed_at, created_at FROM [githubarchive:year.2014] WHERE repository_owner = '"+repo_owner+"' AND repository_name = '"+repo_name+"' AND repository_created_at > '2014-01-01T00:00:00Z' AND (type = 'PushEvent' OR type = 'PullRequestEvent' OR type = 'PullEvent' OR type = 'CreateEvent' OR type = 'DownloadEvent') LIMIT 10000"
          print query
          query_response = query_gitarchive(query)                
 
# In case there is an error in query or credentials appropriate message is displayed the function returns a NULL
         
          if query_response == NULL : 
            print "Returning from main(). Check if the query syntax is correct and if the credentials sent to BigQuery is accurate"
            return 
# If query i successful print the number of rows             
          total_rows = query_response['totalRows']   
          print ("Total rows from query =" + total_rows + ".")
          i = 0 
      
# On successful query, the number of rows from the query is printed and the CSV is appended with the data    
# with open('/Users/medapa/Dropbox/HEC/Summer Project/Data/EventList2014.csv', 'a') as csv_append:
          while i < (int(total_rows)) :
            row_data = query_response['rows'][i]
            j = 0
            event_data = ['']
# J indicates the 6 fields of event data that is being captured
            while j < 6:

              event_data.append(row_data['f'][j]['v'])
              j=j+1 
           
            event_append.writerow(event_data) 
            i = i + 1                      
# Calculate degree of superposition  
          if total_rows == 0:
            deg_super = 0
            num_actors = 1
            event_append.writerow('degree_super',deg_super,'no_actor',num_actors)
                
          else:
            for  
                           

if __name__ == '__main__':
  main()

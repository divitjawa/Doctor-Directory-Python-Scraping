#!/usr/bin/env python
# coding: utf-8

# In[184]:


# import library
from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import numpy as np


# In[185]:


# takes in baseURL and first url as arguments
def returnDFfromAPIStanford(baseURL, url):
    req=requests.get(url)
    content=req.text
    # clean up response and convert to json
    content = content.replace('search_callback  ( ', '')
    content = content[:-1]
    apiJsonObject = json.loads(content)
    doctorData = apiJsonObject['results']['data']
    nextURLQuery = apiJsonObject['pagination']['next']
    nextURL = baseURL + nextURLQuery
    names = []
    isAcceptingNewPatients = []
    clinicAddresses = []
    clinicNames = []
    ratings = []
    specialties = []
    while len(nextURLQuery) > 0: 
        tempSpecialties = []
        for doctor in doctorData:
            names.append(doctor['displayName'])
            isAcceptingNewPatients.append(doctor['isAcceptingNewPatients'])
            currRating = doctor['avg_rating']
            ratings.append(float(currRating) if len(currRating) != 0 else '')
            currFocuses = []
            for focus in doctor['clinicalFocuses']:
                currFocuses.append(focus['value'])        
                tempSpecialties.append(currFocuses)

            currAddressList = []
            currClinicNames = []
            for clinic in doctor['contactInfo']:
                currAddressList.append((clinic['address'] + ' ' + clinic['zip']).replace(',', ' '))
                currClinicNames.append(clinic['OfficeName'])
            clinicAddresses.append(currAddressList)
            
            # go through the populated address list for this doctor, check if the adjacent address zip code is the same
            # and if address is shorter, remove that address and corresponding clinic name since it was a duplicate without
            # "suite" number of the clinic
            for i in range(1, len(currAddressList)):
                currAddressInList = currAddressList[i] if len(currAddressList[i]) != 0 else ''
                previousAddressInList = currAddressList[i - 1] if len(currAddressList[i - 1]) != 0 else ''
                if((len(currAddressInList) > 0) & (len(previousAddressInList) > 4)):
                    if (currAddressInList[-4] == previousAddressInList[-4]):
                        if (len(currAddressInList) > len(previousAddressInList)):
                            currAddressList[i - 1] = currAddressList[i - 1].replace(previousAddressInList, '')
                            currClinicNames[i - 1] = currClinicNames[i - 1].replace(currClinicNames[i - 1], '')
                        else:
                            currAddressList[i] = currAddressList[i].replace(currAddressInList, '')
                            currClinicNames[i] = currClinicNames[i].replace(currClinicNames[i], '')
            clinicNames.append(currClinicNames)
        # convert list to string separated by comma
        for currSpecialty in tempSpecialties:
            currSpecialty = ', '.join(currSpecialty)
            specialties.append(currSpecialty)
            
        # get the next URL and keep processing till the end
        nextURLQuery = ''
        nextURL = ''
        nextURLQuery = apiJsonObject['pagination']['next']
        nextURL = baseURL + nextURLQuery[1:]
        req=requests.get(nextURL)
        content=req.text
        content = content.replace('search_callback  ( ', '')
        content = content[:-1]
        apiJsonObject = json.loads(content)
        doctorData = apiJsonObject['results']['data']
#         print(nextURL)
    zipped = list(zip(names, isAcceptingNewPatients, clinicAddresses, clinicNames, ratings, specialties))
    df_combined = pd.DataFrame(zipped, columns=['Name', 'Accepting New Patients?', 'Clinic Address', 'Clinic Name', 'Rating', 'Specialties'])
    return df_combined


# In[186]:


# Request to website and download HTML contents
# primary care list of Stanford health 
url='https://stanfordhealthcare.org/bin/api/v1/search.json?do=organic_phys&x1=sp_prim_care_phy&?callback=axiosJsonpCallback2;do=organic_phys;i=1;q1=true;sp_c=20;sp_s=sp_isapp_lastName;x1=sp_prim_care_phy'
baseURL = 'https://stanfordhealthcare.org/bin/api/v1/search.json?do=organic_phys&x1=sp_prim_care_phy&'
primaryCareStanfordDF = returnDFfromAPIStanford(baseURL, url)
# in case we want to create a separate row for each address for each doctor
# colsToExpand = ['Clinic Address','Clinic Name']
# primaryCareStanfordDF = primaryCareStanfordDF.explode(colsToExpand)
# primaryCareStanfordDF.to_csv('primaryCareStanfordDF.csv')


# In[188]:


# Request to website and download HTML contents
# specialist data of Stanford health
# NOTE: This command takes about 3-4 minutes to run since it's going through 115 pages and it takes 1-2 seconds for each API call
url='https://stanfordhealthcare.org/bin/api/v1/search.json?do=organic_phys&x1=sp_spec_care_phy&?callback=axiosJsonpCallback2;do=organic_phys;i=1;q1=true;sp_c=20;sp_s=sp_isapp_lastName;x1=sp_spec_care_phy'
baseURL = 'https://stanfordhealthcare.org/bin/api/v1/search.json?do=organic_phys&x1=sp_spec_care_phy&'
specialistStanfordDF = returnDFfromAPIStanford(baseURL, url)
# colsToExpand = ['Clinic Address','Clinic Name']
# specialistStanfordDF = specialistStanfordDF.explode(colsToExpand)
# specialistStanfordDF.to_csv('df2.csv')


# In[192]:


# John Muir Medical
def returnDFfromAPIJohnMuir(url):
    names = []
    ratings = []
    clinicAddresses = []
    clinicNames = []
    isAcceptingNewPatients = []
    specialties = []
    
    req2 = requests.get(url)
    content2 = req2.text
    JohnMuirJsonResp = json.loads(content2)
    JohnMuirDoctorData = JohnMuirJsonResp['filteredSet']
    for doctor in JohnMuirDoctorData:
        tempSpecialties = []
        names.append(doctor['doctor']['firstName'] + ' ' + doctor['doctor']['lastName'])
        ratings.append(doctor['doctor']['rating'])
        isAcceptingNewPatients.append(not(doctor['doctor']['isPracticeClosed']))
        currDoctorSpecialties = []
        for currSpecialty in doctor['doctor']['specialties']:
            currDoctorSpecialties.append(currSpecialty['name'])
        for currExpertise in doctor['doctor']['expertises']:
            currDoctorSpecialties.append(currExpertise['name'])
        tempSpecialties.append(currDoctorSpecialties)
        officeList = []
        for currSpecialty in tempSpecialties:
            currSpecialty = ', '.join(currSpecialty)
            specialties.append(currSpecialty)
        for office in doctor['sortedOfficesByDistance']:
            currOfficeAddress = (office['office']['addressLineOne'] + ' ' + office['office']['addressLineTwo'] 
                                 + office['office']['city'] + ' ' + office['office']['state'] + ' ' + office['office']['zip'])
            officeList.append(currOfficeAddress)
        clinicAddresses.append(officeList)
        clinicNames.append('')
    zipped = list(zip(names, isAcceptingNewPatients, clinicAddresses, clinicNames, ratings, specialties))
    johnMuirDatadf = pd.DataFrame(zipped, columns=['Name', 'Accepting New Patients?', 'Clinic Address', 'Clinic Name', 'Rating', 'Specialties'])
    return johnMuirDatadf
    # print(specialties)


# In[193]:


johnMuirPrimaryCareAPI = 'https://www.johnmuirhealth.com/fad/api/searchResultsWithOffset?name=&specialty=&providerTypeNursePractitioner=on&providerTypePhysicianAssistant=on&jmpn=on&jmhpnRenewed=on&language=&groups=&offset=0&max=46&sortBy=1'
primaryCareJohnMuirDF = returnDFfromAPIJohnMuir(johnMuirPrimaryCareAPI)
# primaryCareJohnMuirDF = primaryCareJohnMuirDF.explode('Clinic Address')
# primaryCareJohnMuirDF.to_csv('primaryCareJohnMuirDF.csv')


# In[194]:


johnMuirSpecialistAPI = 'https://www.johnmuirhealth.com/fad/api/searchResultsWithOffset?name=&specialty=&providerTypeDoctor=on&jmpn=on&jmhpnRenewed=on&language=&groups=&offset=0&max=883&sortBy=1'
specialistJohnMuirDF = returnDFfromAPIJohnMuir(johnMuirSpecialistAPI)
# specialistJohnMuirDF = specialistJohnMuirDF.explode('address')
# specialistJohnMuirDF.to_csv('specialistJohnMuirDF.csv')


# In[195]:


primaryCareCombinedDF = pd.concat([primaryCareStanfordDF, primaryCareJohnMuirDF], ignore_index=True)
primaryCareCombinedDF['isPrimaryCare'] = 'true'
# primaryCareCombinedDF.to_csv('primaryCareCombinedDF.csv')


# In[196]:


specialistCombinedDF = pd.concat([specialistStanfordDF, specialistJohnMuirDF], ignore_index=True)
specialistCombinedDF.to_csv('specialistCombinedDF.csv')
specialistCombinedDF['isPrimaryCare'] = 'false'
# specialistCombinedDF.to_csv('specialistCombinedDF.csv')


# In[197]:


combined_df = pd.concat([primaryCareCombinedDF, specialistCombinedDF], ignore_index=True)
combined_df.to_csv('combined_df.csv')


# In[198]:


combined_df.dtypes


# In[199]:


# Data cleaning. Delete rows with empty data, change data type of cols, replace certain values
combined_df['Name'] = combined_df['Name'].astype('string')
combined_df['Accepting New Patients?'] = combined_df['Accepting New Patients?'].astype('bool')
combined_df['Clinic Name'] = combined_df['Clinic Name'].astype('string')
combined_df['Clinic Address'] = combined_df['Clinic Address'].astype('string')
combined_df['Specialties'] = combined_df['Specialties'].astype('string')
combined_df['Rating'] = combined_df['Rating'].replace('', np.nan)
combined_df['Rating'] = combined_df['Rating'].astype('float')
combined_df['isPrimaryCare'] = combined_df['isPrimaryCare'].astype('string')
combined_df = combined_df[combined_df['Name'] != '']
combined_df = combined_df[combined_df['Clinic Address'] != "[]"]

combined_df.shape


# In[203]:


def searchDF(searchString):
    searchString = searchString
    if searchString == 'primary care':
        queriedDf = combined_df.loc[combined_df['isPrimaryCare'] == 'true']
    else:
        queriedDf = combined_df[combined_df['Name'].str.contains(searchString) | combined_df['Clinic Address'].str.contains(searchString) 
                                | combined_df['Clinic Name'].str.contains(searchString) | combined_df['Specialties'].str.contains(searchString)]
    queriedDf = queriedDf.sort_values(['Rating', 'Name'], ascending=[False, True])
    queriedDf['Rating'] = queriedDf['Rating'].astype('string')
    queriedDf['Rating'] = queriedDf['Rating'].replace(np.nan, 'No Rating')
    return queriedDf if len(queriedDf) > 0 else 'No Results. Search is case-sensitive. Please check the query.' 


# In[204]:


searchDF('susan')


# In[ ]:





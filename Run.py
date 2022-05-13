#######################################################################################################
#######################################################################################################

# Introduction into Programming

#Running Dinner

#######################################################################################################
#######################################################################################################


import streamlit as st
import pandas as pd

import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from geopy.geocoders import Nominatim
from geopy.distance import great_circle
import random

import smtplib
from email.message import EmailMessage

import git

#The class Data is accessing the google spreadsheet data by using the credentials.json and the toke.pickle files as access tokens
class Data:
    
    def __init__(self,SCOPES,SPREADSHEET_ID,DATA_TO_PULL):
        self.SCOPES = SCOPES
        self.SPREADSHEET_ID = SPREADSHEET_ID
        self.DATA_TO_PULL = DATA_TO_PULL
        
    #google api access   
    def gsheet_api_check(self,SCOPES):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds
    
    #data pull from the excel spreadsheet and storing it into a dictionary
    def pull_sheet_data(self):
        creds = self.gsheet_api_check(self.SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=self.DATA_TO_PULL).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            rows = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID,
                                      range=self.DATA_TO_PULL).execute()
            data = rows.get('values')
            print("COMPLETE: Data copied")
            df = pd.DataFrame(data[1:], columns=data[0])
            df = df.to_dict(orient="index")
            return df

        
# Running Dinner Algorithm that imports the data from the spreadsheet by calling the class Data, 
# transforming the addresses into distances to the final destination and finally randomly distributing the teams to final teams of 3
class algorithm:
    
    def __init__(self,SCOPES,SPREADSHEET_ID,DATA_TO_PULL,final_location):
        self.SCOPES = SCOPES
        self.SPREADSHEET_ID = SPREADSHEET_ID
        self.DATA_TO_PULL = DATA_TO_PULL
        self.final_location = final_location
        
    # calling the class Data to get the data
    def get_data(self):
        RD_data = Data(self.SCOPES, self.SPREADSHEET_ID, self.DATA_TO_PULL)
        data = RD_data.pull_sheet_data()
        return data
    
    # getting the latitude and longitude from the final location of the Running Dinner
    def final(self):
        #set up geolocator application
        geolocator = Nominatim(user_agent="RunningDinner")

        #set center of map
        #start_location = "Rua do Forno do Tijolo 29D Lisboa"
        final_location_code = geolocator.geocode(self.start_location)
        final_location_lat_long = (final_location_code.latitude,final_location_code.longitude)
        return final_location_lat_long
    
    # getting the latitude and longitude of each address + calculating distance (distinction between whether or not geopy can read the address or not)
    def geo(self):    
    
        #set up geolocator application
        geolocator = Nominatim(user_agent="RunningDinner")
        
        #miles to kilometer variable
        kilometer_miles=1.60934
        
        #data collection
        data = algorithm.get_data(self)

        #get latitude and longitude from a team and calculate distance to center of map
        for key, item in data.items():
            end_location =data[key]["Address"]
            
            #end_location_code = geolocator.geocode(end_location)
            if geolocator.geocode(end_location) == None:
                help_lat = -89.9999
                help_long = -179.9999
                end_location_lat_long = (help_lat,help_long)
                distance = (great_circle(algorithm.final(self), end_location_lat_long).miles)*kilometer_miles
                data[key]["latitude"] = help_lat
                data[key]["longitude"] = help_long
                data[key]["distance"] = distance
            else:
                end_location_code = geolocator.geocode(end_location)
                end_location_lat_long = (end_location_code.latitude,end_location_code.longitude)
                distance = (great_circle(algorithm.final(self), end_location_lat_long).miles)*kilometer_miles
                data[key]["latitude"] = end_location_lat_long[0]
                data[key]["longitude"] = end_location_lat_long[1]
                data[key]["distance"] = distance
    
        #create a pandas table
        df = pd.DataFrame.from_dict(data)
        dataT = df.transpose()
        
        return dataT
    
    # running dinner algorithm to randomly create final teams of 3 by distance  
    def team(self):
        
        dataT = algorithm.geo(self)
        wrong_address = pd.DataFrame()
        wrong_address = dataT[(dataT["latitude"] == -89.9999) & (dataT["longitude"] == -179.9999)]
        if wrong_address.shape[0] != 0:
            dataT = dataT[(dataT["latitude"] != -89.9999) & (dataT["longitude"] != -179.9999)]
            dataT.reset_index(drop=True, inplace=True)
            wrong_address.reset_index(drop=True, inplace=True)
        else:
            dataT = dataT
        
        #filter out the teams that are to much
        lostData = pd.DataFrame()
        
        if len(dataT) % 3 == 2:
            lostData = dataT.tail(2)
            dataT = dataT.iloc[:-2 , :]
            lostData.reset_index(inplace=True)
        elif len(dataT) % 3 == 1:
            lostData = dataT.tail(1)
            dataT = dataT.iloc[:-1 , :]
            lostData.reset_index(inplace=True)
        else:
            dataT=dataT
           
        #create 3 quantiles
        dataT["TeamID"]=dataT.index
        dataT["Group"] = pd.qcut(dataT["distance"],3,labels=[1,2,3])
        dataT=dataT.sort_values(["Group","distance"])
        
        
        #distribute the teams into its final teams by a random algorythm
        x=[1,2,3]
        final_dict={}
               
        for v in x:
            groupv=dataT[dataT["Group"]==v]
            list_v=list(groupv["TeamID"])

            i=len(dataT)
            u=1
            while i>0: 
                random_v=random.choice(list_v)
                list_v.remove(random_v)
                final_dict[random_v]=u
                i-=3
                u+=1
        
        dataT['FinalTeam'] = dataT['TeamID'].map(final_dict)
        dataT=dataT.sort_values("FinalTeam")
        
        dataT_concat = pd.concat([dataT, lostData, wrong_address])
        dataT_concat.reset_index(drop=True, inplace=True)
        return dataT_concat

    

#######################################################################################################
#######################################################################################################

#Interface with Streamlit

#######################################################################################################
#######################################################################################################

# set page configurations to wide and expand the sidebar when opening the page    
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)
st.write("# Running Dinner")

#####################################
#pre set input for the classes

SCOPES=['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1C1Q7QQ8ZVhCP1ShHdmds6N2kxr1BX8RUqCeNnt4JEPk'
DATA_TO_PULL = "Answers"
final_destination = ""
lost_Data = pd.DataFrame()
wrong_address = pd.DataFrame()

#####################################
#Interface
st.write("""## 📝 Description

Welcome to your Running Dinner Program!


Before you can start, **please first fill in the final destination address** for your Running Dinner!





Here you can access the Running Dinner Survey ➡️ [**Running Dinner Survey**](https://docs.google.com/forms/d/e/1FAIpQLSe01mkoWCHgOh7kSNHZ28DHL5xgaDFEMwfrMjqGQxkX8vt70w/viewform?usp=sf_link)



Here you can access our GitHub profile for the Running Dinner Program for further information ➡️ [**GitHub**](https://github.com/RunningDinnerProgramming/RunningDinnerProgramming)


Here you can access the answers from the Running Dinner Survey ➡️ [**Spreadsheet**](https://docs.google.com/spreadsheets/d/1C1Q7QQ8ZVhCP1ShHdmds6N2kxr1BX8RUqCeNnt4JEPk/edit?usp=sharing)

❗ Important ❗   If you want to create a new Running Dinner, you have to **clear ALL answers from the spreadsheet above**!
""")




st.subheader(""" 📍 Final Destination:
        """)


st.write(""" ❗ Important ❗   

**Please use the following address format** for the final destination:  Streetname Housenumber City 

Example: Cais da Viscondessa Lisboa
""")



final_destination = st.text_input('Please enter the final address here:')
st.write('The Final location is:', final_destination)

# calling the class algorithm
algo = algorithm(SCOPES,SPREADSHEET_ID,DATA_TO_PULL,final_destination)

st.sidebar.subheader(' Quick  Explore')

if final_destination == "":
    st.sidebar.write("In oder to import data please make sure to insert a start location!")

else:
    #####################################
    #import new Data and store each import into a new json file
    
    if st.button('Import'):
        output2 = algo.team()
        file = output2.to_json("data_json.json")
        st.write("Data is up to date!")
    else:
        st.write("Data is not up to date!")
        
    # opening the data json file again to have a fixed data import 
    output1 = pd.read_json("data_json.json")
    
    
    #filter out wrong address entries
    
    wrong = output1[(output1["latitude"] == -89.9999) & (output1["longitude"] == -179.9999)]
    if wrong.shape[0] != 0:
        wrong_address = output1[(output1["latitude"] == -89.9999) & (output1["longitude"] == -179.9999)]
        output1 = output1.drop(output1[(output1["latitude"] == -89.9999) & (output1["longitude"] == -179.9999)].index)
    else:
        output1 = output1
    
    #filter out last entries that cannot be distributet into teams
    
    if len(output1) % 3 == 2:
        lost_Data = output1.tail(2)
        output1 = output1.iloc[:-2 , :] 
    elif len(output1) % 3 == 1:
        lost_Data = output1.tail(1)
        output1 = output1.iloc[:-1 , :]
    else:
        output1=output1
        
    #connect Food Menu to Group ID 1, 2 or 3
    
    u=0
    food_menu = list(output1["Group"])
    for i in food_menu:
        if i==1:
            food_menu[u] = "Dessert"
        elif i==2:
            food_menu[u] = "Main Course"
        else:
            food_menu[u] = "Appetizer"
        u+=1
    output1["Menu"] = food_menu
    output1 = output1.sort_values(["FinalTeam","distance"])
    
    #clean dataset
    output1 = output1.drop(columns=["Zeitstempel","TeamID","Group"])
    
    output1 = output1.reindex(columns=["FinalTeam","Menu", "Name", "Address", "E-Mail", "Phonenumber", "Name Teammember", "E-Mail Partner", "Phonenumber Partner", "Food choice","latitude","longitude","distance"])
    output1["FinalTeam"] = output1["FinalTeam"].astype(int)
    
    #build drop down box
    
    all_teams=["All"]
    final_team = list(output1["FinalTeam"].unique())
                        
    for i in final_team:
        all_teams.append(i)
                            
    final_team_choice = st.sidebar.selectbox('Teams:', all_teams)
    st.sidebar.write('You selected Team:', final_team_choice)
                        
    #code if select all teams in filter
    
    if final_team_choice == "All":

        output = output1
        
        st.subheader(""" 👯‍ Participants List:
        """)
        
        st.write(""" Here you can see the **full participants list** with all necessary information. 
        The Running Dinner Program already **allocated all Participants from this list to their final teams** with a random algorithm, which you can see in the first column. 
        Teams were **allocated according to their distance to the Final Destination**, meaning that the ones farest away from the Final Destination prepare the appetizer, the ones in the middle prepare the main course, and the ones closest to the Final Destination the dessert.
        Consequently, all teams of the Running Dinner are close to each other after the dessert, making it easy to meet for a drink afterwards.
        Additionally, **all necessary information** (**address**, **e-mail**, **phonenumber**) of both team members are included in the participants list.
        """)
         
        hide_dataframe_row_index = """
                                        <style>
                                        .row_heading.level0 {display:none}
                                        .blank {display:none}
                                        </style>
                                        """

        # Inject CSS with Markdown
        
        st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

        st.dataframe(output)


        #get map
        
        st.subheader(""" 🗺️ Map:
        """)
        st.write("Here you can see the **locations of all participants**. Each red dot represents one participant and its address.")
        map_data = output[["latitude","longitude"]]
        st.map(map_data)


        #count food preference
        
        st.subheader(""" 🥗 Food Preferences:
        """)
        st.write(""" Here you can see the **distribution of different Food Preferences**. 
        """)
        output_count = output.groupby("Food choice")["FinalTeam"].count()
        st.bar_chart(output_count)
        
        #####################################
        #Dataset Problems
        
        st.write("""## 🆘 Dataset Problems:""")
        st.write("""Here you can find **all dataset-related problems**.""")
        
        #get teams that submitted to late
        
        if lost_Data.empty == False:
            st.subheader(""" 🕑 Wait List:
            """)
            st.write(""" Here you can see the list of **all people who signed up too late** for the Running Dinner.
            """)
            #st.session_state = output
            hide_dataframe_row_index = """
                                            <style>
                                            .row_heading.level0 {display:none}
                                            .blank {display:none}
                                            </style>
                                            """

            # Inject CSS with Markdown
            st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
            
            lost_Data = lost_Data.drop(columns=["index","Zeitstempel","latitude", "longitude","distance","TeamID","Group","FinalTeam"])
            st.dataframe(lost_Data)
        else: 
            st.write("No team submitted to late!")
         
        
        #table for teams that submitted a wrong address
        
        if wrong_address.empty == False:
            st.subheader(""" ❌ Wrong Address:
            """)
            st.write(""" Here you can find a list of **all people that did not type in their address correctly**.
            Contact those participants privately, verify their address and try to **adapt it manually in the [Spreadsheet](https://docs.google.com/spreadsheets/d/1C1Q7QQ8ZVhCP1ShHdmds6N2kxr1BX8RUqCeNnt4JEPk/edit?usp=sharing)** so that they are included in the algorithm.
            """)
            hide_dataframe_row_index = """
                                            <style>
                                            .row_heading.level0 {display:none}
                                            .blank {display:none}
                                            </style>
                                            """

            # Inject CSS with Markdown
            st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
            
            wrong_address = wrong_address.drop(columns=["index","Zeitstempel","TeamID","Group","FinalTeam"])                                               
            st.dataframe(wrong_address)
        else: 
            st.write("No team submitted a wrong address!")
    
    #code if select specific team in filter                         
    else:

        output = output1
        
        st.subheader(""" 👯‍ Participants List:
        """)
        
        st.write(f""" Here you can see the **participants list of the Final Team {final_team_choice}** with all necessary information. 
        """)
                                
        st.session_state = output
        hide_dataframe_row_index = """
                                        <style>
                                        .row_heading.level0 {display:none}
                                        .blank {display:none}
                                        </style>
                                        """

        # Inject CSS with Markdown
        st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
        data = output[output["FinalTeam"] == final_team_choice]
        st.dataframe(data)


        #get map
        
        st.subheader(""" 🗺️ Map:
        """)
        st.write(f"Here you can see the **locations of all participants within Final Team {final_team_choice}**. Each red dot represents one participant and its address.")
   
        map_data = data[["latitude","longitude"]]
        st.map(map_data)


        #count food preference
        
        st.subheader(""" 🥗 Food Preferences:
        """)
        st.write(f""" Here you can see the **distribution of different Food Preferences within Final Team {final_team_choice}**. 
        """)
        
        data_count = data.groupby("Food choice")["FinalTeam"].count()
        st.bar_chart(data_count)
        
        #####################################
        #Dataset Problems
        
        st.write("""## 🆘 Dataset Problems:""")
        st.write("""Here you can find **all dataset-related problems**.""")
           
        
        #get teams that submitted to late
        
        if lost_Data.empty == False:
            st.subheader(""" 🕑 Wait List:
            """)
            st.write(""" Here you can see the list of **all people who signed up too late** for the Running Dinner.
            """)
            hide_dataframe_row_index = """
                                            <style>
                                            .row_heading.level0 {display:none}
                                            .blank {display:none}
                                            </style>
                                            """

            # Inject CSS with Markdown
            st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
            
            lost_Data = lost_Data.drop(columns=["index","Zeitstempel","latitude", "longitude","distance","TeamID","Group","FinalTeam"])
            st.dataframe(lost_Data)

        else: 
            st.write("No team submitted to late!")

        #table for teams that submitted a wrong address
        if wrong_address.empty == False:
            st.subheader(""" ❌ Wrong Address:
            """)
            st.write(""" Here you can find a list of **all people that did not type in their address correctly**.
            Contact those participants privately, verify their address and try to **adapt it manually in the [Spreadsheet](https://docs.google.com/spreadsheets/d/1C1Q7QQ8ZVhCP1ShHdmds6N2kxr1BX8RUqCeNnt4JEPk/edit?usp=sharing)** so that they are included in the algorithm.
            """)
           
            hide_dataframe_row_index = """
                                            <style>
                                            .row_heading.level0 {display:none}
                                            .blank {display:none}
                                            </style>
                                            """

            # Inject CSS with Markdown
            st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
            
            wrong_address = wrong_address.drop(columns=["index","Zeitstempel","TeamID","Group","FinalTeam"])      
            st.dataframe(wrong_address)
            
        else: 
            st.write("No team submitted a wrong address!")

#######################################################################################################
#######################################################################################################

#E-Mail Server

#######################################################################################################
#######################################################################################################

#E-Mail to participants
    st.sidebar.subheader("E-Mail")
    
    sent_from = st.sidebar.text_input('Please put here your Gmail (ex.: introtorunningprogramming@gmail.com):')
    password = st.sidebar.text_input('Please put here your Password (ex.: JoJuMaPa351):')
    
    st.sidebar.write("Click to send emails to all teams.")
    
    if st.sidebar.button('Send E-Mail'):
        if sent_from == "" or password == "":
            st.sidebar.write("E-Mail or Password is missing!")
        else:
            
            #E-Mail for participants
            number_teams = int(output1.shape[0]/3)
            for var in range(1,number_teams+1):
                var_new = int(var)
                team_df = output1[output1["FinalTeam"] == var_new]
                for mail in team_df["E-Mail"]:                           
                    msg = EmailMessage()
                    msg.set_content(f"""Hello Group {team_df["FinalTeam"].iloc[0]},
                    
Thank you for participating in this Running Dinner. This is your group composition: 

    1. Appetizer: 
        Teammember1: {team_df["Name"].iloc[2]}
        Teammember2: {team_df["Name Teammember"].iloc[2]}
        Address: {team_df["Address"].iloc[2]}
        Phone Number: {team_df["Phonenumber"].iloc[2]}
        Food Preferences: {team_df["Food choice"].iloc[2]}

    2. Main Course: 
        Teammember1: {team_df["Name"].iloc[1]}
        Teammember2: {team_df["Name Teammember"].iloc[1]}
        Address: {team_df["Address"].iloc[1]}
        Phone Number: {team_df["Phonenumber"].iloc[1]}
        Food Preferences: {team_df["Food choice"].iloc[1]}

    3. Dessert: 
        Teammember1: {team_df["Name"].iloc[0]}
        Teammember2: {team_df["Name Teammember"].iloc[0]}
        Address: {team_df["Address"].iloc[0]}
        Phone Number: {team_df["Phonenumber"].iloc[0]}
        Food Preferences: {team_df["Food choice"].iloc[0]}
                                    
                                    
Have a good night and we see each other all toghether at {final_destination}!
                                    
Best,
                                    
Your Running Dinner Team
                                    
P.S.: Please check all food preferences and get in touch with each other!
""")

                    msg['Subject'] = 'Running Dinner Information - Have Fun!'
                    msg['From'] = sent_from
                    msg['To'] = mail

                    # Send the message via our own SMTP server.
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.login(sent_from, password)
                    server.send_message(msg)
                    server.quit()
 
######################################
#E-Mail for Waiting List
            
            if lost_Data.empty == False:
                for mail_lost,name_lost in zip(lost_Data["E-Mail"],lost_Data["Name"]):
                    msg = EmailMessage()
                    msg.set_content(f"""Hello {name_lost},

Unfortunately did you and your Teammember submit this time too late to this Running Dinner.

Our Running Dinner Team is more than sorry for this, but hopefully we see you again next time. If you want, you can join with your Teammember at our final destination, which is {final_destination}, to have some drinks after the Running Dinner 😊


Best,

Your Running Dinner Team

""")
                    
                    msg['Subject'] = "Running Dinner Information - maybe next time"
                    msg['From'] = sent_from
                    msg['To'] = mail_lost

                    # Send the message via our own SMTP server.
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.login(sent_from, password)
                    server.send_message(msg)
                    server.quit()
        
######################################
#E-Mail to teams with a wrong address
            
            if wrong_address.empty == False:
                for mail_wrong,name_wrong in zip(wrong_address["E-Mail"],wrong_address["Name"]):
                    msg = EmailMessage()
                    msg.set_content(f"""Hello {name_wrong},

Unfortunately did you and your Teammember submit an address that is not readable by our Running Dinner Algorythm.

Our Running Dinner Team is more than sorry for this, but hopefully see you again next time. If you want, you can join with your Teammember at our final destination, which is {final_destination}, to have some drinks after the Running Dinner 😊

Best,

Your Running Dinner Team

""")

                    msg['Subject'] = "Running Dinner Information - Sorry but you submitted a wrong address"
                    msg['From'] = sent_from
                    msg['To'] = mail_wrong

                    # Send the message via our own SMTP server.
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.login(sent_from, password)
                    server.send_message(msg)
                    server.quit()


            st.sidebar.write("E-Mail send out successfully!")


            """
             if wrong_address.empty == False:
                number_wait = wrong_address.shape[0]
                for wait in range(0,number_wait):
                    for mail_lost in wrong_address["E-Mail"]:                           
                        msg = EmailMessage()"""
                        #msg.set_content(f"""Hello {wrong_address["Name"].iloc[wait]},
     
      

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


class Data:
    
    def __init__(self,SCOPES,SPREADSHEET_ID,DATA_TO_PULL):
        self.SCOPES = SCOPES
        self.SPREADSHEET_ID = SPREADSHEET_ID
        self.DATA_TO_PULL = DATA_TO_PULL
        
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

        

class algorithm:
    
    def __init__(self,SCOPES,SPREADSHEET_ID,DATA_TO_PULL,start_location):
        self.SCOPES = SCOPES
        self.SPREADSHEET_ID = SPREADSHEET_ID
        self.DATA_TO_PULL = DATA_TO_PULL
        self.start_location = start_location

    def get_data(self):
        RD_data = Data(self.SCOPES, self.SPREADSHEET_ID, self.DATA_TO_PULL)
        data = RD_data.pull_sheet_data()
        return data

    def start(self):
        #set up geolocator application
        geolocator = Nominatim(user_agent="RunningDinner")

        #set center of map
        #start_location = "Rua do Forno do Tijolo 29D Lisboa"
        start_location_code = geolocator.geocode(self.start_location)
        start_location_lat_long = (start_location_code.latitude,start_location_code.longitude)
        return start_location_lat_long

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
            end_location_code = geolocator.geocode(end_location)
            end_location_lat_long = (end_location_code.latitude,end_location_code.longitude)
            distance = (great_circle(algorithm.start(self), end_location_lat_long).miles)*kilometer_miles
            data[key]["latitude"] = end_location_lat_long[0]
            data[key]["longitude"] = end_location_lat_long[1]
            data[key]["distance"] = distance
    
        #create a pandas table
        df = pd.DataFrame.from_dict(data)
        dataT = df.transpose()
        
        return dataT
        
    def team(self):
        
        dataT = algorithm.geo(self)
        
        #filter out the teams that are to much
        lostData = pd.DataFrame()
        
        if len(dataT) % 3 == 2:
            lostData = dataT.tail(2)
            dataT = dataT.iloc[:-2 , :] 
        elif len(dataT) % 3 == 1:
            lostData = dataT.tail(1)
            dataT = dataT.iloc[:-1 , :]
        else:
            dataT=dataT
        
        #create 3 quantiles
        dataT["TeamID"]=dataT.index
        dataT["Group"] = pd.qcut(dataT["distance"],3,labels=[1,2,3])
        dataT=dataT.sort_values(["Group","distance"])

        #distribute the teams into its final teams by a random algorythm
        dataT_grouped=dataT.groupby(dataT["Group"])
        
        x=[1,2,3]
        final_dict={}
               
        for v in x:
            groupv=dataT_grouped.get_group(v)
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
        
        frame=[dataT,lostData]
        dataT_concat = pd.concat(frame)
        
        return dataT_concat
    

#######################################################################################################
#######################################################################################################

#Interface with Streamlit

#######################################################################################################
#######################################################################################################

    
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)
st.write("# Running Dinner")


SCOPES=['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1C1Q7QQ8ZVhCP1ShHdmds6N2kxr1BX8RUqCeNnt4JEPk'
DATA_TO_PULL = "Answers"
final_destination = ""
lost_Data = pd.DataFrame()

st.write("""## 🧶Description
Hallo hier kommt eine riesen zummenfassung hin die alles erklälrt! check out this ➡️ [Survey Link](https://docs.google.com/forms/d/e/1FAIpQLSe01mkoWCHgOh7kSNHZ28DHL5xgaDFEMwfrMjqGQxkX8vt70w/viewform?usp=sf_link)

To clear old event, clear this spreadsheet! ➡️ [Spreadsheet](https://docs.google.com/spreadsheets/d/1C1Q7QQ8ZVhCP1ShHdmds6N2kxr1BX8RUqCeNnt4JEPk/edit?usp=sharing)

For further information check out our README file on GitHub! ➡️ [README](https://github.com/RunningDinnerProgramming/RunningDinnerProgramming/blob/ee946f443f32e5db918f1e8553dc641ef903d597/README.md)
""")


st.write("""### Final Destination:""")
final_destination = st.text_input('Please enter your streetname, housenumber and city (KEEP THE FORMAT LIKE THIS EXAMPLE - Rua do Forno do Tijolo 29D Lisboa)')
st.write('The Final location is:', final_destination)


#start_location = "Rua do Forno do Tijolo 29D Lisboa"

algo = algorithm(SCOPES,SPREADSHEET_ID,DATA_TO_PULL,final_destination)

st.sidebar.subheader(' Quick  Explore')

if final_destination == "":
    st.sidebar.write("In oder to import data please make sure to insert a start location!")

else:
    
    if st.button('Import'):
        output2 = algo.team()
        file = output2.to_json("data_json.json")
        st.write("Data is up to date!")
    else:
        st.write("Data is not up to date!")

    output1 = pd.read_json("data_json.json")
    
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
    output1 = output1.sort_values(by="FinalTeam")
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
                        
    #code if select all teams
    if final_team_choice == "All":

        output = output1

        st.write("""### Data Import:""")
        hide_dataframe_row_index = """
                                        <style>
                                        .row_heading.level0 {display:none}
                                        .blank {display:none}
                                        </style>
                                        """

        # Inject CSS with Markdown
        st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
        #data = output
        st.dataframe(output)


        #get map
        st.subheader("Map")
        map_data = output[["latitude","longitude"]]
        st.map(map_data)


        #count food preference
        st.subheader("Food Preferences")
        
        output_count = output.groupby("Food choice")["FinalTeam"].count()
        st.bar_chart(output_count)

        
        #get teams that submitted to late
        if lost_Data.empty == False:
            st.write("""### Wait List:""")
            #st.session_state = output
            hide_dataframe_row_index = """
                                            <style>
                                            .row_heading.level0 {display:none}
                                            .blank {display:none}
                                            </style>
                                            """

            # Inject CSS with Markdown
            st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
            
            lost_Data = lost_Data.drop(columns=["Zeitstempel","latitude", "longitude","distance","TeamID","Group","FinalTeam"])
            st.dataframe(lost_Data)
     
    
    #code if select specific team                          
    else:

        output = output1
                                
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
        st.subheader("Map")
        map_data = data[["latitude","longitude"]]
        st.map(map_data)


        #count food preference
        st.subheader("Food Preferences")
        
        data_count = data.groupby("Food choice")["FinalTeam"].count()
        st.bar_chart(data_count)

        
        #get teams that submitted to late
        if lost_Data.empty == False:
            st.write("""### Wait List:""")
            hide_dataframe_row_index = """
                                            <style>
                                            .row_heading.level0 {display:none}
                                            .blank {display:none}
                                            </style>
                                            """

            # Inject CSS with Markdown
            st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
            
            lost_Data = lost_Data.drop(columns=["Zeitstempel","latitude", "longitude","distance","TeamID","Group","FinalTeam"])
            st.dataframe(lost_Data)

 
    #E-Mail Server
    st.sidebar.subheader("E-Mail")
    """
    name1_app = list(output1[output1["Menu"] == "Appetizer"]["Name"])
    name2_app = list(output1[output1["Menu"] == "Appetizer"]["Name Teammember"])
    phone_app = list(output1[output1["Menu"] == "Appetizer"]["Name"])
    email = list(output1["E-Mail"])
    team = list(output1["FinalTeam"])
    """
                                
    
    st.write(name1_app)
    st.write(name2_app)
    
    sent_from = st.sidebar.text_input('Please put here your Gmail (ex.: introtorunningprogramming@gmail.com):')
    password = st.sidebar.text_input('Please put here your Password (ex.: JoJuMaPa351):')
    
    st.sidebar.write("Click to send emails to all teams.")
    
    if st.sidebar.button('Send E-Mail'):
        if sent_from == "" or password == "":
            st.sidebar.write("E-Mail or Password is missing!")
        else:
            var = 1
            number_teams = len(output1)/3
            for var in range(1,number_teams+1):
                var = str(var)
                team_df = output1[output1["FinalTeam"] == var]
                for mail in team_df["E-Mail"]:                           
                    msg = EmailMessage()
                    msg.set_content(f"""Hello {team_df["FinalTeam"].iloc[[0]]},
                                    \n 
                                    Thank you for participating in this Running Dinner. This is your group composition: 
                                    \n\n 
                                    1. Appetizer: 
                                    \n Teammember1: {team_df["Name"].iloc[[0]]}
                                    \n Teammember2: {team_df["Name Teammember"].iloc[[0]]}
                                    \n Address: {team_df["Address"].iloc[[0]]}
                                    \n Phone Number: {team_df["Phonenumber"].iloc[[0]]}
                                    \n Food Preferences: {team_df["Food Choice"].iloc[[0]]}
                                    \n
                                    2. Main Course: 
                                    \n Teammember1: {team_df["Name"].iloc[[1]]}
                                    \n Teammember2: {team_df["Name Teammember"].iloc[[1]]}
                                    \n Address: {team_df["Address"].iloc[[1]]}
                                    \n Phone Number: {team_df["Phonenumber"].iloc[[1]]}
                                    \n Food Preferences: {team_df["Food Choice"].iloc[[1]]}
                                    \n
                                    3. Dessert: 
                                    \n Teammember1: {team_df["Name"].iloc[[2]]}
                                    \n Teammember2: {team_df["Name Teammember"].iloc[[2]]}
                                    \n Address: {team_df["Address"].iloc[[2]]}
                                    \n Phone Number: {team_df["Phonenumber"].iloc[[2]]}
                                    \n Food Preferences: {team_df["Food Choice"].iloc[[2]]}
                                    \n\n
                                    Have a good night and we see each other all toghether at {final_destination}!
                                    \n
                                    Best,
                                    \n
                                    Your Running Dinner Team
                                    \n\n
                                    P.S.: Please check all food preferences and get in contact with each other if there are any!
                                   """)

                    msg['Subject'] = 'Running Dinner Information'
                    msg['From'] = sent_from
                    recipients = [team_df["E-Mail"].iloc[[0]],team_df["E-Mail"].iloc[[1]],team_df["E-Mail"].iloc[[2]]
                    msg['To'] = ", ".join(recipients)
                    #msg['To'] = [team_df["E-Mail"].iloc[[0]],team_df["E-Mail"].iloc[[1]],team_df["E-Mail"].iloc[[2]]

                    # Send the message via our own SMTP server.
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.login(sent_from, password)
                    server.send_message(msg)
                    server.quit()

            st.sidebar.write("E-Mail send out successfully!")
        





     

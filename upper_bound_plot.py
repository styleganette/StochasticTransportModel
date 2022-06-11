# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 14:12:10 2022

@author: ingvi
"""
import pandas as pd
import glob
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
pd.set_option("display.max_rows", None, "display.max_columns", None)

from Data.Create_Sets_Class import TransportSets

data = TransportSets('HHH')

path = r'full_solution_anette'
all_files = glob.glob(path+'/*.csv')
col_names = ['from', 'to', 'Mode', "fuel", "route", 'product', 'time_period', 'weight', 'scenario']
li = []

scen_dict = {}
count = 1
for filename in all_files:
    df = pd.read_csv(filename, names = col_names, encoding='utf-8')# 'unicode_escape')
    li.append(df)
    scen_dict[count] = df
    count +=1


dataset = pd.DataFrame(columns = ['from','to','Mode',"fuel","route",'product','weight','time_period', 'scenario'])
for i in range(1,count):
    col_names = ['from', 'to', 'Mode', "fuel", "route", 'product', 'time_period', 'weight', 'scenario']
    scen_n = scen_dict[i]
    temp_df = scen_n[scen_n['from'].str.contains('x_flow')]
    #print(temp_df.head(20))
    for index, row in temp_df.iterrows():
        if float(row['weight']) > 0:
            weight = float(row['weight'])#*data.AVG_DISTANCE[(row['from'], row['to'], row['Mode'], row['route'])]
            a_series = pd.Series([row['from'], row['to'], row['Mode'], row['fuel'], row['route'], row['product'], weight
                                  , row['time_period'],i], 
                                 index=dataset.columns)
            dataset = dataset.append(a_series, ignore_index=True)

dataset['time_period'] = dataset['time_period'].str.replace('\]','')
dataset['time_period'] = dataset['time_period'].astype(int)
dataset['from'] = dataset['from'].str.replace('x_flow\[','')

dataset['weight'] = pd.to_numeric(dataset['weight'])
#dataset['fuel'] = dataset['fuel'].str.replace(' ','')
#dataset['fuel'] = dataset['fuel'].str.replace(' ','')

for index, row in dataset.iterrows():
    dataset.loc[index, 'weight'] = row['weight']*data.AVG_DISTANCE[(row['from'], row['to'], row['Mode'],int(row['route']))]
    

for s in range(1,count): #remove x if ph!!!
    dataset_scen = dataset[dataset["scenario"]==s]
    #print(dataset_scen.tail(10)) #GIR TALL
    fuel_list_road = []
    fuel_list_rail = []
    fuel_list_sea = []
    fuel_list = []
    for m in ["Road","Rail","Sea"]:
        for f in dataset_scen[dataset_scen["Mode"] == m]["fuel"].unique():
            for t in data.T_TIME_PERIODS:
                yearly_weight = dataset_scen[dataset_scen["time_period"] == int(t)]['weight'].sum()
                dataset_temp = dataset_scen[(dataset_scen["Mode"] == m) & (dataset_scen["fuel"] == f) & (dataset_scen["time_period"] == t)]
                #print(dataset_temp.head(10))
                #if len(dataset_temp) > 0:
                #    fuel_list.append((m,f,t,dataset_temp["weight"].sum()*100/yearly_weight))
                #else:
                #    fuel_list.append((m,f,t,0))
                if len(dataset_temp) > 0:
                    fuel_list.append((m,f,t,dataset_temp["weight"].sum()*100/yearly_weight))
                else:
                    fuel_list.append((m,f,t,0))
    #print("fuel list: ")
    #print(fuel_list)
    for e in fuel_list:
        if e[0] == "Road":
            fuel_list_road.append(e)
        elif e[0] == "Rail":
            fuel_list_rail.append(e)
        elif e[0] == "Sea":
            fuel_list_sea.append(e)

    #color_sea = iter(cm.Blues(np.linspace(0.5,1,len(fuel_list_sea)//5)))
    #color_road = iter(cm.Reds(np.linspace(0.4,1,len(fuel_list_road)//5)))
    #color_rail = iter(cm.Greens(np.linspace(0.2,1,len(fuel_list_rail)//5)))

    color_sea = iter(cm.Blues(np.linspace(0.3,1,7)))
    color_road = iter(cm.Reds(np.linspace(0.4,1,5)))
    color_rail = iter(cm.Greens(np.linspace(0.25,1,5)))

    labels = ['2020', '2025', '2030', '2040', '2050']
    width = 0.35       # the width of the bars: can also be len(x) sequence
    bottom = np.array([0,0,0,0,0])

    FM_FUEL = {"Road": ["Diesel","Hydrogen", "Battery electric", 'Biodiesel', 'Biogas'],
                    "Rail": ["Diesel", "Hydrogen", "Battery train", "'Electric train (CL)'", 'Biodiesel'],
                    "Sea": ["LNG", "MGO", "Hydrogen", "Ammonia", "'Biodiesel (HVO)'", 'Biogas', "HFO"]}

    color_dict = {}
    for m in ["Road", "Rail", "Sea"]:
        for f in FM_FUEL[m]:
            if m == "Road":
                color_dict[m,f] = next(color_road)
            elif m == "Sea":
                color_dict[m, f] = next(color_sea)
            elif m == "Rail":
                color_dict[m, f] = next(color_rail)

    fig, ax = plt.subplots()
    for i in range(0,len(fuel_list),5):
        chunk = fuel_list[i:i + 5]
        #print(chunk)
        fuel_flow = []
        for elem in chunk:
            fuel_flow.append(elem[3])
        if sum(fuel_flow) > 0.0001:
            ax.bar(labels, fuel_flow, width, bottom=bottom,
                label=chunk[0][0]+" "+chunk[0][1], color=color_dict[chunk[0][0],chunk[0][1]])
            bottom = np.add(bottom,np.array(fuel_flow))


    #ax.set_ylabel('%')
    ax.set_title('Scenario: '+str(s))
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.7, box.height])
    plt.xticks(fontsize=16)
    #ax.legend()
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    #plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.02),
    #          ncol=3, fancybox=True, shadow=True)
    #plt.legend(ncol=11, bbox_to_anchor=(0.75, 1.15))#,prop={"size":16})
    plt.show()
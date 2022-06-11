# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 13:31:04 2021

@author: ingvi
"""

"Example data"

from collections import Counter
import pandas as pd
import itertools
import numpy as np
import os
from math import cos, asin, sqrt, pi
import networkx as nx
from itertools import islice
pd.set_option("display.max_rows", None, "display.max_columns", None)

# from FreightTransportModel.Utils import plot_all_graphs  #FreightTransportModel.

arr_aggr_dict = {}

class TransportSets():

    def __init__(self, scenario, carbon_scenario, fuel_costs, emission_reduction):# or (self)
        self.run_file = "main"  # "sets" or "main"
        #self.user = "i"  # "i" or "a"
        self.scenario = scenario # "['average']" #or scenario
        self.CO2_scenario = carbon_scenario
        self.fuel_costs = fuel_costs
        self.emission_reduction = emission_reduction
        self.read_dataframes()
        self.construct_pyomo_data()


    def read_dataframes(self):

        if self.run_file=="main":
            self.pwc_aggr = pd.read_csv(r'Data/pwc_riktig')
            self.city_coords = pd.read_csv(r'Data/zonal_aggregation_steffen.csv', sep=';')
        if self.run_file=="sets":
            self.pwc_aggr = pd.read_csv(r'pwc_riktig')
            self.city_coords = pd.read_csv(r'zonal_aggregation_steffen.csv', sep=';')

    def uniq(self, lst):
        last = object()
        for item in lst:
            if item == last:
                continue
            yield item
            last = item

    def sort_and_deduplicate(self, l):
        return list(self.uniq(sorted(l, reverse=True)))

    def construct_pyomo_data(self):

        print("Constructing scenario")

        self.factor = 10000

        self.N_NODES = ["Oslo", "Bergen", "Trondheim", "Hamar", "Bodø", "Tromsø", "Kristiansand",
                        "Ålesund", "Stavanger", "Skien", "Sør-Sverige", "Nord-Sverige",
                        "Kontinentalsokkelen", "Europa", "Verden"]
        self.N_NODES_NORWAY = ["Oslo", "Bergen", "Trondheim", "Hamar", "Bodø", "Tromsø", "Kristiansand",
                        "Ålesund", "Stavanger", "Skien", "Kontinentalsokkelen"]
        
        self.SEA_NODES = self.N_NODES.copy()
        self.SEA_NODES.remove("Hamar")
        
        self.SEA_NODES_NORWAY = self.N_NODES_NORWAY.copy()
        self.SEA_NODES_NORWAY.remove("Kontinentalsokkelen")
        self.SEA_NODES_NORWAY.remove("Hamar")
        
        self.ROAD_NODES = self.N_NODES.copy()
        self.ROAD_NODES.remove("Kontinentalsokkelen")
        self.ROAD_NODES.remove("Verden")
        
        self.RAIL_NODES = self.N_NODES.copy()
        self.RAIL_NODES.remove("Kontinentalsokkelen")
        self.RAIL_NODES.remove("Europa")
        self.RAIL_NODES.remove("Verden")
        
        self.M_MODES = ["Road", "Rail", "Sea"]
        
        self.M_MODES_CAP = ["Rail", "Sea"]
        
        self.RAIL_NODES_NORWAY = self.N_NODES_NORWAY.copy()
        self.RAIL_NODES_NORWAY.remove("Kontinentalsokkelen")
        
        self.N_NODES_CAP_NORWAY = {"Rail": self.RAIL_NODES_NORWAY,
                            "Sea": self.SEA_NODES_NORWAY}

        self.F_FUEL = ["Diesel", "Ammonia", "Hydrogen", "Battery electric", "Electric train (CL)", "LNG", "MGO",
                       'Biogas', 'Biodiesel', 'Biodiesel (HVO)', 'Battery train', "HFO"]

        self.FM_FUEL = {"Road": ["Diesel","Hydrogen", "Battery electric", 'Biodiesel', 'Biogas'],
                        "Rail": ["Diesel", "Hydrogen", "Battery train", "Electric train (CL)", 'Biodiesel'],
                        "Sea": ["LNG", "MGO", "Hydrogen", "Ammonia", 'Biodiesel (HVO)', 'Biogas', "HFO"]} ###HUSK Å SETTE INN HFO

        self.NEW_MF_LIST = [("Road", "Hydrogen"), ("Road", "Battery electric"), ("Rail", "Hydrogen"),
                            ("Rail", "Battery train"), ("Sea", "Hydrogen"), ("Sea", "Ammonia"), ('Road', 'Biodiesel'),
                            ('Road', 'Biogas'), ('Rail', 'Biodiesel'), ('Sea', 'Biodiesel (HVO)'), ('Sea', 'Biogas')]

        self.NEW_F_LIST = set([e[1] for e in self.NEW_MF_LIST])

        self.NM_LIST_CAP = [(node, mode) for mode in self.M_MODES_CAP for node in self.N_NODES_CAP_NORWAY[mode]]
        
        self.T_TIME_PERIODS = [2020, 2025, 2030, 2040, 2050]

        self.T_INTERVALS = [self.T_TIME_PERIODS[i] - self.T_TIME_PERIODS[0] for i in range(len(self.T_TIME_PERIODS))] #ikke i bruke

        self.P_PRODUCTS = ['Dry bulk', 'Fish', 'General cargo', 'Industrial goods', 'Other thermo',
                           'Timber', 'Wet bulk']
        
        self.TERMINAL_TYPE = {"Rail": ["Combination", "Timber"], "Sea": ["All"]}
        
        self.PT = {"Combination": ['Dry bulk', 'Fish', 'General cargo', 'Industrial goods', 'Other thermo','Wet bulk'],
                   "Timber": ['Timber'],
                   "All": self.P_PRODUCTS}
        
        self.U_UPG = ["Partially electrified rail", "Fully electrified rail"]

        self.UF_UPG = {"Battery train": ["Partially electrified rail", "Fully electrified rail"],
                       "Electric train (CL)": ["Fully electrified rail"]}

        self.L_LINKS = []
        self.L_LINKS_CAP = []
        self.L_LINKS_UPG = []
        self.A_ARCS = []
        self.UL_UPG = {}
        self.FL_FUEL_UPG = {}
        # self.OD_PAIRS = []
        self.K_PATHS = []
        self.A_PAIRS = {}
        self.A_TECH = {(m,f): [] for m in self.M_MODES for f in self.FM_FUEL[m]}

        # Create initial modal links
        for i in self.N_NODES:
            for j in self.N_NODES:
                for m in self.M_MODES:
                    if (i == "Hamar" and j == "Trondheim" and m == "Rail") or (
                            i == "Trondheim" and j == "Hamar" and m == "Rail"):
                        self.R_ROUTES = [1, 2]  # 1 = Dovrebanen, 2 = Rørosbanen
                    else:
                        self.R_ROUTES = [1]
                    for r in self.R_ROUTES:
                        link = (i, j, m, r)
                        if ((j, i, m, r) not in self.L_LINKS) and (j!=i):
                            self.L_LINKS.append(link)

        # Defined allowed railway modal links
        self.allowed_rail = {"Oslo": ["Hamar", "Bergen", "Skien", "Sør-Sverige"],
                             "Bergen": ["Oslo"],
                             "Trondheim": ["Bodø", "Hamar", "Nord-Sverige"],
                             "Bodø": ["Trondheim", "Tromsø", "Nord-Sverige"],
                             "Tromsø": ["Bodø"],
                             "Hamar": ["Oslo", "Trondheim", "Ålesund","Sør-Sverige"],
                             "Kristiansand": ["Stavanger", "Skien"],
                             "Skien":["Kristiansand","Oslo"],
                             "Ålesund": ["Hamar"],
                             "Stavanger": ["Kristiansand"],
                             "Sør-Sverige": ["Oslo", "Hamar", "Nord-Sverige","Europa"],
                             "Nord-Sverige": ["Sør-Sverige", "Bodø", "Trondheim"],
                             "Europa": ["Sør-Sverige"]}

        self.allowed_road = {"Oslo": ["Hamar", "Bergen", "Skien", "Sør-Sverige"],
                             "Bergen": ["Oslo","Ålesund","Stavanger"],
                             "Trondheim": ["Bodø", "Hamar", "Nord-Sverige","Ålesund"],
                             "Bodø": ["Trondheim", "Tromsø", "Nord-Sverige"],
                             "Tromsø": ["Bodø"],
                             "Hamar": ["Oslo", "Trondheim", "Ålesund"],
                             "Kristiansand": ["Stavanger", "Skien"],
                             "Skien": ["Kristiansand", "Oslo"],
                             "Ålesund": ["Hamar","Bergen","Trondheim"],
                             "Stavanger": ["Kristiansand","Bergen"],
                             "Sør-Sverige": ["Oslo", "Nord-Sverige", "Europa"],
                             "Nord-Sverige": ["Sør-Sverige", "Bodø", "Trondheim"],
                             "Europa": ["Sør-Sverige"]}

        links_for_deletion = []
        for l in self.L_LINKS:
            if l[2] == "Road":
                if l[0] not in self.allowed_road.keys() or l[1] not in self.allowed_road.keys():
                    links_for_deletion.append(l)
                elif l[1] not in self.allowed_road[l[0]]:
                    links_for_deletion.append(l)
            elif l[2] == "Sea":
                if (l[0] == "Hamar") or (l[1] == "Hamar"):
                    links_for_deletion.append(l)
            elif l[2] == "Rail":
                if l[0] not in self.allowed_rail.keys() or l[1] not in self.allowed_rail.keys():
                    links_for_deletion.append(l)
                elif l[1] not in self.allowed_rail[l[0]]:
                    links_for_deletion.append(l)
        self.L_LINKS = set(self.L_LINKS) - set(links_for_deletion)

        self.L_LINKS_NORWAY = []
        for (i,j,m,r) in self.L_LINKS:
            if i in self.N_NODES_NORWAY or j in self.N_NODES_NORWAY:
                self.L_LINKS_NORWAY.append((i,j,m,r))

        # Create all arcs from allowed modal links
        for (i, j, m, r) in self.L_LINKS:
            for f in self.FM_FUEL[m]:
                arc = (i, j, m, f, r)
                if not(f == "HFO" and i in self.N_NODES_NORWAY and j in self.N_NODES_NORWAY):
                    self.A_ARCS.append(arc)
                    if i != j:
                        arc2 = (j, i, m, f, r)
                        self.A_ARCS.append(arc2)
                    
        #Create arc for specific modes and fuels
        for m in self.M_MODES:
            for f in self.FM_FUEL[m]:
                for a in self.A_ARCS:
                    if a[2] == m and a[3] == f:
                        if a not in self.A_TECH[(m,f)]:
                            self.A_TECH[(m,f)].append(a)
        
        
        for l in self.L_LINKS_NORWAY:
            if l[2] == "Rail":
                self.L_LINKS_CAP.append(l)
        
        for l in self.L_LINKS:
            for f in self.FM_FUEL[l[2]]:
                if not (f == "HFO" and l[0] in self.N_NODES_NORWAY and l[1] in self.N_NODES_NORWAY):
                    self.A_PAIRS[l, f] = [(l[0], l[1], l[2], f, l[3])]
                    if l[0] != l[1]:
                        self.A_PAIRS[l, f].append((l[1], l[0], l[2], f, l[3]))
        
        if self.run_file == "main":
            rail_cap_data = pd.read_excel(r'Data/Ferdig - cap + invest.xlsx', sheet_name='Cap rail')
            inv_rail_data = pd.read_excel(r'Data/Ferdig - cap + invest.xlsx', sheet_name='Invest rail')
            inv_sea_data = pd.read_excel(r'Data/Ferdig - cap + invest.xlsx', sheet_name='Invest sea')
        if self.run_file == "sets":
            rail_cap_data = pd.read_excel(r'Ferdig - cap + invest.xlsx', sheet_name='Cap rail')
            inv_rail_data = pd.read_excel(r'Ferdig - cap + invest.xlsx', sheet_name='Invest rail')
            inv_sea_data = pd.read_excel(r'Ferdig - cap + invest.xlsx', sheet_name='Invest sea')
        
        self.L_LINKS_DIR = []
        for (i, j, m, r) in self.L_LINKS:
            self.L_LINKS_DIR.append((i, j, m, r))
            self.L_LINKS_DIR.append((j, i, m, r))
            
     
        for index, row in inv_rail_data.iterrows():
            if pd.isnull(row["From"]):
                pass
            else:
                self.L_LINKS_UPG.append((row["From"],row["To"],row["Mode"],row["Route"]))  
        
        
        for l in self.L_LINKS_UPG:
            self.FL_FUEL_UPG[l] = [key for key in self.UF_UPG.keys()]
            self.UL_UPG[l] = self.U_UPG

        # Create OD-pairs
        self.OD_PAIRS = {p: [] for p in self.P_PRODUCTS}
        for index, row in self.pwc_aggr[self.pwc_aggr['year'] == 2020].iterrows():
            if row['from_fylke_zone'] in self.N_NODES and row['to_fylke_zone'] in self.N_NODES:
                self.OD_PAIRS[row['commodity_aggr']].append((row['from_fylke_zone'], row['to_fylke_zone']))
        self.ODP = []
        self.OD_PAIRS_ALL = set()
        for p in self.P_PRODUCTS:
            for (o, d) in self.OD_PAIRS[p]:
                self.OD_PAIRS_ALL.add((o, d))
                self.ODP.append((o, d, p))
        self.OD_PAIRS_ALL = list(self.OD_PAIRS_ALL)
        self.ODPTS = [odp + (t,) for odp in self.ODP for t in self.T_TIME_PERIODS]


        self.A_LINKS = {l: [] for l in self.L_LINKS_DIR}
        for (i,j,m,r) in self.L_LINKS_DIR:
            for f in self.FM_FUEL[m]:
                if not (f == "HFO" and i in self.N_NODES_NORWAY and j in self.N_NODES_NORWAY):
                    self.A_LINKS[(i,j,m,r)].append((i,j,m,f,r))

        # ------------------------
        # ----LOAD ALL PATHS------
        # ------------------------

        self.K_LINK_PATHS = []
        if self.run_file == "main":
            all_generated_paths = pd.read_csv(r'Data/all_generated_paths.csv',converters={'paths': eval})
        if self.run_file == "sets":
            all_generated_paths = pd.read_csv(r'all_generated_paths.csv', converters={'paths': eval})
        for index, row in all_generated_paths.iterrows():
            elem = row['paths']
            self.K_LINK_PATHS.append(elem)

        self.OD_PATHS = {od: [] for od in self.OD_PAIRS_ALL}
        for od in self.OD_PAIRS_ALL:
            for k in self.K_LINK_PATHS:
                if od[0] == k[0][0] and od[-1] == k[-1][1]:
                    self.OD_PATHS[od].append(k)

        self.K_PATHS = self.K_LINK_PATHS

        # ---------------------------------------
        # -------CALCULATE LINK DISTANCES--------
        # ---------------------------------------

        if self.run_file == "main":
            sea_distance = pd.read_excel(r'Data/Avstander (1).xlsx', sheet_name='Sea')
            road_distance = pd.read_excel(r'Data/Avstander (1).xlsx', sheet_name='Road')
            rail_distance = pd.read_excel(r'Data/Avstander (1).xlsx', sheet_name='Rail')
        if self.run_file == "sets":
            sea_distance = pd.read_excel(r'Avstander (1).xlsx', sheet_name='Sea')
            road_distance = pd.read_excel(r'Avstander (1).xlsx', sheet_name='Road')
            rail_distance = pd.read_excel(r'Avstander (1).xlsx', sheet_name='Rail')

        road_distances_dict = {}
        sea_distances_dict = {}
        rail_distances_dict = {}
        for i in self.N_NODES:
            for j in self.N_NODES:
                for index, row in sea_distance.iterrows():
                    if row["Fra"] in [i, j] and row["Til"] in [i, j]:
                        sea_distances_dict[(i, j)] = row["Km - sjø"]
                for index, row in road_distance.iterrows():
                    if row["Fra"] in [i, j] and row["Til"] in [i, j]:
                        road_distances_dict[(i,j)] = row["Km - road"]
                for index, row in rail_distance.iterrows():
                    if row["Fra"] in [i, j] and row["Til"] in [i, j]:
                        rail_distances_dict[(i, j)] = row["Km - rail"]

        self.AVG_DISTANCE = {l: 0 for l in self.L_LINKS}
        for l in self.L_LINKS:
            if l[2] == "Road":
                if (l[0], l[1]) in road_distances_dict.keys():
                    self.AVG_DISTANCE[l] = road_distances_dict[(l[0], l[1])]
                    self.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = road_distances_dict[(l[1], l[0])]
            elif l[2] == "Sea":
                if (l[0], l[1]) in sea_distances_dict.keys():
                    self.AVG_DISTANCE[l] = sea_distances_dict[(l[0], l[1])]
                    self.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = sea_distances_dict[(l[1], l[0])]
            elif l[2] == "Rail":
                if (l[0], l[1]) in rail_distances_dict.keys():
                    self.AVG_DISTANCE[l] = rail_distances_dict[(l[0], l[1])]
                    self.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = rail_distances_dict[(l[1], l[0])]
            if l[0] not in self.N_NODES_NORWAY or l[1] not in self.N_NODES_NORWAY:
                self.AVG_DISTANCE[l] = self.AVG_DISTANCE[l] / 2
                self.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = self.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] / 2

        #Indicator function
        self.DELTA = {(l, str(tuple(k))): 0 for l in self.L_LINKS_DIR for k in self.K_PATHS}
        for k in self.K_PATHS:
            for (i,j,m,r) in k:
                self.DELTA[((i,j,m,r), str(tuple(k)))] = 1
                
        #multi-mode paths
        self.MULTI_MODE_PATHS = []
        
        for k in self.K_PATHS:
            if len(k) > 1:
                for i in range(len(k)-1):
                    if k[i][2] != k[i+1][2]:
                        self.MULTI_MODE_PATHS.append(k)
                
        #Paths with transfer in node i to/from mode m
        self.TRANSFER_PATHS = {(i,m) : [] for m in self.M_MODES_CAP for i in self.N_NODES_CAP_NORWAY[m]}
        
        for m in self.M_MODES_CAP:
            for i in self.N_NODES_CAP_NORWAY[m]:
                for k in self.MULTI_MODE_PATHS:
                    for j in range(len(k)-1):
                        if (k[j][1] == i) and (k[j][2] == m or k[j+1][2] == m) and (k[j][2] != k[j+1][2]):
                            self.TRANSFER_PATHS[(i,m)].append(str(k))

        #Origin and destination paths
        self.ORIGIN_PATHS = {(i,m): [] for m in self.M_MODES_CAP for i in self.N_NODES_CAP_NORWAY[m]}
        self.DESTINATION_PATHS = {(i,m): [] for m in self.M_MODES_CAP for i in self.N_NODES_CAP_NORWAY[m]}
        
        for m in self.M_MODES_CAP:
            for i in self.N_NODES_CAP_NORWAY[m]:
                for k in self.K_PATHS:
                    if (k[0][0] == i) and (k[0][2] == m):
                        self.ORIGIN_PATHS[(i,m)].append(str(k))
                    if (k[-1][1] == i) and (k[-1][2] == m):
                        self.DESTINATION_PATHS[(i,m)].append(str(k))
        
        
        
        "Combined sets"
        
        
        
        self.TS = [(t) for t in self.T_TIME_PERIODS]
        

        # Create KPT
        self.KPTS = [(str(k), p, t) for k in self.K_PATHS for p in self.P_PRODUCTS for t in self.T_TIME_PERIODS]

        self.LT_CAP= [l+(t,) for l in self.L_LINKS_CAP for t in self.T_TIME_PERIODS]
        
        self.LUT_UPG = [l + (u,) + (t,) for l in self.L_LINKS_UPG for u in self.UL_UPG[l] for t in self.T_TIME_PERIODS]
        
        self.NMB_CAP = [(i,m) + (b,) for (i,m) in self.NM_LIST_CAP for b in self.TERMINAL_TYPE[m]]
        
        self.NMBT_CAP = [(i,m) + (b,) + (t,) for (i,m) in self.NM_LIST_CAP for b in self.TERMINAL_TYPE[m] for t in self.T_TIME_PERIODS]
        
        
        self.LFT_UPG = [l +(f,)+(t,) for l in self.L_LINKS_UPG for f in self.FL_FUEL_UPG[l] for t in self.T_TIME_PERIODS]

        # Create APT
        self.APTS = [a + (p,) + (t,) for a in self.A_ARCS for p in self.P_PRODUCTS for t in
                         self.T_TIME_PERIODS]
        
        self.LPT = [l + (p,) + (t,) for l in self.L_LINKS_DIR for p in self.P_PRODUCTS for t in
                         self.T_TIME_PERIODS]
        
        # Create MFT
        self.MFTS_CAP = [mf + (t,) for mf in self.NEW_MF_LIST for t in self.T_TIME_PERIODS]

        "Parameters"

        if self.run_file == "main":
            cost_data = pd.read_excel(r'Data/Costs.xlsx', sheet_name='Costs')
            #maturity_data = pd.read_excel(r'Data/DATA_INPUT.xlsx', sheet_name='MaturityLimits')
        if self.run_file == "sets":
            cost_data = pd.read_excel(r'Costs.xlsx', sheet_name='Costs')
        if self.run_file == "main":
            emission_data = pd.read_excel(r'Data/DATA_INPUT.xlsx', sheet_name='EmissionCap')
        if self.run_file == "sets":
            emission_data = pd.read_excel(r'DATA_INPUT.xlsx', sheet_name='EmissionCap')
        if self.emission_reduction == "100%":
            self.CO2_CAP = dict(zip(emission_data['Year'], emission_data['Cap']))
        elif self.emission_reduction == "75%":
            self.CO2_CAP = dict(zip(emission_data['Year'], emission_data['Cap1']))
        elif self.emission_reduction == "73%":
            self.CO2_CAP = dict(zip(emission_data['Year'], emission_data['Cap2']))
        elif self.emission_reduction == "70%":
            self.CO2_CAP = dict(zip(emission_data['Year'], emission_data['Cap3']))
        elif self.emission_reduction == "35%_70%":
            self.CO2_CAP = dict(zip(emission_data['Year'], emission_data['Cap4']))

        if self.run_file == "main":
            transfer_data = pd.read_excel(r'Data/DATA_INPUT.xlsx', sheet_name='TransferCosts')
        if self.run_file == "sets":
            transfer_data = pd.read_excel(r'DATA_INPUT.xlsx', sheet_name='TransferCosts')
            
        self.PATH_TYPES = ["sea-rail", "sea-road", "rail-road"]
        self.MULTI_MODE_PATHS_DICT = {q: [] for q in self.PATH_TYPES}
        
        self.C_MULTI_MODE_PATH = {(q,p): 0  for q in self.PATH_TYPES for p in self.P_PRODUCTS}
       
        transfer_data.columns = ['Product', 'Transfer type', 'Transfer cost']
        
        for p in self.P_PRODUCTS:
            for q in self.PATH_TYPES:
                data_index = transfer_data.loc[(transfer_data['Product'] == p) & (transfer_data['Transfer type'] == q)]
                self.C_MULTI_MODE_PATH[q,p] = data_index.iloc[0]['Transfer cost']
        
        for k in self.MULTI_MODE_PATHS:
            for j in range(len(k)-1):
                if (k[j][2] == "Sea" and k[j+1][2] == "Rail") or (k[j][2] == "Rail" and k[j+1][2] == "Sea"):
                    self.MULTI_MODE_PATHS_DICT["sea-rail"].append(k)
                if (k[j][2] == "Sea" and k[j+1][2] == "Road") or (k[j][2] == "Road" and k[j+1][2] == "Sea"):
                    self.MULTI_MODE_PATHS_DICT["sea-road"].append(k)
                if (k[j][2] == "Rail" and k[j+1][2] == "Road") or (k[j][2] == "Road" and k[j+1][2] == "Rail"):
                    self.MULTI_MODE_PATHS_DICT["rail-road"].append(k)

        self.C_TRANSP_COST = {(a, p, t): 1000000 for a in self.A_ARCS for p in self.P_PRODUCTS for t in
                              self.T_TIME_PERIODS}
        self.E_EMISSIONS = {(a,p, t): 1000000 for a in self.A_ARCS for p in self.P_PRODUCTS for t in
                              self.T_TIME_PERIODS}
        self.C_CO2 = {(a, t): 1000000 for a in self.A_ARCS for t in
                            self.T_TIME_PERIODS}

        for index, row in cost_data.iterrows():
            for (i,j,m,r) in self.L_LINKS_DIR:
                if m == row["Mode"]:
                    f = row["Fuel"]
                    if self.fuel_costs == "avg_costs":
                        self.C_TRANSP_COST[((i, j, m, f, r), row['Product group'], row['Year'])] = self.AVG_DISTANCE[(i, j, m, r)] * row[
                            'Cost (NOK/Tkm)']
                    elif self.fuel_costs == "low_costs":
                        self.C_TRANSP_COST[((i, j, m, f, r), row['Product group'], row['Year'])] = self.AVG_DISTANCE[(i, j, m, r)] * row[
                            'Cost - lav (-25%)']
                    elif self.fuel_costs == "high_costs":
                        self.C_TRANSP_COST[((i, j, m, f, r), row['Product group'], row['Year'])] = self.AVG_DISTANCE[(i, j, m, r)] * row[
                            'Cost - høy (+25%)']
                    elif self.fuel_costs == "very_low_costs":
                        if f in self.NEW_F_LIST:
                            self.C_TRANSP_COST[((i, j, m, f, r), row['Product group'], row['Year'])] = self.AVG_DISTANCE[(i, j, m, r)] * row['Cost (NOK/Tkm)'] *0.5
                        else:
                            self.C_TRANSP_COST[((i, j, m, f, r), row['Product group'], row['Year'])] = self.AVG_DISTANCE[(i, j, m, r)] * row['Cost (NOK/Tkm)']
                    self.E_EMISSIONS[((i, j, m, f, r), row['Product group'], row['Year'])] = self.AVG_DISTANCE[(i, j, m, r)] * row[
                        'Emissions (gCO2/Tkm)']
                    if self.CO2_scenario == 1:
                        self.C_CO2[((i, j, m, f, r), row['Product group'], row['Year'])] = self.E_EMISSIONS[((i, j, m, f, r), row['Product group'], row['Year'])] * row['CO2 fee base scenario (nok/gCO2)']
                    elif self.CO2_scenario == 2:
                        self.C_CO2[((i, j, m, f, r), row['Product group'], row['Year'])] = self.E_EMISSIONS[((i, j, m, f, r), row['Product group'], row['Year'])] *row['CO2 fee scenario 2 (nok/gCO2)']

        #Investments
        self.Y_BASE_CAP = {l: 100000 for l in self.L_LINKS_CAP}
        self.Y_MAX = {l: 0 for l in self.L_LINKS_CAP}
        self.Y_NODE_CAP = {(i,m,b): 100000 for m in self.M_MODES_CAP for i in self.N_NODES_CAP_NORWAY[m] for b in self.TERMINAL_TYPE[m]} #endret
        self.C_CAP_LINK = {l: 0 for l in self.L_LINKS_CAP}
        self.Y_ADD_CAP = {l: 0 for l in self.L_LINKS_CAP}
        self.Y_ADD_CAP_NODE = {(i,m,b): 100000 for m in self.M_MODES_CAP for i in self.N_NODES_CAP_NORWAY[m] for b in self.TERMINAL_TYPE[m]} #lagt til 03.05
        self.C_INV_UPG = {(l,u) : 100000 for l in self.L_LINKS_UPG for u in self.UL_UPG[l]}
        self.INV_NODE = {(i,m,b): 4 for (i,m,b) in self.NMB_CAP}
        self.INV_LINK = {(l): 1 for l in self.L_LINKS_CAP}
        self.C_CAP_NODE = {(i,m,b) : 0 for m in self.M_MODES_CAP for i in self.N_NODES_CAP_NORWAY[m] for b in self.TERMINAL_TYPE[m]}

        self.Y_TECH = {mfts : 0 for mfts in self.MFTS_CAP}
        
        self.cost_data = cost_data

        for index, row in inv_rail_data.iterrows():
            for (i,j,m,r) in self.L_LINKS_UPG:
                l = (i,j,m,r)
                for u in self.U_UPG:
                    if i == row["From"] and j == row["To"] and m == row["Mode"] and r == row["Route"] and u == 'Fully electrified rail':
                        self.C_INV_UPG[(l,u)] = row['Elektrifisering (NOK)']/self.factor
                    if i == row["From"] and j == row["To"] and m == row["Mode"] and r == row["Route"] and u == 'Partially electrified rail':
                        self.C_INV_UPG[(l,u)] = row['Delelektrifisering (NOK)']/self.factor

        for m in self.M_MODES_CAP:
            for i in self.N_NODES_CAP_NORWAY[m]:
                for b in self.TERMINAL_TYPE[m]:
                    if m == "Rail" and b=="Combination":
                        cap_data = rail_cap_data.loc[(rail_cap_data['Fylke'] == i)]
                        self.Y_NODE_CAP[i,m,b] = cap_data.iloc[0]['Kapasitet combi 2014 (tonn)']/self.factor
                        cap_exp_data = inv_rail_data.loc[(inv_rail_data['Fylke'] == i)]
                        self.Y_ADD_CAP_NODE[i,m,b] = cap_exp_data.iloc[0]['Økning i kapasitet (combi)']/self.factor
                        self.C_CAP_NODE[i,m,b] = cap_exp_data.iloc[0]['Kostnad (combi)']/self.factor
                    if m == "Rail" and b=="Timber":
                        cap_data = rail_cap_data.loc[(rail_cap_data['Fylke'] == i)]
                        self.Y_NODE_CAP[i,m,b] = cap_data.iloc[0]['Kapasitet tømmer (tonn)']/self.factor
                        cap_exp_data = inv_rail_data.loc[(inv_rail_data['Fylke'] == i)]
                        self.Y_ADD_CAP_NODE[i,m,b] = cap_exp_data.iloc[0]['Økning av kapasitet (tømmer)']/self.factor
                        self.C_CAP_NODE[i,m,b] = cap_exp_data.iloc[0]['Kostnad (tømmer)']/self.factor
                    if m == "Sea":
                        cap_data = inv_sea_data.loc[(inv_sea_data['Fylke'] == i)]
                        self.Y_NODE_CAP[i,m,b] = cap_data.iloc[0]['Kapasitet']/self.factor
                        self.Y_ADD_CAP_NODE[i,m,b] = cap_data.iloc[0]['Kapasitetsøkning']/self.factor
                        self.C_CAP_NODE[i,m,b] = cap_data.iloc[0]['Kostnad']/self.factor

        for (i, j, m, r) in self.L_LINKS_CAP:
            capacity_data1 = rail_cap_data.loc[(rail_cap_data['Fra'] == i) & (rail_cap_data['Til'] == j) & (rail_cap_data['Rute'] == r)]
            capacity_data2 = rail_cap_data.loc[(rail_cap_data['Fra'] == j) & (rail_cap_data['Til'] == i) & (rail_cap_data['Rute'] == r)]
            capacity_exp_data1 = inv_rail_data.loc[(inv_rail_data['Fra'] == i) & (inv_rail_data['Til'] == j) & (inv_rail_data['Rute'] == r)]
            capacity_exp_data2 = inv_rail_data.loc[(inv_rail_data['Fra'] == j) & (inv_rail_data['Til'] == i) & (inv_rail_data['Rute'] == r)]
            if len(capacity_data1) > 0:
                self.Y_BASE_CAP[i, j, m, r] = capacity_data1.iloc[0]['Maks kapasitet']/self.factor
            if len(capacity_data2) > 0:
                self.Y_BASE_CAP[i, j, m, r] = capacity_data2.iloc[0]['Maks kapasitet']/self.factor
            if len(capacity_exp_data1) > 0:
                self.Y_ADD_CAP[i, j, m, r] = capacity_exp_data1.iloc[0]['Kapasitetsøkning']/self.factor
                self.C_CAP_LINK[i, j, m, r] = capacity_exp_data1.iloc[0]['Kostnad']/self.factor
            if len(capacity_exp_data2) > 0:
                self.Y_ADD_CAP[i, j, m, r] = capacity_exp_data2.iloc[0]['Kapasitetsøkning']/self.factor
                self.C_CAP_LINK[i, j, m, r] = capacity_exp_data2.iloc[0]['Kostnad']/self.factor


        "Discount rate"
        self.risk_free_interest_rate = 0.02  # 2%
        self.D_DISCOUNT_RATE = {self.T_TIME_PERIODS[i]: (1 / (1 + self.risk_free_interest_rate)) ** self.T_INTERVALS[i]
                                for i in range(len(self.T_TIME_PERIODS))}

        self.D_DEMAND = {(o, d, p, t): 0 for (o, d, p) in self.ODP for t in
                         self.T_TIME_PERIODS}  # (o,d,p) Maybe no need to initialize this one

        for index, row in self.pwc_aggr.iterrows():
            if row['from_fylke_zone'] != row['to_fylke_zone'] and row['from_fylke_zone'] in self.N_NODES and row['to_fylke_zone'] in self.N_NODES:
                self.D_DEMAND[(row['from_fylke_zone'], row['to_fylke_zone'], row['commodity_aggr'],
                           int(row['year']))] = float(row['amount_tons'])
            elif row['from_fylke_zone'] == row['to_fylke_zone'] and row['from_fylke_zone'] in self.N_NODES and row['to_fylke_zone'] in self.N_NODES:
                self.D_DEMAND[(row['from_fylke_zone'], row['to_fylke_zone'], row['commodity_aggr'],
                               int(row['year']))] = 0

                        
        
        self.Big_M = {l: [] for l in self.L_LINKS_UPG}
        for l in self.L_LINKS_UPG:
            self.Big_M[l] =  self.Y_BASE_CAP[l] + self.Y_ADD_CAP[l]*self.INV_LINK[l] 
    
        
        # --------------------------
        # --------------------------
        # CHARGING ARC CONSTRAINT
        # --------------------------
        # --------------------------
        if self.run_file == "sets":
           charging_data = pd.read_excel(r'charging_data.xlsx')#, sheet_name='Sea')
        if self.run_file == "main":
           charging_data = pd.read_excel(r'Data/charging_data.xlsx')#, sheet_name='Sea')
        self.CHARGING_TECH = []
        for index,row in charging_data.iterrows():
            #print((row["Mode"],row["Fuel"]))
            self.CHARGING_TECH.append((row["Mode"],row["Fuel"]))
        # all arcs (one per arc pair ij/ji) with mode Road and fuels Battery or Hydrogen
        self.CHARGING_ARCS = []
        for a in self.A_ARCS:
           for (m, f) in self.CHARGING_TECH:
               if a[2] == m and a[3] == f:
                   if a[0] not in ["Europa", "Sør-Sverige", "Nord-Sverige"] or a[1] not in ["Europa",
                                                                                            "Sør-Sverige",
                                                                                            "Nord-Sverige"]:
                       if (a[1], a[0], a[2], a[3], a[4]) not in self.CHARGING_ARCS:
                           self.CHARGING_ARCS.append(a)
        self.CHARGING_AT = [a + (t,) for a in self.CHARGING_ARCS for t in self.T_TIME_PERIODS]
        
        # -----------------
        #      PARAMS
        # -----------------
        # base capacity on a pair of arcs (ij/ji - mfr), often 0 since no charging infrastructure exists now
        self.BASE_CHARGE_CAP = {a: 0 for a in self.CHARGING_ARCS}
        # ALLE DISTANSER PÅ ROAD SOM TRENGER CHARGING INFRASTUCTURE
        self.CHARGE_ROAD_DISTANCE = {a: road_distances_dict[(a[0], a[1])] for a in self.CHARGING_ARCS}
        # self.CHARGE_ROAD_DISTANCE = {mf:  for mf in self.CHARGING_TECH}
        self.ROAD_DIST_COST = {a: 9999 for a in self.CHARGING_ARCS}  # for p in self.P_PRODUCTS}
        max_truck_cap = 30  # random average in tonnes, should be product based? or fuel based??
        for (i, j, m, f, r) in self.CHARGING_ARCS:
            data_index = charging_data.loc[(charging_data['Mode'] == m) & (charging_data['Fuel'] == f)]
            self.ROAD_DIST_COST[(i, j, m, f, r)] = (self.CHARGE_ROAD_DISTANCE[(i, j, m, f, r)]
                                                   / data_index.iloc[0]["Max_station_dist"]
                                                   * data_index.iloc[0]["Station_cost"]
                                                   / (data_index.iloc[0][
                                                          "Trucks_filled_daily"] * max_truck_cap * 365))  # 0.7 or not???

        ######Innlesning av scenarier 

        
        if self.run_file == "main":
            scen_data = pd.read_csv(r'Data/NY Maturities, 27 scenarios.csv')
        if self.run_file == "sets":
            scen_data = pd.read_csv(r'NY Maturities, 27 scenarios.csv')
        
        
        
        self.all_scenarios = []
        for index, row in scen_data.iterrows():
            if row["Scenario"] not in self.all_scenarios:
                self.all_scenarios.append(row["Scenario"])
        internat_cap = 240000000
        total_trans_dict = {'Road': internat_cap*0.4, 'Rail': internat_cap*0.05, 'Sea': internat_cap*0.75}

        fuel_groups = {0: ['Battery electric', 'Battery train'], 1: ['Hydrogen', 'Ammonia'], 
                       2: ['Biodiesel (HVO)', 'Biogas', 'Biodiesel']}

        self.base_scenarios = ['HHH', 'LLL', 'HHL', 'HLH', 'HLL', 'LHH', 'LHL', 'LLH']
        self.three_scenarios = ['HHH', 'MMM', 'LLL']

        self.det_eqvs = {'AVG1': self.base_scenarios,
                         'AVG11': self.base_scenarios,
                         'AVG2': self.three_scenarios,
                         'AVG22': self.three_scenarios,
                         'AVG3': self.three_scenarios,
                         'AVG33': self.three_scenarios}  # yields same avg as all scenarios

        if self.scenario in self.det_eqvs.keys():
            # create deterministIc equivalents
            for w in self.det_eqvs[self.scenario]:
                for index, row in scen_data[scen_data['Scenario'] == w].iterrows():
                    for (m, f) in self.NEW_MF_LIST:
                        if row['Mode'] == m and row['Fuel'] == f:
                            total_trans = total_trans_dict[row['Mode']]
                            self.Y_TECH[(row['Mode'], row['Fuel'], 2020)] += (row['2020'] * total_trans) / (
                                        100 * self.factor * len(self.det_eqvs[self.scenario]))
                            self.Y_TECH[(row['Mode'], row['Fuel'], 2025)] += (row['2025'] * total_trans) / (
                                        100 * self.factor * len(self.det_eqvs[self.scenario]))
                            self.Y_TECH[(row['Mode'], row['Fuel'], 2030)] += (row['2030'] * total_trans) / (
                                        100 * self.factor * len(self.det_eqvs[self.scenario]))
                            self.Y_TECH[(row['Mode'], row['Fuel'], 2040)] += (row['2040'] * total_trans) / (
                                        100 * self.factor * len(self.det_eqvs[self.scenario]))
                            self.Y_TECH[(row['Mode'], row['Fuel'], 2050)] += (row['2050'] * total_trans) / (
                                        100 * self.factor * len(self.det_eqvs[self.scenario]))

        else:
            scen_string = self.scenario
            for w in ['HHH', 'MMM', 'LLL']:
                for key in fuel_groups:
                    if scen_string[key] == w[key]:
                        for index, row in scen_data[scen_data['Scenario'] == w].iterrows():
                            if row['Fuel'] in fuel_groups[key]:
                                total_trans = total_trans_dict[row['Mode']]
                                self.Y_TECH[(row['Mode'], row['Fuel'], 2020)] = (row[
                                                          '2020'] * total_trans / 100) / self.factor
                                self.Y_TECH[(row['Mode'], row['Fuel'], 2025)] = (row[
                                                           '2025'] * total_trans / 100) / self.factor
                                self.Y_TECH[(row['Mode'], row['Fuel'], 2030)] = (row[
                                                              '2030'] * total_trans / 100) / self.factor
                                self.Y_TECH[(row['Mode'], row['Fuel'], 2040)] = (row[
                                                          '2040'] * total_trans / 100) / self.factor
                                self.Y_TECH[(row['Mode'], row['Fuel'], 2050)] = (row[
                                                        '2050'] * total_trans / 100) / self.factor

        VSS = False
        if VSS:
            # colnames = ['','from', 'to', 'Mode', 'fuel', 'route','product','weight','time_period','scenario']
            if self.run_file == "main":
                first_stage_data_x = pd.read_csv(r'Data/Instance_results_with_data/Instance3/Inst_3_X_flow.csv', encoding='utf8')
                first_stage_data_h = pd.read_csv(r'Data/Instance_results_with_data/Instance3/Inst_3_H_flow.csv',
                                                 converters={'path': eval}, encoding='utf8')
                first_stage_data_z_inv_cap = pd.read_csv(r'Data/Instance_results_with_data/Instance3/Inst_3_z_inv_cap.csv',
                                                         encoding='utf8')
                first_stage_data_z_inv_node = pd.read_csv(r'Data/Instance_results_with_data/Instance3/Inst_3_z_inv_node.csv',
                                                          encoding='utf8')
                first_stage_data_z_inv_upg = pd.read_csv(r'Data/Instance_results_with_data/Instance3/Inst_3_z_inv_upg.csv',
                                                         encoding='utf8')
                first_stage_data_charge_link = pd.read_csv(r'Data/Instance_results_with_data/Instance3/Inst_3_charge_link.csv',
                                                           encoding='utf8')
                first_stage_data_emission_violation = pd.read_csv(
                    r'Data/Instance_results_with_data/Instance3/Inst_3_emission_violation.csv', encoding='utf8')
            if self.run_file == "sets":
                first_stage_data_x = pd.read_csv(r'Instance_results_with_data/Instance3/Inst_3_X_flow.csv', encoding='utf8')
                first_stage_data_h = pd.read_csv(r'Instance_results_with_data/Instance3/Inst_3_H_flow.csv',
                                                 converters={'path': eval}, encoding='utf8')
                first_stage_data_z_inv_cap = pd.read_csv(r'Instance_results_with_data/Instance3/Inst_3_z_inv_cap.csv',
                                                         encoding='utf8')
                first_stage_data_z_inv_node = pd.read_csv(r'Instance_results_with_data/Instance3/Inst_3_z_inv_node.csv',
                                                          encoding='utf8')
                first_stage_data_z_inv_upg = pd.read_csv(r'Instance_results_with_data/Instance3/Inst_3_z_inv_upg.csv',
                                                         encoding='utf8')
                first_stage_data_charge_link = pd.read_csv(
                    r'Instance_results_with_data/Instance3/Inst_3_charge_link.csv',
                    encoding='utf8')
                first_stage_data_emission_violation = pd.read_csv(
                    r'Instance_results_with_data/Instance3/Inst_3_emission_violation.csv', encoding='utf8')

            # print(first_stage_data_z_inv_cap)
            self.APT_fs = [a + (p,) + (t,) for a in self.A_ARCS for p in self.P_PRODUCTS for t in
                           [2020, 2025]]
            self.KPT_fs = [(str(k), p, t) for k in self.K_PATHS for p in self.P_PRODUCTS for t in [2020, 2025]]
            self.LT_CAP_fs = [l + (t,) for l in self.L_LINKS_CAP for t in [2020, 2025]]
            self.NMBT_CAP_fs = [(i, m) + (b,) + (t,) for (i, m) in self.NM_LIST_CAP for b in self.TERMINAL_TYPE[m] for t
                                in [2020, 2025]]
            self.LUT_UPG_fs = [l + (u,) + (t,) for l in self.L_LINKS_UPG for u in self.UL_UPG[l] for t in [2020, 2025]]
            self.CHARGING_AT_fs = [a + (t,) for a in self.CHARGING_ARCS for t in [2020, 2025]]
            self.TS_fs = [2020, 2025]

            self.first_stage_x = {apt: 0 for apt in self.APT_fs}
            self.first_stage_h = {kpt: 0 for kpt in self.KPT_fs}
            self.first_stage_z_inv_cap = {lt: 0 for lt in self.LT_CAP_fs}
            self.first_stage_z_inv_node = {imbt: 0 for imbt in self.NMBT_CAP_fs}
            self.first_stage_z_inv_upg = {lut: 0 for lut in self.LUT_UPG_fs}
            self.first_stage_charge_link = {at: 0 for at in self.CHARGING_AT_fs}
            self.first_stage_emission_violation = {t: 0 for t in [2020, 2025]}

            for t in [2020, 2025]:
                for index, row in first_stage_data_x[first_stage_data_x['time_period'] == t].iterrows():
                    if row['scenario'] == 'AVG1':  # egentlig AVG1!!! hvis vi bare regner ut VSS for base case
                        self.first_stage_x[row['from'], row['to'], row['Mode'], row['fuel'], row['route'],
                                           row['product'], row['time_period']] = row['weight']

                for index, row in first_stage_data_h[first_stage_data_h['time_period'] == t].iterrows():
                    if row['scenario'] == 'AVG1':  # egentlig AVG1!!! hvis vi bare regner ut VSS for base case
                        self.first_stage_h[str(row['path']), row['product'], row['time_period']] = row['weight']

                for index, row in first_stage_data_z_inv_cap[first_stage_data_z_inv_cap['time_period'] == t].iterrows():
                    if row['scenario'] == 'AVG1':  # egentlig AVG1!!! hvis vi bare regner ut VSS for base case
                        self.first_stage_z_inv_cap[
                            row['from'], row['to'], row['Mode'], row['route'], row['time_period']] = row['weight']

                for index, row in first_stage_data_z_inv_node[
                    first_stage_data_z_inv_node['time_period'] == t].iterrows():
                    if row['scenario'] == 'AVG1':  # egentlig AVG1!!! hvis vi bare regner ut VSS for base case
                        self.first_stage_z_inv_node[
                            row['Node'], row['Mode'], row['terminal_type'], row['time_period']] = row['weight']

                for index, row in first_stage_data_z_inv_upg[first_stage_data_z_inv_upg['time_period'] == t].iterrows():
                    if row['scenario'] == 'AVG1':  # egentlig AVG1!!! hvis vi bare regner ut VSS for base case
                        self.first_stage_z_inv_upg[row['from'], row['to'], row['Mode'], row['route'],
                                                   row['upgrade'], row['time_period']] = row['weight']

                for index, row in first_stage_data_charge_link[
                    first_stage_data_charge_link['time_period'] == t].iterrows():
                    if row['scenario'] == 'AVG1':  # egentlig AVG1!!! hvis vi bare regner ut VSS for base case
                        self.first_stage_charge_link[row['from'], row['to'], row['Mode'], row['fuel'], row['route'],
                                                     row['time_period']] = row['weight']

                for index, row in first_stage_data_emission_violation[
                    first_stage_data_emission_violation['time_period'] == t].iterrows():
                    if row['scenario'] == 'AVG1':  # egentlig AVG1!!! hvis vi bare regner ut VSS for base case
                        self.first_stage_emission_violation[row['time_period']] = row['weight']



#x = TransportSets("HHH",1,"avg_costs","100%")



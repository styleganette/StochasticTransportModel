import pandas as pd
import itertools
import numpy as np
import operator
pd.set_option("display.max_rows", None, "display.max_columns", None)
pd.options.display.width = 0
pd.options.display.max_colwidth = 100
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import re
from Data.Create_Sets_Class import TransportSets


data = TransportSets('HHH',1,"avg_costs","75%")


instance_dict = {'1': {'sol_met':'ef', 'scen_struct':1, 'co2_price':1, 'costs':"avg_costs", 'probs': "equal", 'emission_reduction': "75%"}, # base case
            '2': {'sol_met':'ef', 'scen_struct':2, 'co2_price':1, 'costs':"avg_costs", 'probs': "equal", 'emission_reduction': "75%"},  # 3 scen
            '3': {'sol_met':'ef', 'scen_struct':4, 'co2_price':1, 'costs':"avg_costs", 'probs': "equal", 'emission_reduction': "75%"},  #deterministic version 8 scen!
            '4': {'sol_met':'ef', 'scen_struct':1, 'co2_price':1, 'costs':"avg_costs", 'probs': "high", 'emission_reduction': "75%"},   # high maturity prob
            '5': {'sol_met':'ef', 'scen_struct':1, 'co2_price':1, 'costs':"avg_costs", 'probs': "low", 'emission_reduction': "75%"},    # low maturity prob
            '6': {'sol_met':'ef', 'scen_struct':1, 'co2_price':1, 'costs':"avg_costs", 'probs': "low_extremes", 'emission_reduction': "75%"}, # low LLL/HHH
            '7': {'sol_met':'ef', 'scen_struct':1, 'co2_price':1, 'costs':"low_costs", 'probs': "equal", 'emission_reduction': "75%"},  # low fuel costs
            '8': {'sol_met':'ef', 'scen_struct':1, 'co2_price':1, 'costs':"high_costs", 'probs': "equal", 'emission_reduction': "75%"},  # high fuel costs
            '9': {'sol_met':'ef', 'scen_struct':1, 'co2_price':2, 'costs':"avg_costs", 'probs': "equal", 'emission_reduction': "75%"},  # high carbon price
            '10': {'sol_met':'ef', 'scen_struct':1, 'co2_price':2, 'costs':"low_costs", 'probs': "equal", 'emission_reduction': "75%"}, # base case# high carbon, low fuel costs
            '11': {'sol_met':'ef', 'scen_struct':3, 'co2_price':1, 'costs':"avg_costs", 'probs': "equal", 'emission_reduction': "75%"}  # 27 scen
    }
# SET THESE VALUES:

inst_A = '1' #must be string
inst_B = '2' #must be string

if inst_A == "3":
    single_scenA = "AVG1"
elif inst_A in ['21','22']:
    single_scenA = "LHH"
else:
    single_scenA = "HHH"

if inst_B == "3":
    single_scenB = "AVG1"
elif inst_B in ['21','22']:
    single_scenB = "LHH"
else:
    single_scenB = "HHH"

print("First instance specs: ", instance_dict[inst_A])
print("Second instance specs: ", instance_dict[inst_B])


#single_scenA = "HHH" #REMOVE IF NORMAL INSTANCES
#single_scenB = "HHH" #REMOVE IF NORMAL INSTANCES



tonnes_vs_tonnkm = "tonnKM"


folder_path = "Data/Instance_results_with_data/"
#instA_x_flow = pd.read_csv(r"Data/Instance_results_with_data/Instance" + inst_A + "/Inst_" + inst_A + "_X_flow.csv")
#instB_x_flow = pd.read_csv(r"Data/Instance_results_with_data/Instance" + inst_B + "/Inst_" + inst_B + "_X_flow.csv")

instA_x_flow = pd.read_csv(folder_path + "Instance" + inst_A + "/Inst_" + inst_A + "_X_flow.csv")
instB_x_flow = pd.read_csv(folder_path + "Instance" + inst_B + "/Inst_" + inst_B + "_X_flow.csv")


#inst_determ = pd.read_csv(r"Data/Instance_results_with_data/Instance" +instance_runB + "/Inst_" +instance_runB+ "_X_flow.csv")

instA_x_flow = instA_x_flow[(instA_x_flow["scenario"] == single_scenA) & (instA_x_flow["time_period"] <= 2025)] #["amount_tons"].sum()
instB_x_flow = instB_x_flow[(instB_x_flow["scenario"] == single_scenB) & (instB_x_flow["time_period"] <= 2025)] #["amount_tons"].sum()

if tonnes_vs_tonnkm == "tonnKM":
    for index,row in instA_x_flow.iterrows():
        instA_x_flow.loc[index, 'weight'] = row["weight"] * data.AVG_DISTANCE[(
                row["from"], row["to"], row["Mode"], row["route"])]
    for index, row in instB_x_flow.iterrows():
        instB_x_flow.loc[index, 'weight'] = row["weight"] * data.AVG_DISTANCE[(
            row["from"], row["to"], row["Mode"], row["route"])]

instA_x_flow = instA_x_flow.drop('Unnamed: 0', 1)
instA_x_flow = instA_x_flow.drop('route', 1)
instB_x_flow = instB_x_flow.drop('Unnamed: 0', 1)
instB_x_flow = instB_x_flow.drop('route', 1)

inst_dict = {inst_A : instA_x_flow,
             inst_B : instB_x_flow}
print("-------------")
print("----------------------------")
print("FIRST SHOWING MODE-FUEL PERCENTAGES FOR EACH YEAR/MODE/FUEL FOR BOTH INSTANCES")
print("----------------------------")
print("-------------")
for inst_name in inst_dict.keys():
    for year in [2020,2025]:
        print("-------------")
        print("Inst",inst_name,year, "in",tonnes_vs_tonnkm)
        print("-------------")
        inst = inst_dict[inst_name]
        grouped_sum_print = inst[inst["time_period"] == year].groupby(["time_period", 'Mode', 'fuel']).sum()
        total = grouped_sum_print["weight"].sum()
        grouped_sum_print["ratio in %"] = grouped_sum_print["weight"] / total * 100
        print(grouped_sum_print)

"""print(" ")
print("--------------------------")
print("------NEXT INSTANCE-------")
print("--------------------------")
print(" ")
for year in [2020,2025]:
    print("-------------")
    print(tonnes_vs_tonnkm, year, " for instance ", instance_runB)
    print("-------------")
    grouped_sum2 = instB[instB["time_period"] == year].groupby(["time_period",'Mode', 'fuel']).sum()
    total2 = grouped_sum2["weight"].sum()
    grouped_sum2["ratio in %"] = grouped_sum2["weight"] / total2 * 100
    #print(grouped_sum2.reset_index())
    print(grouped_sum2.index)

"""

print("-------------")
print("----------------------------")
print("SHOWING RELATIVE CHANGE IN X_FLOW FOR YEAR/MODE/FUEL BETWEEN INSTANCES")
print("----------------------------")
print("-------------")

grouped_sum = instA_x_flow.groupby(["time_period", 'Mode', 'fuel']).sum()
grouped_sum2 = instB_x_flow.groupby(["time_period", 'Mode', 'fuel']).sum()

for t in [2020,2025]:
    for m in data.M_MODES:
        for f in data.FM_FUEL[m]:
            if (t,m,f) in grouped_sum2.index and (t,m,f) in grouped_sum.index:
                print(t,m,f)
                print("Inst ", inst_A, ": ", grouped_sum._get_value((t, m, f), "weight"))
                print("Inst ", inst_B, ": ", grouped_sum2._get_value((t, m, f), "weight"))
                print("Inst", inst_A, "- inst", inst_B, ": ", grouped_sum._get_value((t, m, f), "weight") - grouped_sum2._get_value((t, m, f), "weight"))
                print("Inst", inst_B, "/ inst", inst_A, ": ", grouped_sum2._get_value((t, m, f), "weight") / grouped_sum._get_value((t, m, f), "weight"))

            elif (t, m, f) in grouped_sum2.index and (t, m, f) not in grouped_sum.index:
                print(t, m, f)
                print("Only in inst", inst_B, ": ", grouped_sum2._get_value((t, m, f), "weight"))
            elif (t, m, f) not in grouped_sum2.index and (t, m, f) in grouped_sum.index:
                print(t, m, f)
                print("Only in inst", inst_A, ": ", grouped_sum._get_value((t, m, f), "weight"))
            else:
                print("Not present: ",t,m,f)
            print("---------")
                #df2 = grouped_sum2[(grouped_sum2['Mode'] == m) & (grouped_sum2['fuel'] == f)]
                #df1 = grouped_sum[(grouped_sum['Mode'] == m) & (grouped_sum['fuel'] == f)] #(grouped_sum['time_period'] == t) &


print("-------------")
print("----------------------------")
print("PRINTING DIFFERENCES IN RAIL CAP INVESTMENTS BETWEEN INSTANCES")
print("----------------------------")
print("-------------")

instA_z_inv_cap = pd.read_csv(folder_path + "Instance" + inst_A + "/Inst_" + inst_A + "_z_inv_cap.csv")
instB_z_inv_cap = pd.read_csv(folder_path + "Instance" + inst_B + "/Inst_" + inst_B + "_z_inv_cap.csv")

#inst_determ = pd.read_csv(r"Data/Instance_results_with_data/Instance" +instance_runB + "/Inst_" +instance_runB+ "_X_flow.csv")

instA_z_inv_cap = instA_z_inv_cap[(instA_z_inv_cap["scenario"] == single_scenA) & (instA_z_inv_cap["time_period"] <= 2025)] #["amount_tons"].sum()
instB_z_inv_cap = instB_z_inv_cap[(instB_z_inv_cap["scenario"] == single_scenB) & (instB_z_inv_cap["time_period"] <= 2025)] #["amount_tons"].sum()

if len(instA_z_inv_cap) == len(instB_z_inv_cap):
    print("Equal length of z_inv_cap:", len(instB_z_inv_cap))
else:
    print("Z_cap_inv not equal length:", len(instA_z_inv_cap),"vs",len(instB_z_inv_cap))


print("First check if all investments done in inst ",inst_A," are done in inst", inst_B,":")
for index,row in instA_z_inv_cap.iterrows():
    if len(instB_z_inv_cap[(instB_z_inv_cap["from"] == row["from"]) & (instB_z_inv_cap["to"]==row["to"]) &
                           (instB_z_inv_cap["time_period"]==row["time_period"]) & (instB_z_inv_cap["route"]==row["route"])]) > 0:
        print("Same inv:",row["from"],row["to"],row["Mode"],row["time_period"])
    else:
        print("Investment ONLY made in INST",inst_A,":", row["from"], row["to"], row["Mode"], row["time_period"])

print(" ")
print("Then check if all investments done in inst ", inst_B," are done in inst ",inst_A, ":")
for index, row in instB_z_inv_cap.iterrows():
    if len(instA_z_inv_cap[(instA_z_inv_cap["from"] == row["from"]) & (instA_z_inv_cap["to"] == row["to"]) &
                           (instA_z_inv_cap["time_period"] == row["time_period"]) & (
                                   instA_z_inv_cap["route"] == row["route"])]) > 0:
        print("Same inv:", row["from"], row["to"], row["Mode"], row["time_period"])
    else:
        print("Investment ONLY made in INST",inst_B,":", row["from"], row["to"], row["Mode"], row["time_period"])


print("-------------")
print("----------------------------")
print("PRINTING DIFFERENCES IN NODE INVESTMENTS BETWEEN INSTANCES")
print("----------------------------")
print("-------------")

instA_z_inv_node = pd.read_csv(folder_path + "Instance" + inst_A + "/Inst_" + inst_A + "_z_inv_node.csv")
instB_z_inv_node = pd.read_csv(folder_path + "Instance" + inst_B + "/Inst_" + inst_B + "_z_inv_node.csv")


instA_z_inv_node = instA_z_inv_node[(instA_z_inv_node["scenario"] == single_scenA) & (instA_z_inv_node["time_period"] <= 2025)] #["amount_tons"].sum()
instB_z_inv_node = instB_z_inv_node[(instB_z_inv_node["scenario"] == single_scenB) & (instB_z_inv_node["time_period"] <= 2025)] #["amount_tons"].sum()
if len(instA_z_inv_node) == len(instB_z_inv_node):
    print("Equal length of z_inv_node:", len(instB_z_inv_node))
else:
    print("Z_inv_node not equal length:", len(instA_z_inv_node),"vs",len(instB_z_inv_node))


print("First check if all NODE investments done in inst ",inst_A," are done in inst", inst_B,":")
for index,row in instA_z_inv_node.iterrows():
    if len(instB_z_inv_node[(instB_z_inv_node["Node"] == row["Node"]) & (instB_z_inv_node["Mode"]==row["Mode"]) &
                           (instB_z_inv_node["time_period"]==row["time_period"]) & (instB_z_inv_node["terminal_type"]==row["terminal_type"])]) > 0:
        print("Same inv:",row["Node"],row["Mode"],row["terminal_type"],row["time_period"])
    else:
        print("Investment ONLY made in INST",inst_A,":", row["Node"],row["Mode"],row["terminal_type"],row["time_period"])

print(" ")
print("Then check if all NODE investments done in inst ", inst_B," are done in inst ",inst_A, ":")
for index, row in instB_z_inv_node.iterrows():
    if len(instA_z_inv_node[(instA_z_inv_node["Node"] == row["Node"]) & (instA_z_inv_node["Mode"] == row["Mode"]) &
                           (instA_z_inv_node["time_period"] == row["time_period"]) & (
                                   instA_z_inv_node["terminal_type"] == row["terminal_type"])]) > 0:
        print("Same inv:", row["Node"], row["Mode"], row["terminal_type"], row["time_period"])
    else:
        print("Investment ONLY made in INST",inst_B,":", row["Node"],row["Mode"],row["terminal_type"],row["time_period"])

print("-------------")
print("----------------------------")
print("PRINTING DIFFERENCES IN UPGRADE INVESTMENTS BETWEEN INSTANCES")
print("----------------------------")
print("-------------")

instA_z_inv_upg = pd.read_csv(folder_path + "Instance" + inst_A + "/Inst_" + inst_A + "_z_inv_upg.csv")
instB_z_inv_upg = pd.read_csv(folder_path + "Instance" + inst_B + "/Inst_" + inst_B + "_z_inv_upg.csv")

instA_z_inv_upg = instA_z_inv_upg[(instA_z_inv_upg["scenario"] == single_scenA) & (instA_z_inv_upg["time_period"] <= 2025)] #["amount_tons"].sum()
instB_z_inv_upg = instB_z_inv_upg[(instB_z_inv_upg["scenario"] == single_scenB) & (instB_z_inv_upg["time_period"] <= 2025)] #["amount_tons"].sum()
if len(instA_z_inv_upg) == len(instB_z_inv_upg):
    print("Equal length of z_inv_upg:", len(instB_z_inv_upg))
else:
    print("Z_inv_upg not equal length:", len(instA_z_inv_upg),"vs",len(instB_z_inv_upg))


print("First check if all UPGRADE investments done in inst ",inst_A," are done in inst", inst_B,":")
for index,row in instA_z_inv_upg.iterrows():
    if len(instB_z_inv_upg[(instB_z_inv_upg["from"] == row["from"]) & (instB_z_inv_upg["Mode"]==row["Mode"]) &
                           (instB_z_inv_upg["time_period"]==row["time_period"]) & (instB_z_inv_upg["to"]==row["to"])
                              & (instB_z_inv_upg["upgrade"] == row["upgrade"])]) > 0:
        print("Same inv:",row["from"],row["to"],row["Mode"],row["upgrade"],row["time_period"])
    else:
        print("Investment ONLY made in INST",inst_A,":", row["from"],row["to"],row["Mode"],row["upgrade"],row["time_period"])

print(" ")
print("Then check if all UPGRADE investments done in inst ", inst_B," are done in inst ",inst_A, ":")
for index, row in instB_z_inv_upg.iterrows():
    if len(instA_z_inv_upg[(instA_z_inv_upg["from"] == row["from"]) & (instA_z_inv_upg["Mode"] == row["Mode"]) &
                           (instA_z_inv_upg["time_period"] == row["time_period"]) & (
                                   instA_z_inv_upg["to"] == row["to"]) & (instA_z_inv_upg["upgrade"] == row["upgrade"])]) > 0:
        print("Same inv:", row["from"],row["to"],row["Mode"],row["upgrade"],row["time_period"])
    else:
        print("Investment ONLY made in INST",inst_B,":", row["from"],row["to"],row["Mode"],row["upgrade"],row["time_period"])

print("-------------")
print("----------------------------")
print("PRINTING DIFFERENCES IN CHARGING INFRASTRUCTURE")
print("----------------------------")
print("-------------")

instA_charging = pd.read_csv(folder_path + "Instance" + inst_A + "/Inst_" + inst_A + "_charge_link.csv")
instB_charging = pd.read_csv(folder_path + "Instance" + inst_B + "/Inst_" + inst_B + "_charge_link.csv")

instA_charging = instA_charging[(instA_charging["scenario"] == single_scenA) & (instA_charging["time_period"] <= 2025)] #["amount_tons"].sum()
instB_charging = instB_charging[(instB_charging["scenario"] == single_scenB) & (instB_charging["time_period"] <= 2025)] #["amount_tons"].sum()
if len(instA_charging) == len(instB_charging):
    print("Equal length of link_charge:", len(instB_charging))
else:
    print("Link_charge not equal length:", len(instA_charging),"vs",len(instB_charging))

print(instA_charging)
print(instB_charging)

print("First check if all CHARGING INFRASTRUCTURE made in inst ",inst_A," are done in inst", inst_B,":")
for index,row in instA_charging.iterrows():
    instB_df = (instB_charging[(instB_charging["from"] == row["from"]) & (instB_charging["Mode"]==row["Mode"]) &
                           (instB_charging["time_period"]==row["time_period"]) & (instB_charging["to"]==row["to"])
                              & (instB_charging["fuel"] == row["fuel"])])
    if len(instB_df) > 0:
        print(row["from"],row["to"],row["Mode"],row["fuel"],row["time_period"])
        print("INST ",inst_A, ":",row["weight"])
        print("INST ",inst_B, ":",instB_df["weight"].iloc[0])
        print("INST",inst_B,"/ INST",inst_A," ---> ",instB_df["weight"].iloc[0]/row["weight"])
    else:
        print("Investment ONLY made in INST",inst_A,":", row["from"],row["to"],row["Mode"],row["fuel"],row["time_period"],row["weight"])

print(" ")
print("Then check if all CHARGING INFRASTRUCTURE made in inst ", inst_B," are done in inst ",inst_A, ":")
for index,row in instB_charging.iterrows():
    instA_df = (instA_charging[(instA_charging["from"] == row["from"]) & (instA_charging["Mode"]==row["Mode"]) &
                           (instA_charging["time_period"]==row["time_period"]) & (instA_charging["to"]==row["to"])
                              & (instA_charging["fuel"] == row["fuel"])])
    if len(instA_df) > 0:
        print(row["from"],row["to"],row["Mode"],row["fuel"],row["time_period"])
        print("INST ",inst_B, ":",row["weight"])
        print("INST ",inst_A, ":",instA_df["weight"].iloc[0])
        print("INST",inst_A,"/ INST",inst_B," ---> ",instA_df["weight"].iloc[0]/row["weight"])
    else:
        print("Investment ONLY made in INST",inst_B,":", row["from"],row["to"],row["Mode"],row["fuel"],row["time_period"],row["weight"])

print("-------------")
print("----------------------------")
print("PRINTING MUTLIMODE PATH STUFF")
print("----------------------------")
print("-------------")

instA_h_flow = pd.read_csv(folder_path + "Instance" + inst_A + "/Inst_" + inst_A + "_H_flow.csv")
instB_h_flow = pd.read_csv(folder_path + "Instance" + inst_B + "/Inst_" + inst_B + "_H_flow.csv")

instA_h_flow = instA_h_flow[(instA_h_flow["scenario"] == single_scenA) & (instA_h_flow["time_period"] <= 2025)] #["amount_tons"].sum()
instB_h_flow = instB_h_flow[(instB_h_flow["scenario"] == single_scenB) & (instB_h_flow["time_period"] <= 2025)] #["amount_tons"].sum()
if len(instA_h_flow) == len(instB_h_flow):
    print("Equal number of paths:", len(instB_h_flow))
else:
    print("Link_charge not equal length:", len(instA_h_flow),"vs",len(instB_h_flow))

instA_h_flow = instA_h_flow.drop('Unnamed: 0', 1)
instA_h_flow = instA_h_flow.drop('time_period', 1)
instB_h_flow = instB_h_flow.drop('Unnamed: 0', 1)
instB_h_flow = instB_h_flow.drop('time_period', 1)

instA_h_flow_groups = instA_h_flow.groupby(['path']).sum()
instB_h_flow_groups = instB_h_flow.groupby(['path']).sum()

instA_h_flow_groups = instA_h_flow_groups.reset_index().sort_values("weight",ascending=False)
instB_h_flow_groups = instB_h_flow_groups.reset_index().sort_values("weight",ascending=False)
instA_h_flow_groups = instA_h_flow_groups.rename(columns = {'weight':'weight_inst_'+inst_A})
instB_h_flow_groups = instB_h_flow_groups.rename(columns = {'weight':'weight_inst_'+inst_B})

#print(instA_h_flow_groups.head(20))
#print(instB_h_flow_groups.head(20))

merged_df = instA_h_flow_groups.merge(instB_h_flow_groups, on = "path",how='outer')
print("Length of",inst_A,":",len(instA_h_flow_groups))
print("Length of",inst_B,":",len(instB_h_flow_groups))
print("Length of merged version:",len(merged_df))

print("Comparing the most used paths (sorted descending on inst",inst_A,"):")
print(merged_df.head(20))

merge_domestic = merged_df.copy()
for index,row in merge_domestic.iterrows():
    if "Europa" in row["path"] or "Verden" in row["path"]:
        merge_domestic.drop(index, inplace=True)

print("Only domestic (ish) paths: ")
print(merge_domestic.head(10))

merge_copy = merged_df.copy()
for index,row in merge_copy.iterrows():
    if "Sea" in row["path"] and "Road" in row["path"]:
        pass
    elif "Sea" in row["path"] and "Rail" in row["path"]:
        pass
    elif "Road" in row["path"] and "Rail" in row["path"]:
        pass
    else:
        merge_copy.drop(index, inplace=True)

merge_copy = merge_copy.sort_values("weight_inst_"+inst_A,ascending=False)
print("Number of multimode-paths used: ",len(merge_copy))

print(merge_copy.head(20))

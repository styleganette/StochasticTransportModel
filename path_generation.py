
import pandas as pd
import networkx as nx
from Data.Create_Sets_Class import TransportSets
from itertools import islice
# -----------------
# -----------------------------
# --------------------------------------------
#           PATH GENERATION
# --------------------------------------------
# -----------------------------
# -----------------


data = TransportSets('HHH',1,"avg_costs","100%")

arr_aggr_dict = {}

def bfs2(graph, start, end):
    # maintain a queue of paths
    queue = []
    # push the first path into the queue
    queue.append([start])
    while queue:
        # get the first path from the queue
        path = queue.pop(0)
        # get the last node from the path
        node = path[-1]
        # path found
        if node == end:
            return path
        # enumerate all adjacent nodes, construct a
        # new path and push it into the queue
        for adjacent in graph.get(node, []):
            new_path = list(path)
            new_path.append(adjacent)
            queue.append(new_path)


def k_shortest_paths(G, source, target, k, weight=None):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), int(k)))


print(len(data.L_LINKS_DIR))  # 366 directed links/single link paths = 156 + 182 + 28
print(len(data.L_LINKS))  # 183 modal links (1/2)

data.K_LINK_PATHS = []

for link in data.L_LINKS_DIR:
    data.K_LINK_PATHS.append([link])

print("First add all direct link paths: ", len(data.K_LINK_PATHS))
# ----------------------
# -----------------------------
# -------------------------------------
# NEW LINK FORMULATION WITHOUT DIRECT LINKS - START
# -------------------------------------
# -----------------------------
# ----------------------
road_paths = {}
for key in data.allowed_road.keys():
    for key2 in data.allowed_road.keys():
        path = bfs2(data.allowed_road, key, key2)
        if len(path) > 2:
            if "Oslo" in path and key2 == "Stavanger":
                path.remove("Bergen")
                path.remove("Stavanger")
                path.append("Skien")
                path.append("Kristiansand")
                path.append("Stavanger")
                road_paths[(key, key2)] = path
            elif key == "Stavanger" and "Oslo" in path:
                path.remove("Bergen")
                path.insert(1,"Skien")
                path.insert(1,"Kristiansand")
                road_paths[(key, key2)] = path
            elif path[0] == "Kristiansand" and "Trondheim" in path:
                for e in range(len(path)):
                    if path[e] == "Stavanger":
                        path[e] = "Skien"
                    elif path[e] == "Bergen":
                        path[e] = "Oslo"
                    elif path[e] == "Ålesund":
                        path[e] = "Hamar"
                road_paths[(key, key2)] = path
            elif path[-1] == "Kristiansand" and "Trondheim" in path:
                for e in range(len(path)):
                    if path[e] == "Stavanger":
                        path[e] = "Skien"
                    elif path[e] == "Bergen":
                        path[e] = "Oslo"
                    elif path[e] == "Ålesund":
                        path[e] = "Hamar"
                road_paths[(key, key2)] = path
            else:
                road_paths[(key, key2)] = path

# add road paths to K_Link_Paths
for e in road_paths.keys():
    #print(e," --> ", road_paths[e])
    path = []
    for i in range(len(road_paths[e]) - 1):
        for link in data.L_LINKS_DIR:
            if (road_paths[e][i] == link[0] and road_paths[e][i + 1] == link[1] and link[2] == "Road"):
                path.append(link)
    data.K_LINK_PATHS.append(path)


# ----------------------
# -----------------------------
# -------------------------------------
# NEW LINK FORMULATION WITHOUT DIRECT LINKS - END
# -------------------------------------
# -----------------------------
# ----------------------

# Find shortest path between all city-pairs in railway network
rail_paths = {}
for key in data.allowed_rail.keys():
    for key2 in data.allowed_rail.keys():
        path = bfs2(data.allowed_rail, key, key2)
        if len(path) > 2:
            rail_paths[(key,key2)] = path

# add railway paths to K_Link_Paths
for e in rail_paths.keys():
    path = []
    for i in range(len(rail_paths[e])-1):
        for link in data.L_LINKS_DIR:
            if (rail_paths[e][i] == link[0] and rail_paths[e][i+1] == link[1] and link[2]=="Rail"):
                path.append(link)
    if ('Trondheim', 'Hamar', 'Rail', 2) in path and ('Trondheim', 'Hamar', 'Rail', 1) in path:
        path2 = path.copy()
        path3 = path.copy()
        path3.remove(('Trondheim', 'Hamar', 'Rail', 2))
        path2.remove(('Trondheim', 'Hamar', 'Rail', 1))
        data.K_LINK_PATHS.append(path2)
        data.K_LINK_PATHS.append(path3)
    elif ('Hamar', "Trondheim", 'Rail', 2) in path and ('Hamar', "Trondheim", 'Rail', 1) in path:
        path2 = path.copy()
        path3 = path.copy()
        path3.remove(('Hamar', "Trondheim", 'Rail', 2))
        path2.remove(('Hamar', "Trondheim", 'Rail', 1))
        data.K_LINK_PATHS.append(path2)
        data.K_LINK_PATHS.append(path3)
    else:
        data.K_LINK_PATHS.append(path)

#print(data.K_LINK_PATHS)
#print("366? = (156 + 182 + 28) = (13x12 road + 14x13 sea + 28 rail) total single-link paths")
print("Total after adding multi-link rail/road: ",len(data.K_LINK_PATHS))

print("No duplicates if same as above: ",len(data.sort_and_deduplicate(data.K_LINK_PATHS))) #also 488 so no duplicates <333

#Add ((Oslo)) --> Hamar --> Syd-Sverige --> Nord-Sverige --> Bodø --> ((Tromsø))
# should be 4x2 paths (whole way, no oslo, no tromsø, no both) x both ways
temp_path1 = [('Hamar', 'Sør-Sverige', 'Rail', 1),('Sør-Sverige', 'Nord-Sverige', 'Rail', 1),('Nord-Sverige', 'Bodø', 'Rail', 1)]
temp_path2 = [('Bodø', 'Nord-Sverige', 'Rail', 1),('Nord-Sverige', 'Sør-Sverige', 'Rail', 1),('Sør-Sverige', 'Hamar', 'Rail', 1)]
data.K_LINK_PATHS.append(temp_path1)
data.K_LINK_PATHS.append(temp_path2)
oslo_temp1 = temp_path1.copy()
oslo_temp2 = temp_path2.copy()
oslo_temp1.append(('Oslo', 'Hamar', 'Rail', 1))
oslo_temp2.append(('Hamar', 'Oslo', 'Rail', 1))
data.K_LINK_PATHS.append(oslo_temp1)
data.K_LINK_PATHS.append(oslo_temp2)
all_path1 = oslo_temp1.copy()
all_path2 = oslo_temp2.copy()
all_path1.append(('Bodø', 'Tromsø', 'Rail', 1))
all_path2.append(('Tromsø', 'Bodø', 'Rail', 1))
data.K_LINK_PATHS.append(all_path1)
data.K_LINK_PATHS.append(all_path2)
tromsø_temp1 = all_path1.copy()
tromsø_temp2 = all_path2.copy()
tromsø_temp1.remove(('Oslo', 'Hamar', 'Rail', 1))
tromsø_temp2.remove(('Hamar', 'Oslo', 'Rail', 1))
data.K_LINK_PATHS.append(tromsø_temp1)
data.K_LINK_PATHS.append(tromsø_temp2)

print("Number of paths after adding Sverige-route, should be +8: ",len(data.K_LINK_PATHS))

# -----------------------------
# -----------------------------
# Multi-mode path generation
# -----------------------------
# -----------------------------


if data.run_file == "main":
    sea_distance = pd.read_excel(r'Data/Avstander (1).xlsx', sheet_name='Sea')
    road_distance = pd.read_excel(r'Data/Avstander (1).xlsx', sheet_name='Road')
    rail_distance = pd.read_excel(r'Data/Avstander (1).xlsx', sheet_name='Rail')
if data.run_file == "sets":
    sea_distance = pd.read_excel(r'Avstander (1).xlsx', sheet_name='Sea')
    road_distance = pd.read_excel(r'Avstander (1).xlsx', sheet_name='Road')
    rail_distance = pd.read_excel(r'Avstander (1).xlsx', sheet_name='Rail')

#Right order for distance matrix
city_number_dict = {"Oslo": 0,
                    "Bergen": 1,
                    "Trondheim": 2,
                    "Skien": 3,
                    "Hamar": 4,
                    "Kristiansand": 5,
                    "Stavanger": 6,
                    "Ålesund": 7,
                    "Bodø": 8,
                    "Tromsø": 9,
                    "Kontinentalsokkelen": 10,
                    "Nord-Sverige": 11,
                    "Sør-Sverige": 12,
                    "Europa": 13,
                    "Verden": 14}
new_dict = dict([(value, key) for key, value in city_number_dict.items()])

arr_sea = [[99999 for i in range(len(data.N_NODES))] for j in range(len(data.N_NODES))]
arr_road = [[99999 for i in range(len(data.N_NODES))] for j in range(len(data.N_NODES))]
arr_rail = [[99999 for i in range(len(data.N_NODES))] for j in range(len(data.N_NODES))]

possible_modes_dict = {(i,j) : [] for i in data.N_NODES for j in data.N_NODES if i!=j}
road_distances_dict = {}
sea_distances_dict = {}
rail_distances_dict = {}
for i in data.N_NODES:
    for j in data.N_NODES:
        for index, row in sea_distance.iterrows():
            if row["Fra"] in [i, j] and row["Til"] in [i, j]:
                possible_modes_dict[i,j].append("Sea")
                arr_sea[city_number_dict[i]][city_number_dict[j]] = row["Km - sjø"]
                sea_distances_dict[(i, j)] = row["Km - sjø"]
        for index, row in road_distance.iterrows():
            if row["Fra"] in [i, j] and row["Til"] in [i, j]:
                if (i,j) in road_paths.keys() and "Road" not in possible_modes_dict[i, j]:
                    possible_modes_dict[i, j].append("Road")
                elif j in data.allowed_road[i] and "Road" not in possible_modes_dict[i, j]:
                    possible_modes_dict[i, j].append("Road")
                arr_road[city_number_dict[i]][city_number_dict[j]] = row["Km - road"]
                road_distances_dict[(i, j)] = row["Km - road"]
        for index, row in rail_distance.iterrows():
            if row["Fra"] in [i, j] and row["Til"] in [i, j]:
                if "Rail" not in possible_modes_dict[i, j]:
                    possible_modes_dict[i, j].append("Rail")
                # add elif here for when there is no direct rail link, but rail path!!
                arr_rail[city_number_dict[i]][city_number_dict[j]] = row["Km - rail"]
                rail_distances_dict[(i, j)] = row["Km - rail"]
        if (i,j) in rail_paths.keys():
            if "Rail" not in possible_modes_dict[i, j]:
                possible_modes_dict[i, j].append("Rail")


arr_aggr = [[(0, 0) for i in range(len(data.N_NODES))] for j in range(len(data.N_NODES))]
for i in range(len(data.N_NODES)):
    for j in range(len(data.N_NODES)):
        if arr_road[i][j] >= arr_sea[i][j] and arr_rail[i][j] >= arr_sea[i][j]:
            arr_aggr[i][j] = (arr_sea[i][j], "Sea")
            arr_aggr_dict[new_dict[i],new_dict[j]] = (arr_sea[i][j], "Sea")
        elif arr_sea[i][j] >= arr_road[i][j] and arr_rail[i][j] >= arr_road[i][j]:
            arr_aggr[i][j] = (arr_road[i][j], "Road")
            arr_aggr_dict[new_dict[i],new_dict[j]] = (arr_road[i][j], "Road")
        elif arr_sea[i][j] >= arr_rail[i][j] and arr_road[i][j] >= arr_rail[i][j]:
            arr_aggr[i][j] = (arr_rail[i][j], "Rail")
            arr_aggr_dict[new_dict[i],new_dict[j]] = (arr_rail[i][j], "Rail")

stripped_arr_aggr = [[99999 for i in range(len(data.N_NODES))] for j in range(len(data.N_NODES))]
for i in range(len(data.N_NODES)):
    for j in range(len(data.N_NODES)):
        if arr_aggr[i][j][0] > 0:
            stripped_arr_aggr[i][j] = arr_aggr[i][j][0]

G = nx.DiGraph()
for i in range(len(stripped_arr_aggr)):
    for j in range(len(stripped_arr_aggr[i])):
        if stripped_arr_aggr[i][j] != 99999:
            G.add_edge(new_dict[i], new_dict[j], weight=int(stripped_arr_aggr[i][j]))

#print("Single shortest path: ", nx.single_source_dijkstra(G, "Oslo", "Trondheim"))

K_paths_dict = {}

for i in data.N_NODES:
    for j in data.N_NODES:
        if i != j and (i not in ["Verden","Europa","Nord-Sverige","Sør-Sverige"] or j not in ["Verden","Europa","Nord-Sverige","Sør-Sverige"]):
            for path in k_shortest_paths(G, i, j, 10, weight="weight"):
                if len(path) == 3:
                    if (i, j) not in K_paths_dict.keys():
                        K_paths_dict[(i, j)] = [path]
                        for a in range(len(path) - 1):
                            value = path[a:a + 2]
                            # print(value,"-->",arr_aggr_dict[city_number_dict[value[0]],city_number_dict[value[1]]])
                    else:
                        if len(K_paths_dict[(i, j)]) < 3:
                            K_paths_dict[(i, j)].append(path)
print("")
print("ADDING TRANSFER PATHS")
print("Number of paths before adding single transfer paths: ",len(data.K_LINK_PATHS)) #496 single arc paths (or only rail)

# Method that adds good multi-mode paths to the set of viable paths
for elem in K_paths_dict.keys():
    for path in K_paths_dict[elem]:
        link1 = path[0:2]
        link2 = path[1:3]
        for mode1 in possible_modes_dict[link1[0],link1[1]]:
            for mode2 in possible_modes_dict[link2[0],link2[1]]:
                if mode1 != mode2:
                    #Add multiple rail links if transferring FROM rail
                    if (link1[0],link1[1]) in rail_paths.keys() and mode1 == "Rail":# and (mode2=="Sea" or (mode2=="Road" and link2[1] in data.allowed_road[link2[0]])):
                        path4 = []
                        path5 = []
                        extra_path = False
                        rail_path = rail_paths[link1[0],link1[1]]
                        for a in range(len(rail_path) - 1):
                            node_pair = rail_path[a:a + 2]
                            if node_pair == ["Hamar","Trondheim"] or node_pair == ["Trondheim","Hamar"]:
                                path5.append((node_pair[0], node_pair[1], "Rail", 2))
                                extra_path = True
                            else:
                                path5.append((node_pair[0], node_pair[1], "Rail", 1))
                            path4.append((node_pair[0], node_pair[1], "Rail", 1))
                        #Add multiple road links if transferring TO road (from rail)
                        if (link2[0],link2[1]) in road_paths.keys() and mode2 == "Road":
                            road_path = road_paths[link2[0], link2[1]]
                            for a in range(len(road_path) - 1):
                                node_pair_r = road_path[a:a + 2]
                                path4.append((node_pair_r[0], node_pair_r[1], "Road", 1))
                                path5.append((node_pair_r[0], node_pair_r[1], "Road", 1))
                        else:
                            path4.append((link2[0],link2[1],mode2,1))
                            path5.append((link2[0], link2[1], mode2, 1))
                        data.K_LINK_PATHS.append(path4)
                        if extra_path == True:
                            data.K_LINK_PATHS.append(path5)
                    # Add multiple rail links if transferring TO rail
                    elif (link2[0], link2[1]) in rail_paths.keys() and mode2 == "Rail":
                        path4 = []
                        path5 = []
                        # Add multiple road links if transferring FROM road
                        if (link1[0],link1[1]) in road_paths.keys() and mode1 == "Road":
                            road_path = road_paths[link1[0], link1[1]]
                            for a in range(len(road_path) - 1):
                                node_pair_r = road_path[a:a + 2]
                                path4.append((node_pair_r[0], node_pair_r[1], "Road", 1))
                                path5.append((node_pair_r[0], node_pair_r[1], "Road", 1))
                        else:
                            path4.append((link1[0],link1[1],mode1,1))
                            path5.append((link1[0], link1[1], mode1, 1))
                        extra_path = False
                        rail_path = rail_paths[link2[0], link2[1]]
                        for a in range(len(rail_path) - 1):
                            node_pair = rail_path[a:a + 2]
                            if node_pair == ["Hamar", "Trondheim"] or node_pair == ["Trondheim", "Hamar"]:
                                path5.append((node_pair[0], node_pair[1], "Rail", 2))
                                extra_path = True
                            else:
                                path5.append((node_pair[0], node_pair[1], "Rail", 1))
                            path4.append((node_pair[0], node_pair[1], "Rail", 1))
                        data.K_LINK_PATHS.append(path4)
                        if extra_path == True:
                            data.K_LINK_PATHS.append(path5)
                    elif (link1[0], link1[1]) in road_paths.keys() and mode1 == "Road":
                        road_path = road_paths[link1[0], link1[1]]
                        path4 = []
                        for a in range(len(road_path) - 1):
                            node_pair_r = road_path[a:a + 2]
                            path4.append((node_pair_r[0], node_pair_r[1], "Road", 1))
                        path4.append((link2[0],link2[1],mode2,1))
                        data.K_LINK_PATHS.append(path4)
                    elif (link2[0], link2[1]) in road_paths.keys() and mode2 == "Road":
                        path4 = []
                        path4.append((link1[0], link1[1], mode1, 1))
                        road_path = road_paths[link2[0], link2[1]]
                        for a in range(len(road_path) - 1):
                            node_pair_r = road_path[a:a + 2]
                            path4.append((node_pair_r[0], node_pair_r[1], "Road", 1))
                        data.K_LINK_PATHS.append(path4)
                    else:
                        path1 = [(link1[0],link1[1],mode1,1),(link2[0],link2[1],mode2,1)]
                        #print("Non-rail first link: ",path1)
                        data.K_LINK_PATHS.append(path1)


"""
if data.run_file == "main":
    all_generated_paths = pd.read_csv(r'Data/all_generated_paths.csv', converters={'paths': eval})
if data.run_file == "sets":
    all_generated_paths = pd.read_csv(r'all_generated_paths.csv', converters={'paths': eval})

print("Number of paths before adding list: ", len(data.K_LINK_PATHS))
print("All generated paths should be 756, and is: ", len(all_generated_paths))
org_8_paths = []
for index, row in all_generated_paths.iterrows():
    elem = row['paths']
    data.K_LINK_PATHS.append(elem)
"""

# -----------------------------------------------------
# -------------- REMOVE ALL BAD PATHS -----------------
# -----------------------------------------------------


print("Number of L_link_paths after adding all_paths: ", len(data.K_LINK_PATHS))

# Remove all paths where a city is visited more than once
itr_paths = data.K_LINK_PATHS.copy()
for k in itr_paths:
    count_nodes_from = {n: 0 for n in data.N_NODES}
    count_nodes_to = {n: 0 for n in data.N_NODES}
    for l in k:
        count_nodes_from[l[0]] += 1
        count_nodes_to[l[1]] += 1
    if max(count_nodes_to.values()) > 1 or max(count_nodes_from.values()) > 1:
        data.K_LINK_PATHS.remove(k)
print("Paths after removing bad double city paths: ", len(data.K_LINK_PATHS))

"""temp_hamar_multimode = [("Hamar", "Oslo", "Rail", 1), ("Oslo", "Verden", "Sea", 1)]
temp_hamar_multimode1 = [("Hamar", "Oslo", "Road", 1), ("Oslo", "Verden", "Sea", 1)]
temp_hamar_multimode2 = [("Verden", "Oslo", "Sea", 1), ("Oslo", "Hamar", "Rail", 1)]
temp_hamar_multimode3 = [("Verden", "Oslo", "Sea", 1), ("Oslo", "Hamar", "Road", 1)]
data.K_LINK_PATHS.append(temp_hamar_multimode)
data.K_LINK_PATHS.append(temp_hamar_multimode1)
data.K_LINK_PATHS.append(temp_hamar_multimode2)
data.K_LINK_PATHS.append(temp_hamar_multimode3)"""

# Remove all extra paths if there exists direct links (len=1) with all modes between two cities.
data.OD_PATHS = {od: [] for od in data.OD_PAIRS_ALL}
for od in data.OD_PAIRS_ALL:
    for k in data.K_LINK_PATHS:
        if od[0] == k[0][0] and od[-1] == k[-1][1]:
            data.OD_PATHS[od].append(k)

for od in data.OD_PATHS.keys():
    if [(od[0], od[1], "Road", 1)] in data.OD_PATHS[od] and [(od[0], od[1], "Rail", 1)] in data.OD_PATHS[
        od] and [(od[0], od[1], "Sea", 1)] in data.OD_PATHS[od]:
        iter_dict = data.OD_PATHS[od].copy()
        for k in iter_dict:
            if k != [(od[0], od[1], "Road", 1)] and k != [(od[0], od[1], "Rail", 1)] and k != [
                (od[0], od[1], "Sea", 1)]:
                if k in data.K_LINK_PATHS:
                    data.K_LINK_PATHS.remove(k)
                    data.OD_PATHS[od].remove(k)
print("Paths after removing overly complicated paths between nodes with all direct modes available: ",
      len(data.K_LINK_PATHS))

data.AVG_DISTANCE = {l: 0 for l in data.L_LINKS}
for l in data.L_LINKS:  # Enten bør constraints ta inn halvt sett (ij eller ji) eller så bør denne gjelde for LINKS_DIRECTED
    if l[2] == "Road":
        if (l[0], l[1]) in road_distances_dict.keys():
            data.AVG_DISTANCE[l] = road_distances_dict[(l[0], l[1])]
            data.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = road_distances_dict[(l[1], l[0])]
    elif l[2] == "Sea":
        if (l[0], l[1]) in sea_distances_dict.keys():
            data.AVG_DISTANCE[l] = sea_distances_dict[(l[0], l[1])]
            data.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = sea_distances_dict[(l[1], l[0])]
    elif l[2] == "Rail":
        if (l[0], l[1]) in rail_distances_dict.keys():
            data.AVG_DISTANCE[l] = rail_distances_dict[(l[0], l[1])]
            data.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = rail_distances_dict[(l[1], l[0])]
    if l[0] not in data.N_NODES_NORWAY or l[1] not in data.N_NODES_NORWAY:
        data.AVG_DISTANCE[l] = data.AVG_DISTANCE[l] / 2
        data.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] = data.AVG_DISTANCE[(l[1], l[0], l[2], l[3])] / 2

# Remove all paths with length more than 3x shortest path
data.path_length = {str(k):0 for k in data.K_LINK_PATHS}
for k in data.K_LINK_PATHS:
    for l in k:
        data.path_length[str(k)] += data.AVG_DISTANCE[l] # arr_aggr_dict[l[0],l[1]][0]

for od in data.OD_PATHS.keys():
    paths = []
    lengths = []
    iter_list = data.OD_PATHS[od].copy()
    for k in iter_list:
        paths.append(k)
        lengths.append((data.path_length[str(k)]))
    for i in range(len(lengths)):
        if lengths[i] > 3*min(lengths):
            data.K_LINK_PATHS.remove(paths[i])
            data.OD_PATHS[od].remove(paths[i])

print("Number of paths after removing 3*min-len: ", len(data.K_LINK_PATHS))

# Remove all paths where there is no demand for the origin destination pair
all_paths_list = []
for val_list in data.OD_PATHS.values():
    all_paths_list.extend(val_list)
iter_copy = data.K_LINK_PATHS.copy()
for k in iter_copy:
    if k not in all_paths_list:
        data.K_LINK_PATHS.remove(k)

print("Number of paths after removing unused OD-paths: ", len(data.K_LINK_PATHS))


# -----------------------------------------------------
# ------------ SAVE ALL PROMISING PATHS ---------------
# -----------------------------------------------------
dataset_paths_list = []
dataset_all_paths = pd.DataFrame(columns=['paths'])
for k in data.K_LINK_PATHS:  # Could be K_paths or K_link_paths, doesnt matter
    all_series_path = pd.Series([k],
                              index=dataset_all_paths.columns)
    dataset_all_paths = dataset_all_paths.append(all_series_path, ignore_index=True)
    dataset_paths_list.append(k)

# dataset_all_paths.to_csv("all_promising_paths.csv")

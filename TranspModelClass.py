#Pyomo
import pyomo.opt   # we need SolverFactory,SolverStatus,TerminationCondition
import pyomo.opt.base as mobase
from pyomo.environ import *
from pyomo.util.infeasible import log_infeasible_constraints
import logging

from Data.Create_Sets_Class import TransportSets   #FreightTransportModel.Data.Create_Sets_Class
import os
os.getcwd()

############# Class ################



class TranspModel:

    def __init__(self, instance, one_time_period, scenario, carbon_scenario, fuel_costs, emission_reduction):

        self.instance = instance
        #timelimit in minutes, etc
        #elf.maturity_scenario = maturity_scenario

        self.results = 0  # results is an structure filled out later in solve_model()
        self.status = ""  # status is a string filled out later in solve_model()
        self.model = ConcreteModel()
        self.opt = pyomo.opt.SolverFactory('gurobi') #gurobi
        self.results = 0  # results is an structure filled out later in solve_model()
        self.status = ""  # status is a string filled out later in solve_model()
        self.scenario = scenario
        self.carbon_scenario = carbon_scenario
        self.fuel_costs = fuel_costs
        self.emission_reduction = emission_reduction
        #IMPORT THE DATA
        self.data = TransportSets(self.scenario, self.carbon_scenario, self.fuel_costs, self.emission_reduction)
        self.factor = self.data.factor



    def construct_model(self):

        "VARIABLES"
        # Binary, NonNegativeReals, PositiveReals, etc

        #self.model.x_flow_rest = Var(self.data.APTS_rest, within=NonNegativeReals)
        self.model.x_flow = Var(self.data.APTS, within=NonNegativeReals)
        self.model.h_flow = Var(self.data.KPTS, within=NonNegativeReals)# flow on paths K,p
        #self.model.h_flow_2020 = Var(self.data.KPTS_2020, within=NonNegativeReals)
        self.model.StageCosts = Var(self.data.T_TIME_PERIODS, within = NonNegativeReals)
        
        self.model.z_inv_cap = Var(self.data.LT_CAP, within = Binary) #within = Binary
        self.model.z_inv_upg = Var(self.data.LUT_UPG, within = Binary) #bin.variable for investments upgrade/new infrastructure u at link l, time period t
        self.model.z_inv_node = Var(self.data.NMBT_CAP, within = Binary) #step-wise investment in terminals
        
        #self.model.y_exp_link = Var(self.data.LT_CAP, within = NonNegativeReals) #,bounds=(0,20000)) #expansion in tonnes for capacitated links l, time period t
        #self.model.y_exp_node = Var(self.data.NMT_CAP, within = NonNegativeReals, bounds=(0,100000000)) #expansion in tonnes for capacicated terminals i, time period t
        
        self.model.charge_link = Var(self.data.CHARGING_AT, within=NonNegativeReals)
        #self.model.charge_node = Var(self.data.CHARGING_IMFT, within=NonNegativeReals)
        self.model.emission_violation = Var(self.data.TS, within = NonNegativeReals)
        
        
        """def emission_bound(model, t):
            return (0, self.data.CO2_CAP[t]/self.factor)"""

        self.model.total_emissions = Var(self.data.TS, within=NonNegativeReals) #instead of T_PERIODS!
                                        # bounds=emission_bound)  # just a variable to help with output
        
        
        def StageCostsVar(model, t):
            return(self.model.StageCosts[t] == (sum(self.data.D_DISCOUNT_RATE[t] * (self.data.C_TRANSP_COST[a, p, t]
                                +self.data.C_CO2[a,p,t])*self.model.x_flow[a,p,t] for p in self.data.P_PRODUCTS for a in self.data.A_ARCS)
                   +sum(self.data.D_DISCOUNT_RATE[t]*self.data.C_CAP_LINK[l]*self.model.z_inv_cap[l,t]
                       for l in self.data.L_LINKS_CAP)
                   +sum(self.data.D_DISCOUNT_RATE[t]*self.data.C_INV_UPG[l,u]*self.model.z_inv_upg[l,u,t] for l
                                     in self.data.L_LINKS_UPG for u in self.data.UL_UPG[l])
                   +sum(self.data.D_DISCOUNT_RATE[t]*self.data.C_CAP_NODE[i,m,b]*self.model.z_inv_node[i,m,b,t] for m
                                    in self.data.M_MODES_CAP for i in self.data.N_NODES_CAP_NORWAY[m] for b in self.data.TERMINAL_TYPE[m])
                   +sum(self.data.D_DISCOUNT_RATE[t]*self.model.h_flow[str(k),p,t]*self.data.C_MULTI_MODE_PATH[q,p]
                                for q in self.data.PATH_TYPES for k in self.data.MULTI_MODE_PATHS_DICT[q] for p in self.data.P_PRODUCTS)
                   + sum(self.data.D_DISCOUNT_RATE[t] * self.data.ROAD_DIST_COST[(i,j,m,f,r)] * self.model.charge_link[(i,j,m,f,r,t)]
                         for (i,j,m,f,r) in self.data.CHARGING_ARCS)
                   +self.data.D_DISCOUNT_RATE[t]*self.model.emission_violation[t]*500))
                   #+ sum(self.data.D_DISCOUNT_RATE[t] * self.data.NODE_CHARGE_COST[(i, m, f)] *self.model.charge_node[(i, m, f, t)] for (i, m, f) in self.data.IMF)))
        self.model.stage_costs = Constraint(self.data.T_TIME_PERIODS, rule = StageCostsVar)
        
        
        
        
        
        
        """ 
        self.model.emissions_penalty = Var(self.data.TS, within=NonNegativeReals) #instead of T_PERIODS!
        
        "NEW/ADDED VARIABLES"
        # NonNegativeReals
        self.model.y_exp_link = Var(self.data.LTS_CAP, within = NonNegativeReals) #,bounds=(0,20000)) #expansion in tonnes for capacitated links l, time period t
        self.model.y_exp_node = Var(self.data.NMTS_CAP, within = NonNegativeReals, bounds=(0,10000)) #expansion in tonnes for capacicated terminals i, time period t

        # Binary
        self.model.z_inv_upg = Var(self.data.LUTS_UPG, within = Binary) #bin.variable for investments upgrade/new infrastructure u at link l, time period t
        self.model.z_inv_cap = Var(self.data.LTS_CAP, within = Binary) #bin.variable for investments in double track at link l, time period t
        """

        "OBJECTIVE ORIGINAL"

        """
        def objfun(model):
            obj_value = (1/len(self.data.S_SCENARIOS)*
                (sum(self.data.D_DISCOUNT_RATE[t] * (self.data.C_TRANSP_COST[a, t]+ self.data.C_CO2[a,t])* self.model.x_flow[a, p, t, s]
                             for p in self.data.P_PRODUCTS for a in self.data.A_ARCS for t
                             in self.data.T_TIME_PERIODS for s in self.data.S_SCENARIOS)
                + sum(self.data.D_DISCOUNT_RATE[t]*(self.data.C_CAP_LINK[l] * self.model.y_exp_link[l, t, s]
                + self.data.C_INV_CAP[l]*self.model.z_inv_cap[l,t,s]) for l in self.data.L_LINKS_CAP for t
                                in self.data.T_TIME_PERIODS for s in self.data.S_SCENARIOS)
                + sum(self.data.D_DISCOUNT_RATE[t]*self.data.C_INV_UPG[l,u]*self.model.z_inv_upg[l,u,t,s] for l
                                  in self.data.L_LINKS_UPG for u in self.data.UL_UPG[l] for t in self.data.T_TIME_PERIODS for s in self.data.S_SCENARIOS)
                +sum(self.data.D_DISCOUNT_RATE[t]*self.data.C_CAP_NODE[i,m]*self.model.y_exp_node[i,m,t,s] for i
                                 in self.data.N_NODES_CAP for m in self.data.M_MODES_CAP for t in self.data.T_TIME_PERIODS for s in self.data.S_SCENARIOS)
                +sum(self.data.D_DISCOUNT_RATE[t]*self.model.h_flow[str(k),p,t,s]*self.data.C_MULTI_MODE_PATH[str(k)]
                                 for k in self.data.K_PATHS for p in self.data.P_PRODUCTS for t in self.data.T_TIME_PERIODS for s in self.data.S_SCENARIOS)
                 +sum(self.data.C_CO2_PENALTY[t,s]*self.model.emissions_penalty[t,s] for t in self.data.T_TIME_PERIODS for s in self.data.S_SCENARIOS)))
            return obj_value

        self.model.Obj = Objective(rule=objfun, sense=minimize)
        """


        def objfun(model):
            #obj_value = self.model.first_stage_costs + sum(self.data.D_DISCOUNT_RATE[t] * self.data.C_TRANSP_COST[a, t]*self.model.x_flow[a,p,t]
             #                for p in self.data.P_PRODUCTS for a in self.data.A_ARCS for t
              #               in [2025,2030])
            obj_value = sum(self.model.StageCosts[t] for t in self.data.T_TIME_PERIODS) 
            return obj_value

        self.model.Obj = Objective(rule=objfun, sense=minimize)

        # Flow
        def FlowRule(model, o, d, p, t):
            return sum(self.model.h_flow[str(k), p, t] for k in self.data.OD_PATHS[(o, d)]) >= self.data.D_DEMAND[
                (o, d, p, t)]/self.factor

        # NOTE THAT THIS SHOULD BE AN EQUALITY; BUT THEN THE PROBLEM GETS EASIER WITH A LARGER THAN OR EQUAL
        self.model.Flow = Constraint(self.data.ODPTS, rule=FlowRule)
        #print("OVER FEILEN!")

        # PathFlow-ArcFlow relationship
       
        def PathArcRule(model, i, j, m, r, p, t):
            l= (i,j,m,r)
            return sum(self.model.x_flow[a, p, t] for a in self.data.A_LINKS[l]) == sum(
                self.data.DELTA[(l, str(tuple(k)))] * self.model.h_flow[str(k), p, t] for k in self.data.K_PATHS)
        self.model.PathArcRel = Constraint(self.data.LPT, rule=PathArcRule)

        # CAPACITY constraints (compared to 2018) - TEMPORARY
        # the model quickly becomes infeasible when putting such constraints on the model. Should be tailor-made!

        # def CapacityConstraints(model, i,j,m,p,t):
        #    a = (i,j,m)
        #    return self.model.x_flow[a,p,t] <= self.data.buildchain2018[(i,j,m,p)]*2
        # self.model.CapacityConstr = Constraint(self.data.APT,rule=CapacityConstraints)

        # Emissions
        def emissions_rule(model, t):
            return (self.model.total_emissions[t] == sum(
                self.data.E_EMISSIONS[a, p, t] * self.model.x_flow[a, p, t] for p in self.data.P_PRODUCTS
                for a in self.data.A_ARCS))
        self.model.Emissions = Constraint(self.data.TS, rule=emissions_rule) #removed self.data.T_TIME_PERIODS


        "CONSTRAINT NEW/ADDED"

        # Emission limit
        
        def EmissionCapRule(model, t):
            return self.model.total_emissions[t] <= self.data.CO2_CAP[t]/self.factor + self.model.emission_violation[t]

        self.model.EmissionCap = Constraint(self.data.TS, rule=EmissionCapRule)
        

        
        #Capacity constraint
        def CapacitatedFlowRule(model,i,j,m,r,t):
            l = (i,j,m,r)
            """return sum(self.model.x_flow[a,p,t] for p in self.data.P_PRODUCTS for f in self.data.FM_FUEL[l[2]]
                        for a in self.data.A_PAIRS[l,f]) <= self.data.Y_BASE_CAP[l]
            + sum(self.model.y_exp_link[l,tau] for tau in self.data.T_TIME_PERIODS if tau <= t)
            #+ self.data.Y_ADD_CAP[l]*sum(self.model.z_inv_cap[(l,tau)] for tau in self.data.T_TIME_PERIODS if tau <= t)"""

            return (sum(self.model.x_flow[a, p, t] for p in self.data.P_PRODUCTS for f in self.data.FM_FUEL[m]
                        # so m = l[2], why not replace that
                        for a in self.data.A_PAIRS[l, f]) <= self.data.Y_BASE_CAP[l] +
                   + self.data.Y_ADD_CAP[l] * sum(self.model.z_inv_cap[l, tau] for tau in self.data.T_TIME_PERIODS if tau < t))

        self.model.CapacitatedFlow = Constraint(self.data.LT_CAP, rule = CapacitatedFlowRule)
        
        
        #Expansion in capacity limit
        def ExpansionLimitRule(model,i,j,m,r):
            l = (i,j,m,r)
            return (sum(self.model.z_inv_cap[(l,t)] for t in self.data.T_TIME_PERIODS) <= self.data.INV_LINK[l])
        self.model.ExpansionCap = Constraint(self.data.L_LINKS_CAP, rule = ExpansionLimitRule)
        
        
        #Investment in new infrastructure/upgrade
        def InvestmentInfraRule(model,i,j,m,r,f,t):
            l = (i,j,m,r)
            return (sum(self.model.x_flow[a,p,t] for p in self.data.P_PRODUCTS for a in self.data.A_PAIRS[l, f])
                    <= self.data.Big_M[l]*sum(self.model.z_inv_upg[l,u,tau]
                    for u in self.data.UF_UPG[f] for tau in self.data.T_TIME_PERIODS if tau < t))
        self.model.InvestmentInfra = Constraint(self.data.LFT_UPG, rule = InvestmentInfraRule)
        
        
        """#Terminal capacity constraint OLD
        def TerminalCapRule(model,i,m,t):
            return (sum(self.model.x_flow[a,p,t] for p in self.data.P_PRODUCTS for a in self.data.A_IN[i,m])
            + sum(self.model.x_flow[a,p,t] for p in self.data.P_PRODUCTS for a in self.data.A_OUT[i,m]) <= self.data.Y_NODE_CAP[i,m]
            + sum(self.model.y_exp_node[i,m,tau] for tau in self.data.T_TIME_PERIODS if tau <= t))
        self.model.TerminalCap = Constraint(self.data.NMT_CAP, rule = TerminalCapRule)"""
        
        #Terminal capacity constraint NEW
        def TerminalCapRule(model, i, m, b, t):
            return(sum(self.model.h_flow[k, p, t] for k in self.data.ORIGIN_PATHS[(i,m)] for p in self.data.PT[b]) + 
                   sum(self.model.h_flow[k, p, t] for k in self.data.DESTINATION_PATHS[(i,m)] for p in self.data.PT[b]) +
                   sum(self.model.h_flow[k,p,t] for k in self.data.TRANSFER_PATHS[(i,m)] for p in self.data.PT[b]) <= 
                   self.data.Y_NODE_CAP[i,m,b]+self.data.Y_ADD_CAP_NODE[i,m,b]*sum(self.model.z_inv_node[i,m,b,tau] for tau in self.data.T_TIME_PERIODS if tau < t))
        self.model.TerminalCap = Constraint(self.data.NMBT_CAP, rule = TerminalCapRule)
        
        #Max terminal capacity expansion NEW -- how many times you can perform a step-wise increase of the capacity
        def TerminalCapExpRule(model, i, m, b):
            return(sum(self.model.z_inv_node[i,m,b,t] for t in self.data.T_TIME_PERIODS) <= self.data.INV_NODE[i,m,b])
        self.model.TerminalCapExp = Constraint(self.data.NMB_CAP, rule = TerminalCapExpRule)

        #Technology maturity limit
        def TechMaturityLimitRule(model, m, f, t):
            return (sum(self.model.x_flow[(a, p, t)] for p in self.data.P_PRODUCTS
                        for a in self.data.A_TECH[m, f]) <= self.data.Y_TECH[(m, f, t)])
        self.model.TechMaturityLimit = Constraint(self.data.MFTS_CAP, rule = TechMaturityLimitRule)
        
        
        def ChargingCapArcRule(model, i, j, m, f, r, t):
            l = (i, j, m, r)
            # Must hold for each arc pair a (ijmfr + jimfr) in each time_period t
            # Linear expansion of charging capacity
            return (sum(self.model.x_flow[a, p, t] for p in self.data.P_PRODUCTS
                       for a in self.data.A_PAIRS[l, f]) <= self.data.BASE_CHARGE_CAP[(i,j,m,f,r)] +
                   sum(self.model.charge_link[(i,j,m,f,r,tau)] for tau in self.data.T_TIME_PERIODS if tau <= t))
        self.model.ChargingCapArc = Constraint(self.data.CHARGING_AT, rule=ChargingCapArcRule)

        # NEW CHARGING NODE RESTRICTION
        #
        
        """def ChargingCapNodeRule(model, i, m, f, t):
           # Linear expansion of charging capacity
           return (sum(self.model.x_flow[a, p, t] for p in self.data.P_PRODUCTS
                       for a in self.data.IMF_ARCS[(i, m, f)]) <= self.data.BASE_CHARGE_CAP_NODE[(i,m,f)] +
                   sum(self.model.charge_node[(i,m,f,tau)] for tau in self.data.T_TIME_PERIODS if tau <= t))
        self.model.ChargingCapNode = Constraint(self.data.CHARGING_IMFT, rule=ChargingCapNodeRule)"""


        #def Diesel2020(model, t):
        #    return (sum(self.model.x_flow[(a,p,t)] for p in self.data.P_PRODUCTS
        #        for a in self.data.DIESEL_ROAD) >= sum(self.model.x_flow[(a,p,t)]
        #       for p in self.data.P_PRODUCTS for a in self.data.ARCS_ROAD))
        #self.model.Diesel2020Rate = Constraint(self.data.T_TIME_2020, rule=Diesel2020)
        
        


        return self.model
        """
    def NonAnticipativityRule(model,a,p):
        return(self.model.x_flow[(a, p, 2020, "average")] == self.model.x_flow[(a, p, 2020, "low")]
        == self.model.x_flow[(a, p, 2020, "high")] == self.model.x_flow[(a, p, 2020, "hydrogen")])
        self.model.NonAnticipativity = Constraint(self.data.AP, rule=NonAnticipativityRule)
        """

    def solve_model(self):

        self.results = self.opt.solve(self.model, tee=True, symbolic_solver_labels=True,
                                      keepfiles=True)  # , tee=True, symbolic_solver_labels=True, keepfiles=True)

        if (self.results.solver.status == pyomo.opt.SolverStatus.ok) and (
                self.results.solver.termination_condition == pyomo.opt.TerminationCondition.optimal):
            print('the solution is feasible and optimal')
        elif self.results.solver.termination_condition == pyomo.opt.TerminationCondition.infeasible:
            print('the model is infeasible')
            #log_infeasible_constraints(self.model,log_expression=True, log_variables=True)
            #logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)
            #print(value(model.z))

        else:
            print('Solver Status: '), self.results.solver.status
            print('Termination Condition: '), self.results.solver.termination_condition

        print('Solution time: ' + str(self.results.solver.time))
        
        

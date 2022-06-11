# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 14:56:36 2022

@author: ingvi
"""
import script_MainAnalysis_TwoStage
import mpisppy.utils.sputils as sputils
import mpisppy.cylinders as cylinders 

from mpisppy.spin_the_wheel import WheelSpinner
from mpisppy.utils import baseparsers
from mpisppy.utils import vanilla
from mpisppy.extensions.cross_scen_extension import CrossScenarioExtension 




############### SPOKE STUFF


    
#SPOKE_SLEEP_TIME = 0.0001   #not needed??

write_solution = False

"""def _parse_args():
    #parser = baseparsers.make_multistage_parser()  #used for multi-stage
    parser = baseparsers.make_parser() #used for two-stage
    parser = baseparsers.two_sided_args(parser)
    parser = baseparsers.mip_options(parser)
    parser = baseparsers.xhatlooper_args(parser)
    parser = baseparsers.xhatshuffle_args(parser) #currently only using this
    parser = baseparsers.lagrangian_args(parser)
    parser = baseparsers.xhatspecific_args(parser)
    parser = baseparsers.slamup_args(parser)
    parser = baseparsers.cross_scenario_cuts_args(parser)
    args = parser.parse_args()
    return args"""

def _parse_args():
    parser = baseparsers.make_parser()
    parser = baseparsers.two_sided_args(parser)
    parser = baseparsers.mip_options(parser)
    parser = baseparsers.fixer_args(parser)
    parser = baseparsers.fwph_args(parser)
    parser = baseparsers.lagrangian_args(parser)
    parser = baseparsers.xhatlooper_args(parser)
    parser = baseparsers.xhatshuffle_args(parser)
    args = parser.parse_args()
    return args



def main():  
    args = _parse_args()
    
    num_scen = args.num_scens #finne ut av hva dette eventuelt fikser
    
    #BFs = args.branching_factors
    
    with_xhatshuffle = args.with_xhatshuffle
    with_lagrangian = args.with_lagrangian
    #with_cross_scenario_cuts = args.with_cross_scenario_cuts
    
    
    #all_nodenames = sputils.create_nodenames_from_branching_factors(BFs)
    
    #ScenCount = BFs[0]*BFs[1]
    #scenario_creator_kwargs = {"branching_factors": BFs}
    #scenario_creator_kwargs = {"scenario_count": num_scen}
   # ScenCount = num_scen
    #all_scenario_names = [f"Scen{i+1}" for i in range(ScenCount)]
    scenario_creator = script_MainAnalysis_TwoStage.scenario_creator
    scenario_denouement = script_MainAnalysis_TwoStage.scenario_denouement
    all_scenario_names = script_MainAnalysis_TwoStage.all_scenario_names
    rho_setter = None
    
   
    
    beans = (args, scenario_creator, scenario_denouement, all_scenario_names)
    
    
    
    #Vanilla PH hub
    """hub_dict = vanilla.ph_hub(*beans,
                          scenario_creator_kwargs=scenario_creator_kwargs,
                          ph_extensions=None,
                          rho_setter = rho_setter,
                          all_nodenames = all_nodenames,
                          spoke_sleep_time = SPOKE_SLEEP_TIME)"""
    
    hub_dict = vanilla.ph_hub(*beans,
                              #scenario_creator_kwargs=scenario_creator_kwargs,
                              ph_extensions=None,
                              rho_setter = rho_setter)
    
    
    
    """if with_lagrangian:
        lagrangian_spoke = vanilla.lagrangian_spoke(*beans,
               scenario_creator_kwargs=scenario_creator_kwargs,
               rho_setter = rho_setter,
               all_nodenames = all_nodenames,
               spoke_sleep_time = SPOKE_SLEEP_TIME)"""
    
    
    if with_lagrangian:
        lagrangian_spoke = vanilla.lagrangian_spoke(
            *beans,  rho_setter=rho_setter)
         
            #scenario_creator_kwargs=scenario_creator_kwargs,
           
        
    """#xhat looper bound spoke
    if with_xhatshuffle:
        xhatshuffle_spoke = vanilla.xhatshuffle_spoke(*beans)"""
                    #all_nodenames=all_nodenames
                    #scenario_creator_kwargs=scenario_creator_kwargs,
                    #spoke_sleep_time = SPOKE_SLEEP_TIME)
                    
                    #all_nodenames = None,
                    #scenario_creator_kwargs = None,
                    #spoke_sleep_time = None
        
    # xhat shuffle bound spoke
    if with_xhatshuffle:
        xhatshuffle_spoke = vanilla.xhatshuffle_spoke(
            *beans)
            #scenario_creator_kwargs=scenario_creator_kwargs,
        
    
    list_of_spoke_dict = list()
    if with_xhatshuffle:
        list_of_spoke_dict.append(xhatshuffle_spoke)
    if with_lagrangian:
        list_of_spoke_dict.append(lagrangian_spoke)
    
    
    
    wheel = WheelSpinner(hub_dict, list_of_spoke_dict)
    wheel.spin()
    
    
    
    #if wheel.global_rank == 0:  # we are the reporting hub rank
     #   print(f"BestInnerBound={wheel.BestInnerBound} and BestOuterBound={wheel.BestOuterBound}")
    
    if write_solution:
        #wheel.write_first_stage_solution('first_stage_ekte.csv')
        wheel.write_tree_solution('full_solution_anetvild')

    
    

if __name__ == "__main__":
    main()
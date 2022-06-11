#!/bin/bash

# Author: Aksel Kristiansen Borgmo
# General shell script for automation of scenario executions on Solstorm Cluster

cd "$1"

script=$(ls script*)
Scenarios=("${@: 2: (($# - 2))}")
Threading=${@: $#}

source ./setup.bash

for i in "${!Scenarios[@]}"
do
	if [ $Threading = "true" ]
	then
		python ${script} ${Scenarios[$i]} > "results"${Scenarios[$i]}.txt &
	else
		python ${script} ${Scenarios[$i]} > "results"${Scenarios[$i]}.txt
		wait
	fi
done

sleep 2

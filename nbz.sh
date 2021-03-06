#!/usr/bin/env bash
#
# Author: <Zurdi>

# NBZ Launcher


function show_help {
	echo "NBZ v1.0 - (C) 2017-2019 Zurdi Zurdo"
	echo "Released under the GNU GLP"
	echo ""
	echo "NBZ is a tool to automate navigation and data extraction on the internet."
	echo "It is configured by little scripts coded with nbz-script language. You can find the"
	echo "documentation in the github wiki: https://github.com/zurdi15/nbz/wiki"
	echo ""
	echo "-h    Show this help"
	echo "-v    Show the version"
	echo "-s    Set the .nbz script"
	echo "-p    Set the script parameters"
	echo "-x    Enable screen emulation (server) / hide browser screen (desktop)"
	echo "-r    Set custom resolution for screen emulation"
	echo "-P    Enable proxy"
	echo "-d    Enable debug mode"
}

function show_version {
	echo "NBZ v1.0"
}

#  - Parameters

script=""
display="false"
proxy="false"
debug="false"
resolution="default"

if [ ${#} = 0 ]; then
	show_help
	exit 0
else
	while getopts "hvs:p:xr:Pd" opt
	do
		case ${opt} in
			h)
				show_help
				exit 0
				;;
			v)
				show_version
				exit 0
				;;
			s)
				ext=${OPTARG##*.}
				if [ ${ext} = "nbz" ]
				then
					script=${OPTARG} >&2
				else
					echo "Error: Not compatible script (.${ext}). Extension must be .nbz"
					exit 1
				fi
				;;
			p)
				if [ -z "$script_parameters" ]; then
					script_parameters=("${OPTARG}")
				else
					script_parameters+=("${OPTARG}")
				fi
				;;
			x)
				display="true" >&2
				;;
			r)
				resolution=${OPTARG}
				;;
			P)
				proxy="true" >&2
				;;
			d)
				debug="true" >&2
				;;
			\?)
				echo "Error: invalid option -${OPTARG}" >&2
				exit 1
				;;
			:)
				echo "Error: option -${OPTARG} requires an argument" >&2
				exit 1
				;;
		esac
	done
	shift $((OPTIND -1))
fi

if [ -z ${script} ]; then
	echo "Error: Script required."
	exit 1
else
	if [ ! -f ${script} ]; then
		echo -e "Error: script \"${script}\" does not exist."
		exit 1
	fi
fi

if [[ -z ${script_parameters[@]} ]]; then
	script_parameters=""
fi

if [ -h "${BASH_SOURCE[0]}" ];then
	NBZ_PATH="$(dirname "$(readlink -f "$0")")"
else
	NBZ_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi
PYTHON3=$(which python3)
YELLOW='\e[33m'; RED='\e[31m'; NC='\e[0m'

if [ -z "${PYTHON3}" ]; then
	echo -e "${RED}NBZ - Error: Python 3 is not installed. Please install it in your system.${NC}"
	exit 1
fi

#  - Launch NBZ
TOILET=$(which toilet)
if [ -z "${TOILET}" ]; then
	header=""
else
	header=$(toilet -t -f mono12 -F gay "  NBZ  ")
fi

echo -e "${header}"
python3 -W ignore ${NBZ_PATH}/src/nbz_interface.py -script ${script} -script_parameters "${script_parameters[@]}" -display ${display} -proxy ${proxy} -resolution ${resolution} -debug ${debug}

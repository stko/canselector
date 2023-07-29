#!/bin/bash
# do the inital settings for a virtual car connected by a real or virtual CAN-Bus, realized by socketCAN devices

BAUDRATE=250000
BRMASTER=250000
CAN0=can0
CAN1=can1

echo "Use Baudrate of $BAUDRATE"
sudo modprobe can
sudo modprobe can_raw
sudo modprobe can_bcm
sudo modprobe vcan
#sudo ip link add dev vcan0 type vcan
#sudo ip link set up vcan0

stop_dump () {
	if [ -n "$dump_pid" ] ; then
		kill $dump_pid
		unset dump_pid
	fi
}

stop_send () {
	if [ -n "$send_pid" ] ; then
		kill $send_pid
		unset send_pid
	fi
}

PS3='Please take your choice: '
options=("bitrate 500k" "bitrate 250k" "bitrate 125k" "(re)start bus" "show can state" "send test data" "stop test data" "Quit")
select opt in "${options[@]}"
	do
		case $opt in

			"bitrate 125k")
				echo "you chose bitrate 125k"
				BAUDRATE=125000
				echo "bitrate set to $BAUDRATE"
			;;

			"bitrate 250k")
				echo "you chose bitrate 250k"
				BAUDRATE=250000
				echo "bitrate set to $BAUDRATE"
			;;

			"bitrate 500k")
				echo "you chose bitrate 500k"
				BAUDRATE=500000
				echo "bitrate set to $BAUDRATE"
			;;

			"(re)start bus")
				echo "you chose (re)start bus"
				stop_dump
				stop_send
				if ip link show $CAN0 ; then
				sudo ifconfig $CAN0 down
				fi
				if ip link show $CAN1 ; then
				sudo ifconfig $CAN1 down
				fi
				sudo ip link set $CAN0 type can bitrate $BRMASTER triple-sampling on
				sudo ifconfig $CAN0 up
				sudo ip link set $CAN1 type can bitrate $BAUDRATE triple-sampling on
				sudo ifconfig $CAN1 up
				candump $CAN0 $CAN1 &
				dump_pid=$!

			;;

			"show can state")
				echo "you chose show can state"
				ip -details link show $CAN0
				ip -details link show $CAN1
			;;

			"send test data")
				echo "send test data"
				stop_send
				cangen  $CAN1 &
				send_pid=$!
			;;

			"stop test data")
				echo "stop test data"
				stop_send
			;;

			"Quit")
        		stop_send
				stop_dump
				break
			;;
			*) echo invalid option;;
		esac
	done
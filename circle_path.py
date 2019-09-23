#!/usr/bin/env python

import sys, select, tty, termios
import rospy
from std_msgs.msg import Int16MultiArray

RANGE = 100  # expect all node values to be in interval [-RANGE, RANGE]
STEP = 25    # interpolate between current & target at this rate.
#moving element a towards element of b
def step(a,b):
	s=[]
	for va,vb in zip(a,b):
		if va==vb:
			s.append(va)
		elif va<vb:
			s.append(va +STEP)
		else:
			s.append(va-STEP)
	return s
#ROS publisher
publisher = rospy.Publisher('cmd', Int16MultiArray, queue_size=1, latch=True)
rospy.init_node("teleop")
rate=rospy.Rate(100)

def pub(values):
	values=[-v for v in values]
	rospy.loginfo("publish [%s]" % values)
	msg=Int16MultiArray()
	msg.data=values
	publisher.publish(msg)
#setting initial values to zero and publish them
current=[0]*4
target=[0]*4
pub(current)

# set cbreak on stdin (recall original attr to restore later)
# this is required for the polling select on stdin.
original_t_attr = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())

while not rospy.is_shutdown():
	set_immediately=False
	try:
		print("waiting for input")
		#select for next char, timeout in 0.1s
		if select.select([sys.stdin],[],[],0.1)[0]==[sys.stdin]:
			c=sys.stdin.read(1)
			#immediate stop
			if c==' ':
				set_immediately=True
				target=[0]*4
				print("immediate stopping")
			elif c=='w':
				target=[-RANGE]*4
				print("forward")
			elif c=='s':
				target=[0]*4
				print("slow stop")
			elif c=='x':
				target=[RANGE ]*4
				print("backwards")
			elif c=='a':
				target=[-RANGE,-RANGE, 0, -200]
				print("steer right")
			elif c=='d':
				target=[-RANGE,-RANGE,0,200]
				print("steer left")
	except:
		# select error? assume ctrl-c during in blocking select
        	# and completely bail now.
		break
	#to move current values towards the target if required
	if current != target:
		if set_immediately:
			current=target
		else:
			current=step(current,target)
		pub(current)
		#spin ros
		rate.sleep()

#pub stop and restore terminal settings
pub([0]*4)
termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_t_attr)

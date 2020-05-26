#!/usr/bin/env python3

from rospy import wait_for_service, ServiceProxy, ServiceException, Time, sleep, init_node, is_shutdown, Subscriber
from actionlib import SimpleActionClient
from uob_tour_guide.srv import Speak, Listen
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import String
from utility import get_map_nodes, get_tour_nodes
import json

class RunRobot:
    def __init__(self):
        print('Robot running...')
        self.amcl_pose = None
        self.current_location = None
    
        init_node('uob_tour_guide', anonymous=True)

        while not is_shutdown():
            self.listen_to_robot()

    # TODO: Implement "Ok Robot" before asking for tours?
    # TODO: Implement help feature that loops through available locations?
    def listen_to_robot(self):
        speech = self.robot_listen()
        print(speech)
        map_nodes = get_map_nodes()
        
        if speech['_text'] and speech['entities']:
            if 'intent' in speech['entities'] and speech['entities']['intent'][0]['value'] == 'tour':
                self.robot_speak('Do you want a full tour around the building?')
                new_speech = self.robot_listen()
                print(new_speech)

                if 'intent' in new_speech['entities'] and new_speech['entities']['intent'][0]['value'] == 'true':
                    self.robot_speak('Follow me for the tour')
                    print('Tour method here')
                    self.get_amcl_pose()
                    tour_nodes = get_tour_nodes(map_nodes=map_nodes, location={ 'x': self.current_location.x, 'y': self.current_location.y })

                    for node in tour_nodes:
                        print(f'Moving to: {node["position"]}')
                        self.robot_speak(f'Follow me to the {node["name"]}')
                        self.robot_move(node)
                            
                        self.robot_speak(node['description'])
                        sleep(0.5)
                        
                    self.robot_speak('That concludes the tour.')

                elif 'intent' in new_speech['entities'] and new_speech['entities']['intent'][0]['value'] == 'false':
                    self.robot_speak('Cancelling full tour')
                else:
                    self.robot_speak('Sorry, I didn\'t catch that, cancelling full tour')
            elif 'move_to' in speech['entities']:
                for node in map_nodes:
                    keyword = speech['entities']['move_to'][0]['value'].lower()
                    keywords = [word.lower() for word in node['keywords']]

                    if keyword == node['name'].lower() or keyword in keywords:
                        self.robot_speak(f'Shall I move to {keyword}?')
                        new_speech = self.robot_listen()
                        print(new_speech)

                        if 'intent' in new_speech['entities'] and \
                            new_speech['entities']['intent'][0]['value'] == 'true':
                            self.robot_speak(f'Moving towards {keyword}')
                            print(f'Moving to: {node["position"]}')

                            self.robot_move(node)
                            self.robot_speak(node['description'])

                        elif 'intent' in new_speech['entities'] and \
                            new_speech['entities']['intent'][0]['value'] == 'false':
                            self.robot_speak(f'Cancelling movement to {keyword}')
                        else:
                            self.robot_speak(f'Sorry, I didn\'t catch that, cancelling movement to {keyword}')
    
    def robot_move(self, map_node):
        client = SimpleActionClient('move_base', MoveBaseAction)
        client.wait_for_server()

        goal = MoveBaseGoal()
        
        goal.target_pose.header.frame_id = map_node['frame_id']
        goal.target_pose.header.stamp = Time.now()

        goal.target_pose.pose.position.x = map_node['position']['x']
        goal.target_pose.pose.position.y = map_node['position']['y']
        goal.target_pose.pose.position.z = map_node['position']['z']

        goal.target_pose.pose.orientation.x = map_node['orientation']['x']
        goal.target_pose.pose.orientation.y = map_node['orientation']['y']
        goal.target_pose.pose.orientation.z = map_node['orientation']['z']
        goal.target_pose.pose.orientation.w = map_node['orientation']['w']

        client.send_goal(goal)
        client.wait_for_result()

        return client.get_result()

    def robot_speak(self, value):
        wait_for_service('robot_speak')

        try:
            speak = ServiceProxy('robot_speak', Speak)
            speak(value)
        except ServiceException as e:
            print(e)
        
    def robot_listen(self):
        wait_for_service('robot_listen')

        try:
            listen = ServiceProxy('robot_listen', Listen)
            response = listen()
            replace_chars = ['u\'', '\'']
            data = response.data
            for char in replace_chars:
                data = data.replace(char, '"')

            return json.loads(data)
        except (ServiceException, json.decoder.JSONDecodeError) as e:
            print(e)
            return {'_text': '', 'entities': {}}
        
    def assign_amcl_pose(self, result):
        self.amcl_pose = result
        self.current_location = result.pose.pose.position
    
    def get_amcl_pose(self):
        sub = Subscriber('amcl_pose', PoseWithCovarianceStamped, self.assign_amcl_pose)
        sleep(0.1)
        sub.unregister()


if __name__ == '__main__':
    RunRobot()

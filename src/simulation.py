from time import sleep
import sys
import traci
import traci.constants as tc
import pandas as pd
import numpy as np

class Simulation:
    def __init__(self, simulation_steps, sleep_time, pedestrians, bus_depot_start_edge, bus_depot_end_edge, \
                    capacity, interval, stopDuration, departPref):
        self.simulation_steps = simulation_steps
        self.sleep_time = sleep_time
        self.pedestrians = pedestrians
        self.bus_depot_start_edge = bus_depot_start_edge
        self.bus_depot_end_edge = bus_depot_end_edge
        self.dispatch_interval = interval*60
        self.bus_capacity = capacity
        self.stop_duration = stopDuration
        self.depart_preference = departPref
    
    '''
        Groups passengers according to a predefined depart interval.
        The groups of passengers are sorted according to our preliminary sorting algorithm.
    '''
    def group_n_passenger(self, number_of_passenger_per_group, df_time_interval):
        group = []
        sorted_by_edge_from_df_time_interval = df_time_interval.sort_values('modified_edge_from')
        for number_of_group in range(df_time_interval.shape[0]//number_of_passenger_per_group+1):
            df_group_with_n_passenger = sorted_by_edge_from_df_time_interval[number_of_group*number_of_passenger_per_group:(number_of_group+1)*number_of_passenger_per_group:]
            group.append(df_group_with_n_passenger.sort_values('depart').values)
        return group

    '''
        Returns indices of passengers grouped based on their departure time
    '''
    def divide_data_by_time(self, data):
        time_interval = np.arange(0, self.simulation_steps, self.dispatch_interval)
        idx_time_interval = [] 
        for t in range(time_interval.shape[0] - 1):
            idx_time_interval.append(np.where((data['depart']>time_interval[t]) & (data['depart']<time_interval[t+1]))[0])
        return idx_time_interval

    '''
        Greedy II: Our greedy algorthm to search for the best pick-up and drop-off routes
    '''
    def find_best_route(self, group, bus_id, bus_index):
        route_list = [self.bus_depot_start_edge]
        traci.vehicle.setRoute(bus_id, [self.bus_depot_start_edge])

        possible_directions = []
        # pickup point of the first person
        # possible_directions takes in tuple of (edge, position, src or to, person_idx)
        possible_directions.append((group[0][1], group[0][3], 'src', 0))
        waiting_person_idx = 1
        for i in range(len(group) * 2):
            # if bus_index == 1:
            #     print(possible_directions)
            
            min_len = 999999
            best_idx = -1
            best_route = []
            for j, pd in enumerate(possible_directions):
                traci.vehicle.changeTarget(bus_id, pd[0])
                new_route = traci.vehicle.getRoute(bus_id)
                if len(new_route) < min_len:
                    min_len = len(new_route)
                    best_route = new_route
                    best_idx = j                

            route_list += list(best_route[1:])
            best_direction = possible_directions[best_idx]
            traci.vehicle.changeTarget(bus_id, best_direction[0])
            traci.vehicle.setStop(vehID=bus_id, edgeID=best_direction[0], pos=best_direction[1], 
                laneIndex=0, duration=20 if best_direction[2] == 'src' else self.stop_duration, flags=tc.STOP_DEFAULT)   
            traci.vehicle.setRoute(bus_id, best_direction[0])
            # add new passenger's drop-off location to possible_directions
            if best_direction[2] == 'src':
                person_idx = best_direction[3]
                possible_directions.append((group[person_idx][2], group[person_idx][4], 'to', person_idx))
                # picks up the next waiting passenger
                if waiting_person_idx < len(group):
                    possible_directions.append((group[waiting_person_idx][1], group[waiting_person_idx][3], 'src', waiting_person_idx))
                    waiting_person_idx += 1

            possible_directions.remove(best_direction)

        traci.vehicle.changeTarget(bus_id, self.bus_depot_end_edge)
        route_list += list(traci.vehicle.getRoute(bus_id)[1:])
        traci.vehicle.setRoute(bus_id, route_list)


    '''
        Greedy I: Our greedy algorthm to search for the best drop-off routes
    '''    
    def find_best_route1(self, group, bus_id, bus_index):
        route_list = [self.bus_depot_start_edge]
        traci.vehicle.setRoute(bus_id, [self.bus_depot_start_edge])

        for person in group:
            # ['id', 'edge_from', ' edge_to', ' position_from', ' position_to', ' depart']
            traci.vehicle.changeTarget(bus_id, person[1])
            route_list += list(traci.vehicle.getRoute(bus_id)[1:])
            if bus_index == 1:
                print(traci.vehicle.getRoute(bus_id))      
            traci.vehicle.setStop(vehID=bus_id, edgeID=person[1], pos=person[3], laneIndex=0, duration=20, flags=tc.STOP_DEFAULT)    
            traci.vehicle.setRoute(bus_id, [person[1]])     
            if bus_index == 1:
                print(traci.vehicle.getRoute(bus_id))   

        visited = [False] * len(group)
        for j in range(len(group)):
            min_len = 999999
            best_idx = -1
            best_route = []

            for i in range(len(group)):
                if visited[i] == True:
                    continue
                traci.vehicle.changeTarget(bus_id, group[i][2])
                new_route = traci.vehicle.getRoute(bus_id)
                if len(new_route) < min_len:
                    min_len = len(new_route)
                    best_route = new_route
                    best_idx = i

            route_list += list(best_route[1:])
            visited[best_idx] = True
            traci.vehicle.changeTarget(bus_id, group[best_idx][2])
            traci.vehicle.setStop(vehID=bus_id, edgeID=group[best_idx][2], pos=group[best_idx][4], laneIndex=0, duration=self.stop_duration, flags=tc.STOP_DEFAULT)    
            traci.vehicle.setRoute(bus_id, group[best_idx][2])     

        traci.vehicle.changeTarget(bus_id, self.bus_depot_end_edge)
        route_list += list(traci.vehicle.getRoute(bus_id)[1:])
        traci.vehicle.setRoute(bus_id, route_list)

    def algo(self):
        bus_index = 0
        df = pd.DataFrame(p.to_dict() for p in self.pedestrians)
        # df['modified_edge_from'] = df.edge_from.apply(lambda x: x[1:] if [0] == '-' else x)
        # df['modified_edge_from'] = df.modified_edge_from.apply(lambda x: x[:x.find('#')] if x.find('#') != -1 else x)
        # df['modified_edge_from'] = df.modified_edge_from.apply(lambda x: (len(x), x))
        df['modified_edge_from'] = df.edge_from.apply(lambda x: (len(x[1:]), x[1:]) if [0] == '-' else (len(x), x))
        idx_time_interval = self.divide_data_by_time(df)
        for number_of_group in range(len(idx_time_interval)):
            group_30_min_data = df.loc[idx_time_interval[number_of_group]]   

            groups = self.group_n_passenger(self.bus_capacity, group_30_min_data)
            for group in groups:
                if len(group) == 0:
                    continue
                bus_id = f'bus_{bus_index}'
                bus_index += 1
                traci.vehicle.add(vehID=bus_id, typeID="BUS_L", routeID="", depart=np.min(group[:,5]), departPos=0, departSpeed=0, departLane=0, personCapacity=8)
                

                ##################################################
                # Route Scheduling Function
                ##################################################
                self.find_best_route1(group, bus_id, bus_index)
           
        traci.vehicle.subscribe('bus_0', (tc.VAR_ROAD_ID, tc.VAR_LANEPOSITION, tc.VAR_POSITION , tc.VAR_NEXT_STOPS ))
        step = 0
        while step <= self.simulation_steps:
            traci.simulationStep()
            if self.sleep_time > 0: 
                sleep(self.sleep_time)
            step += 1

        traci.close()

import hlt
import logging
from operator import itemgetter

logging.info("D4m0b0t running")

game = hlt.Game("D4m0b0t")

debugging = True

def planet_sort_by_distance(current_ship, planet_list):
    """
    Sort the given solar system into planets weighted by least distance from given ship to planet
    :param Ship current_ship:
    :param array planet_list:
    :return: List of tuples containing planet_object & distance from current_ship
    :rtype: List of Tuples
    """

    nang = []
    for ouah in planet_list:
        nang.append({'planet_object' : ouah, 'distance' : ouah.calculate_distance_between(current_ship)})

    return sorted(nang, key=itemgetter('distance'))

def planet_sort_by_docked(planet_list):
    """
    Sort the given solar system into planets weighted by least ships docked
    :param array planet_list: List of planets to be weighted
    :return: List of tuples of weighted planets
    :rtype: List of Tuples
    """

    nang = []
    for ouah in planet_list:
        nang.append({'planet_object' : ouah, 'number_docked' : len(ouah.all_docked_ships())})

    return sorted(nang, key=itemgetter('number_docked'))

def find_first_unowned(planet_list, already_targeted, ship_id):
    """
    Check through the list of planets and return the first one that is not owned (or None), and not already targeted by another
    ship in our fleet
    :param array planet_list:
    :param array of arrays/hashes already_targeted:
    :param integer ship_id:
    :return: Unowned planet
    :rtype: Planet
    """

    taken = False

    for target in planet_list:  #each potential target planet
        if not target.is_owned():   #if it isn't already occupied
            for targeted_by in already_targeted:  #loop through already targeted list
                if ship_id == targeted_by[1]:  #is this really necessary?
                    return target
                else:
                    taken = True
            #end targeted loop
        #end not already occupied loop
        if not taken:
            return target
        else:
            taken = False
    #no more potential target planets

    if len(planet_list) > 0:
        return planet_list[0]
    else:
        return 

def other_entities_in_vicinity(current_entity, other_entities, scan_distance):
    """
    Check to see if there are any more specified entities within the immediate vicinity
    :param Entity current_entity:
    :param array other_entities:
    :param integer scan_distance:
    :return: Angle between this entity and the first other found within collision risk area, or None
    :rtype: float
    """

    for other_entity in other_entities:
        if current_entity.calculate_distance_between(other_entity) <= scan_distance:
            return current_entity.calculate_angle_between(other_entity)

    return None

#entrance
DEBUGGING = {
        'reinforce': True
}

#begin primary game loop
while True:
    game_map = game.update_map()
    my_id = game_map.get_me().id
    #default_speed = int(hlt.constants.MAX_SPEED / 2)
    default_speed = hlt.constants.MAX_SPEED

    targeted_list = []
    command_queue = []


    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            #we need to check for incoming enemies and determine what to do here if so
            continue
        else:
            #locate the 'best target' for this particular ship right nao
            success = False
            any_unowned = False
            sorted_planets = planet_sort_by_distance(ship, game_map.all_planets())
            for target in sorted_planets:
                if not target['planet_object'].is_owned():
                    any_unowned = True
                    break

            if any_unowned:
                for target in planet_sort_by_distance(ship, game_map.all_planets()):
                    if target['planet_object'].is_owned():
                        continue
                    elif target['planet_object'] in targeted_list:
                        continue
                    else:
                        #now is our potential target closer to the bad guys?
                        for player in game_map.all_players():
                            if not player == game_map.get_me():
                                if other_entities_in_vicinity(target['planet_object'], player.all_ships(), \
                                        target['planet_object'].calculate_distance_between(ship)):
                                    #someone else is as close or closer
                                    #we can probably throw in some offensive code here
                                    success = False
                                    continue

                        success = True
                        targeted_list.append(target['planet_object'])
                        break
            else:
                #no unowned planets - reinforce my planets or go offensive
                for target in planet_sort_by_distance(ship, game_map.all_planets()):
                    if target['planet_object'].owner == my_id and not target['planet_object'].is_full():
                        if DEBUGGING['reinforce']:
                            logging.info('Reinforcing')

                        if not other_entities_in_vicinity(target['planet_object'], player.all_ships(), \
                                target['planet_object'].calculate_distance_between(ship)):
                            success = True
                            break

            if not success:
                #haven't found anything with the simple targeting criteria; what's next?
                if len(targeted_list) > 0:
                    target = planet_sort_by_distance(ship, targeted_list)[0]
            
            if ship.can_dock(target['planet_object']):
                command_queue.append(ship.dock(target['planet_object']))
                continue
            else:
                #collision_risk_angle = other_ships_in_vicinity(ship, game_map.get_me().all_ships(), 3)
                navigate_command = ship.navigate(
                        ship.closest_point_to(target['planet_object']),
                        game_map,
                        speed = default_speed,
                        ignore_ships = False)

            if navigate_command:
                command_queue.append(navigate_command)
        #end for undocked ship
    #end this ship's processing

    game.send_command_queue(command_queue)

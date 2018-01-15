import hlt
import logging
from operator import itemgetter

logging.info("D4m0b0t running")

game = hlt.Game("D4m0b0t")

debugging = True

def entity_sort_by_distance(current_ship, planet_list):
    """
    Sort the given solar system into planets weighted by least distance from given ship to planet
    :param Ship current_ship:
    :param List planet_list:
    :return: List of tuples containing entity_object & distance from current_ship
    :rtype: List of Tuples
    """
    nang = []
    for ouah in planet_list:
        nang.append({'entity_object' : ouah, 'distance' : ouah.calculate_distance_between(current_ship)})

    return sorted(nang, key=itemgetter('distance'))

def planet_sort_by_docked(planet_list):
    """
    Sort the given solar system into planets weighted by least ships docked
    :param List planet_list: List of planets to be weighted
    :return: List of tuples of weighted planets
    :rtype: List of Tuples
    """
    nang = []
    for ouah in planet_list:
        nang.append({'entity_object' : ouah, 'number_docked' : len(ouah.all_docked_ships())})

    return sorted(nang, key=itemgetter('number_docked'))

def find_first_unowned(planet_list, already_targeted, ship_id):
    """
    Check through the list of planets and return the first one that is not owned (or None), and not already targeted by another
    ship in our fleet
    :param List planet_list:
    :param List of lists/hashes already_targeted:
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
    :param List other_entities:
    :param integer scan_distance:
    :return: Angle between this entity and the first other found within collision risk area, or None
    :rtype: float
    """
    for other_entity in other_entities:
        if current_entity.calculate_distance_between(other_entity) <= scan_distance:
            return current_entity.calculate_angle_between(other_entity)

    return None

def offensive_targeting(current_entity, other_entities):
    """
    Check for enemies within firing range
    :param Entity current_entity:
    :param List other_entities:
    :return: intercept angle or None
    :rtype: float
    """
    enemy_intercept_angle = other_entities_in_vicinity(current_entity, other_entities, 5)

    if enemy_intercept_angle:
        return enemy_intercept_angle
    else:
        return None

def get_enemy_ships():
    """
    Retrieve all enemy ships
    :return: all enemy ships
    :rtype: List of ships
    """
    enemy_ships = []
    for jackass in game_map.all_players():
        if not jackass == game_map.get_me():
            for ship in jackass.all_ships():
                enemy_ships.append(ship)

    return enemy_ships

#entrance
#constants
DEBUGGING = {
        'reinforce': False,
        'targeting': True
}

#begin primary game loop
while True:
    game_map = game.update_map()
    my_id = game_map.get_me().id
    #default_speed = int(hlt.constants.MAX_SPEED / 2)
    #default_speed = int(hlt.constants.MAX_SPEED / 1.75)
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
            sorted_planets = entity_sort_by_distance(ship, game_map.all_planets())
            for target in sorted_planets:
                if not target['entity_object'].is_owned():
                    any_unowned = True
                    break

            if any_unowned:
                for target in entity_sort_by_distance(ship, game_map.all_planets()):
                    if target['entity_object'].is_owned():
                        continue
                    elif target['entity_object'] in targeted_list:
                        continue
                    else:
                        #now is our potential target closer to the bad guys?
                        #for player in game_map.all_players():
                        #    if not player == game_map.get_me():
                        #        if other_entities_in_vicinity(target['entity_object'], player.all_ships(), \
                        #                target['entity_object'].calculate_distance_between(ship)):
                                    #someone else is as close or closer
                                    #we can probably throw in some offensive code here
                        #            success = False
                        #            continue
                        if other_entities_in_vicinity(target['entity_object'], get_enemy_ships(), \
                                target['entity_object'].calculate_distance_between(ship)):
                            success = False
                            continue

                        success = True
                        targeted_list.append(target['entity_object'])
                        break
            else:
                #no unowned planets - reinforce my planets or go offensive
                for target in entity_sort_by_distance(ship, game_map.all_planets()):
                    if target['entity_object'].owner == my_id and not target['planet_object'].is_full():
                        if DEBUGGING['reinforce']:
                            logging.info('Reinforcing')

                        if not other_entities_in_vicinity(target['entity_object'], player.all_ships(), \
                                target['entity_object'].calculate_distance_between(ship)):
                            success = True
                            break

                if not success:
                    #find an enemy to attack
                    if DEBUGGING['targeting']:
                        logging.info('Targeting')

                    target = entity_sort_by_distance(ship, get_enemy_ships())[0]
                    success = True

            if not success:
                #haven't found anything with the simple targeting criteria; what's next?
                if len(targeted_list) > 0:
                    target = entity_sort_by_distance(ship, targeted_list)[0]
            
            if target['entity_object'] in game_map.all_planets() and ship.can_dock(target['entity_object']):
                command_queue.append(ship.dock(target['entity_object']))
                continue
            else:
                #collision_risk_angle = other_ships_in_vicinity(ship, game_map.get_me().all_ships(), 3)
                navigate_command = ship.navigate(
                        ship.closest_point_to(target['entity_object']),
                        game_map,
                        speed = default_speed,
                        ignore_ships = False)

            if navigate_command:
                command_queue.append(navigate_command)
        #end for undocked ship
    #end this ship's processing

    game.send_command_queue(command_queue)

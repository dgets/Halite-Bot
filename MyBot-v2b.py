import hlt
import logging
from operator import itemgetter

game = hlt.Game("D4m0b0t - v2b - rewrite & flow restructuring")

def docked_actions(current_ship):
    """
    Determine what to do with our docked ship
    :param Ship current_ship:
    :return: command to append to the command_queue
    :rtype: List
    """
    if DEBUGGING['method_entry']:
        log.debug("docked_actions():")
        
    if DEBUGGING['ship_loop']:
        log.debug("-+=Docked ship #" + str(current_ship.id) + "=+-")
            
    #did we just complete docking?
    if current_ship in dock_process_list.keys():
        if DEBUGGING['docking_procedures']:
            log.debug(" - completed docking")
            
        dock_process_list.remove(current_ship)
                
    if ALGORITHM['boobytrapping']:    #fully docked
        #is it time to bid thee farewell?
        if current_ship.planet.remaining_resources <= (current_ship.planet.num_docking_spots * DOCKING_TURNS * PRODUCTION) + 10:
            #syntax/logic in the following conditional (specifically the 'not') may be phrased wrong
            if not current_ship.planet in planets_to_avoid:
                if DEBUGGING['boobytrapping']:
                    log.debug("Leaving a present")

                planets_to_avoid.append(current_ship.planet)
                undock_process_list[current_ship] = current_ship.planet
                command_queue.append(ship.undock(current_ship.planet))

def target_planet(current_ship, planets_ranked_by_distance, planets_ranked_ours_by_docked, planets_ranked_untapped):
    """
    Determine if a planet is a viable target for mining; create the navigation command if so
    :param Ship current_ship:
    :param List of Tuples planets_ranked_by_distance:
    :param List of Tuples planets_ranked_ours_by_docked:
    :param List of Tuples planets_ranked_untapped:
    :return: navigation command for command_queue or None
    :rtype: String or None
    """
    navigate_command = None

    #do we navigate to a planet, reinforce, or go offensive?
    #navigate to a planet or begin docking (this also currently handles reinforcing)
    for potential_planet in remove_held_planets(planets_ranked_untapped):
        if (potential_planet['entity_object'] in targeted_list) or \
            (potential_planet['entity_object'].num_docking_spots == len(potential_planet['entity_object'].all_docked_ships())):
                if DEBUGGING['targeting']:
                    log.debug(" - skipping already targeted or full planet #" + str(potential_planet['entity_object'].id))
                    
                continue
        if current_ship.can_dock(potential_planet['entity_object']):    #why ship & not current_ship again?
            if DEBUGGING['planet_selection']:
                log.debug(" - docking with planet #" + str(potential_planet['entity_object'].id))
                
            #dock_process_list[current_ship] = potential_planet['entity_object']
            navigate_command = current_ship.dock(potential_planet['entity_object'])
            if potential_planet['entity_object'] in targeted_list:
                if DEBUGGING['planet_selection']:
                    log.debug(" - removing planet #" + str(potential_planet['entity_object'].id) + " from targeted_list")
                        
                targeted_list.remove(potential_planet['entity_object'])
            break
        elif potential_planet['entity_object'] not in targeted_list:
            if DEBUGGING['targeting']:
                log.debug(" - navigating to planet #" + str(potential_planet['entity_object'].id))
                    
            targeted_list.append(potential_planet['entity_object'])
            navigate_command = current_ship.navigate(
                    current_ship.closest_point_to(potential_planet['entity_object']),
                    game_map,
                    speed = default_speed,
                    ignore_ships = False)
            break
        
    return navigate_command

def undocked_actions(current_ship):
    """
    Determine what to do with the undocked ship
    :param Ship current_ship:
    :return: command to append to the command_queue
    :rtype: List
    """
    if DEBUGGING['method_entry']:
        log.debug("undocked_actions():")
        
    if DEBUGGING['ship_loop']:
        log.debug("-+=Undocked ship #" + str(current_ship.id) + "=+-")
                
    #did we just complete undocking?
    if current_ship in undock_process_list.keys():
        if DEBUGGING['docking_procedures']:
            log.debug(" - completed undocking")
            
        undock_process_list.remove(current_ship)
                
    success = False
    ranked_planets_by_distance = entity_sort_by_distance(current_ship, game_map.all_planets())
    ranked_our_planets_by_docked = planet_sort_ours_by_docked(game_map.all_planets())
    ranked_untapped_planets = remove_tapped_planets(ranked_planets_by_distance, planets_to_avoid)
    enemies = get_enemy_ships()
    
    #get our command, if navigation to/docking with a planet is the best course of action
    #else None
    navigate_command = target_planet(current_ship, ranked_planets_by_distance, ranked_our_planets_by_docked, ranked_untapped_planets)

    if not navigate_command:    
        #potential_angle = other_entities_in_vicinity(current_ship, enemies, ranked_untapped_planets[0]['distance'])
        if ALGORITHM['offense']: # and potential_angle:
            #another entity is closer or at the same distance; we need to go offensive
            if DEBUGGING['offense']:
                log.debug("Engaging enemy")

            closest_enemy = entity_sort_by_distance(current_ship, enemies)[0]['entity_object']
            
            if ALGORITHM['kamikaze']:
                potential_kamikaze_angle = other_entities_in_vicinity(current_ship, enemies, 100)
                
            if DEBUGGING['kamikaze']:
                log.debug(" - potential_kamikaze_angle: " + str(potential_kamikaze_angle))
                
            if ALGORITHM['kamikaze'] and potential_kamikaze_angle:
                if DEBUGGING['kamikaze'] and DEBUGGING['offense']:
                    log.debug(" - going kamikaze")
                    
                navigate_command = current_ship.thrust(hlt.constants.MAX_SPEED, potential_kamikaze_angle)
            else:
                if DEBUGGING['offense']:
                    log.debug(" - engaging ship #" + str(closest_enemy.id))
                    
                navigate_command = current_ship.navigate(
                    current_ship.closest_point_to(closest_enemy),
                    game_map,
                    speed = default_speed,
                    ignore_ships = False)
        elif ALGORITHM['reinforce'] and len(ranked_our_planets_by_docked) > 0:
            #reinforce that sucker
            if DEBUGGING['reinforce']:
                log.debug("Reinforcing planet #" + str(ranked_our_planets_by_docked[0]['entity_object'].id))

            if current_ship.can_dock(ranked_our_planets_by_docked[0]['entity_object']):
                if DEBUGGING['reinforce']:
                    log.debug(" - docking @ planet #" + str(ranked_our_planets_by_docked[0]['entity_object'].id))
            
                navigate_command = current_ship.dock(ranked_our_planets_by_docked[0]['entity_object'])
            else:
                if DEBUGGING['reinforce']:
                    log.debug(" - navigating to reinforce planet #" + str(ranked_untapped_planets[0]['entity_object']))
               
                navigate_command = current_ship.navigate(
                    current_ship.closest_point_to(ranked_untapped_planets[0]['entity_object']),
                    game_map,
                    speed = default_speed,
                    ignore_ships = False)

    return navigate_command

def remove_held_planets(planets_list):
    """
    Remove all planets from the list that are already held by a player
    :param List planets_list: List of Tuples containing planet_object => object
    :return List with owned planets removed:
    :rtype: List of Typles
    """
    if DEBUGGING['method_entry']:
        log.debug("remove_held_planets():")
        
    for possibly_owned_planet in planets_list:
        if not possibly_owned_planet:
            if DEBUGGING['targeting']:
                log.debug(" - removing owned planet #" + str(possibly_owned_planet['entity_object'].id) + " from list")
                
            planets_list.remove(possibly_owned_planet)
            
    return planets_list

def entity_sort_by_distance(current_ship, planet_list):
    """
    Sort the given solar system into planets weighted by least distance from given ship to planet
    :param Ship current_ship:
    :param List planet_list:
    :return: List of tuples containing entity_object & distance from current_ship
    :rtype: List of Tuples
    """
    if DEBUGGING['method_entry']:
        log.debug("entity_sort_by_distance():")
        
    nang = []
    for ouah in planet_list:
        nang.append({'entity_object' : ouah, 'distance' : ouah.calculate_distance_between(current_ship)})

    return sorted(nang, key=itemgetter('distance'))

def planet_sort_ours_by_docked(planet_list):
    """
    Sort the given solar system into planets weighted by least ships docked
    :param List planet_list: List of planets to be weighted
    :return: List of tuples of weighted planets
    :rtype: List of Tuples
    """
    if DEBUGGING['method_entry']:
        log.debug("planet_sort_by_docked():")
        
    nang = []
    for ouah in planet_list:
        if ouah.owner == game_map.get_me():
            nang.append({'entity_object' : ouah, 'number_docked' : len(ouah.all_docked_ships())})
            
    if len(nang) > 0:
        #remove planets with no docking slots open
        for ouah in nang:
            if ouah['number_docked'] >= ouah['entity_object'].num_docking_spots:
                nang.remove(ouah)

    return sorted(nang, key=itemgetter('number_docked'))

def other_entities_in_vicinity(current_entity, other_entities, scan_distance):
    """
    Check to see if there are any more specified entities within the immediate vicinity
    :param Entity current_entity:
    :param List other_entities:
    :param integer scan_distance:
    :return: Collision angle if any
    :rtype: Collision angle or none
    """
    if DEBUGGING['method_entry']:
        log.debug("other_entities_in_vicinity()")
    
    #closest_docked_distance = scan_distance
    target_planet = None
    
    for other_entity in other_entities:
        #if other_entity.docking_status == current_entity.DockingStatus.DOCKED or \
        #   other_entity.docking_status == current_entity.DockingStatus.DOCKING:
        if current_entity.planet:
            continue
        
        proximity = int(current_entity.calculate_distance_between(other_entity))
        if DEBUGGING['kamikaze']:
            log.debug("\t- current_entity's proximity: " + str(proximity) + " vs scan_distance: " + str(scan_distance))
            
        if proximity < scan_distance:
            if DEBUGGING['kamikaze']:
                log.debug("\t- proximity is less than scan_distance")
            
            if current_entity.docking_status == current_entity.DockingStatus.DOCKED or \
               current_entity.docking_status == current_entity.DockingStatus.DOCKING:
                if DEBUGGING['kamikaze']:
                    log.debug("\t\t- setting target_planet to current_entity.planet")
                    
                target_planet = current_entity.planet
                break
            else:
                continue
                
    if target_planet:
        return current_entity.calculate_angle_between(target_planet)

    return None

def offensive_targeting(current_entity, other_entities):
    """
    Check for enemies within firing range
    :param Entity current_entity:
    :param List other_entities:
    :return: intercept angle or None
    :rtype: float
    """
    if DEBUGGING['method_entry']:
        log.debug("offensive_targeting():")
        
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
    if DEBUGGING['method_entry']:
        log.debug("get_enemy_ships():")
        
    enemy_ships = []
    for jackass in game_map.all_players():
        if not jackass == game_map.get_me():
            for ship in jackass.all_ships():
                enemy_ships.append(ship)

    return enemy_ships

def remove_tapped_planets(testing_planets, avoid_planets):
    """
    Remove all avoid_planets from testing_planets
    :param List testing_planets:
    :param List avoid_planets:
    :return: planets sans tapped planets
    :rtype: List of planets
    """
    if DEBUGGING['method_entry']:
        log.debug("remove_tapped_planets():")
        
    for bogus in avoid_planets:
        if bogus in testing_planets:
            testing_planets.remove(bogus)   #this is going to fail if python passes immutably

    return testing_planets

#entrance
#constants
DEBUGGING = {
        'ship_loop': True,
        'docking_procedures': False,
        'reinforce': False,
        'offense': True,
        'kamikaze': False,
        'planet_selection': True,
        'targeting': True,
        'boobytrapping': False,
        'method_entry': True
}
ALGORITHM = {
        'reinforce': False,
        'offense': True,
        'kamikaze': False,
        'boobytrapping': True
}

PRODUCTION = 6
DOCKING_TURNS = 5

planets_to_avoid = []
dock_process_list = {}
undock_process_list = {}
enemy_data = {}

#init
log = logging.getLogger(__name__)
logging.info("D4m0b0t active")

#begin primary game loop
while True:
    if DEBUGGING['ship_loop']:
        log.debug("-+Beginning turn+-")
        
    game_map = game.update_map()
    my_id = game_map.get_me().id
    #default_speed = int(hlt.constants.MAX_SPEED / 2)
    #default_speed = int(hlt.constants.MAX_SPEED / 1.75)
    default_speed = hlt.constants.MAX_SPEED

    command_queue = []
    targeted_list = []

    for ship in game_map.get_me().all_ships():
        if ship.docking_status == ship.DockingStatus.DOCKED:
            new_command = docked_actions(ship)
            if new_command:
                command_queue.append(new_command)
            continue
        elif ship.docking_status == ship.DockingStatus.UNDOCKED:
            new_command = undocked_actions(ship)
            if new_command:
                command_queue.append(new_command)
            continue
    #end per-ship iteration

    game.send_command_queue(command_queue)
    



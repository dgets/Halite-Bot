import hlt
import logging
from operator import itemgetter

game = hlt.Game("D4m0b0t - v2.2b - smarter offense")

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

def go_offensive(current_ship, enemies):
    """
    Returns navigation command for offense, or None if not the best course of action at this juncture
    :param Ship current_ship:
    :param List of Tuples enemies:
    :return navigation_command or None:
    :rtype: String or None
    """
    navigate_command = None

    if DEBUGGING['offense']:
        log.debug("Engaging enemy")

    close_enemies = entity_sort_by_distance(current_ship, enemies)
    closest_enemy = close_enemies[0]['entity_object']
    close_friendlies = entity_sort_by_distance(current_ship, game_map.get_me().all_ships())
    close_planets = entity_sort_by_distance(current_ship, game_map.all_planets())
    
    #implementation of kamikaze was never completed
    if ALGORITHM['kamikaze']:
        potential_kamikaze_angle = other_entities_in_vicinity(current_ship, enemies, 100) #note '100' was for debugging
                
        if DEBUGGING['kamikaze']:
            log.debug(" - potential_kamikaze_angle: " + str(potential_kamikaze_angle))
                
        if potential_kamikaze_angle:
            if DEBUGGING['kamikaze'] and DEBUGGING['offense']:
                log.debug(" - going kamikaze")
                    
            navigate_command = current_ship.thrust(hlt.constants.MAX_SPEED, potential_kamikaze_angle)

    if not ALGORITHM['kamikaze'] or not navigate_command:
        if DEBUGGING['offense']:
            log.debug(" - engaging ship #" + str(closest_enemy.id))
        
        num_enemies_in_range = count_ships_in_firing_range(current_ship, close_enemies, MAX_FIRING_DISTANCE)
        num_friendlies_in_range = count_ships_in_firing_range(current_ship, close_friendlies, MAX_FIRING_DISTANCE)
        
        if ALGORITHM['ram_planets_when_enemy_occupied'] and (close_planets[0]['distance'] <= (MAX_FIRING_DISTANCE * 2) and
                                                             close_planets[0]['entity_object'].owner != current_ship.owner and
                                                             close_planets[0]['entity_object'].num_docking_spots == 
                                                             len(close_planets[0]['entity_object'].all_docked_ships())):
            if DEBUGGING['ram_planets_when_enemy_occupied']:
                log.debug("   - ramming enemy owned planet #" + str(close_planets[0]['entity_object'].id))
                
            return current_ship.navigate(
                close_planets[0]['entity_object'],
                game_map,
                speed = hlt.constants.MAX_SPEED,
                ignore_ships = True)
        
        if not ALGORITHM['ram_ships_when_weak'] and not navigate_command or (closest_enemy.health <= current_ship.health and
                                                                             num_enemies_in_range <= num_friendlies_in_range):
            #standard offense, stay with 'em and shoot 'em
            if DEBUGGING['ram_ships_when_weak']:
                log.debug("   - firing on enemy, not ramming")
                
            navigate_command = current_ship.navigate(
                current_ship.closest_point_to(closest_enemy),
                game_map,
                speed = default_speed,
                ignore_ships = False)
        elif not navigate_command:
            #RAMMING SPEED!
            if DEBUGGING['ram_ships_when_weak'] and (num_enemies_in_range <= num_friendlies_in_range):
                log.debug("   - ship #" + str(closest_enemy.id) + " is stronger w/" + str(closest_enemy.health) + \
                          " health vs my " + str(current_ship.health) + " - ramming speed!")
            elif DEBUGGING['ram_ships_when_weak']:
                log.debug("   - my ship #" + str(current_ship.id) + " is outnumbered " + str(num_enemies_in_range) + ":" + \
                          str(num_friendlies_in_range) + " - ramming speed!")
                
            navigate_command = current_ship.navigate(
                closest_enemy,
                game_map,
                speed = hlt.constants.MAX_SPEED,
                avoid_obstacles = True,
                ignore_ships = True,
                ignore_planets = False)

    return navigate_command

def count_ships_in_firing_range(current_ship, entities_for_consideration, max_range):
    """
    Determine how many ships are within our offensive bubble
    :param Ship current_ship:
    :param List of Tuples entities_for_consideration:
    :param float max_range:
    :return int ships in range:
    :rtype: int
    """
    cntr = 0
    #enemies_potentially_in_range = entity_sort_by_distance(current_ship, enemies)
    for current_enemy in entities_for_consideration:
        if current_enemy['distance'] <= max_range:
            cntr += 1
        else:
            break   #don't waste the processing time
        
    return cntr

def reinforce_planet(current_ship, our_planets_by_docked, our_ranked_untapped_planets):
    """
    Create navigation command to reinforce the nearest planet with an open docking spot
    NOTE: This is currently not utilized, and almost certainly broken
    :param Ship current_ship: derp
    :param List our_planets_by_docked: List of Tuples
    :param List our_ranked_untapped_planets: List of Tuples
    :return String navigation_command:
    :rtype: String
    """
    navigation_command = None

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

    return navigation_command

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
    navigate_command = target_planet(current_ship, ranked_planets_by_distance, ranked_our_planets_by_docked, \
                                     ranked_untapped_planets)

    if not navigate_command:    
        #potential_angle = other_entities_in_vicinity(current_ship, enemies, ranked_untapped_planets[0]['distance'])
        if ALGORITHM['offense']: # and potential_angle:
            navigate_command = go_offensive(current_ship, enemies)
        elif ALGORITHM['reinforce'] and len(ranked_our_planets_by_docked) > 0:
            navigate_command = reinforce_planet(current_ship, ranked_our_planets_by_docked, ranked_untapped_planets)

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
        'ship_loop': False,
        'docking_procedures': False,
        'reinforce': False,
        'offense': True,
        'ram_planets_when_enemy_occupied': False,
        'ram_ships_when_weak': True,
        'kamikaze': False,
        'planet_selection': False,
        'targeting': False,
        'boobytrapping': False,
        'method_entry': False
}
ALGORITHM = {
        'reinforce': False,
        'offense': True,
        'ram_planets_when_enemy_occupied': False,
        'ram_ships_when_weak': True,
        'kamikaze': False,
        'boobytrapping': True
}

PRODUCTION = 6
DOCKING_TURNS = 5
MAX_FIRING_DISTANCE = 5

planets_to_avoid = []
dock_process_list = {}
undock_process_list = {}
enemy_data = {}


#my_id = game.update_map().get_me().id

#init
log = logging.getLogger(__name__)
logging.info("D4m0b0t v2.2b active")

#begin primary game loop
while True:
    if DEBUGGING['ship_loop']:
        log.debug("-+Beginning turn+-")
        
    game_map = game.update_map()
    #my_id = game_map.get_me().id
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

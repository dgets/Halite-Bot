import hlt
import logging
from operator import itemgetter

game = hlt.Game("D4m0b0t - v2a - flow restructuring")

def docked_actions(current_ship):
    """
    Determine what to do with our docked ship
    :param Ship current_ship:
    :return: command to append to the command_queue
    :rtype: List
    """
    if DEBUGGING['ship_loop']:
        log.debug("-+=Docked ship #" + str(ship_loop) + "=+-")
            
    #did we just complete docking?
    if current_ship in dock_process_list.keys():
        dock_process_list.remove(current_ship)
                
    if ALGORITHM['boobytrapping']:    #fully docked
        #is it time to bid thee farewell?
        if current_ship.planet.remaining_resources <= (current_ship.planet.num_docking_spots * DOCKING_TURNS * PRODUCTION) + 10:
            if not current_ship.planet in planets_to_avoid:
                if DEBUGGING['boobytrapping']:
                    log.debug("Leaving a present")

                planets_to_avoid.append(current_ship.planet)
                command_queue.append(ship.undock(current_ship.planet))

def undocked_actions(current_ship):
    """
    Determine what to do with the undocked ship
    :param Ship current_ship:
    :return: command to append to the command_queue
    :rtype: List
    """
    if DEBUGGING['ship_loop']:
        log.debug("-+=Undocked ship #" + str(current_ship.id) + "=+-")
                
    #did we just complete undocking?
    if current_ship in dock_process_list.keys():
        undock_process_list.remove(current_ship)
                
    #locate the 'best target' for this particular ship right nao
    if DEBUGGING['targeting']:
        log.debug("Thinking...")
                
    success = False
    ranked_planets_by_distance = entity_sort_by_distance(current_ship, game_map.all_planets())
    ranked_our_planets_by_docked = planet_sort_ours_by_docked(game_map.all_planets())
    enemies = get_enemy_ships()

    #avoid boobytraps in our considerations
    if len(planets_to_avoid) > 0:
        ranked_untapped_planets = remove_tapped_planets(ranked_planets_by_distance, planets_to_avoid)
    else:
        ranked_untapped_planets = ranked_planets_by_distance

    #do we navigate to a planet, reinforce, or go offensive?
    potential_angle = other_entities_in_vicinity(current_ship, enemies, ranked_untapped_planets[0]['distance'])
    if ALGORITHM['offense'] and potential_angle:
        #another entity is closer or at the same distance; we need to go offensive
        if DEBUGGING['offense']:
            log.debug("Engaging enemy")

        navigate_command = current_ship.navigate(
                current_ship.closest_point_to(entity_sort_by_distance(current_ship, enemies)[0]),
                game_map,
                speed = default_speed,
                ignore_ships = False)
    elif ALGORITHM['reinforce'] and len(ranked_our_planets_by_docked) > 0:
        if ranked_our_planets_by_docked[0]['number_docked'] > 0:
            #reinforce that sucker
            if DEBUGGING['reinforce']:
                log.debug("Reinforcing planet #" + str(ranked_our_planets_by_docked[0]['entity_object'].id))

            navigate_command = current_ship.navigate(
                    current.ship.closest_point_to(ranked_our_planets_by_docked[0]['entity_object']),
                    game_map,
                    speed = default_speed,
                    ignore_ships = False)
    else:
        #navigate to a planet or begin docking
        if ship.can_dock(ranked_untapped_planets[0]['entity_object']):
            if DEBUGGING['planet_selection']:
                log.debug("Selecting planet #" + str(ranked_untapped_planets[0]['entity_object'].id))
                
            dock_process_list['ship'] = ranked_untapped_planets[0]['entity_object']
            navigate_command = ship.dock(ranked_untapped_planets[0]['entity_object'])
        else:
            navigate_command = current_ship.navigate(
                    current_ship.closest_point_to(ranked_untapped_planets[0]['entity_object']),
                    game_map,
                    speed = default_speed,
                    ignore_ships = False)

    return navigate_command


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

    return sorted(nang, key=itemgetter('number_docked'))

def other_entities_in_vicinity(current_entity, other_entities, scan_distance):
    """
    Check to see if there are any more specified entities within the immediate vicinity
    :param Entity current_entity:
    :param List other_entities:
    :param integer scan_distance:
    :return: Angle between this entity and the first other found within collision risk area, or None
    :rtype: float
    """
    if DEBUGGING['method_entry']:
        log.debug("other_entities_in_vicinity")
        
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
        'reinforce': True,
        'offense': True,
        'planet_selection': True,
        'targeting': True,
        'boobytrapping': True,
        'method_entry': False
}
ALGORITHM = {
        'reinforce': True,
        'offense': True,
        'boobytrapping': True
}

PRODUCTION = 6
DOCKING_TURNS = 5

planets_to_avoid = []
dock_process_list = {}
undock_process_list = {}

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

    targeted_list = []
    command_queue = []

    for ship in game_map.get_me().all_ships():
        if ship.docking_status == ship.DockingStatus.DOCKING:
            ship.dock(dock_process_list[ship])
        elif ship.docking_status == ship.DockingStatus.UNDOCKING:
            ship.undock(dock_process_list[ship])
        elif ship.docking_status == ship.DockingStatus.DOCKED:
            if DEBUGGING['ship_loop']:
                log.debug("-+=Docked ship #" + str(ship.id) + "=+-")
            
            command_queue.append(docked_actions(ship))
        else:   #ship.DockingStatus.UNDOCKED
            if DEBUGGING['ship_loop']:
                log.debug("-+=Undocked ship #" + str(ship.id) + "=+-")

            command_queue.append(undocked_actions(ship))
    #end per-ship iteration

    game.send_command_queue(command_queue)
    



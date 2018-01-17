import hlt
import logging
from operator import itemgetter

game = hlt.Game("D4m0b0t - v1b - flow restructuring")

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

def planet_sort_by_docked(planet_list):
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
        'method_entry': True
}
ALGORITHM = {
        'reinforce': True,
        'offense': True,
        'boobytrapping': True
}

PRODUCTION = 6
DOCKING_TURNS = 5

planets_to_avoid = []

#init
log = logging.getLogger(__name__)
logging.info("D4m0b0t active")

#begin primary game loop
while True:
    game_map = game.update_map()
    my_id = game_map.get_me().id
    #default_speed = int(hlt.constants.MAX_SPEED / 2)
    #default_speed = int(hlt.constants.MAX_SPEED / 1.75)
    default_speed = hlt.constants.MAX_SPEED
    
    ship_loop = 0
    navigate_command = None
    targeted_list = []
    command_queue = []

    for ship in game_map.get_me().all_ships():
        if ship.docking_status == ship.DockingStatus.DOCKED:
            if DEBUGGING['ship_loop']:
                log.debug("Docked ship #" + str(ship_loop) + ": ")
                
            if ALGORITHM['boobytrapping'] and ship.docking_status == ship.DockingStatus.DOCKED:    #fully docked
                #is it time to bid thee farewell?
                if ship.planet.remaining_resources <= (ship.planet.num_docking_spots * DOCKING_TURNS * PRODUCTION) + 10:
                    if not ship.planet in planets_to_avoid:
                        if DEBUGGING['boobytrapping']:
                            log.debug("Leaving a present")

                        planets_to_avoid.append(ship.planet)
                        command_queue.append(ship.undock(ship.planet))
                        
            #we need to check for incoming enemies and determine what to do here if so
            continue
        elif ship.docking_status == ship.DockingStatus.UNDOCKED:
            if DEBUGGING['ship_loop']:
                log.debug("Undocked ship #" + str(ship_loop) + ": ")
                
            #locate the 'best target' for this particular ship right nao
            if DEBUGGING['targeting']:
                log.debug("Entered planet selection")
                
            success = False
            any_unowned = False
            ranked_planets = entity_sort_by_distance(ship, game_map.all_planets())
            if len(planets_to_avoid) > 0:
                ranked_untapped_planets = remove_tapped_planets(ranked_planets, planets_to_avoid)
            else:
                ranked_untapped_planets = ranked_planets
                
            for target in ranked_untapped_planets:
                if not target['entity_object'].is_owned():
                    #go for unclaimed planet
                    for target in ranked_untapped_planets:
                        if target['entity_object'] in targeted_list:
                            if DEBUGGING['targeting']:
                                log.debug(" - planet already targeted")
                                
                            continue
                        else:
                            if DEBUGGING['targeting']:
                                log.debug(" - selected target")
                                
                            #now is our potential target closer to the bad guys?
                            if other_entities_in_vicinity(target['entity_object'], get_enemy_ships(), \
                                                          target['entity_object'].calculate_distance_between(ship)):
                                success = False
                                continue

                            success = True
                            targeted_list.append(target['entity_object'])
                            break

            enemies_ranked = entity_sort_by_distance(ship, get_enemy_ships())
            #ranked_untapped_planets = remove_tapped_planets(entity_sort_by_distance(ship, game_map.all_planets()), planets_to_avoid)
            if ranked_planets[0]['distance'] <= enemies_ranked[0]['distance']:
                if ALGORITHM['reinforce']:
                    if DEBUGGING['reinforce']:
                        log.debug("Entered reinforce")
                        
                    #no unowned planets - reinforce my planets or go offensive
                    #for target in entity_sort_by_distance(ship, game_map.all_planets()):
                    for target in ranked_planets:
                        if target['entity_object'].owner == my_id and not target['entity_object'].is_full():
                            if DEBUGGING['reinforce']:
                                log.debug('Reinforcing')

                                if not other_entities_in_vicinity(target['entity_object'], player.all_ships(), \
                                                                  target['entity_object'].calculate_distance_between(ship)):
                                    success = True
                                    break
                                
                                if target['entity_object'] in game_map.all_planets() and ship.can_dock(target['entity_object']):
                                    command_queue.append(ship.dock(target['entity_object']))
                                    continue
                                else:
                                    # collision_risk_angle = other_ships_in_vicinity(ship, game_map.get_me().all_ships(), 3)
                                    navigate_command = ship.navigate(
                                        ship.closest_point_to(target['entity_object']),
                                        game_map,
                                        speed=default_speed,
                                        ignore_ships=False)
            else:
                if ALGORITHM['offense']:
                    if DEBUGGING['offense']:
                        log.debug("Entered offense")
                        
                    if not success:
                        #find an enemy to attack
                        if DEBUGGING['targeting']:
                            log.debug('Targeting')
                    
                            target = entity_sort_by_distance(ship, get_enemy_ships())[0]
                            success = True

            if not success:
                #haven't found anything with the simple targeting criteria; what's next?
                if len(targeted_list) > 0:
                    target = entity_sort_by_distance(ship, targeted_list)[0]
            
            if target['entity_object'] in game_map.all_planets() and ship.can_dock(target['entity_object']):
                if DEBUGGING['targeting']:
                    log.debug("Fallback docking")
                    
                #command_queue.append(ship.dock(target['entity_object']))
                navigate_command = ship.dock(target['entity_object'])
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

    ship_loop += 1
    game.send_command_queue(command_queue)

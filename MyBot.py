import hlt
import logging

logging.info("D4m0b0t running")

while True:
    game_map = game.update_map()
    command_queue = []

    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue
        else:
            #locate what we're going to call the best target for this particular ship right nao
            best_targets = planet_sort_by_distance(ship, game_map.all_planets())

            target = find_first_unowned(best_targets)   #later we'll check to see if anybody else is closer and more likely to be
                                                        #snatching this out from under us, but this is good for now

            if target == None:
                #not sure what the fuck to do here yet
                continue
            
            #maybe checking if anybody is closer is a better idea here; not sure, sedatives are kicking in
            #for now let's just make a b-line for it
            if ship.can_dock(target):
                command_queue.append(ship.dock(target))
            else:
                navigate_command = ship.navigate(
                        ship.closest_point_to(target),
                        game_map,
                        speed = int(hlt.constants.MAX_SPEED / 2),   #we'll improve this after determining whether or not others are
                                                                    #going for it
                        ignore_ships = True)                        #this will be smartened, also

            if navigate_command:
                command_queue.append(navigate_command)


    
def planet_sort_by_docked(planet_list):
    """
    Sort the given solar system into planets weighted by least ships docked
    :param array planet_list: List of planets to be weighted
    :return: Array of weighted planets
    :rtype: Array
    """

    #bubble sort, for now
    for iteration in (0, len(planet_list) - 1):
        cntr = 0
        for current_planet in planet_list:
            #swap
            if len(current_planet.all_docked_ships) > len(planet_list[cntr1 + 1].all_docked_ships):
                planet_list[cntr1] = planet_list[cntr1 + 1]
                planet_list[cntr1 + 1] = current_planet

            cntr++

    return planet_list

def planet_sort_by_distance(current_ship, planet_list):
    """
    Sort the given solar system into planets weighted by least distance from given ship to planet
    :param Ship current_ship:
    :param array planet_list:
    :return: Array of planets rated by distance from current_ship
    :rtype: Array
    """

    #bubble sort, again, for now
    for iteration in (0, len(planet_list) - 1):
        cntr = 0
        for current_planet in planet_list:
            if planet_list[cntr1].calculate_distance_between(current_ship) > \
                    planet_list[cntr1 + 1].calculate_distance_between(current_ship):
                planet_list[cntr1] = planet_list[cntr1 + 1]
                planet_list[cntr1 + 1] = current_planet
                
            cntr++

    return planet_list

def find_first_unowned(planet_list):
    """
    Check through the list of planets and return the first one that is not owned (or None)
    :param array planet_list:
    :return: Unowned planet
    :rtype: Planet
    """

    for target in planet_list:
        if target.is_owned():
            continue

        return target



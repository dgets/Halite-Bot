import hlt
import logging

logging.info("D4m0b0t running")

game = hlt.Game("D4m0b0t")

debugging = True

def planet_sort_by_distance(current_ship, planet_list):
    """
    Sort the given solar system into planets weighted by least distance from given ship to planet
    :param Ship current_ship:
    :param array planet_list:
    :return: Array of planets rated by distance from current_ship
    :rtype: Array
    """

    if debugging:
        logging.info("-=- planet_sort_by_distance -=-")

    #bubble sort, again, for now
    cntr = 0
    for iteration in (1, len(planet_list)):
        for current_planet in planet_list:
            if debugging:
                logging.info("planet: " + str(cntr))

            if planet_list[cntr].calculate_distance_between(current_ship) < \
                    planet_list[cntr - 1].calculate_distance_between(current_ship):
                planet_list[cntr] = planet_list[cntr - 1]
                planet_list[cntr - 1] = current_planet
                
        cntr += 1

    return planet_list
    
def planet_sort_by_docked(planet_list):
    """
    Sort the given solar system into planets weighted by least ships docked
    :param array planet_list: List of planets to be weighted
    :return: Array of weighted planets
    :rtype: Array
    """

    #bubble sort, for now
    cntr = 0
    for iteration in (0, len(planet_list) - 2):
        for current_planet in planet_list:
            #swap
            if len(current_planet.all_docked_ships) > len(planet_list[cntr + 1].all_docked_ships):
                planet_list[cntr] = planet_list[cntr + 1]
                planet_list[cntr + 1] = current_planet

        cntr += 1

    return planet_list

def find_first_unowned(planet_list, already_targetted):
    """
    Check through the list of planets and return the first one that is not owned (or None)
    :param array planet_list:
    :param array already_targetted:
    :return: Unowned planet
    :rtype: Planet
    """

    for target in planet_list:
        if target.is_owned():
            if target not in already_targetted:
                continue

        if target:
            return target
        else:
            return planet_list[0]

def other_ships_in_vicinity(current_ship, other_ships, risk_distance):
    """
    Check to see if there are any more of my ships within the immediate vicinity
    :param Ship current_ship:
    :param array other_ships:
    :param integer risk_distance:
    :return: Angle between this ship and the first other ship found within collision risk area
    :rtype: float
    """

    for other_ship in other_ships:
        if current_ship.calculate_distance_between(other_ship) < risk_distance:
            return current_ship.calculate_distance_between(other_ship)

    return None

#begin primary game loop
while True:
    game_map = game.update_map()
    targetted_list = []
    command_queue = []
    best_targets = []
    default_speed = int(hlt.constants.MAX_SPEED / 2)

    if debugging:
        logging.info("-=- Entered primary loop -=-")

    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue
        else:
            #locate what we're going to call the best target for this particular ship right nao
            best_targets = planet_sort_by_distance(ship, game_map.all_planets())

            #if len(targetted_list) > 0 and len(best_targets) > 0:
            #    for temp_target in targetted_list:
            #        best_targets.remove(temp_target)

            target = find_first_unowned(best_targets, targetted_list)
                                                        #later we'll check to see if anybody else is closer and more likely to be
                                                        #snatching this out from under us, but this is good for now
            #targetted_list.append(target)

            if target == None:
            #    destroy the closest enemy ship
                continue
            
            #maybe checking if anybody is closer is a better idea here; not sure, sedatives are kicking in
            #for now let's just make a b-line for it
            if ship.can_dock(target):
                command_queue.append(ship.dock(target))
                continue
            else:
                #collision_risk_angle = other_ships_in_vicinity(ship, game_map.get_me().all_ships(), 3)

                #if not collision_risk_angle:
                    navigate_command = ship.navigate(
                            ship.closest_point_to(target),
                            game_map,
                            speed = default_speed,
                            ignore_ships = True)
                #else:
                #    thrust_angle = collision_risk_angle + 180
                #    if thrust_angle > 360:
                #        thrust_angle -= 360

                #    navigate_command = ship.thrust(
                #            default_speed,
                #            thrust_angle)
                        

            if navigate_command:
                command_queue.append(navigate_command)
        #end for undocked ship
    #end this ship's processing

    game.send_command_queue(command_queue)


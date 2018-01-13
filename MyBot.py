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

        cntr = 0

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

def find_first_unowned(planet_list, already_targetted, ship_id):
    """
    Check through the list of planets and return the first one that is not owned (or None), and not already targetted by another
    ship in our fleet
    :param array planet_list:
    :param array of arrays/hashes already_targetted:
    :param integer ship_id:
    :return: Unowned planet
    :rtype: Planet
    """

    taken = False

    for target in planet_list:  #each potential target planet
        if not target.is_owned():   #if it isn't already occupied
            for targetted_by in already_targetted:  #loop through already targetted list
                if ship_id == targetted_by[1]:  #is this really necessary?
                    return target
                else:
                    taken = True
            #end targetted loop
        #end not already occupied loop
        if not taken:
            return target
        else:
            taken = False
    #no more potential target planets

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
            return current_ship.calculate_angle_between(other_ship)

    return 0

targetted_list = []
#begin primary game loop
while True:
    game_map = game.update_map()
    #targetted_list = []
    command_queue = []
    best_targets = []
    default_speed = int(hlt.constants.MAX_SPEED / 2)

    if debugging:
        logging.info("-=- Entered primary loop -=-")

    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue
        else:
            my_id = ship.id

            #locate what we're going to call the best target for this particular ship right nao
            best_targets = planet_sort_by_distance(ship, game_map.all_planets())

            if len(targetted_list) > 0 and len(best_targets) > 0:
                for temp_target in targetted_list:
                    if temp_target[0] in best_targets:
                        best_targets.remove(temp_target[0])
            
            target = find_first_unowned(best_targets, targetted_list, my_id)
                                                        #later we'll check to see if anybody else is closer and more likely to be
                                                        #snatching this out from under us, but this is good for now
            if target not in targetted_list:
                targetted_list.append([target, my_id])

            if target == None:
            #    destroy the closest enemy ship
                continue
            
            #maybe checking if anybody is closer is a better idea here; not sure, sedatives are kicking in
            #for now let's just make a b-line for it
            if ship.can_dock(target):
                command_queue.append(ship.dock(target))
                continue
            else:
                collision_risk_angle = other_ships_in_vicinity(ship, game_map.get_me().all_ships(), 3)

                if collision_risk_angle == 0:
                    navigate_command = ship.navigate(
                            ship.closest_point_to(target),
                            game_map,
                            speed = default_speed,
                            ignore_ships = False)
                else:
                    #this is not taking into account any other ships in the vicinity yet
                    previous_angle = ship.calculate_angle_between(ship.closest_point_to(target))
                    if previous_angle >= collision_risk_angle:
                        thrust_angle = previous_angle + 45
                    else:
                        thrust_angle = previous_angle - 45

                    if thrust_angle > 360:
                        thrust_angle -= 360
                    elif thrust_angle <= 0:
                        thrust_angle += 360

                    navigate_command = ship.thrust(
                            default_speed,
                            thrust_angle)
                        

            if navigate_command:
                command_queue.append(navigate_command)
        #end for undocked ship
    #end this ship's processing

    game.send_command_queue(command_queue)


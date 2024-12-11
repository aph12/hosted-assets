#Andrew Herrera
#CS5001
#Final Project RLBot
#12/9/2024
#This is the primary file for my RLBot. It contains two classes, Brain and Mybot.
#Brain contains the sequence of actions the bot should carry out. 
#These specific actions are called within the MyBot class and depending on which action, MyBot carries these actions out.
#Overall, this file combines commands with specific movements to identify what the bot should be doing.
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from util.boost_pad_tracker import BoostPadTracker
from util.drive import steer_toward_target
from util.vec import Vec3

class Brain:
    def decide_action(self, boost_amount, at_goal_position, aligned_with_ball):
        #Make decisions based on current conditions
        if boost_amount < 50:
            return "get_boost"
        #Moved up, if aligned, commit to the shot
        elif aligned_with_ball:
            return "hit_ball"
        elif not at_goal_position:
            return "go_to_goal"
        else:
            return "face_ball"

class MyBot(BaseAgent):
    '''
    NOT MY CODE
    In general, initializes the bot with required components and trackers
    Params:
    Name - The name of the bot in game
    Team - Which team: 0 for blue, 1 for orange
    Index - Bot's player index in the game
    '''
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        #Create tracker for boost pads on the field
        self.boost_pad_tracker = BoostPadTracker()
        #My code: Create an instance of Brain to tell bot what to do
        self.brain = Brain()
    '''
    NOT MY CODE
    Set up information about the boost pads now that the game is active with available info.
    Params: None
    '''
    def initialize_agent(self):
        self.boost_pad_tracker.initialize_boosts(self.get_field_info())

    """
    LINE 52 - 64 NOT MY CODE
    This is the main bot logic that runs every game tick
    This function will be called by the framework many times per second. This is where you can
    see the motion of the ball, etc. and return controls to drive your car.
    PARAMS:
    Packet - Game data from RLBot containing all current game information
    Returns:
    SimpleControllerState - Contains the bot's control inputs for this tick.
    """
    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
      

        # Keep our boost pad info updated with which pads are currently active
        self.boost_pad_tracker.update_boost_status(packet)
        '''
        Not my code but collects information about the car and ball.
        '''
        # Gather some information about our car and the ball
        my_car = packet.game_cars[self.index]
        car_location = Vec3(my_car.physics.location)
        ball_location = Vec3(packet.game_ball.physics.location)

        #Find closest goal
        goal_center = self.nearest_goal_center(car_location)
        #Check if we're close enough to goal position
        at_goal_position = self.at_target(car_location, goal_center)
        #Check if we're facing the right direction to hit the ball
        aligned_with_ball = self.is_aligned(my_car, ball_location)

        #Helpful logging information for debugging sake.
        self.logger.info("Car Location: " + str(car_location))
        self.logger.info("Ball location: " + str(ball_location))
        self.logger.info("Boost amount: " + str(my_car.boost))
        self.logger.info("Got boost: " + str(my_car.boost) + 
                        ", At goal: " + str(at_goal_position) + 
                        ", Ready to hit: " + str(aligned_with_ball))

        #Get the next action from our little brain
        next_action = self.brain.decide_action(my_car.boost, at_goal_position, aligned_with_ball)

        #Actions to be executed based on our brains decision
        if next_action == "get_boost":
            #Find the location of the nearest corner boost pad
            nearest_boost = self.find_Corner(car_location)
            #Log that were going for boost
            self.logger.info("Going for boost pad: " + str(nearest_boost))
            #Return controls to drive to the boost pad
            return self.drive_to(my_car, nearest_boost)
        
        #If we need to get to goal, execute the goal positioning behavior
        elif next_action == "go_to_goal":
            #Find the center of the nearest goal
            goal_center = self.nearest_goal_center(car_location)
            #Log that were going for goal
            self.logger.info("Going to goal center: " + str(goal_center))
            #Drive to target (goal center)
            return self.drive_to(my_car, goal_center)

        #If we need to face the ball, execute the ball facing behavior
        elif next_action == "face_ball":
            #Log that we're trying to face the ball
            self.logger.info("Facing ball")
            #Create new controls object for turning
            controls = SimpleControllerState()
            #Set the steering to turn toward the ball
            controls.steer = steer_toward_target(my_car, ball_location)
            controls.throttle = 0.0
            #Return the controls
            return controls
        #If we're ready to hit, execute ball charge behavior
        else:
            #Log we are charging
            self.logger.info("Charging ball")
            #Return controls to charge at the ball
            return self.charge(my_car, ball_location)
    '''
    HELPER METHODS
    '''
    #Find corner finds the nearest corner boost pad in proximity to the car's location.
    #Params:
    #Car_location - The car's location, where it is in on the field
    def find_Corner(self, car_location):
        '''
        Returns the nearest corner boost pad location
        '''
        corner_boosts = [
            Vec3(-4096, 4096, 0), #Top-Left corner boost
            Vec3(4096, 4096, 0), #Top-right corner boost
            Vec3(-4096, -4096, 0), #Bottom-left corner boost
            Vec3(4096, -4096, 0), #Bottom-right corner boost
        ]
        #Initialize variables to store nearest boost pad
        nearest_boost = None
        nearest_distance = 10000

        #Iterate through corner_boosts to find closest
        for boost in corner_boosts:
            distance = car_location.dist(boost)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_boost = boost
        return nearest_boost

    #Drive to is a method that tells the car to drive to the nearest target.
    #Params: 
    #Car_location - The car's location, where it is in on the field
    #Target - The target location of where the bot must go
    def drive_to(self, my_car, target):
        '''
        Returns the controls to drive the car towards the target
        '''
        #Create a new controls object for driving
        controls = SimpleControllerState()
        #Drive towards the target
        controls.steer = steer_toward_target(my_car, target)
        #Set full speed to drive towards target
        controls.throttle = 1.0
        #Return calculated controls
        return controls

    #At target is a method that checks if the car is close to a specific location.
    #Params:
    #Current_location - The car's location, where it is in on the field currently.
    #Target_location - The target location of where the bot should be at.
    def at_target(self, current_location, target_location):
        '''
        Returns: boolean - whether the car is at the target location or not
        '''
        #Ensures car is within 500 units of the target location
        return current_location.dist(target_location) <= 500
    
    #Nearest goal line is a method that identifies the closest goal line to the bot
    #Params:
    #Car_location - The car's location on the field
    def nearest_goal_center(self, car_location):
        '''
        Returns: the nearest goal line (2 goals, blue team, orange team)
        '''
        if car_location.y < 0:
            #Center of blue goal line
            return Vec3(0, -5120, 0)
        else:
            #Center of orange goal line
            return Vec3(0, 5120, 0)

    #Is aligned is a method that checks the bots position in relation to the ball location.
    #Params:
    #My_car: The complete car object with physics data
    #Ball_location: Location of the ball
    def is_aligned(self, my_car, ball_location):
        '''
        Returns: boolean - if car is facing ball or not
        '''
        #Check if we're facing the ball
        facing_ball = abs(steer_toward_target(my_car, ball_location)) < 0.2
        #Log alignment for debugging
        self.logger.info("Facing ball: " + str(facing_ball))
        return facing_ball

    #Charge is a method where the bot will be told to boost at the ball
    #Params:
    #My_car - The complete car object with physics data
    #Ball_location - Where the ball is on the field
    def charge(self, my_car, ball_location):
        '''
        Returns the controls to steer toward the ball
        '''
        #Create a new simplecontrollerstate object to store the car's control inputs
        controls = SimpleControllerState()
        #Get the car's current location
        car_location = Vec3(my_car.physics.location)
        #Calculate the distance between car and balls location
        distance_to_ball = car_location.dist(ball_location)
        #Full throttle to approach ball
        controls.throttle = 1.0
        #When lined up with the ball, boost
        controls.boost = distance_to_ball < 1500
        #Steer towards the ball
        controls.steer = steer_toward_target(my_car, ball_location)
        self.logger.info("Distance to ball: " + str(distance_to_ball) + "Boosting: " + str(controls.boost))
        return controls
    #Test bot decisions is a method that allows interaction with my bot and its decisions depending on the input
    def test_bot_decisions():
        print("Bot Decision Tester")
        #Create an instance of Brain class
        brain = Brain()
        #Continuous loop for testing
        while True:
            #Prompt user for input
            print("Enter Values to test:")
            #Check if user wants to quit
            try:
                #Get boost amount from user
                boost = float(input("Boost amount: "))
                #Yes no input for goal position
                at_goal = input("At goal? (y/n): ").lower()
                #Yes no input for ball alignment
                aligned = input("Aligned with ball? (y/n): ").lower()
                #Pass values to brain and get decision
                decision = brain.decide_action(boost, at_goal, aligned)
                #Print decision
                print("Bot will: " + str(decision))
            #Handle errors
            except ValueError:
                print("Please enter a number for boost")

    if __name__ == "__main__":
        test_bot_decisions()
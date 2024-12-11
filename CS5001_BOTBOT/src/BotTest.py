#Andrew Herrera
#CS5001
#Final Project RLBot
#12/9/2024
#This is the test file for various methods created within bot.py.
#Methods like drive_to, is_aligned, charge, rely heavily on physics and I am unsure on how to test them.
import unittest
from util.vec import Vec3
from bot import MyBot
from bot import Brain

class TestHelpers(unittest.TestCase):
    
    def setUp(self):
        '''
        Create bot instance to call before each test
        '''
        self.bot = MyBot("TestBot", 0, 0)

    def test_decisions(self):
        '''
        Test Brain's decision making
        '''
        brain = Brain()
        #Test getting boost when low (<50)
        self.assertEqual(brain.decide_action(45, True, True), "get_boost")
        #Test hitting ball when aligned (and enough boost)
        self.assertEqual(brain.decide_action(100, False, True), "hit_ball")
        #Test going to goal when out of position (and enough boost but not aligned)
        self.assertEqual(brain.decide_action(100, False, False), "go_to_goal")
        #Test facing ball when in position but not aligned
        self.assertEqual(brain.decide_action(100, True, False), "face_ball")

    def test_find_corner(self):
        '''
        Test finding nearest corner boost pad
        '''
        #Test from center field
        pos1 = Vec3(0, 0, 0)
        #switching to assertalmostequal because passing a vector does not work!
        nearest1 = self.bot.find_Corner(pos1)
        self.assertAlmostEqual(nearest1.x, -4096)

        #Test from near top-left corner
        pos2 = Vec3(-4000, 4000, 0)
        nearest2 = self.bot.find_Corner(pos2)
        #-4096, 4096, 0 is top left boost
        self.assertAlmostEqual(nearest2.x, -4096)
        self.assertAlmostEqual(nearest2.y, 4096)

    def test_at_target(self):
        '''
        Test if bot recognizes when it's at the target
        '''
        #Test when near target
        pos = Vec3(0, 0, 0)
        #Within 500 units
        target1 = Vec3(100, 100, 0)
        self.assertTrue(self.bot.at_target(pos, target1))

        #Test when far from target (>500 units)
        target2 = Vec3(1000, 1000, 0)
        self.assertFalse(self.bot.at_target(pos, target2))

    def test_nearest_goal(self):
        '''
        Test finding nearest goal
        '''
        #Test from blue half
        pos1 = Vec3(0, -2000, 0)
        blue_goal = self.bot.nearest_goal_center(pos1)
        #Test with almostequal because Vec3(0, -5120, 0) does not work!
        #Blue goal.y = -5120 
        #.y because length of field (end to end)
        self.assertAlmostEqual(blue_goal.y, -5120)

        #Test from orange half
        #Orange goal.y = 5120
        pos2 = Vec3(0, 2000, 0)
        orange_goal = self.bot.nearest_goal_center(pos2)
        self.assertEqual(orange_goal.y, 5120)

if __name__ == "__main__":
    unittest.main()
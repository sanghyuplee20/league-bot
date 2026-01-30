import random
from typing import List, Tuple, Dict

class TeamGenerator:
    
    @staticmethod
    def random_teams(players: List[int]) -> Tuple[List[int], List[int]]:
        """Completely random team generation"""
        if len(players) != 10:
            raise ValueError("Need exactly 10 players")
        
        shuffled = players.copy()
        random.shuffle(shuffled)
        
        team1 = shuffled[:5]
        team2 = shuffled[5:]
        
        return team1, team2
    
    @staticmethod
    def role_based_teams(role_assignments: Dict[str, List[int]]) -> Tuple[List[int], List[int]]:
        """
        Generate teams based on role assignments
        role_assignments: {
            'top': [player1_id, player2_id],
            'jungle': [player3_id, player4_id],
            'mid': [player5_id, player6_id],
            'adc': [player7_id, player8_id],
            'support': [player9_id, player10_id]
        }
        """
        roles = ['top', 'jungle', 'mid', 'adc', 'support']
        
        # Validate input
        for role in roles:
            if role not in role_assignments or len(role_assignments[role]) != 2:
                raise ValueError(f"Need exactly 2 players for {role}")
        
        team1 = []
        team2 = []
        
        # For each role, randomly assign one player to each team
        for role in roles:
            players = role_assignments[role].copy()
            random.shuffle(players)
            team1.append(players[0])
            team2.append(players[1])
        
        return team1, team2
    
    @staticmethod
    def rock_paper_scissors() -> int:
        """Simulate rock paper scissors, returns 1 or 2 for winner"""
        return random.randint(1, 2)
    
    @staticmethod
    def captain_draft_order(total_picks: int, first_captain: int) -> List[int]:
        """
        Generate snake draft order
        first_captain: 1 or 2
        Returns list of captain numbers in pick order
        Example for 10 picks: [1, 2, 2, 1, 1, 2, 2, 1, 1, 2]
        """
        order = []
        current_captain = first_captain
        other_captain = 2 if first_captain == 1 else 1
        
        # Snake draft pattern
        for round_num in range(total_picks // 2):
            if round_num == 0:
                # First round: 1 pick each
                order.append(current_captain)
                order.append(other_captain)
            else:
                # Subsequent rounds: 2 picks each, alternating
                if round_num % 2 == 1:
                    order.extend([other_captain, other_captain])
                    order.extend([current_captain, current_captain])
                else:
                    order.extend([current_captain, current_captain])
                    order.extend([other_captain, other_captain])
        
        return order[:total_picks]

# Example usage functions
def example_random():
    players = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    team1, team2 = TeamGenerator.random_teams(players)
    print(f"Team 1: {team1}")
    print(f"Team 2: {team2}")

def example_role_based():
    roles = {
        'top': [1, 2],
        'jungle': [3, 4],
        'mid': [5, 6],
        'adc': [7, 8],
        'support': [9, 10]
    }
    team1, team2 = TeamGenerator.role_based_teams(roles)
    print(f"Team 1: {team1}")
    print(f"Team 2: {team2}")

def example_draft_order():
    # Captain 1 wins RPS
    winner = TeamGenerator.rock_paper_scissors()
    print(f"Captain {winner} won RPS and picks first!")
    
    order = TeamGenerator.captain_draft_order(8, winner)  # 8 picks (2 captains already chosen)
    print(f"Draft order: {order}")
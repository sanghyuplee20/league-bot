from supabase import create_client, Client
import os
from typing import List, Dict, Optional
from datetime import datetime

class SupabaseDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(url, key)
    
    # ============ USER OPERATIONS ============
    
    async def get_or_create_user(self, discord_id: int, username: str) -> Dict:
        """Get user or create if doesn't exist"""
        # Check if user exists
        result = self.client.table('users').select('*').eq('discord_id', discord_id).execute()
        
        if result.data:
            return result.data[0]
        
        # Create new user
        new_user = {
            'discord_id': discord_id,
            'username': username,
            'total_games': 0,
            'total_wins': 0
        }
        result = self.client.table('users').insert(new_user).execute()
        return result.data[0]
    
    async def get_user_stats(self, discord_id: int) -> Optional[Dict]:
        """Get user statistics"""
        result = self.client.table('users').select('*').eq('discord_id', discord_id).execute()
        return result.data[0] if result.data else None
    
    async def update_user_stats(self, discord_id: int, won: bool):
        """Update user win/loss stats"""
        user = await self.get_user_stats(discord_id)
        if not user:
            return
        
        new_games = user['total_games'] + 1
        new_wins = user['total_wins'] + (1 if won else 0)
        
        self.client.table('users').update({
            'total_games': new_games,
            'total_wins': new_wins
        }).eq('discord_id', discord_id).execute()
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by win rate"""
        result = self.client.table('users').select('*').gt('total_games', 0).execute()
        
        # Calculate win rates and sort
        users = result.data
        for user in users:
            user['win_rate'] = (user['total_wins'] / user['total_games']) * 100 if user['total_games'] > 0 else 0
        
        users.sort(key=lambda x: (x['win_rate'], x['total_wins']), reverse=True)
        return users[:limit]
    
    # ============ MATCH OPERATIONS ============
    
    async def create_match(self, series_type: str, team1_players: List[int], team2_players: List[int]) -> Dict:
        """Create a new match series"""
        match_data = {
            'series_type': series_type,
            'status': 'ongoing',
            'team1_name': f'Team 1',
            'team2_name': f'Team 2'
        }
        
        result = self.client.table('matches').insert(match_data).execute()
        match = result.data[0]
        
        # Create player_match_stats entries
        for player_id in team1_players:
            self.client.table('player_match_stats').insert({
                'discord_id': player_id,
                'match_id': match['match_id'],
                'team_number': 1
            }).execute()
        
        for player_id in team2_players:
            self.client.table('player_match_stats').insert({
                'discord_id': player_id,
                'match_id': match['match_id'],
                'team_number': 2
            }).execute()
        
        return match
    
    async def record_game(self, match_id: str, game_number: int, team1_players: List[int], 
                         team2_players: List[int], winner: int) -> Dict:
        """Record a single game in a series"""
        game_data = {
            'match_id': match_id,
            'game_number': game_number,
            'team1_players': team1_players,
            'team2_players': team2_players,
            'winner': winner
        }
        
        result = self.client.table('games').insert(game_data).execute()
        return result.data[0]
    
    async def get_match(self, match_id: str) -> Optional[Dict]:
        """Get match details"""
        result = self.client.table('matches').select('*').eq('match_id', match_id).execute()
        return result.data[0] if result.data else None
    
    async def get_match_games(self, match_id: str) -> List[Dict]:
        """Get all games in a match"""
        result = self.client.table('games').select('*').eq('match_id', match_id).order('game_number').execute()
        return result.data
    
    async def get_match_players(self, match_id: str) -> Dict[int, List[int]]:
        """Get players grouped by team for a match"""
        result = self.client.table('player_match_stats').select('*').eq('match_id', match_id).execute()
        
        teams = {1: [], 2: []}
        for stat in result.data:
            teams[stat['team_number']].append(stat['discord_id'])
        
        return teams
    
    async def complete_match(self, match_id: str, winner_team: int):
        """Mark match as completed and update player stats"""
        # Update match status
        self.client.table('matches').update({
            'status': 'completed',
            'winner_team': winner_team,
            'completed_at': datetime.now().isoformat()
        }).eq('match_id', match_id).execute()
        
        # Get all players in the match
        result = self.client.table('player_match_stats').select('*').eq('match_id', match_id).execute()
        
        # Update each player's stats
        for stat in result.data:
            won = stat['team_number'] == winner_team
            
            # Update player_match_stats result
            self.client.table('player_match_stats').update({
                'result': 'win' if won else 'loss'
            }).eq('id', stat['id']).execute()
            
            # Update user stats
            await self.update_user_stats(stat['discord_id'], won)
    
    async def get_recent_matches(self, limit: int = 10) -> List[Dict]:
        """Get recent matches"""
        result = self.client.table('matches').select('*').order('created_at', desc=True).limit(limit).execute()
        return result.data
    
    async def get_user_match_history(self, discord_id: int, limit: int = 10) -> List[Dict]:
        """Get match history for a specific user"""
        # Get matches user participated in
        stats_result = self.client.table('player_match_stats').select('match_id, team_number, result').eq('discord_id', discord_id).execute()
        
        if not stats_result.data:
            return []
        
        match_ids = [stat['match_id'] for stat in stats_result.data]
        
        # Get match details
        matches_result = self.client.table('matches').select('*').in_('match_id', match_ids).order('created_at', desc=True).limit(limit).execute()
        
        # Add user's team and result to each match
        matches = matches_result.data
        for match in matches:
            user_stat = next((s for s in stats_result.data if s['match_id'] == match['match_id']), None)
            if user_stat:
                match['user_team'] = user_stat['team_number']
                match['user_result'] = user_stat['result']
        
        return matches

# Global instance
db = SupabaseDB()
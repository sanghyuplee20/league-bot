import discord
from discord import app_commands
from discord.ext import commands
from database.supabase_client import db
from typing import List

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="match_create", description="Create a new BO3 or BO5 series")
    @app_commands.describe(
        series_type="Type of series (BO3 or BO5)",
        team1="Mention all Team 1 players (space separated)",
        team2="Mention all Team 2 players (space separated)"
    )
    async def match_create(self, interaction: discord.Interaction, series_type: str, 
                          team1: str, team2: str):
        """Create a new match series"""
        # Validate series type
        series_type = series_type.upper()
        if series_type not in ['BO3', 'BO5']:
            await interaction.response.send_message("❌ Series type must be BO3 or BO5", ephemeral=True)
            return
        
        # Parse mentions
        team1_ids = [int(u.id) for u in interaction.message.mentions[:5]] if interaction.message else []
        team2_ids = [int(u.id) for u in interaction.message.mentions[5:]] if interaction.message else []
        
        # For slash commands, we need to parse differently
        if not team1_ids or not team2_ids:
            await interaction.response.send_message(
                "⚠️ Please mention players using @username format.\n"
                "Example: `/match_create BO3 @player1 @player2 @player3 @player4 @player5 @player6 @player7 @player8 @player9 @player10`",
                ephemeral=True
            )
            return
        
        if len(team1_ids) != 5 or len(team2_ids) != 5:
            await interaction.response.send_message("❌ Each team must have exactly 5 players!", ephemeral=True)
            return
        
        # Create users if they don't exist
        for member in interaction.guild.members:
            if member.id in team1_ids + team2_ids:
                await db.get_or_create_user(member.id, member.name)
        
        # Create match
        match = await db.create_match(series_type, team1_ids, team2_ids)
        
        embed = discord.Embed(
            title=f"🎮 New {series_type} Match Created!",
            description=f"Match ID: `{match['match_id']}`",
            color=discord.Color.green()
        )
        
        team1_mentions = [f"<@{uid}>" for uid in team1_ids]
        team2_mentions = [f"<@{uid}>" for uid in team2_ids]
        
        embed.add_field(name="🔵 Team 1", value="\n".join(team1_mentions), inline=True)
        embed.add_field(name="🔴 Team 2", value="\n".join(team2_mentions), inline=True)
        embed.add_field(name="Status", value="⏳ Ongoing", inline=False)
        embed.set_footer(text="Use /match_record to record game results!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="match_record", description="Record a game result in a series")
    @app_commands.describe(
        match_id="The match ID",
        game_number="Game number (1, 2, 3, etc.)",
        winner="Winning team (1 or 2)"
    )
    async def match_record(self, interaction: discord.Interaction, match_id: str, 
                          game_number: int, winner: int):
        """Record a game result"""
        if winner not in [1, 2]:
            await interaction.response.send_message("❌ Winner must be 1 or 2", ephemeral=True)
            return
        
        # Get match
        match = await db.get_match(match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found!", ephemeral=True)
            return
        
        if match['status'] == 'completed':
            await interaction.response.send_message("❌ This match is already completed!", ephemeral=True)
            return
        
        # Get players
        teams = await db.get_match_players(match_id)
        
        # Record game
        await db.record_game(match_id, game_number, teams[1], teams[2], winner)
        
        # Check if series is complete
        games = await db.get_match_games(match_id)
        team1_wins = sum(1 for g in games if g['winner'] == 1)
        team2_wins = sum(1 for g in games if g['winner'] == 2)
        
        series_type = match['series_type']
        games_to_win = 2 if series_type == 'BO3' else 3
        
        embed = discord.Embed(
            title=f"📊 Game {game_number} Recorded",
            description=f"Match ID: `{match_id}`",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Winner", value=f"🎉 Team {winner}", inline=False)
        embed.add_field(name="🔵 Team 1 Score", value=f"{team1_wins} wins", inline=True)
        embed.add_field(name="🔴 Team 2 Score", value=f"{team2_wins} wins", inline=True)
        
        # Check if match is complete
        if team1_wins >= games_to_win or team2_wins >= games_to_win:
            winner_team = 1 if team1_wins > team2_wins else 2
            await db.complete_match(match_id, winner_team)
            
            embed.color = discord.Color.gold()
            embed.title = f"🏆 {series_type} Complete!"
            embed.add_field(name="Match Winner", value=f"👑 Team {winner_team}", inline=False)
            embed.set_footer(text="All player stats have been updated!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="match_status", description="Check the status of a match")
    @app_commands.describe(match_id="The match ID")
    async def match_status(self, interaction: discord.Interaction, match_id: str):
        """Check match status"""
        match = await db.get_match(match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found!", ephemeral=True)
            return
        
        games = await db.get_match_games(match_id)
        teams = await db.get_match_players(match_id)
        
        team1_wins = sum(1 for g in games if g['winner'] == 1)
        team2_wins = sum(1 for g in games if g['winner'] == 2)
        
        embed = discord.Embed(
            title=f"📋 Match Status - {match['series_type']}",
            description=f"Match ID: `{match_id}`",
            color=discord.Color.blue() if match['status'] == 'ongoing' else discord.Color.gold()
        )
        
        team1_mentions = [f"<@{uid}>" for uid in teams[1]]
        team2_mentions = [f"<@{uid}>" for uid in teams[2]]
        
        embed.add_field(name="🔵 Team 1", value="\n".join(team1_mentions), inline=True)
        embed.add_field(name="🔴 Team 2", value="\n".join(team2_mentions), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Score", value=f"🔵 {team1_wins} - {team2_wins} 🔴", inline=False)
        
        if games:
            game_results = "\n".join([
                f"Game {g['game_number']}: Team {g['winner']} won"
                for g in games
            ])
            embed.add_field(name="Game Results", value=game_results, inline=False)
        
        status_emoji = "✅" if match['status'] == 'completed' else "⏳"
        embed.add_field(name="Status", value=f"{status_emoji} {match['status'].title()}", inline=False)
        
        if match['status'] == 'completed':
            embed.add_field(name="Winner", value=f"👑 Team {match['winner_team']}", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="match_history", description="View recent matches")
    @app_commands.describe(limit="Number of matches to show (default: 5)")
    async def match_history(self, interaction: discord.Interaction, limit: int = 5):
        """View recent match history"""
        if limit > 20:
            limit = 20
        
        matches = await db.get_recent_matches(limit)
        
        if not matches:
            await interaction.response.send_message("No matches found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📜 Recent Match History",
            color=discord.Color.purple()
        )
        
        for match in matches:
            status = "✅ Complete" if match['status'] == 'completed' else "⏳ Ongoing"
            winner_text = f" - Winner: Team {match['winner_team']}" if match.get('winner_team') else ""
            
            embed.add_field(
                name=f"{match['series_type']} - {status}",
                value=f"ID: `{match['match_id']}`{winner_text}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="match_add_past", description="Add a past/completed match to the system")
    @app_commands.describe(
        series_type="Type of series (BO3 or BO5)",
        winner_team="Which team won (1 or 2)",
        team1_score="Team 1 final score (games won)",
        team2_score="Team 2 final score (games won)",
        team1="Mention all Team 1 players (space separated)",
        team2="Mention all Team 2 players (space separated)"
    )
    async def match_add_past(self, interaction: discord.Interaction, series_type: str,
                            winner_team: int, team1_score: int, team2_score: int,
                            team1: str, team2: str):
        """Add a past match to the system"""
        # Validate inputs
        series_type = series_type.upper()
        if series_type not in ['BO3', 'BO5']:
            await interaction.response.send_message("❌ Series type must be BO3 or BO5", ephemeral=True)
            return
        
        if winner_team not in [1, 2]:
            await interaction.response.send_message("❌ Winner must be 1 or 2", ephemeral=True)
            return
        
        # Validate scores
        max_score = 2 if series_type == 'BO3' else 3
        if winner_team == 1:
            if team1_score < max_score or team2_score >= max_score:
                await interaction.response.send_message(
                    f"❌ Invalid scores for {series_type}. Team 1 (winner) must have {max_score}+ wins, Team 2 must have less.",
                    ephemeral=True
                )
                return
        else:
            if team2_score < max_score or team1_score >= max_score:
                await interaction.response.send_message(
                    f"❌ Invalid scores for {series_type}. Team 2 (winner) must have {max_score}+ wins, Team 1 must have less.",
                    ephemeral=True
                )
                return
        
        await interaction.response.defer()
        
        # Parse player mentions - this is a simplified version
        # In production, you'd want better mention parsing
        team1_ids = []
        team2_ids = []
        
        # Try to extract user IDs from mentions
        # For slash commands, we need to handle this differently
        await interaction.followup.send(
            "⚠️ **Important**: Please use the interactive version instead!\n\n"
            "Use `/match_add_past_interactive` which will let you select players with buttons.",
            ephemeral=True
        )
    
    @app_commands.command(name="match_import", description="Import a past match with individual players")
    @app_commands.describe(
        series_type="BO3 or BO5",
        winner_team="Which team won (1 or 2)",
        team1_score="Team 1's score",
        team2_score="Team 2's score",
        team1_p1="Team 1 Player 1",
        team1_p2="Team 1 Player 2",
        team1_p3="Team 1 Player 3",
        team1_p4="Team 1 Player 4",
        team1_p5="Team 1 Player 5",
        team2_p1="Team 2 Player 1",
        team2_p2="Team 2 Player 2",
        team2_p3="Team 2 Player 3",
        team2_p4="Team 2 Player 4",
        team2_p5="Team 2 Player 5"
    )
    async def match_import(self, interaction: discord.Interaction, series_type: str,
                          winner_team: int, team1_score: int, team2_score: int,
                          team1_p1: discord.User, team1_p2: discord.User, team1_p3: discord.User,
                          team1_p4: discord.User, team1_p5: discord.User,
                          team2_p1: discord.User, team2_p2: discord.User, team2_p3: discord.User,
                          team2_p4: discord.User, team2_p5: discord.User):
        """Import a past completed match"""
        # Validate inputs
        series_type = series_type.upper()
        if series_type not in ['BO3', 'BO5']:
            await interaction.response.send_message("❌ Series type must be BO3 or BO5", ephemeral=True)
            return
        
        if winner_team not in [1, 2]:
            await interaction.response.send_message("❌ Winner must be 1 or 2", ephemeral=True)
            return
        
        # Validate scores make sense
        max_score = 2 if series_type == 'BO3' else 3
        total_games = team1_score + team2_score
        
        if winner_team == 1:
            if team1_score < max_score:
                await interaction.response.send_message(
                    f"❌ Team 1 (winner) must have at least {max_score} wins in a {series_type}",
                    ephemeral=True
                )
                return
        else:
            if team2_score < max_score:
                await interaction.response.send_message(
                    f"❌ Team 2 (winner) must have at least {max_score} wins in a {series_type}",
                    ephemeral=True
                )
                return
        
        await interaction.response.defer()
        
        # Collect player IDs
        team1_ids = [team1_p1.id, team1_p2.id, team1_p3.id, team1_p4.id, team1_p5.id]
        team2_ids = [team2_p1.id, team2_p2.id, team2_p3.id, team2_p4.id, team2_p5.id]
        
        # Check for duplicate players
        all_players = team1_ids + team2_ids
        if len(all_players) != len(set(all_players)):
            await interaction.followup.send("❌ You have duplicate players! Each player can only be on one team.", ephemeral=True)
            return
        
        # Create users if they don't exist
        all_users = [team1_p1, team1_p2, team1_p3, team1_p4, team1_p5,
                     team2_p1, team2_p2, team2_p3, team2_p4, team2_p5]
        
        for user in all_users:
            await db.get_or_create_user(user.id, user.name)
        
        # Create the match as completed
        match = await db.create_match(series_type, team1_ids, team2_ids)
        
        # Record individual games
        for game_num in range(1, total_games + 1):
            # Alternate winners based on final score
            # This is a simplified version - we're estimating game winners
            if game_num <= team1_score:
                game_winner = 1
            else:
                game_winner = 2
            
            await db.record_game(match['match_id'], game_num, team1_ids, team2_ids, game_winner)
        
        # Complete the match
        await db.complete_match(match['match_id'], winner_team)
        
        # Create result embed
        embed = discord.Embed(
            title="📥 Past Match Imported!",
            description=f"Match ID: `{match['match_id']}`",
            color=discord.Color.green()
        )
        
        team1_mentions = [f"<@{uid}>" for uid in team1_ids]
        team2_mentions = [f"<@{uid}>" for uid in team2_ids]
        
        embed.add_field(name="🔵 Team 1", value="\n".join(team1_mentions), inline=True)
        embed.add_field(name="🔴 Team 2", value="\n".join(team2_mentions), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        
        embed.add_field(name="Series Type", value=series_type, inline=True)
        embed.add_field(name="Final Score", value=f"🔵 {team1_score} - {team2_score} 🔴", inline=True)
        embed.add_field(name="Winner", value=f"👑 Team {winner_team}", inline=True)
        
        embed.set_footer(text="All player stats have been updated!")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MatchCommands(bot))
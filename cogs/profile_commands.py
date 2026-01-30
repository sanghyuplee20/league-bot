import discord
from discord import app_commands
from discord.ext import commands
from database.supabase_client import db

class ProfileCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="profile", description="View a user's profile and stats")
    @app_commands.describe(user="The user to view (leave empty for yourself)")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        """View user profile"""
        target_user = user or interaction.user
        
        # Get or create user
        user_data = await db.get_or_create_user(target_user.id, target_user.name)
        
        # Calculate win rate
        win_rate = (user_data['total_wins'] / user_data['total_games'] * 100) if user_data['total_games'] > 0 else 0
        
        embed = discord.Embed(
            title=f"📊 {target_user.name}'s Profile",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        embed.add_field(name="🎮 Total Games", value=str(user_data['total_games']), inline=True)
        embed.add_field(name="🏆 Wins", value=str(user_data['total_wins']), inline=True)
        embed.add_field(name="💔 Losses", value=str(user_data['total_games'] - user_data['total_wins']), inline=True)
        embed.add_field(name="📈 Win Rate", value=f"{win_rate:.1f}%", inline=True)
        
        # Get recent match history
        match_history = await db.get_user_match_history(target_user.id, limit=5)
        
        if match_history:
            history_text = []
            for match in match_history:
                result_emoji = "✅" if match.get('user_result') == 'win' else "❌"
                team = match.get('user_team', '?')
                status = "Complete" if match['status'] == 'completed' else "Ongoing"
                history_text.append(f"{result_emoji} {match['series_type']} - Team {team} - {status}")
            
            embed.add_field(
                name="📜 Recent Matches",
                value="\n".join(history_text[:5]) if history_text else "No matches yet",
                inline=False
            )
        
        embed.set_footer(text=f"Player since {user_data['created_at'][:10]}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="stats", description="View detailed stats for a user")
    @app_commands.describe(user="The user to view stats for")
    async def stats(self, interaction: discord.Interaction, user: discord.User = None):
        """View detailed user statistics"""
        target_user = user or interaction.user
        
        user_data = await db.get_user_stats(target_user.id)
        
        if not user_data:
            await interaction.response.send_message("User not found in database!", ephemeral=True)
            return
        
        total_games = user_data['total_games']
        total_wins = user_data['total_wins']
        total_losses = total_games - total_wins
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        embed = discord.Embed(
            title=f"📈 Detailed Stats - {target_user.name}",
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Overall stats
        embed.add_field(name="Overall Record", value=f"{total_wins}W - {total_losses}L", inline=False)
        embed.add_field(name="Win Rate", value=f"{win_rate:.2f}%", inline=True)
        embed.add_field(name="Total Games", value=str(total_games), inline=True)
        
        # Match history breakdown
        match_history = await db.get_user_match_history(target_user.id, limit=20)
        
        if match_history:
            # Count BO3 vs BO5
            bo3_games = [m for m in match_history if m['series_type'] == 'BO3']
            bo5_games = [m for m in match_history if m['series_type'] == 'BO5']
            
            bo3_wins = sum(1 for m in bo3_games if m.get('user_result') == 'win')
            bo5_wins = sum(1 for m in bo5_games if m.get('user_result') == 'win')
            
            if bo3_games:
                bo3_wr = (bo3_wins / len(bo3_games) * 100)
                embed.add_field(
                    name="BO3 Stats",
                    value=f"{bo3_wins}W - {len(bo3_games) - bo3_wins}L ({bo3_wr:.1f}%)",
                    inline=True
                )
            
            if bo5_games:
                bo5_wr = (bo5_wins / len(bo5_games) * 100)
                embed.add_field(
                    name="BO5 Stats",
                    value=f"{bo5_wins}W - {len(bo5_games) - bo5_wins}L ({bo5_wr:.1f}%)",
                    inline=True
                )
            
            # Recent form (last 10 games)
            recent_10 = match_history[:10]
            recent_wins = sum(1 for m in recent_10 if m.get('user_result') == 'win')
            form_emojis = []
            for m in recent_10:
                if m.get('user_result') == 'win':
                    form_emojis.append("🟢")
                elif m.get('user_result') == 'loss':
                    form_emojis.append("🔴")
                else:
                    form_emojis.append("⚪")
            
            embed.add_field(
                name="Recent Form (Last 10)",
                value=f"{recent_wins}W - {len([m for m in recent_10 if m.get('user_result') == 'loss'])}L\n{''.join(form_emojis)}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="View the top players")
    @app_commands.describe(limit="Number of players to show (default: 10)")
    async def leaderboard(self, interaction: discord.Interaction, limit: int = 10):
        """View leaderboard"""
        if limit > 25:
            limit = 25
        
        top_players = await db.get_leaderboard(limit)
        
        if not top_players:
            await interaction.response.send_message("No players found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏆 Leaderboard - Top Players",
            description="Ranked by Win Rate (minimum 1 game)",
            color=discord.Color.gold()
        )
        
        medal_emojis = ["🥇", "🥈", "🥉"]
        
        leaderboard_text = []
        for i, player in enumerate(top_players, 1):
            medal = medal_emojis[i-1] if i <= 3 else f"{i}."
            
            win_rate = player['win_rate']
            total_games = player['total_games']
            total_wins = player['total_wins']
            
            # Try to get Discord user
            user = self.bot.get_user(player['discord_id'])
            username = user.name if user else player['username']
            
            leaderboard_text.append(
                f"{medal} **{username}** - {win_rate:.1f}% ({total_wins}W-{total_games - total_wins}L)"
            )
        
        embed.description = "\n".join(leaderboard_text)
        embed.set_footer(text=f"Showing top {len(top_players)} players")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="my_matches", description="View your match history")
    @app_commands.describe(limit="Number of matches to show (default: 10)")
    async def my_matches(self, interaction: discord.Interaction, limit: int = 10):
        """View your match history"""
        if limit > 20:
            limit = 20
        
        matches = await db.get_user_match_history(interaction.user.id, limit)
        
        if not matches:
            await interaction.response.send_message("You haven't played any matches yet!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📜 {interaction.user.name}'s Match History",
            color=discord.Color.purple()
        )
        
        for match in matches:
            result = match.get('user_result', 'ongoing')
            team = match.get('user_team', '?')
            
            if result == 'win':
                result_emoji = "✅ WIN"
                color = "🟢"
            elif result == 'loss':
                result_emoji = "❌ LOSS"
                color = "🔴"
            else:
                result_emoji = "⏳ ONGOING"
                color = "⚪"
            
            match_info = f"{color} {match['series_type']} - Team {team} - {result_emoji}"
            
            embed.add_field(
                name=f"Match {match['match_id'][:8]}...",
                value=match_info,
                inline=False
            )
        
        embed.set_footer(text=f"Showing {len(matches)} most recent matches")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ProfileCommands(bot))
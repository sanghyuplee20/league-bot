import discord
from discord import app_commands
from discord.ext import commands

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Show all bot commands and how to use them")
    @app_commands.describe(category="Specific category to view (optional)")
    async def help_command(self, interaction: discord.Interaction, category: str = None):
        """Display help information"""
        
        if category:
            category = category.lower()
            if category in ['match', 'matches']:
                await self._show_match_help(interaction)
            elif category in ['profile', 'stats', 'profiles']:
                await self._show_profile_help(interaction)
            elif category in ['team', 'teams']:
                await self._show_team_help(interaction)
            else:
                await interaction.response.send_message(
                    f"❌ Unknown category: `{category}`\n"
                    "Valid categories: `match`, `profile`, `team`",
                    ephemeral=True
                )
        else:
            await self._show_main_help(interaction)
    
    async def _show_main_help(self, interaction: discord.Interaction):
        """Show main help menu"""
        embed = discord.Embed(
            title="🎮 League Bot - Command Guide",
            description="Your all-in-one bot for managing custom League games!",
            color=discord.Color.blue()
        )
        
        # Match Commands
        embed.add_field(
            name="🎯 Match Management",
            value=(
                "`/match_create` - Start a new BO3/BO5 series\n"
                "`/match_record` - Record game results\n"
                "`/match_status` - Check match progress\n"
                "`/match_history` - View recent matches\n"
                "`/match_import` - Import past completed matches"
            ),
            inline=False
        )
        
        # Profile Commands
        embed.add_field(
            name="👤 Player Profiles",
            value=(
                "`/profile` - View player stats\n"
                "`/stats` - Detailed performance breakdown\n"
                "`/leaderboard` - Top players ranking\n"
                "`/my_matches` - Your match history"
            ),
            inline=False
        )
        
        # Team Commands
        embed.add_field(
            name="🎲 Team Generation",
            value=(
                "`/team_random_select` - Random 5v5 teams\n"
                "`/team_roles` - Role-based balanced teams\n"
                "`/team_draft` - Captain draft with RPS"
            ),
            inline=False
        )
        
        # Quick Start
        embed.add_field(
            name="⚡ Quick Start",
            value=(
                "1. Generate teams: `/team_random_select`\n"
                "2. Create match: `/match_create BO3 [players]`\n"
                "3. Record games: `/match_record [id] [game#] [winner]`\n"
                "4. Check stats: `/profile`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📚 Detailed Help",
            value=(
                "Use `/help match` for match commands\n"
                "Use `/help profile` for profile commands\n"
                "Use `/help team` for team generation"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: All commands use Discord's slash command system - just type / to see them!")
        
        await interaction.response.send_message(embed=embed)
    
    async def _show_match_help(self, interaction: discord.Interaction):
        """Show detailed match command help"""
        embed = discord.Embed(
            title="🎯 Match Management Commands",
            description="Everything you need to create and track custom game series",
            color=discord.Color.green()
        )
        
        # Create Match
        embed.add_field(
            name="`/match_create`",
            value=(
                "**Create a new BO3 or BO5 match series**\n"
                "**Usage:** `/match_create BO3 @p1 @p2 ... @p10`\n"
                "**Parameters:**\n"
                "• `series_type`: BO3 or BO5\n"
                "• `team1`: First 5 player mentions (Team 1)\n"
                "• `team2`: Last 5 player mentions (Team 2)\n"
                "**Returns:** Match ID (save this!)\n"
                "**Example:** `/match_create BO3 @Alice @Bob @Charlie @David @Eve @Frank @Grace @Henry @Ivy @Jack`"
            ),
            inline=False
        )
        
        # Record Game
        embed.add_field(
            name="`/match_record`",
            value=(
                "**Record the result of an individual game**\n"
                "**Usage:** `/match_record [match_id] [game_number] [winner]`\n"
                "**Parameters:**\n"
                "• `match_id`: The ID from /match_create\n"
                "• `game_number`: 1, 2, 3, etc.\n"
                "• `winner`: 1 or 2 (which team won)\n"
                "**Auto-completes** when a team wins 2/3 (BO3) or 3/5 (BO5)\n"
                "**Example:** `/match_record abc123 1 1`"
            ),
            inline=False
        )
        
        # Match Status
        embed.add_field(
            name="`/match_status`",
            value=(
                "**Check current match status and scores**\n"
                "**Usage:** `/match_status [match_id]`\n"
                "Shows: Teams, current score, game results, match status\n"
                "**Example:** `/match_status abc123`"
            ),
            inline=False
        )
        
        # Match History
        embed.add_field(
            name="`/match_history`",
            value=(
                "**View recently played matches**\n"
                "**Usage:** `/match_history [limit]`\n"
                "• `limit`: Number of matches (1-20, default: 5)\n"
                "**Example:** `/match_history 10`"
            ),
            inline=False
        )
        
        # Import Match
        embed.add_field(
            name="`/match_import`",
            value=(
                "**Import a past/completed match**\n"
                "**Usage:** `/match_import BO3 1 2 1 @p1 ... @p10`\n"
                "**Parameters:**\n"
                "• `series_type`: BO3 or BO5\n"
                "• `winner_team`: 1 or 2\n"
                "• `team1_score`: Team 1's wins\n"
                "• `team2_score`: Team 2's wins\n"
                "• `team1_p1` through `team2_p5`: All 10 players\n"
                "**Updates all player stats automatically!**"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Match IDs are long UUID strings - copy them when creating matches!")
        
        await interaction.response.send_message(embed=embed)
    
    async def _show_profile_help(self, interaction: discord.Interaction):
        """Show detailed profile command help"""
        embed = discord.Embed(
            title="👤 Player Profile Commands",
            description="Track your performance and climb the leaderboard",
            color=discord.Color.purple()
        )
        
        # Profile
        embed.add_field(
            name="`/profile`",
            value=(
                "**View player profile and stats**\n"
                "**Usage:** `/profile [@user]`\n"
                "• Leave empty to view your own profile\n"
                "• Mention someone to view their profile\n"
                "Shows: Total games, wins, losses, win rate, recent matches\n"
                "**Examples:**\n"
                "• `/profile` (your stats)\n"
                "• `/profile @Alice` (Alice's stats)"
            ),
            inline=False
        )
        
        # Stats
        embed.add_field(
            name="`/stats`",
            value=(
                "**View detailed performance breakdown**\n"
                "**Usage:** `/stats [@user]`\n"
                "Shows:\n"
                "• Overall record and win rate\n"
                "• BO3 vs BO5 performance\n"
                "• Recent form (last 10 games)\n"
                "• Win/loss visualization\n"
                "**Example:** `/stats @Bob`"
            ),
            inline=False
        )
        
        # Leaderboard
        embed.add_field(
            name="`/leaderboard`",
            value=(
                "**View top players ranking**\n"
                "**Usage:** `/leaderboard [limit]`\n"
                "• `limit`: Number of players (1-25, default: 10)\n"
                "• Ranked by win rate (minimum 1 game)\n"
                "• Shows: Rank, name, win rate, record\n"
                "**Example:** `/leaderboard 20`"
            ),
            inline=False
        )
        
        # My Matches
        embed.add_field(
            name="`/my_matches`",
            value=(
                "**View your personal match history**\n"
                "**Usage:** `/my_matches [limit]`\n"
                "• `limit`: Number of matches (1-20, default: 10)\n"
                "• Shows: Match type, team, result (W/L)\n"
                "**Example:** `/my_matches 15`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 How Stats Work",
            value=(
                "• Stats update automatically when matches complete\n"
                "• Win rate = (Wins / Total Games) × 100\n"
                "• All players start at 0-0 until their first match\n"
                "• Imported matches count toward your stats too!"
            ),
            inline=False
        )
        
        embed.set_footer(text="🏆 Climb the leaderboard by winning matches!")
        
        await interaction.response.send_message(embed=embed)
    
    async def _show_team_help(self, interaction: discord.Interaction):
        """Show detailed team generation help"""
        embed = discord.Embed(
            title="🎲 Team Generation Commands",
            description="Three ways to create balanced 5v5 teams",
            color=discord.Color.gold()
        )
        
        # Random Teams
        embed.add_field(
            name="`/team_random_select`",
            value=(
                "**Generate completely random teams**\n"
                "**How it works:**\n"
                "1. Command creates a 'Join Game' button\n"
                "2. 10 players click the button\n"
                "3. Bot randomly splits into two teams\n"
                "**Best for:** Casual games, quick setup\n"
                "**Pros:** Fast, simple, fair\n"
                "**Usage:** Just type `/team_random_select`!"
            ),
            inline=False
        )
        
        # Role-Based
        embed.add_field(
            name="`/team_roles`",
            value=(
                "**Generate role-balanced teams**\n"
                "**How it works:**\n"
                "1. Command shows 5 role buttons (Top/Jungle/Mid/ADC/Support)\n"
                "2. Each player picks their role\n"
                "3. Bot ensures each team gets one of each role\n"
                "**Best for:** When everyone has role preferences\n"
                "**Pros:** Balanced comps, fair role distribution\n"
                "**Usage:** Just type `/team_roles`!"
            ),
            inline=False
        )
        
        # Captain Draft
        embed.add_field(
            name="`/team_draft`",
            value=(
                "**Captain draft with Rock-Paper-Scissors**\n"
                "**How it works:**\n"
                "1. Choose two captains: `/team_draft @Alice @Bob`\n"
                "2. Captains play RPS to determine first pick\n"
                "3. All 10 players (including captains) join\n"
                "4. Captains alternate picking players (snake draft)\n"
                "**Best for:** Competitive games, strategic team building\n"
                "**Draft order:** 1-2-2-1-1-2-2-1 (snake format)\n"
                "**Usage:** `/team_draft @captain1 @captain2`"
            ),
            inline=False
        )
        
        # Tips
        embed.add_field(
            name="💡 Team Generation Tips",
            value=(
                "• **Random** is fastest for casual games\n"
                "• **Roles** ensures balanced team comps\n"
                "• **Draft** creates most competitive teams\n"
                "• All methods wait for exactly 10 players\n"
                "• Buttons timeout after 5 minutes\n"
                "• After teams form, use `/match_create` to start tracking!"
            ),
            inline=False
        )
        
        embed.set_footer(text="⏱️ All team generation commands timeout after 5 minutes")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
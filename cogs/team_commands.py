import discord
from discord import app_commands
from discord.ext import commands
from utils.team_generator import TeamGenerator
from utils.rps import play_rps, RPSGame
from typing import List, Dict, Optional
import asyncio

class TeamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_drafts: Dict[int, 'DraftSession'] = {}  # channel_id -> DraftSession
    
    @app_commands.command(name="team_random", description="Generate completely random teams")
    @app_commands.describe(players="Mention all 10 players")
    async def team_random(self, interaction: discord.Interaction, players: str):
        """Generate random teams"""
        # This is a simplified version - in production you'd parse mentions properly
        await interaction.response.send_message(
            "⚠️ Please use the button-based version: `/team_random_select` and have 10 players click the join button!",
            ephemeral=True
        )
    
    @app_commands.command(name="team_random_select", description="Generate random teams - players join with buttons")
    async def team_random_select(self, interaction: discord.Interaction):
        """Generate random teams with interactive selection"""
        view = PlayerSelectionView(self.bot, "random")
        
        embed = discord.Embed(
            title="🎲 Random Team Generator",
            description="Click the button below to join! Need 10 players.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Players Joined", value="None yet (0/10)", inline=False)
        
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
    
    @app_commands.command(name="team_roles", description="Generate teams based on roles")
    async def team_roles(self, interaction: discord.Interaction):
        """Generate role-based teams"""
        view = RoleSelectionView(self.bot)
        
        embed = discord.Embed(
            title="🎯 Role-Based Team Generator",
            description="Select your role! Need 2 players per role (10 total).",
            color=discord.Color.green()
        )
        
        roles = ['Top', 'Jungle', 'Mid', 'ADC', 'Support']
        for role in roles:
            embed.add_field(name=f"{role}", value="No players", inline=True)
        
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
    
    @app_commands.command(name="team_draft", description="Captain draft mode with RPS")
    @app_commands.describe(
        captain1="First captain",
        captain2="Second captain"
    )
    async def team_draft(self, interaction: discord.Interaction, captain1: discord.User, captain2: discord.User):
        """Start a captain draft"""
        if captain1.id == captain2.id:
            await interaction.response.send_message("❌ Captains must be different players!", ephemeral=True)
            return
        
        # Start RPS to determine first pick
        await interaction.response.send_message(
            f"🎮 **Captain Draft Starting!**\n\n"
            f"Captains: {captain1.mention} vs {captain2.mention}\n\n"
            f"Playing Rock Paper Scissors to determine first pick..."
        )
        
        winner = await play_rps(interaction, captain1, captain2)
        
        if not winner:
            await interaction.followup.send("Game timed out or tied! Please try again.")
            return
        
        # Determine first captain
        first_captain = 1 if winner.id == captain1.id else 2
        
        # Create draft session
        draft = DraftSession(captain1, captain2, first_captain, interaction.channel)
        self.pending_drafts[interaction.channel.id] = draft
        
        # Start draft
        view = PlayerSelectionView(self.bot, "draft", draft=draft)
        
        embed = discord.Embed(
            title="⚔️ Captain Draft - Player Selection",
            description=f"**{winner.mention}** won RPS and picks first!\n\n"
                       f"All 10 players (including captains) click JOIN below!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Players Available", value="None yet (0/10)", inline=False)
        
        message = await interaction.followup.send(embed=embed, view=view)
        view.message = message

class PlayerSelectionView(discord.ui.View):
    def __init__(self, bot, mode: str, draft: 'DraftSession' = None):
        super().__init__(timeout=300)
        self.bot = bot
        self.mode = mode  # "random", "draft"
        self.draft = draft
        self.players: List[discord.User] = []
        self.message: Optional[discord.Message] = None
    
    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.green, emoji="✋")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        
        # Check if already joined
        if user in self.players:
            await interaction.response.send_message("You already joined!", ephemeral=True)
            return
        
        # Check if full
        if len(self.players) >= 10:
            await interaction.response.send_message("Game is full!", ephemeral=True)
            return
        
        # Add player
        self.players.append(user)
        
        # Update embed
        embed = self.message.embeds[0]
        player_list = "\n".join([f"{i+1}. {p.mention}" for i, p in enumerate(self.players)])
        
        if self.mode == "random":
            embed.set_field_at(0, name="Players Joined", value=f"{player_list}\n\n({len(self.players)}/10)", inline=False)
        elif self.mode == "draft":
            embed.set_field_at(0, name="Players Available", value=f"{player_list}\n\n({len(self.players)}/10)", inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # If we have 10 players, generate teams
        if len(self.players) == 10:
            button.disabled = True
            await interaction.message.edit(view=self)
            
            if self.mode == "random":
                await self._generate_random_teams(interaction)
            elif self.mode == "draft":
                await self._start_draft(interaction)
    
    async def _generate_random_teams(self, interaction: discord.Interaction):
        """Generate and display random teams"""
        player_ids = [p.id for p in self.players]
        team1_ids, team2_ids = TeamGenerator.random_teams(player_ids)
        
        team1 = [p for p in self.players if p.id in team1_ids]
        team2 = [p for p in self.players if p.id in team2_ids]
        
        embed = discord.Embed(
            title="🎲 Random Teams Generated!",
            color=discord.Color.blue()
        )
        
        team1_text = "\n".join([f"{i+1}. {p.mention}" for i, p in enumerate(team1)])
        team2_text = "\n".join([f"{i+1}. {p.mention}" for i, p in enumerate(team2)])
        
        embed.add_field(name="🔵 Team 1", value=team1_text, inline=True)
        embed.add_field(name="🔴 Team 2", value=team2_text, inline=True)
        
        await interaction.followup.send(embed=embed)
    
    async def _start_draft(self, interaction: discord.Interaction):
        """Start the draft process"""
        if not self.draft:
            return
        
        self.draft.available_players = [p for p in self.players if p.id not in [self.draft.captain1.id, self.draft.captain2.id]]
        
        # Captains auto-join their teams
        if self.draft.first_captain == 1:
            self.draft.team1.append(self.draft.captain1)
            self.draft.team2.append(self.draft.captain2)
        else:
            self.draft.team1.append(self.draft.captain2)
            self.draft.team2.append(self.draft.captain1)
        
        # Start draft picks
        view = DraftPickView(self.bot, self.draft)
        
        current_captain = self.draft.captain1 if self.draft.current_pick_captain == 1 else self.draft.captain2
        
        embed = discord.Embed(
            title="⚔️ Captain Draft - Picking Phase",
            description=f"**{current_captain.mention}'s turn to pick!**\n\nSelect a player below.",
            color=discord.Color.gold()
        )
        
        team1_text = "\n".join([p.mention for p in self.draft.team1]) or "None yet"
        team2_text = "\n".join([p.mention for p in self.draft.team2]) or "None yet"
        
        embed.add_field(name="🔵 Team 1", value=team1_text, inline=True)
        embed.add_field(name="🔴 Team 2", value=team2_text, inline=True)
        
        message = await interaction.followup.send(embed=embed, view=view)
        view.message = message

class RoleSelectionView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.role_assignments: Dict[str, List[discord.User]] = {
            'top': [],
            'jungle': [],
            'mid': [],
            'adc': [],
            'support': []
        }
        self.message: Optional[discord.Message] = None
    
    async def _update_embed(self, interaction: discord.Interaction):
        """Update the embed with current role assignments"""
        embed = self.message.embeds[0]
        
        role_names = {'top': 'Top', 'jungle': 'Jungle', 'mid': 'Mid', 'adc': 'ADC', 'support': 'Support'}
        
        for i, (role_key, role_name) in enumerate(role_names.items()):
            players = self.role_assignments[role_key]
            if players:
                value = "\n".join([p.mention for p in players]) + f" ({len(players)}/2)"
            else:
                value = "No players (0/2)"
            embed.set_field_at(i, name=role_name, value=value, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Check if all roles filled
        if all(len(players) == 2 for players in self.role_assignments.values()):
            await self._generate_teams(interaction)
    
    async def _generate_teams(self, interaction: discord.Interaction):
        """Generate teams based on roles"""
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        # Convert to player IDs
        role_ids = {
            role: [p.id for p in players]
            for role, players in self.role_assignments.items()
        }
        
        team1_ids, team2_ids = TeamGenerator.role_based_teams(role_ids)
        
        # Get player objects
        all_players = []
        for players in self.role_assignments.values():
            all_players.extend(players)
        
        team1 = [p for p in all_players if p.id in team1_ids]
        team2 = [p for p in all_players if p.id in team2_ids]
        
        embed = discord.Embed(
            title="🎯 Role-Based Teams Generated!",
            color=discord.Color.green()
        )
        
        team1_text = "\n".join([p.mention for p in team1])
        team2_text = "\n".join([p.mention for p in team2])
        
        embed.add_field(name="🔵 Team 1", value=team1_text, inline=True)
        embed.add_field(name="🔴 Team 2", value=team2_text, inline=True)
        
        await interaction.followup.send(embed=embed)
    
    async def _add_to_role(self, interaction: discord.Interaction, role: str):
        """Add player to a role"""
        user = interaction.user
        
        # Check if user already has a role
        for r, players in self.role_assignments.items():
            if user in players:
                await interaction.response.send_message(f"You're already assigned to {r.title()}!", ephemeral=True)
                return
        
        # Check if role is full
        if len(self.role_assignments[role]) >= 2:
            await interaction.response.send_message(f"{role.title()} is full!", ephemeral=True)
            return
        
        # Add to role
        self.role_assignments[role].append(user)
        await self._update_embed(interaction)
    
    @discord.ui.button(label="Top", style=discord.ButtonStyle.primary, row=0)
    async def top_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._add_to_role(interaction, 'top')
    
    @discord.ui.button(label="Jungle", style=discord.ButtonStyle.primary, row=0)
    async def jungle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._add_to_role(interaction, 'jungle')
    
    @discord.ui.button(label="Mid", style=discord.ButtonStyle.primary, row=1)
    async def mid_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._add_to_role(interaction, 'mid')
    
    @discord.ui.button(label="ADC", style=discord.ButtonStyle.primary, row=1)
    async def adc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._add_to_role(interaction, 'adc')
    
    @discord.ui.button(label="Support", style=discord.ButtonStyle.primary, row=2)
    async def support_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._add_to_role(interaction, 'support')

class DraftSession:
    def __init__(self, captain1: discord.User, captain2: discord.User, first_captain: int, channel):
        self.captain1 = captain1
        self.captain2 = captain2
        self.first_captain = first_captain
        self.channel = channel
        self.team1: List[discord.User] = []
        self.team2: List[discord.User] = []
        self.available_players: List[discord.User] = []
        self.pick_count = 0
        self.current_pick_captain = first_captain
    
    def make_pick(self, player: discord.User):
        """Add a player to the current captain's team"""
        if self.current_pick_captain == 1:
            self.team1.append(player)
        else:
            self.team2.append(player)
        
        self.available_players.remove(player)
        self.pick_count += 1
        
        # Determine next picker using snake draft
        draft_order = TeamGenerator.captain_draft_order(8, self.first_captain)
        if self.pick_count < len(draft_order):
            self.current_pick_captain = draft_order[self.pick_count]
    
    def is_complete(self) -> bool:
        """Check if draft is complete"""
        return len(self.team1) == 5 and len(self.team2) == 5

class DraftPickView(discord.ui.View):
    def __init__(self, bot, draft: DraftSession):
        super().__init__(timeout=300)
        self.bot = bot
        self.draft = draft
        self.message: Optional[discord.Message] = None
        
        # Add a button for each available player
        for player in draft.available_players[:25]:  # Max 25 buttons
            button = discord.ui.Button(
                label=player.name[:80],
                style=discord.ButtonStyle.secondary,
                custom_id=f"pick_{player.id}"
            )
            button.callback = self._create_pick_callback(player)
            self.add_item(button)
    
    def _create_pick_callback(self, player: discord.User):
        async def callback(interaction: discord.Interaction):
            # Check if it's the right captain's turn
            current_captain = self.draft.captain1 if self.draft.current_pick_captain == 1 else self.draft.captain2
            
            if interaction.user.id != current_captain.id:
                await interaction.response.send_message("It's not your turn to pick!", ephemeral=True)
                return
            
            # Make the pick
            self.draft.make_pick(player)
            
            # Check if draft is complete
            if self.draft.is_complete():
                await self._finish_draft(interaction)
            else:
                await self._update_draft(interaction)
        
        return callback
    
    async def _update_draft(self, interaction: discord.Interaction):
        """Update the draft view"""
        current_captain = self.draft.captain1 if self.draft.current_pick_captain == 1 else self.draft.captain2
        
        embed = discord.Embed(
            title="⚔️ Captain Draft - Picking Phase",
            description=f"**{current_captain.mention}'s turn to pick!**\n\nSelect a player below.",
            color=discord.Color.gold()
        )
        
        team1_text = "\n".join([p.mention for p in self.draft.team1])
        team2_text = "\n".join([p.mention for p in self.draft.team2])
        
        embed.add_field(name="🔵 Team 1", value=team1_text, inline=True)
        embed.add_field(name="🔴 Team 2", value=team2_text, inline=True)
        
        # Recreate view with remaining players
        new_view = DraftPickView(self.bot, self.draft)
        new_view.message = self.message
        
        await interaction.response.edit_message(embed=embed, view=new_view)
    
    async def _finish_draft(self, interaction: discord.Interaction):
        """Finish the draft and show final teams"""
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        embed = discord.Embed(
            title="⚔️ Captain Draft Complete!",
            color=discord.Color.gold()
        )
        
        team1_text = "\n".join([f"{i+1}. {p.mention}" for i, p in enumerate(self.draft.team1)])
        team2_text = "\n".join([f"{i+1}. {p.mention}" for i, p in enumerate(self.draft.team2)])
        
        embed.add_field(name="🔵 Team 1", value=team1_text, inline=True)
        embed.add_field(name="🔴 Team 2", value=team2_text, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(TeamCommands(bot))
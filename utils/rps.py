import discord
from typing import Optional, Literal
import asyncio

Choice = Literal['rock', 'paper', 'scissors']

EMOJIS = {
    'rock': '🪨',
    'paper': '📄', 
    'scissors': '✂️'
}

WINNING_COMBOS = {
    'rock': 'scissors',
    'scissors': 'paper',
    'paper': 'rock'
}

class RPSGame:
    def __init__(self, player1: discord.User, player2: discord.User):
        self.player1 = player1
        self.player2 = player2
        self.choices = {}
        self.winner: Optional[discord.User] = None
    
    def make_choice(self, player: discord.User, choice: Choice) -> bool:
        """Record a player's choice. Returns True if both players have chosen."""
        if player.id not in [self.player1.id, self.player2.id]:
            return False
        
        self.choices[player.id] = choice
        return len(self.choices) == 2
    
    def determine_winner(self) -> Optional[discord.User]:
        """Determine the winner. Returns None for a tie."""
        if len(self.choices) != 2:
            return None
        
        p1_choice = self.choices[self.player1.id]
        p2_choice = self.choices[self.player2.id]
        
        if p1_choice == p2_choice:
            return None  # Tie
        
        if WINNING_COMBOS[p1_choice] == p2_choice:
            self.winner = self.player1
            return self.player1
        else:
            self.winner = self.player2
            return self.player2
    
    def get_result_text(self) -> str:
        """Get formatted result text"""
        p1_choice = self.choices.get(self.player1.id, 'unknown')
        p2_choice = self.choices.get(self.player2.id, 'unknown')
        
        p1_emoji = EMOJIS.get(p1_choice, '❓')
        p2_emoji = EMOJIS.get(p2_choice, '❓')
        
        result = f"{self.player1.mention} chose {p1_emoji}\n"
        result += f"{self.player2.mention} chose {p2_emoji}\n\n"
        
        if self.winner:
            result += f"🏆 **{self.winner.mention} wins!**"
        else:
            result += "🤝 **It's a tie! Play again.**"
        
        return result

class RPSView(discord.ui.View):
    def __init__(self, game: RPSGame):
        super().__init__(timeout=60)
        self.game = game
        self.message: Optional[discord.Message] = None
    
    async def on_timeout(self):
        """Disable buttons when timeout occurs"""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            await self.message.edit(view=self)
    
    async def _handle_choice(self, interaction: discord.Interaction, choice: Choice):
        """Handle a player's choice"""
        # Check if player is part of the game
        if interaction.user.id not in [self.game.player1.id, self.game.player2.id]:
            await interaction.response.send_message("You're not part of this game!", ephemeral=True)
            return
        
        # Check if player already chose
        if interaction.user.id in self.game.choices:
            await interaction.response.send_message("You already made your choice!", ephemeral=True)
            return
        
        # Record choice
        both_chosen = self.game.make_choice(interaction.user, choice)
        
        if not both_chosen:
            await interaction.response.send_message(f"You chose {EMOJIS[choice]}! Waiting for opponent...", ephemeral=True)
        else:
            # Both players chose, determine winner
            self.game.determine_winner()
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            # Show results
            await interaction.response.edit_message(
                content=self.game.get_result_text(),
                view=self
            )
            self.stop()
    
    @discord.ui.button(emoji='🪨', style=discord.ButtonStyle.primary)
    async def rock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 'rock')
    
    @discord.ui.button(emoji='📄', style=discord.ButtonStyle.primary)
    async def paper_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 'paper')
    
    @discord.ui.button(emoji='✂️', style=discord.ButtonStyle.primary)
    async def scissors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 'scissors')

async def play_rps(interaction: discord.Interaction, player1: discord.User, player2: discord.User) -> Optional[discord.User]:
    """
    Start an RPS game between two players.
    Returns the winner or None if tie/timeout.
    """
    game = RPSGame(player1, player2)
    view = RPSView(game)
    
    embed = discord.Embed(
        title="🎮 Rock Paper Scissors!",
        description=f"{player1.mention} vs {player2.mention}\n\nClick a button to make your choice!",
        color=discord.Color.blue()
    )
    
    message = await interaction.followup.send(embed=embed, view=view)
    view.message = message
    
    # Wait for game to complete or timeout
    await view.wait()
    
    return game.winnerimport discord
from typing import Optional, Literal
import asyncio

Choice = Literal['rock', 'paper', 'scissors']

EMOJIS = {
    'rock': '🪨',
    'paper': '📄', 
    'scissors': '✂️'
}

WINNING_COMBOS = {
    'rock': 'scissors',
    'scissors': 'paper',
    'paper': 'rock'
}

class RPSGame:
    def __init__(self, player1: discord.User, player2: discord.User):
        self.player1 = player1
        self.player2 = player2
        self.choices = {}
        self.winner: Optional[discord.User] = None
    
    def make_choice(self, player: discord.User, choice: Choice) -> bool:
        """Record a player's choice. Returns True if both players have chosen."""
        if player.id not in [self.player1.id, self.player2.id]:
            return False
        
        self.choices[player.id] = choice
        return len(self.choices) == 2
    
    def determine_winner(self) -> Optional[discord.User]:
        """Determine the winner. Returns None for a tie."""
        if len(self.choices) != 2:
            return None
        
        p1_choice = self.choices[self.player1.id]
        p2_choice = self.choices[self.player2.id]
        
        if p1_choice == p2_choice:
            return None  # Tie
        
        if WINNING_COMBOS[p1_choice] == p2_choice:
            self.winner = self.player1
            return self.player1
        else:
            self.winner = self.player2
            return self.player2
    
    def get_result_text(self) -> str:
        """Get formatted result text"""
        p1_choice = self.choices.get(self.player1.id, 'unknown')
        p2_choice = self.choices.get(self.player2.id, 'unknown')
        
        p1_emoji = EMOJIS.get(p1_choice, '❓')
        p2_emoji = EMOJIS.get(p2_choice, '❓')
        
        result = f"{self.player1.mention} chose {p1_emoji}\n"
        result += f"{self.player2.mention} chose {p2_emoji}\n\n"
        
        if self.winner:
            result += f"🏆 **{self.winner.mention} wins!**"
        else:
            result += "🤝 **It's a tie! Play again.**"
        
        return result

class RPSView(discord.ui.View):
    def __init__(self, game: RPSGame):
        super().__init__(timeout=60)
        self.game = game
        self.message: Optional[discord.Message] = None
    
    async def on_timeout(self):
        """Disable buttons when timeout occurs"""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            await self.message.edit(view=self)
    
    async def _handle_choice(self, interaction: discord.Interaction, choice: Choice):
        """Handle a player's choice"""
        # Check if player is part of the game
        if interaction.user.id not in [self.game.player1.id, self.game.player2.id]:
            await interaction.response.send_message("You're not part of this game!", ephemeral=True)
            return
        
        # Check if player already chose
        if interaction.user.id in self.game.choices:
            await interaction.response.send_message("You already made your choice!", ephemeral=True)
            return
        
        # Record choice
        both_chosen = self.game.make_choice(interaction.user, choice)
        
        if not both_chosen:
            await interaction.response.send_message(f"You chose {EMOJIS[choice]}! Waiting for opponent...", ephemeral=True)
        else:
            # Both players chose, determine winner
            self.game.determine_winner()
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            # Show results
            await interaction.response.edit_message(
                content=self.game.get_result_text(),
                view=self
            )
            self.stop()
    
    @discord.ui.button(emoji='🪨', style=discord.ButtonStyle.primary)
    async def rock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 'rock')
    
    @discord.ui.button(emoji='📄', style=discord.ButtonStyle.primary)
    async def paper_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 'paper')
    
    @discord.ui.button(emoji='✂️', style=discord.ButtonStyle.primary)
    async def scissors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 'scissors')

async def play_rps(interaction: discord.Interaction, player1: discord.User, player2: discord.User) -> Optional[discord.User]:
    """
    Start an RPS game between two players.
    Returns the winner or None if tie/timeout.
    """
    game = RPSGame(player1, player2)
    view = RPSView(game)
    
    embed = discord.Embed(
        title="🎮 Rock Paper Scissors!",
        description=f"{player1.mention} vs {player2.mention}\n\nClick a button to make your choice!",
        color=discord.Color.blue()
    )
    
    message = await interaction.followup.send(embed=embed, view=view)
    view.message = message
    
    # Wait for game to complete or timeout
    await view.wait()
    
    return game.winner
import discord
from discord.ext import commands

class Eventos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot iniciado com sucesso!")

    @commands.Cog.listener()
    async def on_member_join(self, membro:discord.Member):
        canal = self.bot.get_channel(821282819833724952)
        embed = discord.Embed()
        embed.title = "Bem-vindo ao servidor!"
        embed.description = f"**{membro.mention}** caiu de paraquedas no servidor!"
        embed.set_thumbnail(url=membro.avatar)
        embed.set_image(url=membro.banner)
        embed.set_footer(text=f"ID: {membro.id}")
        await canal.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        if str(reaction.emoji) == "🎫":
            guild = reaction.message.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            
            channel = await guild.create_text_channel(
                f"ticket-{user.name}",
                overwrites=overwrites,
                category=reaction.message.channel.category
            )
            
            embed = discord.Embed(
                title="Ticket Criado",
                description=f"Ticket criado por {user.mention}\nUm staff irá atendê-lo em breve!"
            )
            await channel.send(embed=embed)
            await reaction.message.remove_reaction(reaction.emoji, user)

async def setup(bot):
    await bot.add_cog(Eventos(bot)) 
import discord
from discord.ext import commands

class Moderacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def clear(self, ctx:commands.Context, quantidade:int):
        try:
            await ctx.channel.purge(limit=quantidade + 1)
            await ctx.send(f"✅ {quantidade} mensagens foram apagadas!", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Erro ao apagar mensagens: {str(e)}")
        
    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def kick(self, ctx:commands.Context, member:discord.Member, *, motivo:str = "Não especificado"):
        try:
            await member.kick(reason=motivo)
            await ctx.send(f"✅ **{member.name}** foi kickado do servidor por **{motivo}**")
        except Exception as e:
            await ctx.send(f"❌ Erro ao kickar: {str(e)}")
        
    @commands.has_permissions(kick_members=True)
    @commands.command()
    async def ban(self, ctx:commands.Context, member:discord.Member, *, motivo:str = "Não especificado"):
        try:
            await member.ban(reason=motivo)
            await ctx.send(f"✅ **{member.name}** foi banido do servidor por **{motivo}**")
        except Exception as e:
            await ctx.send(f"❌ Erro ao banir: {str(e)}")

    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def unban(self, ctx:commands.Context, member:discord.Member, *, motivo:str = "Não especificado"):
        try:
            await member.unban(reason=motivo)
            await ctx.send(f"✅ **{member.name}** foi desbanido do servidor por **{motivo}**")
        except Exception as e:
            await ctx.send(f"❌ Erro ao desbanir: {str(e)}")
        
    @commands.command()
    async def unmute(self, ctx:commands.Context, member:discord.Member, *, motivo:str = "Não especificado"):
        try:
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if muted_role:
                await member.remove_roles(muted_role)
                await ctx.send(f"✅ **{member.name}** foi desmutado do servidor por **{motivo}**")
            else:
                await ctx.send("❌ Cargo 'Muted' não encontrado. Por favor, reinicie o bot para criar os cargos padrão.")
        except Exception as e:
            await ctx.send(f"❌ Erro ao desmutar: {str(e)}")
        
    @commands.has_permissions(manage_roles=True)
    @commands.command()
    async def mute(self, ctx:commands.Context, member:discord.Member, *, motivo:str = "Não especificado"):
        try:
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if muted_role:
                await member.add_roles(muted_role)
                await ctx.send(f"✅ **{member.name}** foi mutado do servidor por **{motivo}**")
            else:
                await ctx.send("❌ Cargo 'Muted' não encontrado. Por favor, reinicie o bot para criar os cargos padrão.")
        except Exception as e:
            await ctx.send(f"❌ Erro ao mutar: {str(e)}")

async def setup(bot):
    await bot.add_cog(Moderacao(bot)) 
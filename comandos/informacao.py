import discord
from discord.ext import commands

class Informacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def userinfo(self, ctx:commands.Context, member:discord.Member = None):
        try:
            member = ctx.author if member is None else member
            newembed = discord.Embed()
            newembed.title = "Informações do usuário"
            newembed.set_author(name=member.name, icon_url=member.avatar)
            newembed.set_thumbnail(url=member.avatar)
            newembed.set_image(url=member.banner)
            newembed.set_footer(text=f"Requisitado por {ctx.author.name}")
            newembed.add_field(name="Nome do usuário", value=member.name)
            newembed.add_field(name="ID do usuário", value=member.id)
            newembed.add_field(name="Criado em", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"))
            newembed.add_field(name="Entrou em", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"))
            newembed.add_field(name="Bot?", value=member.bot)
            newembed.add_field(name="Top role", value=member.top_role)
            newembed.add_field(name="Status", value=member.status)
            
            await ctx.reply(embed=newembed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao mostrar informações: {str(e)}")
            
    @commands.command()
    async def serverinfo(self, ctx:commands.Context):
        try:
            server = ctx.guild
            online = len([m for m in server.members if m.status == discord.Status.online])
            offline = len([m for m in server.members if m.status == discord.Status.offline])
            dnd = len([m for m in server.members if m.status == discord.Status.dnd])
            
            newembed = discord.Embed(color=discord.Color.blue())
            newembed.title = "📊 Informações do Servidor"
            newembed.set_author(name=server.name, icon_url=server.icon)
            newembed.set_thumbnail(url=server.icon)
            newembed.set_image(url=server.banner)
            newembed.set_footer(text=f"Requisitado por {ctx.author.name}")
            
            # Informações gerais
            newembed.add_field(name="🏷️ Nome do servidor", value=server.name, inline=True)
            newembed.add_field(name="🆔 ID do servidor", value=server.id, inline=True)
            newembed.add_field(name="📅 Criado em", value=server.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
            
            # Status dos membros
            newembed.add_field(name="👥 Status dos Membros", value=
                f"🟢 **Online**: ``{online}``\n"
                f"⭕ **Offline**: ``{offline}``\n"
                f"🔴 **Não perturbe**: ``{dnd}``\n"
                f"📊 **Total**: ``{server.member_count}``", inline=False)
            
            # Canais
            newembed.add_field(name="💬 Canais de Texto", value=len(server.text_channels), inline=True)
            newembed.add_field(name="🔊 Canais de Voz", value=len(server.voice_channels), inline=True)
            newembed.add_field(name="📺 Canais de Stage", value=len(server.stage_channels), inline=True)
            
            await ctx.reply(embed=newembed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao mostrar informações: {str(e)}")

    @commands.command()
    async def ping(self, ctx:commands.Context):
        try:
            before = ctx.message.created_at.timestamp()
            message = await ctx.send("🏓 Pong!")
            ping = (message.created_at.timestamp() - before) * 1000
            await message.edit(content=f"🏓 Pong!\n⌛ Latência com a API: {round(self.bot.latency * 1000)}ms\n📡 Latência na rede: {round(ping)}ms")
        except Exception as e:
            await ctx.send(f"❌ Erro ao verificar ping: {str(e)}")

async def setup(bot):
    await bot.add_cog(Informacao(bot)) 
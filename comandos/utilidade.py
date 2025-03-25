import discord
from discord.ext import commands

class Utilidade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def say(self, ctx:commands.Context, *,texto):
        try:
            await ctx.send(texto)
        except Exception as e:
            await ctx.send(f"❌ Erro ao enviar mensagem: {str(e)}")

    @commands.command()
    async def somar(self, ctx:commands.Context, num1:float, num2:float):
        try:
            resultado = num1 + num2
            await ctx.reply(f"✅ O resultado da soma será: {resultado}")
        except Exception as e:
            await ctx.send(f"❌ Erro ao somar: {str(e)}")

    @commands.command()
    async def ticket(self, ctx: commands.Context):
        try:
            embed = discord.Embed(title="Sistema de Tickets", description="Reaja com 🎫 para criar um ticket")
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("🎫")
        except Exception as e:
            await ctx.send(f"❌ Erro ao criar ticket: {str(e)}")

    @commands.command()
    async def convidar(self, ctx: commands.Context):
        """Mostra como adicionar o bot a um novo servidor"""
        try:
            # Gerar link de convite com permissões necessárias
            invite_url = discord.utils.oauth_url(
                self.bot.user.id,
                permissions=discord.Permissions(
                    send_messages=True,
                    read_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    add_reactions=True,
                    use_external_emojis=True,
                    manage_messages=True,
                    manage_channels=True,
                    manage_roles=True
                )
            )

            embed = discord.Embed(
                title="🤖 Adicione o Bot ao seu Servidor",
                description="Clique no botão abaixo para adicionar o bot ao seu servidor!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="⚠️ Importante",
                value="O bot precisa ser administrador do servidor para funcionar corretamente com todos os recursos.",
                inline=False
            )

            embed.set_footer(text="Clique no botão abaixo para adicionar o bot!")

            # Criar botão para o link de convite
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="Adicionar ao Servidor",
                url=invite_url,
                style=discord.ButtonStyle.url,
                emoji="➕"
            ))

            await ctx.reply(embed=embed, view=view)

        except Exception as e:
            await ctx.send(f"❌ Erro ao gerar link de convite: {str(e)}")
            
        

async def setup(bot):
    await bot.add_cog(Utilidade(bot)) 
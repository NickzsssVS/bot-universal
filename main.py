import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração do bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="b!", intents=intents)

# Carrega os cogs
async def load_extensions():
    try:
        for filename in os.listdir("./eventos"):
            if filename.endswith(".py") and not filename.startswith("_"):
                await bot.load_extension(f"eventos.{filename[:-3]}")
                print(f"Carregado: eventos.{filename[:-3]}")
        
        for filename in os.listdir("./comandos"):
            if filename.endswith(".py") and not filename.startswith("_"):
                await bot.load_extension(f"comandos.{filename[:-3]}")
                print(f"Carregado: comandos.{filename[:-3]}")
    except Exception as e:
        print(f"Erro ao carregar extensões: {e}")

@bot.event
async def on_ready():
    print(f'Bot está online como {bot.user.name}')
    print('------')

async def setup_default_role(guild):
    try:
        # Nome dos cargos padrão
        roles_to_create = {
            "Muted": discord.Permissions(
                send_messages=False,
                speak=False,
                add_reactions=False,
                connect=False
            )
        }
        
        # Verifica e cria cada cargo se não existir
        for role_name, permissions in roles_to_create.items():
            role = discord.utils.get(guild.roles, name=role_name)
            
            if not role:
                role = await guild.create_role(
                    name=role_name,
                    permissions=permissions,
                    reason=f"Criação do cargo {role_name} para sistema do bot"
                )
                print(f"Cargo '{role_name}' criado no servidor {guild.name}")
            else:
                print(f"Cargo '{role_name}' já existe no servidor {guild.name}")
                
        return True
    except Exception as e:
        print(f"Erro ao configurar cargos padrão: {e}")
        return False

async def main():
    try:
        async with bot:
            await load_extensions()
            token = os.getenv('DISCORD_TOKEN')
            if not token:
                raise ValueError("Token não encontrado no arquivo .env")
            await bot.start(token)
    except Exception as e:
        print(f"Erro ao iniciar o bot: {e}")
        
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Comando para exibir o avatar de um usuário."""
    member = member or ctx.author  # Se nenhum membro for mencionado, usa o autor
    embed = discord.Embed(title=f"Avatar de {member.name}", color=discord.Color.blue())
    embed.set_image(url=member.avatar.url + "?size=1024")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot encerrado pelo usuário")
    except Exception as e:
        print(f"Erro fatal: {e}")
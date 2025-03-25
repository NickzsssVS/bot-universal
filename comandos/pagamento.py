import discord
from discord.ext import commands
import aiohttp
import json
import asyncio
from discord import ui
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
import os
import pandas as pd
from pathlib import Path

class ProdutoSelect(discord.ui.Select):
    def __init__(self, produtos, cog):
        options = []
        for produto_id, produto in produtos.items():
            options.append(
                discord.SelectOption(
                    label=f"{produto['nome']} - R$ {produto['preco']:.2f}",
                    value=produto_id,
                    description=f"Estoque: {produto['estoque']}"
                )
            )
        super().__init__(
            placeholder="Selecione um produto",
            min_values=1,
            max_values=1,
            options=options
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        produto_id = self.values[0]
        produto = self.cog.produtos[produto_id]
        
        if produto["estoque"] <= 0:
            await interaction.response.send_message("❌ Este produto está fora de estoque!", ephemeral=True)
            return

        # Criar canal privado para a transação
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await interaction.guild.create_text_channel(
            f"compra-{interaction.user.name}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🛒 Carrinho",
            description=f"**Produto:** {produto['nome']}\n**Preço:** R$ {produto['preco']:.2f}\n**Descrição:** {produto['descricao']}",
            color=discord.Color.blue()
        )

        view = PagamentoView(produto_id, produto, self.cog, channel)
        await channel.send(f"{interaction.user.mention}", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Canal de compra criado: {channel.mention}", ephemeral=True)

class ProdutoView(discord.ui.View):
    def __init__(self, produtos, cog):
        super().__init__(timeout=None)
        self.add_item(ProdutoSelect(produtos, cog))

class PagamentoView(ui.View):
    def __init__(self, produto_id, produto, cog, channel):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.produto_id = produto_id
        self.produto = produto
        self.cog = cog
        self.channel = channel

    @discord.ui.button(label="Pagar com PIX", style=discord.ButtonStyle.green)
    async def pagar_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Desabilitar o botão após clicar
        button.disabled = True
        await interaction.response.edit_message(view=self)

        # Gerar pagamento PIX
        pagamento = await self.cog.gerar_pix(
            self.produto["nome"],
            self.produto["preco"],
            interaction.user.name
        )

        if pagamento:
            try:
                # Criar QR Code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(pagamento['qr_code'])
                qr.make(fit=True)
                
                # Converter QR Code para imagem
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Salvar a imagem em um buffer
                buffered = BytesIO()
                img.save(buffered, format="PNG", quality=100)
                buffered.seek(0)
                
                # Criar o embed
                embed = discord.Embed(
                    title="💰 Pagamento PIX",
                    description=f"**Produto:** {self.produto['nome']}\n**Valor:** R$ {self.produto['preco']:.2f}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="QR Code PIX",
                    value=f"```{pagamento['qr_code']}```"
                )
                embed.add_field(
                    name="Código PIX",
                    value=f"```{pagamento['pix_code']}```"
                )
                
                # Enviar a imagem como arquivo
                file = discord.File(buffered, filename="qrcode.png")
                embed.set_image(url="attachment://qrcode.png")
                embed.set_footer(text="Escaneie o QR Code ou copie o código PIX para pagar")
                
                # Registrar pagamento pendente
                self.cog.pagamentos_pendentes[pagamento['id']] = {
                    'produto_id': self.produto_id,
                    'valor': self.produto['preco'],
                    'usuario': interaction.user.id,
                    'canal': self.channel.id,
                    'timestamp': datetime.now()
                }

                await interaction.followup.send(embed=embed, file=file)
            except Exception as e:
                print(f"Erro ao gerar QR Code: {str(e)}")
                await interaction.followup.send("❌ Erro ao gerar QR Code. Por favor, tente novamente.")
        else:
            await interaction.followup.send("❌ Erro ao gerar pagamento PIX!")

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Compra cancelada!", embed=None, view=None)
        await asyncio.sleep(5)
        await self.channel.delete()

class ProdutoForm(discord.ui.Modal, title='Adicionar Novo Produto'):
    nome = discord.ui.TextInput(
        label='Nome do Produto',
        placeholder='Digite o nome do produto...',
        required=True
    )
    
    preco = discord.ui.TextInput(
        label='Preço',
        placeholder='Digite o preço (ex: 99.99)',
        required=True
    )
    
    estoque = discord.ui.TextInput(
        label='Quantidade em Estoque',
        placeholder='Digite a quantidade disponível',
        required=True
    )
    
    descricao = discord.ui.TextInput(
        label='Descrição',
        placeholder='Digite a descrição do produto...',
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            preco = float(self.preco.value)
            estoque = int(self.estoque.value)
            
            produto_id = str(len(self.cog.produtos) + 1)
            dados_produto = {
                "id": produto_id,
                "nome": self.nome.value,
                "preco": preco,
                "estoque": estoque,
                "descricao": self.descricao.value,
                "data_criacao": datetime.now().isoformat()
            }
            
            self.cog.produtos[produto_id] = dados_produto
            self.cog.salvar_produto(produto_id, dados_produto)

            embed = discord.Embed(
                title=f"🛍️ {self.nome.value}",
                description=self.descricao.value,
                color=discord.Color.blue()
            )
            embed.add_field(name="Preço", value=f"R$ {preco:.2f}", inline=True)
            embed.add_field(name="Estoque", value=str(estoque), inline=True)
            embed.set_footer(text="Use o menu abaixo para selecionar e comprar")

            view = ProdutoView(self.cog.produtos, self.cog)
            await interaction.channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Produto '{self.nome.value}' postado com sucesso! ID: {produto_id}", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ Erro: Preço e estoque devem ser números válidos!", ephemeral=True)

class Pagamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mercadopago_access_token = "TEST-4628755507678002-032414-d41fb55e08daccae2b9fc9a2717a19fb-2243475468" 
        self.mercadopago_api_url = "https://api.mercadopago.com/v1"
        self.produtos = {}
        self.pagamentos_pendentes = {}
        self.data_dir = Path("data")
        self.produtos_dir = self.data_dir / "produtos"
        self.transacoes_dir = self.data_dir / "transacoes"
        
        # Carregar produtos existentes
        self.carregar_produtos()
        self.bot.loop.create_task(self.verificar_pagamentos())

    def carregar_produtos(self):
        """Carrega produtos do diretório de dados"""
        for arquivo in self.produtos_dir.glob("*.json"):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    produto = json.load(f)
                    self.produtos[produto['id']] = produto
            except Exception as e:
                print(f"Erro ao carregar produto {arquivo}: {str(e)}")

    def salvar_produto(self, produto_id, dados):
        """Salva um produto no diretório de dados"""
        arquivo = self.produtos_dir / f"{produto_id}.json"
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar produto {produto_id}: {str(e)}")

    def registrar_transacao(self, transacao):
        """Registra uma transação no diretório de dados"""
        data = datetime.now().strftime("%Y-%m-%d")
        arquivo = self.transacoes_dir / f"{data}.json"
        
        try:
            # Carregar transações existentes do dia
            if arquivo.exists():
                with open(arquivo, 'r', encoding='utf-8') as f:
                    transacoes = json.load(f)
            else:
                transacoes = []
            
            # Adicionar nova transação
            transacoes.append(transacao)
            
            # Salvar transações atualizadas
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(transacoes, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao registrar transação: {str(e)}")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def postar_produto(self, ctx: commands.Context):
        """Inicia o processo de adicionar um novo produto"""
        form = ProdutoForm()
        form.cog = self
        await ctx.send("Clique no botão abaixo para adicionar um novo produto:", view=ProdutoFormView(form))

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def remover_produto(self, ctx: commands.Context, produto_id: str):
        """Remove um produto da loja"""
        if produto_id in self.produtos:
            nome = self.produtos[produto_id]["nome"]
            arquivo = self.produtos_dir / f"{produto_id}.json"
            if arquivo.exists():
                arquivo.unlink()
            del self.produtos[produto_id]
            await ctx.reply(f"✅ Produto '{nome}' removido com sucesso!")
        else:
            await ctx.reply("❌ Produto não encontrado!")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def atualizar_produto(self, ctx: commands.Context, produto_id: str, preco: float = None, estoque: int = None, *, descricao: str = None):
        """Atualiza informações de um produto"""
        if produto_id not in self.produtos:
            await ctx.reply("❌ Produto não encontrado!")
            return

        if preco is not None:
            self.produtos[produto_id]["preco"] = preco
        if estoque is not None:
            self.produtos[produto_id]["estoque"] = estoque
        if descricao is not None:
            self.produtos[produto_id]["descricao"] = descricao

        self.salvar_produto(produto_id, self.produtos[produto_id])
        await ctx.reply("✅ Produto atualizado com sucesso!")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def desempenho(self, ctx: commands.Context):
        """Mostra o desempenho das vendas nos últimos 30 dias"""
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=30)
        
        # Coletar todas as transações do período
        transacoes = []
        for i in range(30):
            data = data_fim - timedelta(days=i)
            arquivo = self.transacoes_dir / f"{data.strftime('%Y-%m-%d')}.json"
            if arquivo.exists():
                with open(arquivo, 'r', encoding='utf-8') as f:
                    transacoes.extend(json.load(f))

        if not transacoes:
            await ctx.reply("❌ Nenhuma transação encontrada nos últimos 30 dias!")
            return

        # Criar DataFrame com as transações
        df = pd.DataFrame(transacoes)
        df['data'] = pd.to_datetime(df['timestamp'])
        
        # Calcular métricas
        total_vendas = len(df)
        total_receita = df['valor'].sum()
        media_diaria = total_vendas / 30
        media_receita_diaria = total_receita / 30
        
        # Produtos mais vendidos
        produtos_mais_vendidos = df.groupby('produto_nome').size().sort_values(ascending=False).head(5)
        
        # Criar embed com as informações
        embed = discord.Embed(
            title="📊 Desempenho dos Últimos 30 Dias",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Total de Vendas",
            value=f"{total_vendas} vendas",
            inline=True
        )
        embed.add_field(
            name="Total de Receita",
            value=f"R$ {total_receita:.2f}",
            inline=True
        )
        embed.add_field(
            name="Média Diária de Vendas",
            value=f"{media_diaria:.1f} vendas/dia",
            inline=True
        )
        embed.add_field(
            name="Média Diária de Receita",
            value=f"R$ {media_receita_diaria:.2f}/dia",
            inline=True
        )
        
        # Adicionar produtos mais vendidos
        produtos_texto = ""
        for produto, quantidade in produtos_mais_vendidos.items():
            produtos_texto += f"• {produto}: {quantidade} vendas\n"
        embed.add_field(
            name="Top 5 Produtos Mais Vendidos",
            value=produtos_texto or "Nenhum dado disponível",
            inline=False
        )
        
        await ctx.reply(embed=embed)

    async def gerar_pix(self, title, price, payer_name):
        """Gera um pagamento PIX"""
        headers = {
            "Authorization": f"Bearer {self.mercadopago_access_token}",
            "Content-Type": "application/json"
        }

        payment_data = {
            "transaction_amount": float(price),
            "description": title,
            "payment_method_id": "pix",
            "payer": {
                "email": f"{payer_name}@discord.com",
                "first_name": payer_name,
                "last_name": "Discord",
                "identification": {
                    "type": "CPF",
                    "number": "00000000000"
                }
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mercadopago_api_url}/payments",
                    headers=headers,
                    json=payment_data
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return {
                            'id': data['id'],
                            'qr_code': data['qr_code'],
                            'pix_code': data['qr_code_base64']
                        }
        except Exception as e:
            print(f"Erro ao gerar PIX: {str(e)}")
        return None

    async def verificar_pagamentos(self):
        """Verifica pagamentos pendentes a cada 30 segundos"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            headers = {
                "Authorization": f"Bearer {self.mercadopago_access_token}"
            }

            for payment_id, info in list(self.pagamentos_pendentes.items()):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.mercadopago_api_url}/payments/{payment_id}",
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                payment_info = await response.json()
                                
                                if payment_info['status'] == 'approved':
                                    # Atualizar estoque
                                    produto_id = info['produto_id']
                                    self.produtos[produto_id]["estoque"] -= 1
                                    self.salvar_produto(produto_id, self.produtos[produto_id])
                                    
                                    # Registrar transação
                                    transacao = {
                                        'id': payment_id,
                                        'produto_id': produto_id,
                                        'produto_nome': self.produtos[produto_id]['nome'],
                                        'valor': info['valor'],
                                        'usuario_id': info['usuario'],
                                        'timestamp': info['timestamp'].isoformat()
                                    }
                                    self.registrar_transacao(transacao)
                                    
                                    # Notificar usuário e fechar canal
                                    channel = self.bot.get_channel(info['canal'])
                                    if channel:
                                        embed = discord.Embed(
                                            title="✅ Pagamento Aprovado!",
                                            description=f"Seu pagamento para {self.produtos[produto_id]['nome']} foi aprovado!",
                                            color=discord.Color.green()
                                        )
                                        await channel.send(embed=embed)
                                        await asyncio.sleep(5)
                                        await channel.delete()
                                    
                                    # Remover pagamento pendente
                                    del self.pagamentos_pendentes[payment_id]
                                    
                except Exception as e:
                    print(f"Erro ao verificar pagamento {payment_id}: {str(e)}")

            await asyncio.sleep(30)  # Verificar a cada 30 segundos

    @commands.command()
    async def loja(self, ctx: commands.Context):
        """Mostra a loja com produtos disponíveis"""
        embed = discord.Embed(
            title="🛍️ Loja",
            description="Selecione um produto para comprar",
            color=discord.Color.blue()
        )

        for produto_id, produto in self.produtos.items():
            embed.add_field(
                name=f"{produto['nome']} - R$ {produto['preco']:.2f}",
                value=f"{produto['descricao']}\nEstoque: {produto['estoque']}\nID: {produto_id}",
                inline=False
            )

        await ctx.reply(embed=embed)

class ProdutoFormView(discord.ui.View):
    def __init__(self, form):
        super().__init__(timeout=None)
        self.form = form

    @discord.ui.button(label="Adicionar Produto", style=discord.ButtonStyle.green)
    async def adicionar_produto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.form)

async def setup(bot):
    await bot.add_cog(Pagamento(bot))

import discord
from discord.ext import commands
import random
from datetime import datetime
import json
import os
import logging

class Banco(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configuração do logging
        self.logger = logging.getLogger('banco')
        self.logger.setLevel(logging.INFO)
        
        # Criar diretório de dados se não existir
        if not os.path.exists('data'):
            os.makedirs('data')
            
        # Configurar arquivo de log
        file_handler = logging.FileHandler('data/transactions.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Carregar dados das contas
        self.accounts_file = 'data/accounts.json'
        self.saldos = self.load_accounts()

    def load_accounts(self):
        """Carrega os dados das contas do arquivo JSON"""
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r') as f:
                return json.load(f)
        return {}

    def save_accounts(self):
        """Salva os dados das contas no arquivo JSON"""
        with open(self.accounts_file, 'w') as f:
            json.dump(self.saldos, f, indent=4, default=str)

    def log_transaction(self, transaction_type, details):
        """Registra uma transação no arquivo de log"""
        self.logger.info(f"{transaction_type}: {json.dumps(details, default=str)}")

    @commands.command()
    async def criarconta(self, ctx:commands.Context):
        """Cria uma conta bancária simulada para o usuário"""
        try:
            user_id = str(ctx.author.id)
            
            if user_id in self.saldos:
                await ctx.send("❌ Você já possui uma conta!")
                return

            # Cria uma conta com saldo inicial aleatório entre 1000 e 5000
            saldo_inicial = random.randint(1000, 5000)
            self.saldos[user_id] = {
                "saldo": saldo_inicial,
                "criado_em": datetime.now().isoformat(),
                "ultima_atividade": datetime.now().isoformat()
            }

            # Salva os dados da conta
            self.save_accounts()

            # Registra a criação da conta
            self.log_transaction("CRIACAO_CONTA", {
                "user_id": user_id,
                "username": ctx.author.name,
                "saldo_inicial": saldo_inicial
            })

            embed = discord.Embed(
                title="🏦 Conta Criada com Sucesso!",
                description=f"Bem-vindo ao banco simulado, {ctx.author.name}!",
                color=discord.Color.green()
            )
            embed.add_field(name="Saldo Inicial", value=f"R$ {saldo_inicial:.2f}")
            embed.add_field(name="Data de Criação", value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            embed.set_footer(text=f"ID da Conta: {user_id}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao criar conta: {str(e)}")

    @commands.command()
    async def saldo(self, ctx:commands.Context):
        """Mostra o saldo atual da conta"""
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.saldos:
                await ctx.send("❌ Você não possui uma conta! Use `.criarconta` para criar uma.")
                return

            saldo = self.saldos[user_id]["saldo"]
            embed = discord.Embed(
                title="💰 Saldo da Conta",
                color=discord.Color.blue()
            )
            embed.add_field(name="Titular", value=ctx.author.name)
            embed.add_field(name="Saldo Atual", value=f"R$ {saldo:.2f}")
            embed.add_field(name="Última Atividade", value=datetime.fromisoformat(self.saldos[user_id]["ultima_atividade"]).strftime("%d/%m/%Y %H:%M:%S"))
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao verificar saldo: {str(e)}")

    @commands.command()
    async def transferir(self, ctx:commands.Context, membro:discord.Member, valor:float):
        """Transfere dinheiro para outro usuário"""
        try:
            remetente_id = str(ctx.author.id)
            destinatario_id = str(membro.id)
            
            if remetente_id not in self.saldos or destinatario_id not in self.saldos:
                await ctx.send("❌ Um dos usuários não possui conta!")
                return

            if valor <= 0:
                await ctx.send("❌ O valor da transferência deve ser maior que zero!")
                return

            if self.saldos[remetente_id]["saldo"] < valor:
                await ctx.send("❌ Saldo insuficiente para realizar a transferência!")
                return

            # Realiza a transferência
            self.saldos[remetente_id]["saldo"] -= valor
            self.saldos[destinatario_id]["saldo"] += valor
            self.saldos[remetente_id]["ultima_atividade"] = datetime.now().isoformat()
            self.saldos[destinatario_id]["ultima_atividade"] = datetime.now().isoformat()

            # Salva as alterações
            self.save_accounts()

            # Registra a transação
            self.log_transaction("TRANSFERENCIA", {
                "remetente_id": remetente_id,
                "remetente_nome": ctx.author.name,
                "destinatario_id": destinatario_id,
                "destinatario_nome": membro.name,
                "valor": valor,
                "data": datetime.now().isoformat()
            })

            embed = discord.Embed(
                title="💸 Transferência Realizada",
                color=discord.Color.green()
            )
            embed.add_field(name="De", value=ctx.author.name)
            embed.add_field(name="Para", value=membro.name)
            embed.add_field(name="Valor", value=f"R$ {valor:.2f}")
            embed.add_field(name="Data", value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao realizar transferência: {str(e)}")

    @commands.command()
    async def extrato(self, ctx:commands.Context):
        """Mostra o extrato das últimas transações"""
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.saldos:
                await ctx.send("❌ Você não possui uma conta!")
                return

            # Lê o arquivo de log para obter as transações do usuário
            with open('data/transactions.log', 'r') as f:
                transacoes = []
                for line in f:
                    if user_id in line:
                        transacoes.append(line.strip())

            if not transacoes:
                await ctx.send("❌ Nenhuma transação encontrada!")
                return

            embed = discord.Embed(
                title="📊 Extrato de Transações",
                color=discord.Color.blue()
            )
            
            # Mostra as últimas 5 transações
            for transacao in transacoes[-5:]:
                embed.add_field(
                    name=transacao.split(" - ")[0],
                    value=transacao.split(" - ")[1],
                    inline=False
                )

            embed.set_footer(text=f"Saldo Atual: R$ {self.saldos[user_id]['saldo']:.2f}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao gerar extrato: {str(e)}")

    @commands.command()
    async def depositar(self, ctx:commands.Context, valor:float):
        """Simula um depósito na conta"""
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.saldos:
                await ctx.send("❌ Você não possui uma conta!")
                return

            if valor <= 0:
                await ctx.send("❌ O valor do depósito deve ser maior que zero!")
                return

            # Realiza o depósito
            self.saldos[user_id]["saldo"] += valor
            self.saldos[user_id]["ultima_atividade"] = datetime.now().isoformat()

            # Salva as alterações
            self.save_accounts()

            # Registra a transação
            self.log_transaction("DEPOSITO", {
                "user_id": user_id,
                "username": ctx.author.name,
                "valor": valor,
                "data": datetime.now().isoformat()
            })

            embed = discord.Embed(
                title="💰 Depósito Realizado",
                color=discord.Color.green()
            )
            embed.add_field(name="Titular", value=ctx.author.name)
            embed.add_field(name="Valor", value=f"R$ {valor:.2f}")
            embed.add_field(name="Novo Saldo", value=f"R$ {self.saldos[user_id]['saldo']:.2f}")
            embed.add_field(name="Data", value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao realizar depósito: {str(e)}")
    @commands.command()
    async def trabalhar(self, ctx:commands.Context):
        """Trabalha para ganhar dinheiro"""
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.saldos:
                await ctx.send("❌ Você não possui uma conta!")
                return

            # Gera um valor aleatório entre 100 e 1000
            valor = random.randint(100, 1000)
            
            # Adiciona o valor ao saldo
            self.saldos[user_id]["saldo"] += valor
            self.saldos[user_id]["ultima_atividade"] = datetime.now().isoformat()

            # Salva as alterações
            self.save_accounts()

            # Registra a transação
            self.log_transaction("TRABALHO", {
                "user_id": user_id,
                "username": ctx.author.name,
                "valor": valor,
                "data": datetime.now().isoformat()
            })

            embed = discord.Embed(
                title="💼 Trabalho Concluído",
                description=f"Você trabalhou duro e ganhou R$ {valor:.2f}!",
                color=discord.Color.green()
            )
            embed.add_field(name="Novo Saldo", value=f"R$ {self.saldos[user_id]['saldo']:.2f}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao trabalhar: {str(e)}")

    @commands.command()
    async def jackpot(self, ctx:commands.Context, valor:float):
        """Aposta um valor no jackpot"""
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.saldos:
                await ctx.send("❌ Você não possui uma conta!")
                return

            if valor <= 0:
                await ctx.send("❌ O valor da aposta deve ser maior que zero!")
                return

            if valor > self.saldos[user_id]["saldo"]:
                await ctx.send("❌ Saldo insuficiente para realizar esta aposta!")
                return

            # 30% de chance de ganhar
            ganhou = random.random() < 0.30

            if ganhou:
                # Ganha 2x o valor apostado
                premio = valor * 2
                self.saldos[user_id]["saldo"] += premio - valor
                resultado = f"🎉 Você ganhou R$ {premio:.2f}!"
                cor = discord.Color.green()
            else:
                # Perde o valor apostado
                self.saldos[user_id]["saldo"] -= valor
                resultado = "😢 Você perdeu!"
                cor = discord.Color.red()

            self.saldos[user_id]["ultima_atividade"] = datetime.now().isoformat()

            # Salva as alterações
            self.save_accounts()

            # Registra a transação
            self.log_transaction("JACKPOT", {
                "user_id": user_id,
                "username": ctx.author.name,
                "valor_apostado": valor,
                "ganhou": ganhou,
                "data": datetime.now().isoformat()
            })

            embed = discord.Embed(
                title="🎰 Jackpot",
                description=resultado,
                color=cor
            )
            embed.add_field(name="Valor Apostado", value=f"R$ {valor:.2f}")
            embed.add_field(name="Novo Saldo", value=f"R$ {self.saldos[user_id]['saldo']:.2f}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao apostar no jackpot: {str(e)}")

async def setup(bot):
    await bot.add_cog(Banco(bot)) 
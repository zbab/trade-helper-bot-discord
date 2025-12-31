import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from market_analysis import BinanceMarketAnalyzer, format_symbol

# Charger les variables d'environnement
load_dotenv()

# Créer le bot avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Initialiser l'analyseur de marché
analyzer = BinanceMarketAnalyzer()

# Supprimer la commande help par défaut pour créer la nôtre
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté!')
    print(f'Serveurs: {len(bot.guilds)}')

# ============================================================================
# COMMANDES DE CALCUL EXISTANTES
# ============================================================================

@bot.slash_command(name="position", description="Calculer la taille d'une position spot")
async def position(
    ctx,
    capital: float = discord.Option(float, description="Capital à risquer ($)"),
    entry: float = discord.Option(float, description="Prix d'entrée"),
    stop_loss: float = discord.Option(float, description="Prix du stop loss"),
    take_profit: float = discord.Option(float, description="Prix du take profit (optionnel)", required=False, default=None)
):
    await ctx.defer()
    
    if capital <= 0 or entry <= 0 or stop_loss <= 0:
        await ctx.respond("❌ Toutes les valeurs doivent être positives!")
        return
    
    if entry == stop_loss:
        await ctx.respond("❌ Le prix d'entrée et le stop loss ne peuvent pas être identiques!")
        return
    
    # Déterminer si c'est un LONG ou SHORT
    is_long = entry > stop_loss
    
    # Calculer le risque par unité
    risk_per_unit = abs(entry - stop_loss)
    risk_percent = (risk_per_unit / entry) * 100
    
    # Calculer la quantité
    quantity = capital / risk_per_unit
    
    # Calculer la valeur totale de la position
    position_value = quantity * entry
    
    # Calculer le R/R si take profit fourni
    rr_info = ""
    if take_profit and take_profit > 0:
        reward_per_unit = abs(take_profit - entry)
        rr_ratio = reward_per_unit / risk_per_unit
        potential_profit = quantity * reward_per_unit
        
        rr_info = f"\n**Ratio R/R:** {rr_ratio:.2f}\n**Profit potentiel:** ${potential_profit:,.2f}"
    
    # Créer l'embed
    embed = discord.Embed(
        title="📊 Calcul de Position Spot",
        color=discord.Color.green() if is_long else discord.Color.red()
    )
    
    embed.add_field(name="Type", value=f"{'🟢 LONG' if is_long else '🔴 SHORT'}", inline=False)
    embed.add_field(name="Capital risqué", value=f"${capital:,.2f}", inline=True)
    embed.add_field(name="Prix d'entrée", value=f"${entry:,.4f}", inline=True)
    embed.add_field(name="Stop Loss", value=f"${stop_loss:,.4f}", inline=True)
    embed.add_field(name="Risque par unité", value=f"${risk_per_unit:,.4f} ({risk_percent:.2f}%)", inline=True)
    embed.add_field(name="Quantité à acheter", value=f"{quantity:,.4f}", inline=True)
    embed.add_field(name="Valeur de la position", value=f"${position_value:,.2f}", inline=True)
    
    if rr_info:
        embed.add_field(name="Take Profit", value=f"${take_profit:,.4f}", inline=False)
        embed.description = rr_info
    
    embed.set_footer(text="💡 Position calculée pour le spot trading")
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="leverage", description="Calculer une position avec effet de levier")
async def leverage(
    ctx,
    capital: float = discord.Option(float, description="Capital à risquer ($)"),
    entry: float = discord.Option(float, description="Prix d'entrée"),
    stop_loss: float = discord.Option(float, description="Prix du stop loss"),
    leverage: int = discord.Option(int, description="Effet de levier (ex: 10 pour 10x)")
):
    await ctx.defer()
    
    if capital <= 0 or entry <= 0 or stop_loss <= 0 or leverage <= 0:
        await ctx.respond("❌ Toutes les valeurs doivent être positives!")
        return
    
    if leverage > 125:
        await ctx.respond("⚠️ Attention: Levier très élevé (max généralement 125x)")
    
    is_long = entry > stop_loss
    
    # Calcul du risque
    risk_per_unit = abs(entry - stop_loss)
    risk_percent = (risk_per_unit / entry) * 100
    
    # Avec levier
    effective_capital = capital * leverage
    quantity = effective_capital / entry
    
    # Marge requise (sans levier ce serait la valeur totale)
    margin_required = effective_capital / leverage
    
    # Perte maximale = capital risqué
    max_loss = capital
    
    embed = discord.Embed(
        title="⚡ Calcul de Position avec Levier",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="Type", value=f"{'🟢 LONG' if is_long else '🔴 SHORT'}", inline=False)
    embed.add_field(name="Capital risqué", value=f"${capital:,.2f}", inline=True)
    embed.add_field(name="Levier", value=f"{leverage}x", inline=True)
    embed.add_field(name="Marge requise", value=f"${margin_required:,.2f}", inline=True)
    embed.add_field(name="Prix d'entrée", value=f"${entry:,.4f}", inline=True)
    embed.add_field(name="Stop Loss", value=f"${stop_loss:,.4f}", inline=True)
    embed.add_field(name="Risque", value=f"{risk_percent:.2f}%", inline=True)
    embed.add_field(name="Quantité", value=f"{quantity:,.4f}", inline=True)
    embed.add_field(name="Valeur de position", value=f"${effective_capital:,.2f}", inline=True)
    embed.add_field(name="Perte maximale", value=f"${max_loss:,.2f}", inline=True)
    
    embed.set_footer(text="⚠️ Le levier amplifie les gains ET les pertes!")
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="rr", description="Calculer rapidement le ratio risque/rendement")
async def rr(
    ctx,
    entry: float = discord.Option(float, description="Prix d'entrée"),
    stop_loss: float = discord.Option(float, description="Prix du stop loss"),
    take_profit: float = discord.Option(float, description="Prix du take profit")
):
    await ctx.defer()
    
    if entry <= 0 or stop_loss <= 0 or take_profit <= 0:
        await ctx.respond("❌ Toutes les valeurs doivent être positives!")
        return
    
    is_long = entry > stop_loss
    
    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)
    
    if risk == 0:
        await ctx.respond("❌ Le risque ne peut pas être nul!")
        return
    
    rr_ratio = reward / risk
    risk_percent = (risk / entry) * 100
    reward_percent = (reward / entry) * 100
    
    # Déterminer la couleur selon le R/R
    if rr_ratio >= 3:
        color = discord.Color.green()
        quality = "🟢 Excellent"
    elif rr_ratio >= 2:
        color = discord.Color.blue()
        quality = "🔵 Bon"
    elif rr_ratio >= 1:
        color = discord.Color.orange()
        quality = "🟠 Acceptable"
    else:
        color = discord.Color.red()
        quality = "🔴 Mauvais"
    
    embed = discord.Embed(
        title="📊 Ratio Risque/Rendement",
        color=color
    )
    
    embed.add_field(name="Type", value=f"{'🟢 LONG' if is_long else '🔴 SHORT'}", inline=False)
    embed.add_field(name="Entry", value=f"${entry:,.4f}", inline=True)
    embed.add_field(name="Stop Loss", value=f"${stop_loss:,.4f}", inline=True)
    embed.add_field(name="Take Profit", value=f"${take_profit:,.4f}", inline=True)
    embed.add_field(name="Risque", value=f"${risk:,.4f} ({risk_percent:.2f}%)", inline=True)
    embed.add_field(name="Rendement", value=f"${reward:,.4f} ({reward_percent:.2f}%)", inline=True)
    embed.add_field(name="Ratio R/R", value=f"**1:{rr_ratio:.2f}**", inline=True)
    embed.add_field(name="Qualité", value=quality, inline=False)
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="dca", description="Calculer le prix moyen d'achat (DCA)")
async def dca(
    ctx,
    entries: str = discord.Option(str, description="Format: prix1:quantité1,prix2:quantité2 (ex: 100:1,90:1.5)")
):
    await ctx.defer()
    
    try:
        # Parser les entrées
        positions = []
        total_quantity = 0
        total_cost = 0
        
        for entry in entries.split(','):
            price, quantity = entry.split(':')
            price = float(price.strip())
            quantity = float(quantity.strip())
            
            if price <= 0 or quantity <= 0:
                await ctx.respond("❌ Les prix et quantités doivent être positifs!")
                return
            
            cost = price * quantity
            positions.append({
                'price': price,
                'quantity': quantity,
                'cost': cost
            })
            
            total_quantity += quantity
            total_cost += cost
        
        # Calculer le prix moyen
        average_price = total_cost / total_quantity
        
        # Créer l'embed
        embed = discord.Embed(
            title="💰 Dollar Cost Averaging (DCA)",
            color=discord.Color.blue()
        )
        
        # Ajouter chaque position
        for i, pos in enumerate(positions, 1):
            embed.add_field(
                name=f"Position {i}",
                value=f"Prix: ${pos['price']:,.4f}\nQté: {pos['quantity']:,.4f}\nCoût: ${pos['cost']:,.2f}",
                inline=True
            )
        
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Quantité totale", value=f"{total_quantity:,.4f}", inline=True)
        embed.add_field(name="Coût total", value=f"${total_cost:,.2f}", inline=True)
        embed.add_field(name="**Prix moyen**", value=f"**${average_price:,.4f}**", inline=True)
        
        await ctx.respond(embed=embed)
        
    except ValueError:
        await ctx.respond("❌ Format invalide! Utilisez: `prix1:quantité1,prix2:quantité2`\nExemple: `/dca 100:1,90:1.5,85:2`")
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")

# ============================================================================
# NOUVELLES COMMANDES - ANALYSE DE MOYENNES MOBILES
# ============================================================================

@bot.slash_command(name="ma_check", description="Vérifier l'état des moyennes mobiles (BTC ou ETH)")
async def ma_check(
    ctx,
    crypto: str = discord.Option(
        str,
        description="Crypto à analyser",
        choices=["BTC", "ETH"]
    )
):
    await ctx.defer()
    
    # Convertir en symbole Binance
    symbol = format_symbol(crypto)
    
    if not symbol:
        await ctx.respond("❌ Crypto non supportée! Utilisez BTC ou ETH.")
        return
    
    try:
        # Analyser le symbole
        analysis = analyzer.analyze_symbol(symbol)
        
        if analysis['status'] != 'success':
            await ctx.respond(f"❌ Erreur: {analysis.get('message', 'Erreur inconnue')}")
            return
        
        # Déterminer la couleur selon l'alignement
        if analysis['aligned_bullish']:
            color = discord.Color.green()
            status_emoji = "🟢"
            status_text = "ALIGNEMENT HAUSSIER"
        elif analysis['aligned_bearish']:
            color = discord.Color.red()
            status_emoji = "🔴"
            status_text = "ALIGNEMENT BAISSIER"
        else:
            color = discord.Color.orange()
            status_emoji = "🟠"
            status_text = "PAS D'ALIGNEMENT"
        
        # Créer l'embed
        embed = discord.Embed(
            title=f"📊 Analyse Moyennes Mobiles - {crypto}",
            description=f"**{status_emoji} {status_text}**",
            color=color
        )
        
        # Prix actuel
        current_price = analysis['current_price']
        embed.add_field(
            name="💰 Prix Actuel",
            value=f"${current_price:,.2f}",
            inline=False
        )
        
        # Moyennes mobiles
        ma_values = analysis['ma_values']
        ma_text = ""
        for period in [112, 336, 375, 448, 750]:
            ma_value = ma_values.get(period, 0)
            # Indiquer si le prix est au-dessus ou en-dessous
            if current_price > ma_value:
                indicator = "↑"
            else:
                indicator = "↓"
            ma_text += f"MA{period}: ${ma_value:,.2f} {indicator}\n"
        
        embed.add_field(
            name="📈 Moyennes Mobiles",
            value=ma_text,
            inline=True
        )
        
        # Compression
        compression = analysis['compression_pct']
        is_compressed = analysis['is_compressed']
        
        if is_compressed:
            compression_status = "🔥 COMPRESSION DÉTECTÉE!"
            compression_color = "```diff\n+ ALERTE COMPRESSION\n```"
        else:
            compression_status = "Normale"
            compression_color = f"```\n{compression:.2f}%\n```"
        
        embed.add_field(
            name="📊 Compression",
            value=f"{compression_status}\n{compression_color}",
            inline=True
        )
        
        # Position du prix
        if analysis['price_above_all_ma']:
            price_position = "🟢 Au-dessus de toutes les MA"
        elif analysis['price_below_all_ma']:
            price_position = "🔴 En-dessous de toutes les MA"
        else:
            price_position = "🟠 Entre les MA"
        
        embed.add_field(
            name="📍 Position du Prix",
            value=price_position,
            inline=False
        )
        
        # Ordre actuel des MA
        current_order = analysis['current_order']
        order_text = " > ".join([f"MA{p}" for p in current_order])
        embed.add_field(
            name="🔄 Ordre actuel (par valeur)",
            value=f"`{order_text}`",
            inline=False
        )
        
        # Distances entre MA
        distances = analysis.get('ma_distances', {})
        if distances:
            dist_text = ""
            for pair, dist in distances.items():
                dist_text += f"{pair}: {dist:.2f}%\n"
            embed.add_field(
                name="📏 Distances entre MA",
                value=dist_text,
                inline=False
            )
        
        # Footer avec info
        embed.set_footer(
            text=f"Données: {analysis['data_points']} jours | Dernière mise à jour: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}"
        )
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors de l'analyse: {str(e)}")

@bot.slash_command(name="ma_compare", description="Comparer BTC et ETH")
async def ma_compare(ctx):
    await ctx.defer()
    
    try:
        # Analyser BTC et ETH
        btc_analysis = analyzer.analyze_symbol('BTCUSDT')
        eth_analysis = analyzer.analyze_symbol('ETHUSDT')
        
        if btc_analysis['status'] != 'success' or eth_analysis['status'] != 'success':
            await ctx.respond("❌ Erreur lors de l'analyse")
            return
        
        embed = discord.Embed(
            title="📊 Comparaison BTC vs ETH",
            color=discord.Color.blue()
        )
        
        # BTC
        btc_status = "🟢 Haussier" if btc_analysis['aligned_bullish'] else "🔴 Baissier" if btc_analysis['aligned_bearish'] else "🟠 Neutre"
        btc_compression = "🔥 OUI" if btc_analysis['is_compressed'] else "Non"
        
        embed.add_field(
            name="₿ BITCOIN",
            value=f"Prix: ${btc_analysis['current_price']:,.2f}\n"
                  f"Alignement: {btc_status}\n"
                  f"Compression: {btc_compression}\n"
                  f"Écart MA: {btc_analysis['compression_pct']:.2f}%",
            inline=True
        )
        
        # ETH
        eth_status = "🟢 Haussier" if eth_analysis['aligned_bullish'] else "🔴 Baissier" if eth_analysis['aligned_bearish'] else "🟠 Neutre"
        eth_compression = "🔥 OUI" if eth_analysis['is_compressed'] else "Non"
        
        embed.add_field(
            name="⟠ ETHEREUM",
            value=f"Prix: ${eth_analysis['current_price']:,.2f}\n"
                  f"Alignement: {eth_status}\n"
                  f"Compression: {eth_compression}\n"
                  f"Écart MA: {eth_analysis['compression_pct']:.2f}%",
            inline=True
        )
        
        # Résumé
        both_bullish = btc_analysis['aligned_bullish'] and eth_analysis['aligned_bullish']
        both_bearish = btc_analysis['aligned_bearish'] and eth_analysis['aligned_bearish']
        both_compressed = btc_analysis['is_compressed'] and eth_analysis['is_compressed']
        
        summary = ""
        if both_bullish:
            summary = "🟢 Les deux sont alignés HAUSSIER!"
        elif both_bearish:
            summary = "🔴 Les deux sont alignés BAISSIER!"
        else:
            summary = "🟠 Alignements divergents"
        
        if both_compressed:
            summary += "\n🔥 COMPRESSION DÉTECTÉE SUR LES DEUX!"
        
        embed.add_field(
            name="📋 Résumé",
            value=summary,
            inline=False
        )
        
        embed.set_footer(text="💡 Utilisez /ma_check pour plus de détails")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")

@bot.slash_command(name="help", description="Afficher toutes les commandes disponibles")
async def help_command(ctx):
    embed = discord.Embed(
        title="📚 Guide des Commandes - Trading Helper Bot",
        description="Bot d'aide au trading avec calculs de position et analyse technique",
        color=discord.Color.blue()
    )
    
    # Calculs de position
    embed.add_field(
        name="💼 Calculs de Position",
        value=(
            "`/position` - Calculer une position spot\n"
            "`/leverage` - Calculer avec effet de levier\n"
            "`/rr` - Ratio risque/rendement\n"
            "`/dca` - Prix moyen d'achat"
        ),
        inline=False
    )
    
    # Analyse technique
    embed.add_field(
        name="📊 Analyse Technique",
        value=(
            "`/ma_check <BTC|ETH>` - Analyser les moyennes mobiles\n"
            "`/ma_compare` - Comparer BTC et ETH\n"
            "```Moyennes: MA112, MA336, MA375, MA448, MA750```"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎯 Détection Automatique",
        value=(
            "✅ Alignement haussier/baissier\n"
            "✅ Compression des moyennes (<5%)\n"
            "✅ Position du prix vs MA"
        ),
        inline=False
    )
    
    embed.set_footer(text="💡 Toutes les données proviennent de Binance")
    
    await ctx.respond(embed=embed)

# Lancer le bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ DISCORD_TOKEN non trouvé dans .env")
    else:
        bot.run(TOKEN)

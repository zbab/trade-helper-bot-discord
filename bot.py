import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from market_analysis import BinanceMarketAnalyzer, YFinanceMarketAnalyzer
from crypto_manager import CryptoManager
from stock_manager import StockManager
from symbol_search import BinanceSymbolSearch, YFinanceSymbolSearch
from volume_monitor import VolumeMonitor
import asyncio
from datetime import datetime
from ma_alerts import MAAlertMonitor

# Charger les variables d'environnement
load_dotenv()

# Créer le bot avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Initialiser les analyseurs et gestionnaires
crypto_analyzer = BinanceMarketAnalyzer()
stock_analyzer = YFinanceMarketAnalyzer()
crypto_manager = CryptoManager()
stock_manager = StockManager()
crypto_searcher = BinanceSymbolSearch()
stock_searcher = YFinanceSymbolSearch()
volume_monitor = VolumeMonitor()
ma_alert_monitor = MAAlertMonitor()

# Supprimer la commande help par défaut
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté!')
    print(f'Serveurs: {len(bot.guilds)}')
    print(f'Cryptos supportées: {", ".join(crypto_manager.get_crypto_symbols())}')
    print(f'Stocks supportés: {", ".join(stock_manager.get_stock_symbols())}')
    
    # Démarrer la surveillance des volumes
    if not volume_check_task.is_running():
        volume_check_task.start()
        print('🔍 Surveillance des volumes activée')

    # Démarrer la surveillance des croisements MA
    if not ma_alert_check_task.is_running():
        ma_alert_check_task.start()
        print('🔍 Surveillance des croisements MA activée')
# Tâche de surveillance des volumes (toutes les 15 minutes)
@tasks.loop(minutes=15)
async def volume_check_task():
    """Vérifie les volumes et envoie des alertes si nécessaire"""
    print(f"🔍 Vérification des volumes - {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Exécuter dans un thread pour ne pas bloquer le bot
        loop = asyncio.get_event_loop()
        alerts = await loop.run_in_executor(None, volume_monitor.check_all_assets)
        
        if alerts:
            print(f"✅ {len(alerts)} alerte(s) envoyée(s)")
            for alert in alerts:
                print(f"   └ {alert['symbol']}: {alert['level']} (+{alert['increase']:.1f}%)")
        else:
            print("   Aucun pic détecté")
            
    except Exception as e:
        print(f"❌ Erreur surveillance volumes: {e}")

@volume_check_task.before_loop
async def before_volume_check():
    """Attendre que le bot soit prêt avant de démarrer la surveillance"""
    await bot.wait_until_ready()

# Tâche de surveillance des croisements MA (toutes les heures)
@tasks.loop(minutes=60)
async def ma_alert_check_task():
    """Vérifie les croisements MA et envoie des alertes"""
    print(f"🔍 Vérification croisements MA - {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        loop = asyncio.get_event_loop()
        
        # Premier run : warm-up silencieux
        if not hasattr(ma_alert_check_task, 'warmed_up'):
            print("⏳ Premier démarrage - Mode warm-up (pas d'alertes)")
            alerts = await loop.run_in_executor(None, ma_alert_monitor.check_all_assets, True)
            ma_alert_check_task.warmed_up = True
            print(f"✅ Warm-up terminé - {len(alerts)} état(s) enregistré(s)")
            return
        
        # Runs suivants : normal
        alerts = await loop.run_in_executor(None, ma_alert_monitor.check_all_assets, False)
        
        if alerts:
            print(f"✅ {len(alerts)} alerte(s) MA envoyée(s)")
            for alert in alerts:
                print(f"   └ {alert['symbol']}: {alert['type']} ({alert['system']})")
        else:
            print("   Aucun croisement/alignement détecté")
            
    except Exception as e:
        print(f"❌ Erreur surveillance MA: {e}")

@ma_alert_check_task.before_loop
async def before_ma_alert_check():
    """Attendre que le bot soit prêt"""
    await bot.wait_until_ready()

def sync_alerts_with_managers():
    """Synchronise les alertes avec les actifs des managers"""
    # Récupérer tous les symboles Binance
    crypto_symbols = [
        crypto_manager.get_binance_symbol(symbol) 
        for symbol in crypto_manager.get_crypto_symbols()
    ]
    
    # Récupérer tous les symboles stocks
    stock_symbols = [
        stock_manager.get_yfinance_symbol(symbol)
        for symbol in stock_manager.get_stock_symbols()
    ]
    
    # Synchroniser
    volume_monitor.sync_assets_from_managers(crypto_symbols, stock_symbols)
    ma_alert_monitor.sync_assets_from_managers(crypto_symbols, stock_symbols)
    
    print(f"🔄 Synchronisation terminée: {len(crypto_symbols)} cryptos, {len(stock_symbols)} stocks")
# ============================================================================
# COMMANDES DE CALCUL DE POSITION
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
    
    is_long = entry > stop_loss
    risk_per_unit = abs(entry - stop_loss)
    risk_percent = (risk_per_unit / entry) * 100
    quantity = capital / risk_per_unit
    position_value = quantity * entry
    
    rr_info = ""
    if take_profit and take_profit > 0:
        reward_per_unit = abs(take_profit - entry)
        rr_ratio = reward_per_unit / risk_per_unit
        potential_profit = quantity * reward_per_unit
        rr_info = f"\n**Ratio R/R:** {rr_ratio:.2f}\n**Profit potentiel:** ${potential_profit:,.2f}"
    
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
    capital: float = discord.Option(float, description="Capital total disponible ($)"),
    risk_percent: float = discord.Option(float, description="Pourcentage du capital à risquer (ex: 2 pour 2%)"),
    entry: float = discord.Option(float, description="Prix d'entrée"),
    stop_loss: float = discord.Option(float, description="Prix du stop loss"),
    take_profit: float = discord.Option(float, description="Prix du take profit (target)"),
    leverage: int = discord.Option(int, description="Effet de levier (ex: 10 pour 10x)")
):
    await ctx.defer()
    
    # Validations
    if capital <= 0 or entry <= 0 or stop_loss <= 0 or take_profit <= 0 or leverage <= 0:
        await ctx.respond("❌ Toutes les valeurs doivent être positives!")
        return
    
    if risk_percent <= 0 or risk_percent > 100:
        await ctx.respond("❌ Le pourcentage de risque doit être entre 0 et 100!")
        return
    
    if leverage > 125:
        await ctx.respond("⚠️ Attention: Levier très élevé (max généralement 125x)")
    
    # Déterminer si LONG ou SHORT
    is_long = entry > stop_loss
    
    # Vérifier cohérence du take profit
    if is_long and take_profit <= entry:
        await ctx.respond("❌ Pour un LONG, le take profit doit être AU-DESSUS du prix d'entrée!")
        return
    
    if not is_long and take_profit >= entry:
        await ctx.respond("❌ Pour un SHORT, le take profit doit être EN-DESSOUS du prix d'entrée!")
        return
    
    # Calculs
    # Montant à risquer (en $)
    risk_amount = capital * (risk_percent / 100)
    
    # Distance du stop loss (en % et $)
    risk_per_unit = abs(entry - stop_loss)
    stop_distance_percent = (risk_per_unit / entry) * 100
    
    # Distance du take profit (en % et $)
    reward_per_unit = abs(take_profit - entry)
    target_distance_percent = (reward_per_unit / entry) * 100
    
    # Ratio R/R
    rr_ratio = reward_per_unit / risk_per_unit
    
    # Taille de position (exposition totale)
    position_value = risk_amount / (stop_distance_percent / 100)
    
    # Quantité
    quantity = position_value / entry
    
    # Marge requise (avec levier)
    margin_required = position_value / leverage
    
    # Pourcentage du capital utilisé comme marge
    capital_percent_used = (margin_required / capital) * 100
    
    # Pertes et gains
    max_loss = risk_amount
    potential_profit = quantity * reward_per_unit
    
    # ROI sur marge
    roi_on_margin = (potential_profit / margin_required) * 100
    
    # ========================================
    # SYSTÈME DE CONSEIL INTELLIGENT
    # ========================================
    
    advice_color = discord.Color.blue()
    advice_emoji = "💡"
    advice_text = ""
    warnings = []
    
    # 1. Évaluation du ratio R/R
    if rr_ratio >= 3:
        advice_emoji = "🟢"
        advice_color = discord.Color.green()
        advice_text = "**EXCELLENT TRADE**\nRatio R/R très favorable (≥3:1)"
    elif rr_ratio >= 2:
        advice_emoji = "🔵"
        advice_color = discord.Color.blue()
        advice_text = "**BON TRADE**\nRatio R/R correct (≥2:1)"
    elif rr_ratio >= 1.5:
        advice_emoji = "🟠"
        advice_color = discord.Color.orange()
        advice_text = "**TRADE ACCEPTABLE**\nRatio R/R limite (≥1.5:1)"
    else:
        advice_emoji = "🔴"
        advice_color = discord.Color.red()
        advice_text = "**TRADE RISQUÉ**\nRatio R/R défavorable (<1.5:1)"
        warnings.append("❌ Risque supérieur au gain potentiel")
    
    # 2. Évaluation du levier
    if leverage >= 20:
        warnings.append("⚠️ Levier très élevé (≥20x) - Liquidation rapide possible")
    elif leverage >= 10:
        warnings.append("⚠️ Levier élevé (≥10x) - Gestion stricte requise")
    
    # 3. Évaluation du risque
    if risk_percent > 5:
        warnings.append("⚠️ Risque élevé (>5% du capital)")
    elif risk_percent > 2:
        warnings.append("💡 Risque modéré (2-5% du capital)")
    
    # 4. Évaluation de la marge utilisée
    if capital_percent_used > 50:
        warnings.append("⚠️ Plus de 50% du capital immobilisé en marge")
    
    # 5. Distance du stop loss
    if stop_distance_percent < 1:
        warnings.append("⚠️ Stop loss très serré (<1%) - Risque de faux déclenchement")
    elif stop_distance_percent > 10:
        warnings.append("⚠️ Stop loss large (>10%) - Perte importante possible")
    
    # ========================================
    # CONSTRUCTION DE L'EMBED
    # ========================================
    
    embed = discord.Embed(
        title="⚡ Calcul de Position avec Levier",
        color=advice_color
    )
    
    # Type de position
    embed.add_field(
        name="Type", 
        value=f"{'🟢 LONG' if is_long else '🔴 SHORT'}", 
        inline=False
    )
    
    # Capital & Risque
    embed.add_field(
        name="💰 Capital & Risque",
        value=(
            f"**Capital total:** ${capital:,.2f}\n"
            f"**Risque accepté:** {risk_percent}% (${risk_amount:,.2f})\n"
            f"**Perte maximale:** ${max_loss:,.2f}"
        ),
        inline=False
    )
    
    # Levier & Marge
    embed.add_field(
        name="📊 Levier & Marge",
        value=(
            f"**Levier:** {leverage}x\n"
            f"**Marge requise:** ${margin_required:,.2f}\n"
            f"**% capital immobilisé:** {capital_percent_used:.1f}%"
        ),
        inline=False
    )
    
    # Prix
    embed.add_field(name="💵 Entry", value=f"${entry:,.4f}", inline=True)
    embed.add_field(name="🛑 Stop Loss", value=f"${stop_loss:,.4f}\n({stop_distance_percent:.2f}%)", inline=True)
    embed.add_field(name="🎯 Target", value=f"${take_profit:,.4f}\n({target_distance_percent:.2f}%)", inline=True)
    
    # Position
    embed.add_field(
        name="📈 Position",
        value=(
            f"**Quantité:** {quantity:,.4f}\n"
            f"**Exposition totale:** ${position_value:,.2f}"
        ),
        inline=False
    )
    
    # Ratio R/R & Gains
    embed.add_field(
        name="💎 Ratio R/R",
        value=f"**1:{rr_ratio:.2f}**",
        inline=True
    )
    
    embed.add_field(
        name="💰 Profit potentiel",
        value=f"${potential_profit:,.2f}",
        inline=True
    )
    
    embed.add_field(
        name="📊 ROI sur marge",
        value=f"{roi_on_margin:,.1f}%",
        inline=True
    )
    
    # Séparateur
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━",
        value="** **",
        inline=False
    )
    
    # Conseil intelligent
    embed.add_field(
        name=f"{advice_emoji} CONSEIL",
        value=advice_text,
        inline=False
    )
    
    # Avertissements
    if warnings:
        embed.add_field(
            name="⚠️ POINTS D'ATTENTION",
            value="\n".join(warnings),
            inline=False
        )
    
    # Footer
    embed.set_footer(text="⚠️ Le levier amplifie les gains ET les pertes - Tradez prudemment")
    
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
        
        average_price = total_cost / total_quantity
        
        embed = discord.Embed(
            title="💰 Dollar Cost Averaging (DCA)",
            color=discord.Color.blue()
        )
        
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
# COMMANDES CRYPTO - ANALYSE DE MOYENNES MOBILES
# ============================================================================

async def crypto_autocomplete(ctx: discord.AutocompleteContext):
    """Autocomplétion pour les cryptos disponibles"""
    return crypto_manager.get_crypto_symbols()

@bot.slash_command(name="crypto_check", description="Vérifier l'état des moyennes mobiles d'une crypto")
async def crypto_check(
    ctx,
    crypto: str = discord.Option(
        str,
        description="Crypto à analyser",
        autocomplete=crypto_autocomplete
    ),
    timeframe: str = discord.Option(
        str,
        description="Timeframe d'analyse",
        choices=["5m", "15m", "1h", "4h", "1d"],
        default="1d"
    )
):
    await ctx.defer()
    
    binance_symbol = crypto_manager.get_binance_symbol(crypto)
    
    if not binance_symbol:
        await ctx.respond(f"❌ Crypto '{crypto}' non supportée! Utilisez `/crypto_list` pour voir les cryptos disponibles.")
        return
    
    try:
        analysis = crypto_analyzer.analyze_symbol(binance_symbol, interval=timeframe)
        
        if analysis['status'] != 'success':
            await ctx.respond(f"❌ Erreur: {analysis.get('message', 'Erreur inconnue')}")
            return
        
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
        
        embed = discord.Embed(
            title=f"📊 Analyse MA - {crypto.upper()} ({analysis['interval_label']})",
            description=f"**{status_emoji} {status_text}**",
            color=color
        )
        
        current_price = analysis['current_price']
        embed.add_field(
            name="💰 Prix Actuel",
            value=f"${current_price:,.2f}",
            inline=False
        )
        
        ma_values = analysis['ma_values']
        ma_text = ""
        for period in [112, 336, 375, 448, 750]:
            ma_value = ma_values.get(period, 0)
            indicator = "↑" if current_price > ma_value else "↓"
            ma_text += f"MA{period}: ${ma_value:,.2f} {indicator}\n"
        
        embed.add_field(
            name="📈 Moyennes Mobiles",
            value=ma_text,
            inline=True
        )
        
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
        
        current_order = analysis['current_order']
        order_text = " > ".join([f"MA{p}" for p in current_order])
        embed.add_field(
            name="🔄 Ordre actuel (par valeur)",
            value=f"`{order_text}`",
            inline=False
        )
        
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
        
        embed.set_footer(
            text=f"Binance | {analysis['data_points']} périodes | MAJ: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}"
        )
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors de l'analyse: {str(e)}")

@bot.slash_command(name="crypto_compare", description="Comparer toutes les cryptos")
async def crypto_compare(
    ctx,
    timeframe: str = discord.Option(
        str,
        description="Timeframe d'analyse",
        choices=["5m", "15m", "1h", "4h", "1d"],
        default="1d"
    )
):
    await ctx.defer()
    
    try:
        cryptos = crypto_manager.get_all_cryptos()
        
        if len(cryptos) == 0:
            await ctx.respond("❌ Aucune crypto configurée!")
            return
        
        timeframe_label = crypto_analyzer.get_interval_label(timeframe)
        
        embed = discord.Embed(
            title=f"📊 Comparaison Cryptos ({timeframe_label})",
            color=discord.Color.blue()
        )
        
        alerts = []
        
        for symbol, binance_symbol in cryptos.items():
            try:
                analysis = crypto_analyzer.analyze_symbol(binance_symbol, interval=timeframe)
                
                if analysis['status'] != 'success':
                    embed.add_field(
                        name=f"❌ {symbol}",
                        value="Erreur d'analyse",
                        inline=True
                    )
                    continue
                
                if analysis['aligned_bullish']:
                    status = "🟢 Haussier"
                    if analysis['is_compressed']:
                        alerts.append(f"{symbol}: Haussier + Compression!")
                elif analysis['aligned_bearish']:
                    status = "🔴 Baissier"
                    if analysis['is_compressed']:
                        alerts.append(f"{symbol}: Baissier + Compression!")
                else:
                    status = "🟠 Neutre"
                
                compression = "🔥 OUI" if analysis['is_compressed'] else "Non"
                
                embed.add_field(
                    name=f"{symbol}",
                    value=f"Prix: ${analysis['current_price']:,.2f}\n"
                          f"Alignement: {status}\n"
                          f"Compression: {compression}\n"
                          f"Écart: {analysis['compression_pct']:.2f}%",
                    inline=True
                )
                
            except Exception as e:
                embed.add_field(
                    name=f"❌ {symbol}",
                    value=f"Erreur: {str(e)[:50]}",
                    inline=True
                )
        
        if alerts:
            embed.add_field(
                name="🔥 ALERTES",
                value="\n".join(alerts),
                inline=False
            )
        
        embed.set_footer(text=f"Binance | {len(cryptos)} crypto(s) | Timeframe: {timeframe_label}")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")

# ============================================================================
# COMMANDES CRYPTO - GESTION
# ============================================================================

@bot.slash_command(name="crypto_search", description="Rechercher un symbole crypto sur Binance")
async def crypto_search(
    ctx,
    query: str = discord.Option(str, description="Terme de recherche (ex: DOGE, SOL, BTC)")
):
    await ctx.defer()
    
    try:
        results = crypto_searcher.search(query, limit=15)
        
        if not results:
            await ctx.respond(f"❌ Aucun résultat pour '{query}' sur Binance.")
            return
        
        embed = discord.Embed(
            title=f"🔍 Recherche Binance : '{query}'",
            description=f"Trouvé {len(results)} résultat(s)",
            color=discord.Color.blue()
        )
        
        usdt_pairs = []
        busd_pairs = []
        btc_pairs = []
        other_pairs = []
        
        for r in results:
            pair_text = f"`{r['symbol']}` ({r['baseAsset']}/{r['quoteAsset']})"
            
            if r['quoteAsset'] == 'USDT':
                usdt_pairs.append(pair_text)
            elif r['quoteAsset'] == 'BUSD':
                busd_pairs.append(pair_text)
            elif r['quoteAsset'] == 'BTC':
                btc_pairs.append(pair_text)
            else:
                other_pairs.append(pair_text)
        
        if usdt_pairs:
            embed.add_field(
                name="💵 Paires USDT (recommandé)",
                value="\n".join(usdt_pairs[:5]),
                inline=False
            )
        
        if busd_pairs:
            embed.add_field(
                name="💰 Paires BUSD",
                value="\n".join(busd_pairs[:3]),
                inline=False
            )
        
        if btc_pairs:
            embed.add_field(
                name="₿ Paires BTC",
                value="\n".join(btc_pairs[:3]),
                inline=False
            )
        
        if other_pairs:
            embed.add_field(
                name="🔸 Autres paires",
                value="\n".join(other_pairs[:3]),
                inline=False
            )
        
        embed.set_footer(text="💡 Utilisez /crypto_add pour ajouter une crypto")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors de la recherche: {str(e)}")

@bot.slash_command(name="crypto_list", description="Lister toutes les cryptos supportées")
async def crypto_list(ctx):
    await ctx.defer()
    
    cryptos = crypto_manager.get_all_cryptos()
    
    if len(cryptos) == 0:
        await ctx.respond("❌ Aucune crypto configurée!")
        return
    
    embed = discord.Embed(
        title="📋 Cryptos Supportées",
        description=f"Total: {len(cryptos)} crypto(s)",
        color=discord.Color.blue()
    )
    
    crypto_text = ""
    for symbol, binance_symbol in sorted(cryptos.items()):
        crypto_text += f"**{symbol}** → `{binance_symbol}`\n"
    
    embed.add_field(
        name="Liste",
        value=crypto_text,
        inline=False
    )
    
    embed.set_footer(text="💡 Source: Binance | Utilisez /crypto_add pour ajouter")
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="crypto_add", description="Ajouter une nouvelle crypto")
async def crypto_add(
    ctx,
    symbol: str = discord.Option(str, description="Symbole court (ex: BTC, SOL, DOGE)"),
    binance_symbol: str = discord.Option(
        str, 
        description="Symbole Binance (optionnel, auto-détecté si vide)",
        required=False,
        default=None
    )
):
    await ctx.defer()
    
    symbol = symbol.upper().strip()
    
    if crypto_manager.crypto_exists(symbol):
        await ctx.respond(f"❌ La crypto `{symbol}` existe déjà!")
        return
    
    if not binance_symbol:
        await ctx.respond(f"🔄 Recherche automatique de `{symbol}` sur Binance...")
        
        binance_symbol = crypto_searcher.get_best_match(symbol)
        
        if not binance_symbol:
            await ctx.edit(
                content=f"❌ Impossible de trouver automatiquement `{symbol}`.\n"
                       f"💡 Utilisez `/crypto_search {symbol}` pour chercher le symbole exact."
            )
            return
        
        await ctx.edit(content=f"✅ Trouvé automatiquement : `{binance_symbol}`\n🔄 Vérification...")
    else:
        binance_symbol = binance_symbol.upper().strip()
        
        if not crypto_manager.validate_binance_symbol(binance_symbol):
            await ctx.respond(
                "❌ Symbole Binance invalide!\n"
                "Le symbole doit se terminer par: USDT, BUSD, BTC, ou ETH\n"
                f"💡 Utilisez `/crypto_search {symbol}` pour trouver le bon symbole."
            )
            return
        
        await ctx.respond(f"🔄 Vérification de `{binance_symbol}` sur Binance...")
    
    if not crypto_analyzer.test_symbol_exists(binance_symbol):
        await ctx.edit(
            content=f"❌ Le symbole `{binance_symbol}` n'existe pas sur Binance!\n"
                   f"💡 Utilisez `/crypto_search {symbol}` pour trouver le bon symbole."
        )
        return
    
    if crypto_manager.add_crypto(symbol, binance_symbol):
        sync_alerts_with_managers()
        
        embed = discord.Embed(
            title="✅ Crypto Ajoutée",
            color=discord.Color.green()
        )
        embed.add_field(name="Symbole", value=symbol, inline=True)
        embed.add_field(name="Binance", value=binance_symbol, inline=True)
        embed.set_footer(text=f"Total: {crypto_manager.get_count()} crypto(s) • Alertes synchronisées ✓")
        
        await ctx.edit(content=None, embed=embed)
    else:
        await ctx.edit(content="❌ Erreur lors de l'ajout")

@bot.slash_command(name="crypto_remove", description="Supprimer une crypto")
async def crypto_remove(
    ctx,
    crypto: str = discord.Option(
        str,
        description="Crypto à supprimer",
        autocomplete=crypto_autocomplete
    )
):
    await ctx.defer()
    
    crypto = crypto.upper().strip()
    
    if not crypto_manager.crypto_exists(crypto):
        await ctx.respond(f"❌ La crypto `{crypto}` n'existe pas!")
        return
    
    if crypto_manager.remove_crypto(crypto):
        # ✅ SYNCHRONISER LES ALERTES ← AJOUT ICI
        sync_alerts_with_managers()
        
        embed = discord.Embed(
            title="✅ Crypto Supprimée",
            description=f"La crypto **{crypto}** a été supprimée",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Total: {crypto_manager.get_count()} crypto(s) restante(s) • Alertes synchronisées ✓")
        
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("❌ Erreur lors de la suppression")

@bot.slash_command(name="alerts_sync", description="Synchroniser les alertes avec les actifs configurés")
async def alerts_sync(ctx):
    await ctx.defer()
    
    try:
        # Avant sync
        before_crypto_count = len(volume_monitor.config['assets']['crypto'])
        before_stock_count = len(volume_monitor.config['assets']['stocks'])
        
        # Synchroniser
        sync_alerts_with_managers()
        
        # Après sync
        after_crypto_count = len(volume_monitor.config['assets']['crypto'])
        after_stock_count = len(volume_monitor.config['assets']['stocks'])
        
        embed = discord.Embed(
            title="✅ Synchronisation des Alertes",
            description="Les alertes ont été synchronisées avec vos actifs configurés",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📊 Cryptos",
            value=f"Avant: {before_crypto_count}\nAprès: {after_crypto_count}",
            inline=True
        )
        
        embed.add_field(
            name="📈 Stocks",
            value=f"Avant: {before_stock_count}\nAprès: {after_stock_count}",
            inline=True
        )
        
        embed.add_field(
            name="\u200b",
            value="\u200b",
            inline=True
        )
        
        # Liste des actifs
        crypto_list = ", ".join([s.replace('USDT', '') for s in volume_monitor.config['assets']['crypto']])
        stock_list = ", ".join(volume_monitor.config['assets']['stocks'])
        
        embed.add_field(
            name="₿ Cryptos surveillées",
            value=crypto_list or "Aucune",
            inline=False
        )
        
        embed.add_field(
            name="📈 Stocks surveillés",
            value=stock_list or "Aucun",
            inline=False
        )
        
        embed.set_footer(text="Les alertes de volume et MA sont maintenant à jour")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors de la synchronisation: {str(e)}")
# ============================================================================
# COMMANDES STOCKS - ANALYSE DE MOYENNES MOBILES
# ============================================================================

async def stock_autocomplete(ctx: discord.AutocompleteContext):
    """Autocomplétion pour les stocks disponibles"""
    return stock_manager.get_stock_symbols()

@bot.slash_command(name="stock_check", description="Vérifier l'état des moyennes mobiles d'une action/indice")
async def stock_check(
    ctx,
    stock: str = discord.Option(
        str,
        description="Action/Indice à analyser",
        autocomplete=stock_autocomplete
    ),
    timeframe: str = discord.Option(
        str,
        description="Timeframe d'analyse",
        choices=["5m", "15m", "1h", "4h", "1d"],
        default="1d"
    )
):
    await ctx.defer()
    
    yfinance_symbol = stock_manager.get_yfinance_symbol(stock)
    
    if not yfinance_symbol:
        await ctx.respond(f"❌ Stock '{stock}' non supporté! Utilisez `/stock_list` pour voir les stocks disponibles.")
        return
    
    try:
        analysis = stock_analyzer.analyze_symbol(yfinance_symbol, interval=timeframe)
        
        if analysis['status'] != 'success':
            await ctx.respond(f"❌ Erreur: {analysis.get('message', 'Erreur inconnue')}")
            return
        
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
        
        embed = discord.Embed(
            title=f"📊 Analyse MA - {stock.upper()} ({analysis['interval_label']})",
            description=f"**{status_emoji} {status_text}**",
            color=color
        )
        
        current_price = analysis['current_price']
        embed.add_field(
            name="💰 Prix Actuel",
            value=f"${current_price:,.2f}",
            inline=False
        )
        
        ma_values = analysis['ma_values']
        ma_text = ""
        for period in [112, 336, 375, 448, 750]:
            ma_value = ma_values.get(period, 0)
            indicator = "↑" if current_price > ma_value else "↓"
            ma_text += f"MA{period}: ${ma_value:,.2f} {indicator}\n"
        
        embed.add_field(
            name="📈 Moyennes Mobiles",
            value=ma_text,
            inline=True
        )
        
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
        
        current_order = analysis['current_order']
        order_text = " > ".join([f"MA{p}" for p in current_order])
        embed.add_field(
            name="🔄 Ordre actuel (par valeur)",
            value=f"`{order_text}`",
            inline=False
        )
        
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
        
        embed.set_footer(
            text=f"Yahoo Finance | {analysis['data_points']} périodes | MAJ: {analysis['timestamp'].strftime('%Y-%m-%d')}"
        )
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors de l'analyse: {str(e)}")

@bot.slash_command(name="stock_compare", description="Comparer tous les stocks/indices")
async def stock_compare(
    ctx,
    timeframe: str = discord.Option(
        str,
        description="Timeframe d'analyse",
        choices=["5m", "15m", "1h", "4h", "1d"],
        default="1d"
    )
):
    await ctx.defer()
    
    try:
        stocks = stock_manager.get_all_stocks()
        
        if len(stocks) == 0:
            await ctx.respond("❌ Aucun stock configuré!")
            return
        
        timeframe_label = stock_analyzer.get_interval_label(timeframe)
        
        embed = discord.Embed(
            title=f"📊 Comparaison Stocks ({timeframe_label})",
            color=discord.Color.blue()
        )
        
        alerts = []
        
        for symbol, yfinance_symbol in stocks.items():
            try:
                analysis = stock_analyzer.analyze_symbol(yfinance_symbol, interval=timeframe)
                
                if analysis['status'] != 'success':
                    embed.add_field(
                        name=f"❌ {symbol}",
                        value="Erreur d'analyse",
                        inline=True
                    )
                    continue
                
                if analysis['aligned_bullish']:
                    status = "🟢 Haussier"
                    if analysis['is_compressed']:
                        alerts.append(f"{symbol}: Haussier + Compression!")
                elif analysis['aligned_bearish']:
                    status = "🔴 Baissier"
                    if analysis['is_compressed']:
                        alerts.append(f"{symbol}: Baissier + Compression!")
                else:
                    status = "🟠 Neutre"
                
                compression = "🔥 OUI" if analysis['is_compressed'] else "Non"
                
                embed.add_field(
                    name=f"{symbol}",
                    value=f"Prix: ${analysis['current_price']:,.2f}\n"
                          f"Alignement: {status}\n"
                          f"Compression: {compression}\n"
                          f"Écart: {analysis['compression_pct']:.2f}%",
                    inline=True
                )
                
            except Exception as e:
                embed.add_field(
                    name=f"❌ {symbol}",
                    value=f"Erreur: {str(e)[:50]}",
                    inline=True
                )
        
        if alerts:
            embed.add_field(
                name="🔥 ALERTES",
                value="\n".join(alerts),
                inline=False
            )
        
        embed.set_footer(text=f"Yahoo Finance | {len(stocks)} stock(s) | Timeframe: {timeframe_label}")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")

# ============================================================================
# COMMANDES STOCKS - GESTION
# ============================================================================

@bot.slash_command(name="stock_search", description="Rechercher un symbole stock/indice sur Yahoo Finance")
async def stock_search(
    ctx,
    query: str = discord.Option(str, description="Terme de recherche (ex: TSLA, AAPL, SPX)")
):
    await ctx.defer()
    
    try:
        results = stock_searcher.search(query, limit=10)
        
        if not results:
            await ctx.respond(f"❌ Aucun résultat pour '{query}' sur Yahoo Finance.\n"
                            f"💡 Essayez sur https://finance.yahoo.com")
            return
        
        embed = discord.Embed(
            title=f"🔍 Recherche Yahoo Finance : '{query}'",
            description=f"Trouvé {len(results)} résultat(s)",
            color=discord.Color.blue()
        )
        
        result_text = ""
        for r in results:
            yf_sym = r['yfinance_symbol']
            name = r['name']
            result_text += f"**{r['symbol']}** → `{yf_sym}`\n└ {name}\n\n"
        
        embed.add_field(
            name="📊 Résultats",
            value=result_text,
            inline=False
        )
        
        embed.set_footer(text="💡 Utilisez /stock_add pour ajouter un stock")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors de la recherche: {str(e)}")

@bot.slash_command(name="stock_list", description="Lister tous les stocks/indices supportés")
async def stock_list(ctx):
    await ctx.defer()
    
    stocks = stock_manager.get_all_stocks()
    
    if len(stocks) == 0:
        await ctx.respond("❌ Aucun stock configuré!")
        return
    
    embed = discord.Embed(
        title="📋 Stocks/Indices Supportés",
        description=f"Total: {len(stocks)} stock(s)",
        color=discord.Color.blue()
    )
    
    stock_text = ""
    for symbol, yfinance_symbol in sorted(stocks.items()):
        stock_text += f"**{symbol}** → `{yfinance_symbol}`\n"
    
    embed.add_field(
        name="Liste",
        value=stock_text,
        inline=False
    )
    
    embed.set_footer(text="💡 Source: Yahoo Finance | Utilisez /stock_add pour ajouter")
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="stock_add", description="Ajouter un nouveau stock/indice")
async def stock_add(
    ctx,
    symbol: str = discord.Option(str, description="Symbole court (ex: AAPL, SPX, NVDA)"),
    yfinance_symbol: str = discord.Option(
        str,
        description="Symbole yfinance (optionnel, auto-détecté si vide)",
        required=False,
        default=None
    )
):
    await ctx.defer()
    
    symbol = symbol.upper().strip()
    
    if stock_manager.stock_exists(symbol):
        await ctx.respond(f"❌ Le stock `{symbol}` existe déjà!")
        return
    
    if not yfinance_symbol:
        await ctx.respond(f"🔄 Recherche automatique de `{symbol}` sur Yahoo Finance...")
        
        yfinance_symbol = stock_searcher.get_best_match(symbol)
        
        if not yfinance_symbol:
            await ctx.edit(
                content=f"❌ Impossible de trouver automatiquement `{symbol}`.\n"
                       f"💡 Utilisez `/stock_search {symbol}` pour chercher le symbole exact."
            )
            return
        
        await ctx.edit(content=f"✅ Trouvé automatiquement : `{yfinance_symbol}`\n🔄 Vérification...")
    else:
        yfinance_symbol = yfinance_symbol.strip()
        
        if not stock_manager.validate_yfinance_symbol(yfinance_symbol):
            await ctx.respond("❌ Symbole yfinance invalide!")
            return
        
        await ctx.respond(f"🔄 Vérification de `{yfinance_symbol}` sur Yahoo Finance...")
    
    if not stock_analyzer.test_symbol_exists(yfinance_symbol):
        await ctx.edit(
            content=f"❌ Le symbole `{yfinance_symbol}` n'existe pas sur Yahoo Finance!\n"
                   f"💡 Utilisez `/stock_search {symbol}` pour trouver le bon symbole."
        )
        return
    
    if stock_manager.add_stock(symbol, yfinance_symbol):
        # ✅ SYNCHRONISER LES ALERTES ← AJOUT ICI
        sync_alerts_with_managers()
        
        embed = discord.Embed(
            title="✅ Stock Ajouté",
            color=discord.Color.green()
        )
        embed.add_field(name="Symbole", value=symbol, inline=True)
        embed.add_field(name="Yahoo Finance", value=yfinance_symbol, inline=True)
        embed.set_footer(text=f"Total: {stock_manager.get_count()} stock(s) • Alertes synchronisées ✓")
        
        await ctx.edit(content=None, embed=embed)
    else:
        await ctx.edit(content="❌ Erreur lors de l'ajout")

@bot.slash_command(name="stock_remove", description="Supprimer un stock/indice")
async def stock_remove(
    ctx,
    stock: str = discord.Option(
        str,
        description="Stock à supprimer",
        autocomplete=stock_autocomplete
    )
):
    await ctx.defer()
    
    stock = stock.upper().strip()
    
    if not stock_manager.stock_exists(stock):
        await ctx.respond(f"❌ Le stock `{stock}` n'existe pas!")
        return
    
    if stock_manager.remove_stock(stock):
        # ✅ SYNCHRONISER LES ALERTES ← AJOUT ICI
        sync_alerts_with_managers()
        
        embed = discord.Embed(
            title="✅ Stock Supprimé",
            description=f"Le stock **{stock}** a été supprimé",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Total: {stock_manager.get_count()} stock(s) restant(s) • Alertes synchronisées ✓")
        
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("❌ Erreur lors de la suppression")

# ============================================================================
# COMMANDES DE SURVEILLANCE DES VOLUMES
# ============================================================================

@bot.slash_command(name="volume_status", description="Afficher l'état actuel des volumes")
async def volume_status(ctx):
    await ctx.defer()
    
    try:
        status = volume_monitor.get_current_status()
        
        embed = discord.Embed(
            title="📊 État des Volumes",
            description="BTC/ETH + MAG7",
            color=discord.Color.blue()
        )
        
        if status['crypto']:
            crypto_text = ""
            for data in status['crypto']:
                symbol = data['symbol'].replace('USDT', '')
                emoji = "🔥" if data['increase_24h'] >= 150 else "📊"
                crypto_text += f"{emoji} **{symbol}**\n"
                crypto_text += f"└ Volume: {data['current_volume']:,.0f}\n"
                crypto_text += f"└ vs 24h: **{data['increase_24h']:+.1f}%**\n"
                crypto_text += f"└ vs 7j: {data['increase_7d']:+.1f}%\n\n"
            
            embed.add_field(
                name="₿ Cryptos",
                value=crypto_text,
                inline=False
            )
        
        if status['stocks']:
            stock_text = ""
            for data in status['stocks']:
                emoji = "🔥" if data['increase_24h'] >= 150 else "📈"
                stock_text += f"{emoji} **{data['symbol']}**\n"
                stock_text += f"└ Volume: {data['current_volume']:,.0f}\n"
                stock_text += f"└ vs 24h: **{data['increase_24h']:+.1f}%**\n"
                stock_text += f"└ vs 7j: {data['increase_7d']:+.1f}%\n\n"
            
            embed.add_field(
                name="📈 MAG7 Stocks",
                value=stock_text,
                inline=False
            )
        
        config = volume_monitor.config
        embed.set_footer(
            text=f"Seuils: {config['thresholds']['moderate']}% / {config['thresholds']['high']}% / {config['thresholds']['critical']}% • Check: {config['check_interval_minutes']}min"
        )
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")

@bot.slash_command(name="volume_config", description="Afficher la configuration de surveillance")
async def volume_config_cmd(ctx):
    await ctx.defer()
    
    try:
        config = volume_monitor.config
        
        embed = discord.Embed(
            title="⚙️ Configuration Surveillance Volumes",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🕐 Fréquence",
            value=f"Toutes les {config['check_interval_minutes']} minutes",
            inline=True
        )
        
        embed.add_field(
            name="⏳ Cooldown",
            value=f"{config['cooldown_minutes']} minutes",
            inline=True
        )
        
        embed.add_field(
            name="\u200b",
            value="\u200b",
            inline=True
        )
        
        embed.add_field(
            name="⚠️ Seuil Modéré",
            value=f"+{config['thresholds']['moderate']}%",
            inline=True
        )
        
        embed.add_field(
            name="🔥 Seuil Élevé",
            value=f"+{config['thresholds']['high']}%",
            inline=True
        )
        
        embed.add_field(
            name="🚨 Seuil Critique",
            value=f"+{config['thresholds']['critical']}%",
            inline=True
        )
        
        crypto_list = ", ".join([s.replace('USDT', '') for s in config['assets']['crypto']])
        embed.add_field(
            name="₿ Cryptos surveillées",
            value=crypto_list,
            inline=False
        )
        
        stock_list = ", ".join(config['assets']['stocks'])
        embed.add_field(
            name="📈 Stocks surveillés (MAG7)",
            value=stock_list,
            inline=False
        )
        
        embed.set_footer(text="💡 Les alertes sont envoyées sur le channel configuré")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")

@bot.slash_command(name="volume_test", description="Tester la surveillance immédiatement")
async def volume_test(ctx):
    await ctx.defer()
    
    try:
        await ctx.respond("🔍 Lancement du test de surveillance...")
        
        loop = asyncio.get_event_loop()
        alerts = await loop.run_in_executor(None, volume_monitor.check_all_assets)
        
        if alerts:
            alert_text = "\n".join([
                f"• {a['symbol']}: {a['level']} (+{a['increase']:.1f}%)"
                for a in alerts
            ])
            await ctx.edit(content=f"✅ Test terminé!\n\n**Alertes envoyées:**\n{alert_text}")
        else:
            await ctx.edit(content="✅ Test terminé!\n\nℹ️ Aucun pic détecté pour le moment.")
            
    except Exception as e:
        await ctx.edit(content=f"❌ Erreur lors du test: {str(e)}")

# ============================================================================
# COMMANDES DE SURVEILLANCE DES CROISEMENTS MA
# ============================================================================

@bot.slash_command(name="ma_alerts_config", description="Configuration des alertes MA")
async def ma_alerts_config(ctx):
    await ctx.defer()
    
    try:
        config = ma_alert_monitor.config
        
        embed = discord.Embed(
            title="⚙️ Configuration Alertes MA",
            description="Surveillance des croisements, alignements et compressions",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🕐 Paramètres",
            value=(
                f"**Fréquence:** Toutes les {config['check_interval_minutes']} minutes\n"
                f"**Cooldown:** {config['cooldown_hours']} heures\n"
                f"**Seuil compression:** < {config['compression_threshold']}%"
            ),
            inline=False
        )
        
        # Timeframes
        tf_text = ", ".join(config['timeframes'])
        embed.add_field(
            name="⏰ Timeframes surveillés",
            value=tf_text,
            inline=False
        )
        
        # Types d'alertes
        alert_types = []
        if config['alert_types']['golden_cross']:
            alert_types.append("✅ Golden Cross")
        if config['alert_types']['death_cross']:
            alert_types.append("✅ Death Cross")
        if config['alert_types']['alignment']:
            alert_types.append("✅ Alignements")
        if config['alert_types']['compression']:
            alert_types.append("✅ Compressions")
        
        embed.add_field(
            name="🔔 Types d'alertes actives",
            value="\n".join(alert_types),
            inline=False
        )
        
        # Systèmes MA
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━",
            value="** **",
            inline=False
        )
        
        embed.add_field(
            name="📈 Système 1 (Court terme)",
            value="**MA:** 13, 25, 32, 100, 200, 300\n**Pairs surveillées:** 13/25, 25/32, 32/100, 100/200, 200/300",
            inline=False
        )
        
        embed.add_field(
            name="📈 Système 2 (Long terme)",
            value="**MA:** 112, 336, 375, 448, 750\n**Pairs surveillées:** 112/336, 336/375, 375/448, 448/750",
            inline=False
        )
        
        # Assets
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━",
            value="** **",
            inline=False
        )
        
        crypto_list = ", ".join([s.replace('USDT', '') for s in config['assets']['crypto']])
        stock_list = ", ".join(config['assets']['stocks'])
        
        embed.add_field(
            name="₿ Cryptos",
            value=crypto_list,
            inline=True
        )
        
        embed.add_field(
            name="📈 Stocks",
            value=stock_list,
            inline=True
        )
        
        embed.set_footer(text="💡 Alertes envoyées automatiquement sur le channel configuré")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")

@bot.slash_command(name="ma_alerts_test", description="Tester la surveillance MA immédiatement")
async def ma_alerts_test(ctx):
    await ctx.defer()
    
    try:
        await ctx.respond("🔍 Lancement du test de surveillance MA...\n⏳ Cela peut prendre 30-60 secondes...")
        
        loop = asyncio.get_event_loop()
        alerts = await loop.run_in_executor(None, ma_alert_monitor.check_all_assets)
        
        if alerts:
            alert_text = ""
            for a in alerts:
                compression_info = f" ({a.get('compression', 0):.2f}%)" if 'compression' in a else ""
                alert_text += f"• **{a['symbol']}**: {a['type']} ({a['system']}){compression_info}\n"
            
            embed = discord.Embed(
                title="✅ Test terminé - Alertes envoyées",
                description=alert_text,
                color=discord.Color.green()
            )
            await ctx.edit(content=None, embed=embed)
        else:
            embed = discord.Embed(
                title="✅ Test terminé",
                description="ℹ️ Aucun croisement/alignement/compression détecté pour le moment.",
                color=discord.Color.blue()
            )
            await ctx.edit(content=None, embed=embed)
            
    except Exception as e:
        await ctx.edit(content=f"❌ Erreur lors du test: {str(e)}")

@bot.slash_command(name="ma_alerts_status", description="Voir les dernières alertes envoyées")
async def ma_alerts_status(ctx):
    await ctx.defer()
    
    try:
        history = ma_alert_monitor.alert_history
        
        if not history:
            await ctx.respond("ℹ️ Aucune alerte MA envoyée récemment.")
            return
        
        # Trier par date (plus récent en premier)
        sorted_alerts = sorted(history.items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="📋 Historique des Alertes MA",
            description=f"Dernières {min(len(sorted_alerts), 10)} alertes",
            color=discord.Color.blue()
        )
        
        for i, (alert_key, timestamp) in enumerate(sorted_alerts[:10], 1):
            # Parser le alert_key
            parts = alert_key.split('_')
            symbol = parts[0].replace('USDT', '').replace('BUSD', '')
            timeframe = parts[1] if len(parts) > 1 else 'N/A'
            alert_type = parts[-1] if len(parts) > 2 else 'N/A'
            
            time_ago = datetime.now() - timestamp
            hours_ago = int(time_ago.total_seconds() / 3600)
            
            embed.add_field(
                name=f"{i}. {symbol} - {alert_type}",
                value=f"Timeframe: {timeframe}\nIl y a {hours_ago}h",
                inline=True
            )
        
        embed.set_footer(text=f"Cooldown: {ma_alert_monitor.config['cooldown_hours']}h entre chaque alerte")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur: {str(e)}")
# ============================================================================
# COMMANDE HELP
# ============================================================================

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
    
    # Analyse Crypto
    embed.add_field(
        name="₿ Analyse Crypto (Binance)",
        value=(
            "`/crypto_check <crypto> [timeframe]` - Analyser les MA\n"
            "  └ Timeframes: 5m, 15m, 1h, 4h, 1d\n"
            "`/crypto_compare [timeframe]` - Comparer toutes les cryptos\n"
            "`/crypto_list` - Lister les cryptos\n"
            "`/crypto_search <terme>` - Rechercher un symbole 🔍\n"
            "`/crypto_add <symbol>` - Ajouter (auto-détection) 🆕\n"
            "`/crypto_remove` - Supprimer une crypto"
        ),
        inline=False
    )
    
    # Analyse Stocks
    embed.add_field(
        name="📈 Analyse Stocks (Yahoo Finance)",
        value=(
            "`/stock_check <stock> [timeframe]` - Analyser les MA\n"
            "  └ Timeframes: 5m, 15m, 1h, 4h, 1d\n"
            "`/stock_compare [timeframe]` - Comparer tous les stocks\n"
            "`/stock_list` - Lister les stocks\n"
            "`/stock_search <terme>` - Rechercher un symbole 🔍\n"
            "`/stock_add <symbol>` - Ajouter (auto-détection) 🆕\n"
            "`/stock_remove` - Supprimer un stock"
        ),
        inline=False
    )
    
    # Surveillance Volumes
    embed.add_field(
        name="📊 Surveillance Volumes",
        value=(
            "`/volume_status` - État actuel des volumes\n"
            "`/volume_config` - Configuration des alertes\n"
            "`/volume_test` - Tester la surveillance\n"
            "└ Alertes auto toutes les 15min: BTC/ETH + MAG7"
        ),
        inline=False
    )
    
    # Détection automatique
    embed.add_field(
        name="🎯 Détection Automatique",
        value=(
            "✅ Alignement haussier/baissier\n"
            "✅ Compression des moyennes (<5%)\n"
            "✅ Position du prix vs MA\n"
            "✅ Pics de volume (+150%/+200%/+300%)\n"
            "```Moyennes: MA13, MA25, MA32, MA100, MA200, MA300```"
        ),
        inline=False
    )
    
    # Exemples
    embed.add_field(
        name="💡 Exemples d'utilisation",
        value=(
            "**Recherche + Ajout:**\n"
            "`/crypto_search doge` → Trouver DOGEUSDT\n"
            "`/crypto_add symbol:DOGE` → Ajout auto ✨\n\n"
            "**Analyse:**\n"
            "`/crypto_check crypto:BTC timeframe:1h`\n"
            "`/stock_check stock:AAPL timeframe:1d`\n\n"
            "**Surveillance:**\n"
            "`/volume_status` → État des volumes\n"
            "`/volume_test` → Test immédiat"
        ),
        inline=False
    )

    embed.add_field(
    name="📈 Alertes Croisements MA",
    value=(
        "`/ma_alerts_config` - Configuration\n"
        "`/ma_alerts_test` - Test immédiat\n"
        "`/ma_alerts_status` - Historique\n"
        "└ 2 systèmes: Court (13-300) + Long (112-750)"
    ),
    inline=False
)
    
    embed.set_footer(
        text=f"💡 {crypto_manager.get_count()} crypto(s) | {stock_manager.get_count()} stock(s) | Surveillance: ON 🔥"
    )
    
    await ctx.respond(embed=embed)

# Lancer le bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ DISCORD_TOKEN non trouvé dans .env")
    else:
        bot.run(TOKEN)

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Créer le bot avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} est connecté et prêt !')
    print(f'📊 Connecté à {len(bot.guilds)} serveur(s)')
    print('🔄 Synchronisation des commandes...')
    await bot.sync_commands()
    print('✅ Commandes synchronisées !')

# ==========================================
# CALCULATEUR 1 : TAILLE DE POSITION
# ==========================================

@bot.slash_command(
    name="position",
    description="Calcule la taille de position optimale selon votre risque"
)
async def position(
    ctx,
    capital: discord.Option(float, "Capital total disponible (ex: 10000)", required=True),
    risk_percent: discord.Option(float, "Pourcentage de risque par trade (ex: 2 pour 2%)", required=True),
    entry: discord.Option(float, "Prix d'entrée prévu", required=True),
    stop_loss: discord.Option(float, "Prix du stop loss", required=True)
):
    try:
        # Validation des inputs
        if capital <= 0:
            await ctx.respond("❌ Le capital doit être positif !", ephemeral=True)
            return
        if risk_percent <= 0 or risk_percent > 100:
            await ctx.respond("❌ Le pourcentage de risque doit être entre 0 et 100 !", ephemeral=True)
            return
        if entry <= 0 or stop_loss <= 0:
            await ctx.respond("❌ Les prix doivent être positifs !", ephemeral=True)
            return
        
        # Calculs
        risk_amount = capital * (risk_percent / 100)
        risk_per_share = abs(entry - stop_loss)
        
        if risk_per_share == 0:
            await ctx.respond("❌ Le prix d'entrée et le stop loss ne peuvent pas être identiques !", ephemeral=True)
            return
        
        position_size = risk_amount / risk_per_share
        investment = position_size * entry
        
        # Déterminer si c'est un long ou short
        position_type = "LONG 📈" if stop_loss < entry else "SHORT 📉"
        color = discord.Color.green() if stop_loss < entry else discord.Color.red()
        
        # Créer l'embed
        embed = discord.Embed(
            title="💰 Calculateur de Position",
            description=f"**Type de position : {position_type}**",
            color=color
        )
        
        embed.add_field(
            name="📊 Paramètres",
            value=f"```\nCapital total    : ${capital:,.2f}\nRisque accepté   : {risk_percent}%\nMontant à risquer: ${risk_amount:,.2f}```",
            inline=False
        )
        
        embed.add_field(
            name="📍 Prix",
            value=f"```\nEntrée     : ${entry:,.2f}\nStop Loss  : ${stop_loss:,.2f}\nRisque/unité: ${risk_per_share:,.2f}```",
            inline=False
        )
        
        embed.add_field(
            name="✅ Résultat",
            value=f"```\n🎯 Taille position : {position_size:,.2f} unités\n💵 Investissement  : ${investment:,.2f}\n📉 Perte maximale  : ${risk_amount:,.2f} ({risk_percent}%)```",
            inline=False
        )
        
        embed.set_footer(text="💡 Utilisez /help pour voir toutes les commandes")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors du calcul : {str(e)}", ephemeral=True)

# ==========================================
# CALCULATEUR 2 : RATIO RISQUE/RENDEMENT
# ==========================================

@bot.slash_command(
    name="rr",
    description="Calcule le ratio risque/rendement (Risk/Reward)"
)
async def risk_reward(
    ctx,
    entry: discord.Option(float, "Prix d'entrée", required=True),
    stop_loss: discord.Option(float, "Prix du stop loss", required=True),
    target: discord.Option(float, "Prix cible (take profit)", required=True)
):
    try:
        # Validation
        if entry <= 0 or stop_loss <= 0 or target <= 0:
            await ctx.respond("❌ Tous les prix doivent être positifs !", ephemeral=True)
            return
        
        # Calculs
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        
        if risk == 0:
            await ctx.respond("❌ Le stop loss ne peut pas être égal au prix d'entrée !", ephemeral=True)
            return
        
        rr_ratio = reward / risk
        
        # Déterminer le type de trade
        is_long = stop_loss < entry < target
        is_short = stop_loss > entry > target
        
        if not (is_long or is_short):
            await ctx.respond("❌ Configuration invalide ! Vérifiez l'ordre des prix.\n💡 Long: SL < Entry < Target\n💡 Short: SL > Entry > Target", ephemeral=True)
            return
        
        position_type = "LONG 📈" if is_long else "SHORT 📉"
        
        # Couleur selon le ratio
        if rr_ratio >= 3:
            color = discord.Color.green()
            verdict = "✅ Excellent ratio !"
        elif rr_ratio >= 2:
            color = discord.Color.blue()
            verdict = "👍 Bon ratio"
        elif rr_ratio >= 1:
            color = discord.Color.gold()
            verdict = "⚠️ Ratio acceptable"
        else:
            color = discord.Color.red()
            verdict = "❌ Ratio défavorable"
        
        # Créer l'embed
        embed = discord.Embed(
            title="⚖️ Ratio Risque/Rendement",
            description=f"**Type : {position_type}**",
            color=color
        )
        
        embed.add_field(
            name="📍 Prix",
            value=f"```\nEntrée     : ${entry:,.2f}\nStop Loss  : ${stop_loss:,.2f}\nCible      : ${target:,.2f}```",
            inline=False
        )
        
        embed.add_field(
            name="📊 Analyse",
            value=f"```\nRisque    : ${risk:,.2f}\nGain espéré: ${reward:,.2f}```",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Ratio R/R",
            value=f"```\n{rr_ratio:.2f} : 1\n\n{verdict}```",
            inline=False
        )
        
        embed.add_field(
            name="💡 Signification",
            value=f"Pour chaque $1 risqué, vous pouvez gagner ${rr_ratio:.2f}",
            inline=False
        )
        
        embed.set_footer(text="💡 Un ratio ≥ 2:1 est généralement recommandé")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors du calcul : {str(e)}", ephemeral=True)

# ==========================================
# CALCULATEUR 3 : DOLLAR COST AVERAGING (DCA)
# ==========================================

@bot.slash_command(
    name="dca",
    description="Calcule le prix moyen d'achat après plusieurs entrées"
)
async def dca(
    ctx,
    positions: discord.Option(str, "Format: prix1,quantité1 prix2,quantité2 (ex: 50,100 45,200 48,150)", required=True)
):
    try:
        # Parser les positions
        entries = []
        for entry_str in positions.split():
            try:
                price_str, qty_str = entry_str.split(',')
                price = float(price_str)
                qty = float(qty_str)
                if price <= 0 or qty <= 0:
                    await ctx.respond("❌ Les prix et quantités doivent être positifs !", ephemeral=True)
                    return
                entries.append((price, qty))
            except ValueError:
                await ctx.respond(f"❌ Format invalide ! Utilisez : `prix,quantité prix,quantité`\nExemple : `50,100 45,200 48,150`", ephemeral=True)
                return
        
        if len(entries) == 0:
            await ctx.respond("❌ Aucune position valide trouvée !", ephemeral=True)
            return
        
        # Calculs
        total_cost = sum(price * qty for price, qty in entries)
        total_quantity = sum(qty for _, qty in entries)
        average_price = total_cost / total_quantity
        
        # Prix min et max
        prices = [price for price, _ in entries]
        min_price = min(prices)
        max_price = max(prices)
        
        # Créer l'embed
        embed = discord.Embed(
            title="📊 Dollar Cost Averaging (DCA)",
            description=f"Analyse de vos {len(entries)} entrées",
            color=discord.Color.blue()
        )
        
        # Détail des entrées
        entries_detail = ""
        for i, (price, qty) in enumerate(entries, 1):
            cost = price * qty
            entries_detail += f"Entrée {i}: {qty:,.2f} × ${price:,.2f} = ${cost:,.2f}\n"
        
        embed.add_field(
            name="📍 Détail des Entrées",
            value=f"```\n{entries_detail}```",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Résultat",
            value=f"```\n💰 Prix moyen      : ${average_price:.4f}\n📦 Quantité totale : {total_quantity:,.2f}\n💵 Investissement  : ${total_cost:,.2f}```",
            inline=False
        )
        
        embed.add_field(
            name="📈 Statistiques",
            value=f"```\nPrix le plus bas  : ${min_price:,.2f}\nPrix le plus haut : ${max_price:,.2f}\nÉcart            : ${max_price - min_price:,.2f}```",
            inline=False
        )
        
        embed.set_footer(text="💡 Le DCA permet de lisser le prix d'achat dans le temps")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors du calcul : {str(e)}", ephemeral=True)


# ==========================================
# CALCULATEUR 4 : POSITION AVEC LEVIER
# ==========================================

@bot.slash_command(
    name="leverage",
    description="Calcule une position avec effet de levier (futures/margin trading)"
)
async def leverage(
    ctx,
    capital: discord.Option(float, "Capital total disponible", required=True),
    leverage_amount: discord.Option(
        int, 
        "Effet de levier (ex: 10 pour 10x)", 
        required=True,
        choices=[1, 2, 5, 10, 20, 50, 100, 125]
    ),
    risk_percent: discord.Option(float, "Pourcentage de risque par trade (ex: 2 pour 2%)", required=True),
    entry: discord.Option(float, "Prix d'entrée prévu", required=True),
    stop_loss: discord.Option(float, "Prix du stop loss", required=True)
):
    try:
        # Validation des inputs
        if capital <= 0:
            await ctx.respond("❌ Le capital doit être positif !", ephemeral=True)
            return
        if risk_percent <= 0 or risk_percent > 100:
            await ctx.respond("❌ Le pourcentage de risque doit être entre 0 et 100 !", ephemeral=True)
            return
        if entry <= 0 or stop_loss <= 0:
            await ctx.respond("❌ Les prix doivent être positifs !", ephemeral=True)
            return
        if leverage_amount < 1:
            await ctx.respond("❌ Le levier doit être au minimum 1x !", ephemeral=True)
            return
        
        # Déterminer le type de position
        is_long = stop_loss < entry
        position_type = "LONG 📈" if is_long else "SHORT 📉"
        color = discord.Color.green() if is_long else discord.Color.red()
        
        # === CALCULS AVEC LEVIER ===
        
        # Montant risqué (en $)
        risk_amount = capital * (risk_percent / 100)
        
        # Distance du stop loss (en %)
        stop_distance_percent = abs(entry - stop_loss) / entry * 100
        
        # Marge requise pour la position (sans levier, ce serait 100%)
        # Avec levier, on divise par le levier
        # Formule : Marge = (Taille Position / Levier)
        
        # Taille de position en $ (exposition totale)
        # On veut risquer X$ sur Y% de mouvement
        # Position size = Risk Amount / (Stop Distance % / 100)
        position_value = risk_amount / (stop_distance_percent / 100)
        
        # Marge réellement utilisée (avec levier)
        margin_required = position_value / leverage_amount
        
        # Quantité d'unités
        position_size = position_value / entry
        
        # Prix de liquidation approximatif
        # Pour un LONG : Liquidation = Entry - (Margin / Position Size)
        # Pour un SHORT : Liquidation = Entry + (Margin / Position Size)
        if is_long:
            liquidation_price = entry - (margin_required / position_size)
        else:
            liquidation_price = entry + (margin_required / position_size)
        
        # Distance jusqu'à liquidation (en %)
        liquidation_distance_percent = abs(liquidation_price - entry) / entry * 100
        
        # Vérifier si le stop loss est avant ou après la liquidation
        if is_long and stop_loss < liquidation_price:
            warning = "⚠️ ATTENTION : Votre stop loss est en dessous du prix de liquidation !"
        elif not is_long and stop_loss > liquidation_price:
            warning = "⚠️ ATTENTION : Votre stop loss est au-dessus du prix de liquidation !"
        else:
            warning = "✅ Stop loss correctement placé (avant liquidation)"
        
        # Vérifier si on a assez de capital
        if margin_required > capital:
            await ctx.respond(
                f"❌ **Capital insuffisant !**\n\n"
                f"Marge requise : ${margin_required:,.2f}\n"
                f"Capital disponible : ${capital:,.2f}\n\n"
                f"💡 Réduisez le levier ou augmentez votre capital.",
                ephemeral=True
            )
            return
        
        # Pourcentage du capital utilisé
        capital_used_percent = (margin_required / capital) * 100
        
        # === CRÉATION DE L'EMBED ===
        
        embed = discord.Embed(
            title="⚡ Calculateur de Position avec Levier",
            description=f"**Type : {position_type} | Levier : {leverage_amount}x**",
            color=color
        )
        
        embed.add_field(
            name="💰 Capital & Risque",
            value=f"```\nCapital total      : ${capital:,.2f}\nRisque accepté     : {risk_percent}%\nMontant à risquer  : ${risk_amount:,.2f}```",
            inline=False
        )
        
        embed.add_field(
            name="📊 Position",
            value=f"```\nExposition totale  : ${position_value:,.2f}\nMarge utilisée     : ${margin_required:,.2f} ({capital_used_percent:.1f}% du capital)\nQuantité          : {position_size:,.4f} unités```",
            inline=False
        )
        
        embed.add_field(
            name="📍 Prix",
            value=f"```\nEntrée            : ${entry:,.2f}\nStop Loss         : ${stop_loss:,.2f}\nDistance SL       : {stop_distance_percent:.2f}%```",
            inline=False
        )
        
        embed.add_field(
            name="🔥 Liquidation",
            value=f"```\nPrix liquidation  : ${liquidation_price:,.2f}\nDistance liquidation: {liquidation_distance_percent:.2f}%\n\n{warning}```",
            inline=False
        )
        
        # Calcul du P&L potentiel à différents niveaux
        # Exemple : +5%, +10%, -5%, -10%
        pnl_scenarios = []
        for percent in [10, 5, -5, -10]:
            if is_long:
                target_price = entry * (1 + percent/100)
            else:
                target_price = entry * (1 - percent/100)
            
            pnl_dollar = (target_price - entry) * position_size if is_long else (entry - target_price) * position_size
            pnl_percent = (pnl_dollar / margin_required) * 100
            
            sign = "+" if pnl_dollar >= 0 else ""
            pnl_scenarios.append(f"{sign}{percent}%: {sign}${pnl_dollar:,.2f} ({sign}{pnl_percent:.1f}%)")
        
        embed.add_field(
            name="📈 Scénarios P&L (sur la marge)",
            value=f"```\n" + "\n".join(pnl_scenarios) + "```",
            inline=False
        )
        
        # Avertissements
        warnings = []
        if leverage_amount >= 50:
            warnings.append("⚠️ Levier très élevé (≥50x) : risque de liquidation important")
        if capital_used_percent > 80:
            warnings.append("⚠️ Vous utilisez >80% de votre capital en marge")
        if liquidation_distance_percent < 5:
            warnings.append("⚠️ Prix de liquidation très proche (< 5%)")
        
        if warnings:
            embed.add_field(
                name="⚠️ Avertissements",
                value="\n".join(warnings),
                inline=False
            )
        
        embed.set_footer(text=f"💡 Avec {leverage_amount}x de levier, les gains ET les pertes sont multipliés par {leverage_amount}")
        
        await ctx.respond(embed=embed)
        
    except Exception as e:
        await ctx.respond(f"❌ Erreur lors du calcul : {str(e)}", ephemeral=True)


# ==========================================
# COMMANDE D'AIDE
# ==========================================
@bot.slash_command(
    name="help",
    description="Affiche la liste des commandes disponibles"
)
async def help_command(ctx):
    embed = discord.Embed(
        title="📚 Guide des Commandes - Trading Calculator Bot",
        description="Voici toutes les commandes disponibles pour vous aider dans vos calculs de trading",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="💰 /position",
        value="```Calcule la taille optimale de position (SPOT)\n\nParamètres:\n- capital: Votre capital total\n- risk_percent: % de risque (ex: 2)\n- entry: Prix d'entrée\n- stop_loss: Prix du stop loss```",
        inline=False
    )
    
    embed.add_field(
        name="⚡ /leverage",
        value="```Calcule une position avec LEVIER (Futures/Margin)\n\nParamètres:\n- capital: Votre capital\n- leverage: Levier (10x, 20x, 50x, 100x)\n- risk_percent: % de risque\n- entry: Prix d'entrée\n- stop_loss: Stop loss\n\nAffiche: Marge, liquidation, P&L```",
        inline=False
    )
    
    embed.add_field(
        name="⚖️ /rr",
        value="```Calcule le ratio risque/rendement\n\nParamètres:\n- entry: Prix d'entrée\n- stop_loss: Prix du stop loss\n- target: Prix cible```",
        inline=False
    )
    
    embed.add_field(
        name="📊 /dca",
        value="```Calcule le prix moyen d'achat (DCA)\n\nFormat: prix1,qty1 prix2,qty2\nExemple: 50,100 45,200 48,150```",
        inline=False
    )
    
    embed.add_field(
        name="💡 Conseils",
        value="• **SPOT**: Utilisez /position (pas de liquidation)\n• **FUTURES**: Utilisez /leverage (attention liquidation !)\n• Visez un ratio R/R ≥ 2:1\n• Levier élevé = risque élevé",
        inline=False
    )
    
    embed.set_footer(text="Bot créé pour faciliter vos calculs de trading | Utilisez avec prudence")
    
    await ctx.respond(embed=embed)



# ==========================================
# LANCER LE BOT
# ==========================================

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERREUR: Token Discord non trouvé dans .env")
        print("💡 Créez un fichier .env avec: DISCORD_TOKEN=votre_token")
    else:
        print("🚀 Démarrage du bot...")
        bot.run(token)

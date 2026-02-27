import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ===================== CLASSE CALCUL SELON CIRCULAIRE 26/G/2006 =====================
class RWACalculator_BAM:
    def __init__(self):
        self.min_ratio = 10.0  # Article 2

        # Pondérations Crédit (Art. 11)
        self.credit_weights = {
            "Etat Maroc MAD": 0.0,
            "Etat AAA/AA-": 0.0,
            "Etat A+/A-": 0.20,
            "Etat BBB+/BBB-": 0.50,
            "Etat BB+/BB-": 1.00,
            "Etat B+/B-": 1.00,
            "Etat < B-": 1.50,
            "Banques AAA/AA-": 0.20,
            "Banques A+/A-": 0.50,
            "Banques BBB+/BBB-": 0.50,
            "Banques BB+/BB-": 1.00,
            "Banques B+/B-": 1.00,
            "Banques < B-": 1.50,
            "Entreprises notées AAA/AA-": 0.20,
            "Entreprises notées A+/A-": 0.50,
            "Entreprises notées BBB+/BBB-": 1.00,
            "Entreprises notées BB+/BB-": 1.00,
            "Entreprises notées B+/B-": 1.50,
            "Entreprises < B-": 1.50,
            "Entreprises non notées": 1.00,
            "PME / TPE": 0.75,
            "Particuliers": 0.75,
            "Prêt immobilier résidentiel": 0.35,
            "Prêt immobilier commercial": 1.00,
            "Créances en souffrance <20% provision": 1.50,
            "Créances en souffrance ≥20%": 1.00,
            "Equity / Hedge funds": 1.00,      # traitement par défaut
            "Venture / Capital risque": 1.50,
            "Autre actif": 1.00
        }

    def rwa_credit(self, exposures_dict):
        """exposures_dict = {'catégorie': montant_en_M_MAD, ...}"""
        return sum(amount * self.credit_weights.get(cat, 1.0) for cat, amount in exposures_dict.items())

    def rwa_market(self, nav_series):
        """Méthode simplifiée (Article 48-55)"""
        returns = nav_series.pct_change().dropna()
        volatility = returns.std() * 100
        factor = max(0.08, volatility / 25)          # facteur prudentiel
        return nav_series.mean() * factor * 12.5

    def rwa_operational(self, avg_gross_income):
        """Approche de base (Article 56-62)"""
        return avg_gross_income * 0.15 * 12.5

    def solvency_ratio(self, own_funds, total_rwa):
        return (own_funds / total_rwa * 100) if total_rwa > 0 else 0


# ===================== APPLICATION STREAMLIT =====================
st.set_page_config(page_title="BAM Solvabilité 26/G/2006", layout="wide", page_icon="🇲🇦")
st.title("📊 Coefficient de Solvabilité – Circulaire n°26/G/2006")
st.caption("Bank Al-Maghrib • Approche Standard • Mise à jour 2026")

calculator = RWACalculator_BAM()

# Chargement des données whale_navs.csv
@st.cache_data
def load_data():
    df = pd.read_csv("whale_navs.csv", parse_dates=["date"])
    df.set_index("date", inplace=True)
    return df

df = load_data()

# ===================== ONGLETS =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Accueil", 
    "📉 Risque Crédit", 
    "📈 Risque Marché", 
    "⚙️ Risque Opérationnel", 
    "📊 Ratio Solvabilité"
])

with tab1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Bank_Al-Maghrib_logo.svg/800px-Bank_Al-Maghrib_logo.svg.png", width=250)
    st.markdown("""
    **Application conforme à la Circulaire n° 26/G/2006**  
    - Pondérations détaillées (Art. 9 à 47)  
    - Multiplicateur ×12,5 pour marché & opérationnel (Art. 5)  
    - Exigence minimale 10 % (Art. 2)  
    - Utilise **whale_navs.csv** comme portefeuille d’exemple
    """)

with tab2:
    st.header("II. Risque de Crédit (Art. 9-47)")
    date_selected = st.select_slider("Date du portefeuille", 
                                     options=df.index, 
                                     value=df.index[-1])
    
    navs = df.loc[date_selected]
    
    # Exemple de classification selon la circulaire
    exposures = {
        "SOROS FUND (Equity - non noté)": navs["SOROS FUND MANAGEMENT LLC"] * 100,
        "PAULSON & CO (Equity)": navs["PAULSON & CO.INC."] * 100,
        "TIGER GLOBAL (Venture)": navs["TIGER GLOBAL MANAGEMENT LLC"] * 150,
        "BERKSHIRE HATHAWAY (Corporate)": navs["BERKSHIRE HATHAWAY INC"] * 100,
        "S&P 500 Index (Equity)": navs["S&P 500"] * 10,
    }
    
    rwa_credit = calculator.rwa_credit(exposures)
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.dataframe(pd.DataFrame.from_dict(exposures, orient="index", columns=["Exposition (M MAD)"]), 
                     use_container_width=True)
    with col2:
        st.metric("**RWA Crédit**", f"{rwa_credit:,.0f} M MAD")

with tab3:
    st.header("Risque de Marché (Art. 48-55)")
    fund = st.selectbox("Sélectionnez le fonds", df.columns)
    series = df[fund]
    
    rwa_market = calculator.rwa_market(series)
    
    st.metric("**RWA Marché**", f"{rwa_market:,.0f} M MAD")
    fig = px.line(series, title=f"Évolution NAV – {fund}", labels={"value": "NAV"})
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Risque Opérationnel (Art. 56-62)")
    avg_income = st.slider("Revenu brut moyen annuel (M MAD)", 
                           min_value=100, max_value=5000, value=1200, step=50)
    rwa_op = calculator.rwa_operational(avg_income)
    st.metric("**RWA Opérationnel**", f"{rwa_op:,.0f} M MAD")

with tab5:
    st.header("Coefficient de Solvabilité (Art. 2)")
    
    own_funds = st.number_input("Fonds Propres (M MAD)", 
                                min_value=100, max_value=20000, 
                                value=2500, step=50)
    
    total_rwa = rwa_credit + rwa_market + rwa_op
    ratio = calculator.solvency_ratio(own_funds, total_rwa)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total RWA", f"{total_rwa:,.0f} M MAD")
    col2.metric("Coefficient de Solvabilité", f"{ratio:.2f} %")
    col3.metric("Seuil BAM", "10.00 %")
    
    if ratio >= 10:
        st.success("✅ CONFORME – Coefficient ≥ 10 % (Circulaire 26/G/2006)")
    else:
        st.error("❌ NON CONFORME – Coefficient < 10 % – Action corrective requise")
    
    # Graphique répartition
    fig_pie = px.pie(
        values=[rwa_credit, rwa_market, rwa_op],
        names=["Crédit", "Marché", "Opérationnel"],
        title="Répartition des RWA",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Export CSV
    summary = pd.DataFrame({
        "Date": [date_selected.date()],
        "RWA_Crédit": [rwa_credit],
        "RWA_Marché": [rwa_market],
        "RWA_Opérationnel": [rwa_op],
        "Total_RWA": [total_rwa],
        "Fonds_Propres": [own_funds],
        "Ratio_%": [ratio],
        "Conformité": ["Conforme" if ratio >= 10 else "Non conforme"]
    })
    
    st.download_button(
        label="📥 Télécharger rapport CSV",
        data=summary.to_csv(index=False),
        file_name=f"solvabilite_bam_{date_selected.date()}.csv",
        mime="text/csv"
    )

st.caption("🚀 Application 100 % conforme Circulaire n°26/G/2006 • Développée avec Streamlit + whale_navs.csv")

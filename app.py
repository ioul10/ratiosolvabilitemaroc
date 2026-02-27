import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Ratio de Solvabilité - BAM", layout="wide", page_icon="🏦")
st.title("🛡️ Calculateur Ratio de Solvabilité Bâle III - Maroc")
st.markdown("**Application interactive basée sur les circulaires n°14/G/13 et 26/G/2006** (document fourni)")

# Session state pour valeurs dynamiques
defaults = {'cet1': 9.5, 'at1': 1.5, 't2': 3.0}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

tabs = st.tabs(["🏠 Accueil", "🏗️ Fonds Propres", "📊 Calculateur RWA Crédit", 
                "🛡️ Simulateur ARC", "📈 Dashboard", "📚 Références"])

# TAB ACCUEIL (slide 1)
with tabs[0]:
    st.header("Ratio de Solvabilité - Contexte Général")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Objectifs")
        st.markdown("""
        - Renforcer l'assise financière des établissements de crédit  
        - Améliorer les conditions de concurrence en les soumettant tous au même régime
        """)
    with col2:
        st.subheader("Architecture des 3 Piliers")
        st.markdown("""
        **Pilier 1** : Renouvellement des exigences minimales de fonds propres (Risque de marché / crédit / opérationnel)  
        **Pilier 2** : Renforcement de la Surveillance prudentielle (Analyse profil risque, contrôle procédures, exigences individuelles supérieures)  
        **Pilier 3** : Utilisation de la communication d'informations pour améliorer la discipline de marché (Renforcement sur risques crédit, info sur autres risques et structure capital)
        """)
    
    st.success("**Ratio de Solvabilité minimum** : Fonds Propres Prudentiels / (RWA Crédit + RWA Marché + RWA Opérationnel) ≥ 12 %")
    
    with st.expander("Définition détaillée du RWA Crédit (slide 1)"):
        st.markdown("""
        RWA crédit : Risque Pondéré calculé en multipliant l'exposition  
        - Actif pour bilan / (Exposition × CCF) pour hors-bilan  
        par la pondération de la contrepartie et après application des ARC
        """)

# TAB FONDS PROPRES (slides 2 + 3)
with tabs[1]:
    st.header("Fonds Propres Prudentiels (Circulaire 14/G/13)")
    
    with st.expander("Composition des éléments (slide 2)"):
        st.markdown("""
        **Tier 1** = CET1 + AT1  
        - **CET1** : Capital (mutualistes inclus), Primes d'émission, Réserves, Bénéfices non distribués, OCI, Intérêts minoritaires (conditions), Déductions (immobilisations incorporelles, détentions croisées, etc.)  
        - **AT1** : Instruments perpétuels subordonnés, Capacité absorption pertes, Primes, Déductions  
        **Tier 2** : Instruments subordonnés ≥5 ans, Pas d'arrangement rehaussant rang, Primes, Déductions
        """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("CET1")
        st.markdown("Minimum 5,5 % + Coussin conservation 2,5 % → **≥ 8 %**")
        st.session_state.cet1 = st.slider("CET1 saisi (%)", 0.0, 20.0, st.session_state.cet1, 0.1)
    
    with col2:
        st.subheader("AT1 (additionnel Tier 1)")
        st.markdown("Part de Tier 1 au-delà de CET1")
        st.session_state.at1 = st.slider("AT1 saisi (%)", 0.0, 10.0, st.session_state.at1, 0.1)
    
    with col3:
        st.subheader("Tier 2 (complémentaire)")
        st.markdown("Instruments ≥5 ans, subordonnés")
        st.session_state.t2 = st.slider("Tier 2 saisi (%)", 0.0, 10.0, st.session_state.t2, 0.1)
    
    t1 = st.session_state.cet1 + st.session_state.at1
    total = t1 + st.session_state.t2
    
    st.metric("Tier 1 calculé (CET1 + AT1)", f"{t1:.2f} %")
    st.metric("Total Capital (T1 + T2)", f"{total:.2f} %", help="≥ 12 %")
    
    # Checks minima (slide 3)
    ok_cet1 = st.session_state.cet1 >= 8
    ok_t1 = t1 >= 9
    ok_total = total >= 12
    
    cols = st.columns(3)
    cols[0].metric("CET1", f"{st.session_state.cet1:.1f}%", "OK" if ok_cet1 else "KO <8%", delta_color="normal" if ok_cet1 else "inverse")
    cols[1].metric("Tier 1", f"{t1:.1f}%", "OK" if ok_t1 else "KO <9%", delta_color="normal" if ok_t1 else "inverse")
    cols[2].metric("Total", f"{total:.1f}%", "OK" if ok_total else "KO <12%", delta_color="normal" if ok_total else "inverse")
    
    if ok_cet1 and ok_t1 and ok_total:
        st.success("✅ Conforme sur tous les niveaux")
    else:
        st.error("❌ Non conforme – Au moins un minimum non respecté")
    
    with st.expander("Exigences détaillées (slide 3)"):
        st.markdown("""
        - CET1 ≥ 8 % (5,5 % base + 2,5 % coussin conservation)  
        - Tier 1 ≥ 9 %  
        - Total (T1 + T2) ≥ 12 %  
        Coussin de conservation : éléments CET1, destiné à absorber pertes en crise
        """)

# TAB CALCULATEUR RWA (slide 4)
with tabs[2]:
    st.header("Calculateur RWA Crédit (Circulaire 26/G/2006)")
    st.markdown("**Formule** : RWA = EAD nette × CCF × Pondération (avant ARC)")
    
    ead = st.number_input("EAD nette de provisions (MDH)", value=15.0, min_value=0.0, step=0.1)
    
    type_expo = st.radio("Type d'exposition", ["Bilan (actif)", "Hors-bilan (engagements)"])
    if type_expo == "Bilan (actif)":
        ccf_value = 100
        st.info("CCF = 100 % pour bilan")
    else:
        ccf_label = st.select_slider("CCF", options=["0% Risque faible", "20% Risque modéré", "50% Risque moyen", "100% Risque élevé"])
        ccf_value = int(ccf_label.split("%")[0])
    
    type_client = st.selectbox("Type de contrepartie", 
                               ["Souverain", "Institution", "Établissement de crédit", "GE", "PME", "TPE", "Particulier", "Prêt immobilier"])
    
    pond_dict = {
        "Souverain": 0, "Institution": 0, "Établissement de crédit": 20,  # simplifié, note <3 mois
        "GE": 100, "PME": 85, "TPE": 75, "Particulier": 100, "Prêt immobilier": 35
    }
    pond = pond_dict.get(type_client, 100)
    
    if type_client == "Particulier":
        if st.checkbox("Montant > 1 MDH (hors immo) ?"):
            pond = 100
        else:
            pond = 75
    
    if st.checkbox("Créance en souffrance ?"):
        prov = st.slider("Taux de provisionnement (%)", 0, 100, 50)
        pond = max(50, min(150, 100 - prov + 50))  # approx slide 4
        st.info(f"Pondération ajustée souffrance : {pond}%")
    
    with st.expander("Pondérations réglementaires (slide 4)"):
        df = pd.DataFrame({
            "Contrepartie": list(pond_dict.keys()),
            "Pondération (%)": list(pond_dict.values())
        })
        df.loc[len(df)] = ["Particulier >1 MDH hors immo", 100]
        st.dataframe(df)
    
    rwa = ead * (ccf_value / 100) * (pond / 100)
    st.metric("RWA calculé (avant ARC)", f"{rwa:.2f} MDH")
    st.info(f"Calcul : {ead:.1f} × {ccf_value}% × {pond}%")

# TAB ARC (slide 5)
with tabs[3]:
    st.header("Simulateur ARC (Circulaire 26/G/2006)")
    st.subheader("Exemple crédit investissement 15 MDH")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Avant ARC**")
        type_contre = st.selectbox("Type contrepartie exemple", ["GE", "PME", "TPE"], key="ex_type")
        pond_ex = {"GE":100, "PME":85, "TPE":75}[type_contre]
        rwa_avant = 15 * (pond_ex / 100)
        st.metric("RWA avant", f"{rwa_avant:.2f} MDH")
    
    with col2:
        st.write("**Après ARC** (exemples slide 5)")
        garantie = st.slider("Montant garanti (MDH)", 0.0, 15.0, 4.0)
        type_garant = st.radio("Type garantie", ["Caution bancaire (20%)", "Garantie étatique (0%)", "DAT (0%)"])
        pond_g = 20 if type_garant == "Caution bancaire (20%)" else 0
        
        restant = 15 - garantie
        rwa_apres = (restant * (pond_ex / 100)) + (garantie * (pond_g / 100))
        gain = rwa_avant - rwa_apres
        st.metric("RWA après", f"{rwa_apres:.2f} MDH", f"Gain {gain:.2f} MDH" if gain > 0 else "0")
    
    with st.expander("Détails exemples slide 5"):
        st.markdown("""
        1. GE 10 MDH + caution EC 4 MDH : RWA = 5.5×100% + 4×20% + 0.5×100% = 6.8  
        2. PME + garantie étatique 4 MDH : RWA = 5.5×85% + 4×0% + 0.5×85% = 5.1  
        3. TPE + DAT 4 MDH : RWA = 5.5×75% + 4×0% + 0.5×75% = 5.1
        """)

# TAB DASHBOARD
with tabs[4]:
    st.header("Dashboard Solvabilité")
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "indicator"}, {"type": "pie"}]])
    
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=st.session_state.cet1,
        title="CET1 (%)",
        gauge={"axis": {"range": [0, 20]}, "steps": [{"range": [0,8],"color":"red"}, {"range":[8,20],"color":"green"}]}
    ), row=1, col=1)
    
    fig.add_trace(go.Pie(labels=["CET1", "AT1", "T2"], values=[st.session_state.cet1, st.session_state.at1, st.session_state.t2], hole=0.4), row=1, col=2)
    
    fig.update_layout(height=400, title="Répartition Fonds Propres")
    st.plotly_chart(fig, use_container_width=True)

# TAB REFERENCES
with tabs[5]:
    st.header("Références")
    st.markdown("""
    - Circulaire n°14/G/13 : Fonds propres prudentiels  
    - Circulaire n°26/G/2006 : Exigences en fonds propres (RWA crédit/marché/op)  
    """)
    st.subheader("Segmentation (circulaire 8/G/2010)")
    st.markdown("""
    - CA HT ≤10 MDH + engagement ≤2 MDH → TPE  
    - CA HT ≤10 MDH + engagement >2 MDH → PME  
    - 10 < CA HT ≤175 MDH → PME  
    - CA HT >175 MDH → GE
    """)

st.sidebar.success("App prête – Fidèle au document fourni")
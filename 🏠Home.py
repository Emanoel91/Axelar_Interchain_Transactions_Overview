import streamlit as st

# --- Page Config: Tab Title & Icon ---
st.set_page_config(
    page_title="Axelar: Interchain Transactions Overview",
    page_icon="https://img.cryptorank.io/coins/axelar1663924228506.png",
    layout="wide"
)

# --- Title with Logo ---
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 15px;">
        <img src="https://img.cryptorank.io/coins/axelar1663924228506.png" alt="Axelar Logo" style="width:60px; height:60px;">
        <h1 style="margin: 0;">Axelar: Interchain Transactions Overview</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Reference and Rebuild Info ---
st.markdown(
    """
    <div style="margin-top: 20px; margin-bottom: 20px; font-size: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="https://pbs.twimg.com/profile_images/1841479747332608000/bindDGZQ_400x400.jpg" alt="Eman Raz" style="width:25px; height:25px; border-radius: 50%;">
            <span>Built by: <a href="https://x.com/0xeman_raz" target="_blank">Eman Raz</a></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# --- Info Box1 ---
st.markdown(
    """
    <div style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">
        📜Introduction
    </div>

    <div style="background-color: #eff2f6; padding: 15px; border-radius: 10px; border: 1px solid #eff2f6;">
        Axelar facilitates secure cross-chain communication within the Web3 ecosystem. It empowers dApp users to seamlessly engage with any 
        asset or application across multiple chains with a single click. Currently, Axelar supports 50 different chains.
        Interchain dApps like Prime Protocol and Mint DAO utilize Axelar's capabilities to offer cross-chain services to users, while other 
        protocols like Squid and Satellite, also powered by Axelar, facilitate cross-chain swaps among these 50 chains.
        Axelar's journey began with interchain transfers, primarily introduced through Satellite. In the summer of 2022, the utilization of 
        GMPs (General Message Passing) was introduced by Squid and other dApps such as Prime Protocol and MintDAO. This dashboard aims to provide 
        an overview of Axelar's evolution by distinguishing between Interchain Transfers and GMPs. It also offers a comprehensive overview of Squid 
        and Satellite, two major protocols powered by Axelar.
    </div>
    """,
    unsafe_allow_html=True
)

# --- Info Box2 ---
st.markdown(
    """
    <div style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">
        🧫Method
    </div>

    <div style="background-color: #eff2f6; padding: 15px; border-radius: 10px; border: 1px solid #eff2f6;">
        In this dashboard, we first provide an overview of Axelar performance, including transactions, blocks, and users. Then, 
        we dive into specific transaction types, namely interchain transactions. These transactions can be used exclusively for 
        token transfers or as general message passing (GMPs), which have a general use.
        Focusing on interchain token transfers and general message passing, we distinguish between the Satellite and Squid routers, 
        which facilitate interchain transfers: Satellite utilizes interchain transfers, and Squid utilizes GMPs.
        Finally, we focus on these two protocols and provide a comprehensive comparative analysis of them on different dimensions, 
        such as users and volume.
    </div>
    """,
    unsafe_allow_html=True
)

# --- Info Box3 ---
st.markdown(
    """
    <div style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">
        🔰Limitations
    </div>

    <div style="background-color: #eff2f6; padding: 15px; border-radius: 10px; border: 1px solid #eff2f6;">
        Axelar's integrations extend to over 50 chains, but not all of them are supported by data providers. This dashboard relies on Flipside's 
        data, which covers nearly all of the prominent EVM chains. Consequently, the analysis is centered around the top supported chains by 
        activity, including Ethereum, Binance, Arbitrum, Polygon, Optimism, Base, and Avalanche. All interchain transfers and GMPs sent from these 
        chains have been included in this analysis.
    </div>
    """,
    unsafe_allow_html=True
)

# --- Reference Info ---
st.markdown(
    """
    <div style="margin-top: 20px; margin-bottom: 20px; font-size: 16px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <img src="https://cdn-icons-png.flaticon.com/512/3178/3178287.png" alt="Reference" style="width:20px; height:20px;">
            <span>Dashboard Reference: <a href="https://flipsidecrypto.xyz/SocioAnalytica/axelar-interchain-transactions-overview-49M0W3" target="_blank">https://flipsidecrypto.xyz/SocioAnalytica/axelar-interchain-transactions-overview-49M0W3</a></span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="https://pbs.twimg.com/profile_images/1856738793325268992/OouKI10c_400x400.jpg" alt="Flipside" style="width:25px; height:25px; border-radius: 50%;">
            <span>Data Powered by: <a href="https://flipsidecrypto.xyz/home/" target="_blank">Flipside</a></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Links with Logos ---
st.markdown(
    """
    <div style="font-size: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="https://axelarscan.io/logos/logo.png" alt="Axelar" style="width:20px; height:20px;">
            <a href="https://www.axelar.network/" target="_blank">Axelar Website</a>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="https://axelarscan.io/logos/logo.png" alt="Axelar" style="width:20px; height:20px;">
            <a href="https://x.com/axelar" target="_blank">Axelar X Account</a>
        </div>
        
    </div>
    """,
    unsafe_allow_html=True
)

# --- Sidebar Footer Fixed at Bottom ---
st.markdown(
    """
    <style>
    /* Position footer at bottom of sidebar */
    [data-testid="stSidebar"]::after {
        content: "Powered by Axelar\\A Built by Eman Raz";
        white-space: pre-line;
        display: block;
        position: absolute;
        bottom: 20px;
        width: 100%;
        text-align: center;
        font-size: 14px;
        color: gray;
    }
    </style>
    """,
    unsafe_allow_html=True
)


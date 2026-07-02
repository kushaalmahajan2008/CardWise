import streamlit as st
from data import get_data
from config import SPREADSHEET_ID,keys_file
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

def format_inr(number):
    number = round(number)
    sign = "-" if number < 0 else ""
    number = abs(number)

    s = str(number)
    if len(s) <= 3:
        return f"{sign}₹{s}"

    last3 = s[-3:]
    rest = s[:-3]

    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)

    return f"{sign}₹{','.join(parts)},{last3}"


@st.cache_data()
def reward_rules():
    reward_rules=get_data(filename=keys_file,SPREADSHEET_ID=SPREADSHEET_ID,worksheet_name="Reward Rules")
    return reward_rules


def check_fields():
    cat=st.session_state["category"]
    merchant=st.session_state["merchant"]
    amt=st.session_state["amount"]
    if cat=="Select Category":
        st.session_state["error_msg"]="Please Select a Category"
    elif merchant=="Select Merchant":
        st.session_state["error_msg"]="Please Select a Merchant"
    elif amt<=0:
        st.session_state["error_msg"]="Please Enter a Valid Amount"
    else:
        return True
    return False


def clean_numeric(series, default=0):
    return pd.to_numeric(series, errors="coerce").fillna(default)


def calculate_reward_rate(df):
    df = df.copy()
    
    reward = clean_numeric(df["Reward"])
    spend = clean_numeric(df["Spend for reward"]).replace(0, np.nan)  # avoid div/0
    point_value = clean_numeric(df.get("Reward Point Value", 1))  # 1 default for cashback rows

    cashback_rate = (reward / spend) * 100
    points_rate = (reward * point_value / spend) * 100

    df["Reward Rate"] = np.where(
        df["Reward Type"].str.lower() == "cashback",
        cashback_rate,
        np.where(df["Reward Type"].str.lower() == "reward points", points_rate, np.nan)
    ).round(2)

    return df


def find_best_card():
    cat=st.session_state["category"]
    merchant=st.session_state["merchant"]
    amt=st.session_state["amount"]
    mode=st.session_state["mode"]

    reward_rules_df=reward_rules()
    reward_rules_df["Min Txn Value"] = pd.to_numeric(
        reward_rules_df["Min Txn Value"], errors="coerce"
    ).fillna(0).astype(int)

    reward_rules_df["Max Txn Value"] = pd.to_numeric(
        reward_rules_df["Max Txn Value"], errors="coerce"
    ).fillna(10**10).astype(int) 
    eligible_options = reward_rules_df[
        (reward_rules_df["Category"] == cat) &
        (reward_rules_df["Mode"].isin([mode,"All"])) &
        (reward_rules_df["Merchant"].isin([merchant, "All"])) &
        (reward_rules_df["Min Txn Value"]<=amt)&
        (reward_rules_df["Max Txn Value"]>=amt)
    ]
    eligible_options=calculate_reward_rate(eligible_options)

    return eligible_options

def rank_options(options):
    amt = st.session_state["amount"]
    
    fee = st.session_state.get("fee", 0)
    
    
    options["Net Reward"] = (
        (options["Reward Rate"] * amt / 100)
        - (options["Category Fee (in pct)"] * amt / 100)
        - fee
    )


    if "upi" in st.session_state:
        amt_for_upi=st.session_state.upi
        net_reward=amt-amt_for_upi
        options.loc[len(options)] = {'Payment Method': 'UPI', 'Reward Type': "Instant Discount",'Net Reward':net_reward,"Reward Rate":net_reward/amt*100}
    if "gift card" in st.session_state:
        discount=st.session_state["gift card"]
        net_reward=amt*discount/100
        options.loc[len(options)] = {'Payment Method': 'Gift Card', 'Reward Type': "Instant Discount",'Net Reward':net_reward,"Reward Rate":net_reward/amt*100}


    options["Effective Reward Rate"]=(
        options["Net Reward"]/amt*100
    )
    # Rank: highest net reward first
    options = options.sort_values("Net Reward", ascending=False).reset_index(drop=True)
    options["Rank"] = options.index + 1
    
    return options
        

def give_options(df,cards_per_row=3):
    st.write(df)
    rows_needed = -(-len(df) // cards_per_row)
    rank=0
    for i in range(rows_needed):
        more_cards_req=min(cards_per_row,len(df)-rank)
        cards_row=st.columns(cards_per_row)
        for col_number in range(more_cards_req):
            with cards_row[col_number].container(border=True):
                rank+=1
                row=df.loc[rank-1]
                st.markdown(f"#### #{rank} {row["Payment Method"]}")
                st.markdown("---")
                col1,_,col2=st.columns([2,0.8,2])
                col1.metric("Total Reward(₹)",value=f'₹{round(row["Net Reward"],2)}',border=True)
                col2.metric("Effective Reward Rate",value=f'{round(row["Effective Reward Rate"],2)}%',border=True)
                st.caption(f"Base Reward Considered: {row["Reward Rate"]}%")
                if "fee" in st.session_state:
                    st.markdown(f"* Fee Considered:  \n  * Category fee: {row["Category Fee (in pct)"]}%  \n  * Convinience fee: ₹{st.session_state.fee}")






def btn_clicked():
    fields_check=check_fields()
    if fields_check:
        reward_rules.clear()
        options=find_best_card()
        ranked_options=rank_options(options)
        st.session_state["results"] = ranked_options 
        st.session_state["show_results"] = True
    else:
        st.session_state["show_results"] = False




#--------------------------------------------------------------Body--------------------------------------------------------------


if "show_results" not in st.session_state:
    st.session_state["show_results"] = False
#Getting Reward Rules
reward_rules_df=reward_rules()

_,col1,_=st.columns([1,2,1])
col1.markdown("## Let's Find Best Card For Your Expense")
col1.space()
cat_options_list=reward_rules_df["Category"].unique().tolist()
# cat_options_list.insert(0,"Select Category*")
cat=col1.selectbox("Select Category",options=cat_options_list,key="category")


merchant_options_list=reward_rules_df["Merchant"].unique().tolist()
# merchant_options_list.insert(0,"Select Merchant")
merchant=col1.selectbox("Select Merchant*",options=merchant_options_list,key="merchant")


mode=col1.selectbox("Mode*",options=["Online","Offline"],key="mode")

amt=col1.number_input("Transaction Amount*",key="amount",step=1,value=100)



_,fee_col,upi_col,gift_card_col,_=st.columns([3,2,2,2,3])
fee_check=fee_col.checkbox("Include fee On Card Payments")
if fee_check:
    fee=fee_col.number_input("Fee Amount (₹)",key="fee")


upi_check=upi_col.checkbox("Include UPI Option")
if upi_check:
    upi=upi_col.number_input("Payment Amount For UPI",key="upi")

gift_card_check=gift_card_col.checkbox("Include Gift Card Option")
if gift_card_check:
    gift_card=gift_card_col.number_input("% Discount on gift card purchase",min_value=0.00,max_value=100.00,step=0.01,key="gift card")

if "error_msg" in st.session_state:
    st.warning(st.session_state.error_msg)
    del st.session_state["error_msg"]
if "success_msg" in st.session_state:
    st.success(st.session_state.success_msg)
    del st.session_state["success_msg"]
_,col1,_=st.columns([1,2,1])
btn=col1.button("Find Best Card",type="primary",on_click=btn_clicked)

if st.session_state["show_results"]:
    give_options(st.session_state.results)
    st.session_state["show_results"]=False
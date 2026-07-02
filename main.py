import streamlit as st




my_cards_page=st.Page(
    title="My Cards",
    page="pages/my_cards.py",
    icon="💳",
    default=True
)

best_cards_page=st.Page(
    page="pages/best_card.py",
    icon="🏆",
    title="Find Best Card"
)


import streamlit as st





all_pages=[my_cards_page,best_cards_page]
pg=st.navigation(all_pages,position="hidden")

with st.sidebar:
    st.markdown("# CardWise")
    st.space()
    st.page_link(my_cards_page)
    st.page_link(best_cards_page)
    st.markdown("---")
    st.markdown("CardWise v1.0  \nBuilt with ❤️ By Kushaal Mahajan")
pg.run()
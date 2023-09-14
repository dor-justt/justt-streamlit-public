import streamlit as st
from bayesian_ab_test_calculator import BayesianABTestCalculator


def main():
    st.title('Justt ABtest calculator')

    # check boxes
    a_total = st.number_input("A total", min_value=0)
    a_won = st.number_input("A won", min_value=0, max_value=a_total)
    b_total = st.number_input("B total", min_value=0)
    b_won = st.number_input("B won", min_value=0, max_value=b_total)

    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            width: 400px;
            height: 60px;
            font-size: 40px;
            display: flex;
            margin: auto;
            background-color: #006400;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    if st.button("GO!", key="go_button") and a_total is not None and a_won is not None and b_total is not None and b_won is not None:
        a_lost = a_total-a_won
        b_lost = b_total-b_won
        df, txt = BayesianABTestCalculator.run_test(a_lost, a_won, b_lost, b_won)
        st.table(df)
        st.write(txt)


if __name__ == '__main__':
    main()

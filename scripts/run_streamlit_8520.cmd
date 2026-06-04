@echo off
cd /d "%~dp0"
"C:\Users\athar\anaconda3\python.exe" -m streamlit run app.py --server.port 8520 --server.headless true >> streamlit-8520.out.log 2>> streamlit-8520.err.log

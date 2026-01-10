Quick start services guide.

1.  cd D:\AETHERA_2.0

2. Frontend: (opens in a new window-teminal)

    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\AETHERA_2.0; python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8001 --reload"

3. Backend:(opens in a new window-teminal)

    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\AETHERA_2.0\frontend; python -m streamlit run app.py"

4. Start docker manually

5. Celery worker:

    $env:PYTHONPATH = 'D:\AETHERA_2.0'
    
    python -m celery -A backend.src.workers.celery_app worker --pool=solo --loglevel=info

be:
	cd api && uvicorn server:app --host 0.0.0.0 --port 8000 --reload
fe:
	cd web && npm run dev
recover:
	cd api && python -m recovery.recovery --assistants --sessions --files --out dumps
fmt:
	black api || true
check:
	echo "Use 'make be' and 'make fe' to run; 'make recover' to dump from DR"
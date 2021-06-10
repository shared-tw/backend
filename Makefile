dev-env:
	python -m venv venv || true
	source venv/bin/activate \
	&& pip install -r requirements-dev.txt \
	&& pre-commit install


local-db:
	if [ ! -d pg-data ]; then mkdir pg-data; fi
	docker run -d --name shared-tw_db --rm  -e POSTGRES_DB=sharedtw -e POSTGRES_PASSWORD=password -v $$PWD/pg-data:/var/lib/postgresql/data:Z,shared -p 127.0.0.1:5432:5432 postgres:13

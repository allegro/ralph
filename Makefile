install: contributors-data
	bundle install

serve:
	bundle exec jekyll serve

dev:
	bundle exec jekyll serve --incremental --livereload

contributors-data:
	curl https://api.github.com/repos/allegro/ralph/contributors -o _data/contributors.json
	python3 get_core_team_data.py

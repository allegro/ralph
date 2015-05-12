.PHONY: flake
test:
	ralph test --settings=ralph.settings.test

flake: clean
	flake8 --exclude=migrations,tests,doc,www,settings.py --ignore=E501 src/ralph

clean:
	find . -name '*.pyc' -exec rm -rf {} \;

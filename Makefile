quicktest:
	DJANGO_SETTINGS_PROFILE=test-ralph ralph test ralph --failfast 2> /dev/null

flake:
	flake8 --exclude=migrations,tests,doc,www,settings.py --ignore=E501 src/ralph

runserver:
	ralph runserver

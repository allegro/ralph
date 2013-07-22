quicktest:
	DJANGO_SETTINGS_PROFILE=test ralph test ralph --failfast 2> /dev/null

runserver:
	ralph runserver

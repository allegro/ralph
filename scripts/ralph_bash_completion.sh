# Based on https://github.com/django/django/blob/master/extras/django_bash_completion

# To activate run (od add to .profile):
# source <ralph_path>/ralph_bash_completion.sh

_ralph_completion()
{
    COMPREPLY=( $( COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   DJANGO_AUTO_COMPLETE=1 $1 ) )
}
complete -F _ralph_completion -o default ralph dev_ralph test_ralph



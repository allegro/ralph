# FAQ

## I've got `ImproperlyConfigured` error after attaching extra view to admin class

Single extra view class **CANNOT** be reused in multiple admin sites. To use it in multiple admin sites create separated class of extra view:

```django
class MyView(RalphDetailViewAdmin):
    icon = 'chain'
    ...

class MyView2(MyView):
    pass
```

Then use it in your admin:

```django
@register(MyModel)
class MyAdmin(RalphAdmin):
    change_views = [MyView]

@register(MyModel2)
class MyAdmin2(RalphAdmin):
    change_views = [MyView2]
```

Attachments app is an example usage of this mechanism - for every admin site that
uses `AttachmentsMixin`, there is created separated class of `AttachmentsView`.


## how to see asset boxes in front dashboard or I've got  `NoReverseMatch at / Reverse for 'back_office_backofficeasset_transition_bulk'`

By default, when you visit front dashboard, you see no "Hardware loan", "Hardware release" nor "Hardware return" boxes. They should be visible only when you have assigned asset in back office, which is in 'in progress' or 'in use' state. However - when you add such item on empty database, you will ecounter error: 

```
NoReverseMatch at /
Reverse for 'back_office_backofficeasset_transition_bulk' with arguments '(None,)' and keyword arguments '{}' not found. 1 pattern(s) tried: ['back_office/backofficeasset/transition/(?P<transition_pk>\\d+)$']
```

To overcome this problem, you may do following steps:

*(assumptions: empty database, assets will be assigned to user **r2** by user **root**)*

* dev_ralph migrate
* make menu (if you didn't do it already)
* dev_ralph createsuperuser --email='foo@bar.pl' --username=root
* dev_ralph createsuperuser --email='foo@bar.pl' --username=r2 (or create user in by root in web)
* dev_ralph runserver
* http://localhost:8000/transitions/transitionmodel/1/ -> [add another transition]
 * source: 'in progress'
 * destination: 'in use'
 * -> [Save]
 * run `dev_ralph dbshell` and run following query to check what's id of newly created transition:
    
    ```
    mysql> SELECT * FROM transitions_transition;
    +----+------+--------+--------+----------+--------------------+--------------------+---------------+-------------+
    | id | name | source | target | model_id | async_service_name | run_asynchronously | template_name | success_url |
    +----+------+--------+--------+----------+--------------------+--------------------+---------------+-------------+
    |  1 | foo  | ["2"]  | 4      |        1 |                    |                  0 |               | NULL        |
    +----+------+--------+--------+----------+--------------------+--------------------+---------------+-------------+
    1 row in set (0,00 sec)
    ```
* write following lines into settings/dev.py:


```
ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['RETURN_TRANSITION_ID'] = <id of transition>
ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['LOAN_TRANSITION_ID'] = <id of transition>
ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['TRANSITION_ID'] = <id of transition>
```

In this case, id of transition is `1`. 

* go to http://localhost:8000/back_office/backofficeasset/add/ and create asset with
 * status: in progress
 * assigned to user: r2
 * owner: r2
 * click [save]
* repeat adding step with statuses 'return in progress' and 'loan in progress'
* now open incognito mode and login to http://localhost:8000/ as user=r2



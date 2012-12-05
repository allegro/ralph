# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase, LiveServerTestCase
from ralph.ui.tests.helper import login_as_su
from selenium.webdriver.firefox.webdriver import WebDriver

class MySeleniumTests(TestCase, LiveServerTestCase):
    def create_user(self):
        self.client = login_as_su(login=False)

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(MySeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MySeleniumTests, cls).tearDownClass()

    def test_login(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('ralph')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('ralph')
        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
        url = '/ui/search/info/'
        view = self.client.get(url, follow=True)
        self.assertEqual(view.status_code, 200, 'Hey, we need Selenium!')

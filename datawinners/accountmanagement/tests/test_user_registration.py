from celery.tests.case import MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from mock import patch
from datawinners.accountmanagement.forms import UserProfileForm
from datawinners.accountmanagement.mobile_number_validater import MobileNumberValidater
from datawinners.accountmanagement.models import Organization
from datawinners.accountmanagement.organization_id_creator import OrganizationIdCreator


class TestUserRegistration(TestCase):
    def test_user_email_validation_should_be_case_insensitive(self):
        User.objects.create_user('User@user.com', 'User@user.com', 'password')
        trial_organization = Organization(name='test_org_for_trial_account',
                                  sector='PublicHealth', address='add',
                                  city='Pune', country='IN',
                                  zipcode='411006', account_type='Basic',
                                  org_id=OrganizationIdCreator().generateId(),
                                  status='Activated')
        trial_organization.save()
        mobile_validater = MobileNumberValidater(trial_organization, '788522', 'no_id')
        mobile_validater.validate = MagicMock(return_value=(True, ''))
        with patch("datawinners.accountmanagement.forms.MobileNumberValidater") as validater:
            with patch("datawinners.accountmanagement.forms.datasender_count_with") as datasender_count_with_mock:
                validater.return_value = mobile_validater
                form = UserProfileForm(organization=trial_organization,
                                       data={'title': 'manager', 'full_name': 'user one', 'username': 'uSER@User.com',
                                             'mobile_phone': '7889522', 'role': 'Project Managers'})

                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors['username'],['This email address is already in use. Please supply a different email address'])
                mobile_validater.validate.assert_called_with()
                datasender_count_with_mock.return_value = 0
                
                #Role validation
                form = UserProfileForm(organization=trial_organization,
                               data={'title': 'manager', 'full_name': 'user one', 'username': 'uSER1@User.com',
                                     'mobile_phone': '7889522'})

                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors['role'],['This field is required.'])
                
                #Valid form
                form = UserProfileForm(organization=trial_organization,
                               data={'title': 'manager', 'full_name': 'user one', 'username': 'uSER1@User.com',
                                     'mobile_phone': '7889522', 'role': 'Extended Users'})
                self.assertTrue(form.is_valid())
                self.assertEqual(form.clean_username(),'user1@user.com')

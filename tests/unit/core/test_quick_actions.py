import pytest
from django.urls import reverse
from core.models import UserProfile
from django.contrib.auth.models import User
from django.test import Client

@pytest.mark.django_db
def test_quick_actions_visibility_for_staff():
    client = Client()
    user = User.objects.create_user(username='teststaff', password='password123', is_staff=True)
    profile = user.profile
    profile.role = 'Director'
    profile.can_use_ftl = False
    profile.save()
    
    client.force_login(user)
    
    response = client.get(reverse('operations_center'))
    assert response.status_code == 200
    
    dashboard = response.context['dashboard']
    quick_actions = dashboard.quick_actions
    
    # We should have all quick actions appended, but their enabled status should vary
    ftl_action = next((a for a in quick_actions if a.title == "FTL"), None)
    assert ftl_action is not None, "FTL action should be present"
    assert ftl_action.enabled is False, "FTL action should be disabled for this user"

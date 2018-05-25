from django.db import IntegrityError

def create_user_company(user):
    """Create company for the user

    Arguments:
        user {people.User} -- user object

    Returns:
        company {people.Company} object
    """
    data = {
        'name': user.get_full_name() or user.username,
        'slug': user.username,
        'users': user.__class__.objects.filter(pk=user.pk),
    }
    for i in range(10):
        try:
            company = user.company_set.create(**data)
            company.users.add(user)
            return company
        except IntegrityError:
            data['name'] = '%s-%s' % (data['name'].split('-')[0], i)
            data['slug'] = '%s-%s' % (data['slug'].split('-')[0], i)            
    return None

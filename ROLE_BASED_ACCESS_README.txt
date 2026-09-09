NIBE Investor CMS - Role Based Access
=====================================

Roles
-----
ADMIN    → Full system (Dashboard, Documents, Upload, Audit Log, Employees)
EMPLOYEE → Only Dashboard, Documents, Upload Document
CLIENT   → Public website only (https://www.nibelimited.com) — no dashboard

Employees page (Admin only)
---------------------------
- Sidebar → Employees
- List all users with Role + Status
- Add User (Employee ID, name, email, role, password)
- Edit User (change name, email, role, password, active)
- Activate / Deactivate
- Delete user
- Roles when creating/editing: ADMIN | EMPLOYEE | CLIENT

Setup steps
-----------
1. Unzip this folder
2. Activate your virtualenv / install Django if needed
3. Run:
     python manage.py migrate
4. Make your user Admin:
     python manage.py shell

     from django.contrib.auth.models import User
     u = User.objects.get(username='YOUR_USERNAME')
     u.profile.role = 'ADMIN'
     u.profile.save()
     print(u.username, '→', u.profile.role)

5. Run server:
     python manage.py runserver

Notes
-----
- New users get role EMPLOYEE by default (Profile model)
- Client users who login are redirected to www.nibelimited.com
- Only Admin sees Audit Log and Employees menus
- Backend APIs are also protected by role_required decorator

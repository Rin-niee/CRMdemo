import os

{
    'NAME': "crm_db",
    'USER': "crm_user",
    'PASSWORD': "securepassword",
    'HOST': "db",
    'PORT': "5432"
}



for var in ["NAME", "USER", "PASSWORD", "HOST"]:
    print(var, repr(var))
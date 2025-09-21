from enums import Role

class User:
    """
        This class is the data needed for our user and which will be installed,
        It won't differ even if the user is parent, child.
    """
    def __init__(self, phone, uid, name, password,fa =0,lu = None, role=Role.USER,fm = None, wid = None):
        self._name = name
        self._phone_number = phone
        self._national_id = uid
        self._password = password
        self._role:Role = role
        self._walletid = wid
        self._family_id = fm 
        self._failed_attempts = fa
        self._lock_until = lu        
    @property
    def phone_number(self):
        return self._phone_number        
    @property
    def national_id(self):
        return self._national_id       
    @property
    def name(self):
        return self._name        
    @property
    def role(self):
        return self._role        
    @property
    def password(self):
        return self._password        
    @property
    def wallet(self):
        return self._walletid        
    @property
    def family_id(self):
        return self._family_id        
    @property
    def failed_attempts(self):
        return self._failed_attempts         
    @wallet.setter
    def wallet(self, val):
        if self._walletid == None:
            self._walletid = val
    @family_id.setter
    def family_id(self,val):
        if self._family_id == None:
            self._family_id = val
        else:
            raise ValueError("You already have a family wallet")
    @failed_attempts.setter
    def failed_attempts(self,val):
        self._failed_attempts = val

class UserSession:
    _instance = None
    _current_user = None    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)
        return cls._instance        
    @classmethod
    def set_user(cls, user):
        cls._current_user = user
        
    @classmethod
    def get_user(cls):
        return cls._current_user
        
    @classmethod
    def clear_user(cls):
        cls._current_user = None

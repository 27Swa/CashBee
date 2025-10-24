from enum import Enum

class PaymentType(Enum):
    """
        The system has main payments operations which are: 
        send, recieve, donate, bill pay
    """
    SEND = "Send"
    DONATE = "Donate"
    BILL_PAY = "Bill Pay"

class BillOrganization(Enum):
    """
        Bill Organizations contains Gas, Water, Electricity 
    """
    GAS = "Gas"
    WATER = "Water"
    ELECTRICITY = "Electricity"

class CharityOrganization(Enum):
    """
        Charity Organizations in the system at this time
    """
    MISR_EL_KHEIR = "Misr El Kheir Foundation"
    RESALA = "Resala Charity Organization"
    FOOD_BANK = "Egyptian Food Bank"
    MAGDI_YACOUB = "Magdi Yacoub Heart Foundation"
    HOSPITAL_57357 = "57357 Children's Cancer Hospital Foundation"
    BAHEYA = "Baheya Foundation"
    COPTIC_ORTHODOX = "Coptic Orthodox"
    RED_CRESCENT = "Egyptian Red Crescent"

class Role(Enum):
    """
        Users role
    """
    PARENT = "Parent"
    CHILD = "Child"
    USER = "User"

class TransactionLimits(Enum):
    """
        For any transaction there are limits for daily, weekly, monthly limits
    """
    PER_OPERATION_LIMIT = 500
    DAILY_LIMIT = 1500
    WEEKLY_LIMIT = 10500
    MONTHLY_LIMIT = 315000

class CollectionMoneyOptions(Enum):
    """Different Users and how to recharge their wallet"""
    PARENT = ['User', 'Parent','Credit Card'] 
    USER = ['User', 'Credit Card',"Parent"] 
    CHILD = "Parent" 

class BillStatus(Enum):
    UNPAID = 'UNPAID'
    PAID = 'PAID'
class RequestStatus(Enum):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
class RequestType(Enum):
    COLLECT_MONEY = "Collect Money"
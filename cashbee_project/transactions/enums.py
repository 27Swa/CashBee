from enum import Enum

class PaymentType(Enum):
    """
        The system has main payments operations which are: 
        send, recieve, donate, bill pay
    """
    SEND = "Send"
    #RECEIVE = "Receive"
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
    USER = ['User', 'Credit Card'] 
    CHILD = "Parent" 

class AppllicationDisplay(Enum):
    STARTING_APPLICATION = "\n=== CashBee - Family Wallet Management ==="
    OPERATION_CANCELLED = "\nOperation cancelled."
    INVALID_OPERATIION = "\nInvalid option. Please try again."
    INVALID_TRANSCTION = "Invalid transaction type"
    CLOSING_APPLICATION = "\nThanks for using CashBee!" 
    SELECTING_OPTION = "Please choose an option: "
    GET_USER_MESSAGE = "1. Register\n2. Login\n3. Exit\n"
    Registration = "\n--- Registration ---"
    LOGIN = "\n--- Login ---"
    PHONE_NUMBER = "Phone number: "
    NATIONAL_ID = "National ID: "
    NAME = "Full name (First Last): "
    PASSWORD = "Password: "
    INITIAL_SPENDING_LIMIT = "Initial spending limit: "
    MAIN_OPERATIONS_APPLIED = "1. View Wallet\n2. " \
    "Make Transaction\n3. View Transaction History\n4. " \
    "Change Role"
    PARENTOPERATIONS = "5. Family Wallet Operations\n"
    LOGOUT = "Logout"
    LOGOUTMSG = "Logged out successfully!"
    MAKE_TRANSACTION = "\n--- Make Transaction ---\n1. Send Money\n" \
    "2. Collect Money\n3. Donate to Charity\n4. Pay Bill"
    CHANGE_RULE_BLOCK = "\n--- Change Role ---\nAvailable roles:\n1. User\n2. Parent"
    SELECTING_NEW_RULE = "Choose new role: "
    FAMILY_BLOCK =  "\n--- Family Wallet Operations ---\n1. Add Family Member\n2. View Member Info\n3. Set Spending Limit" \
    "\n4. View Member Transaction History\n5. View All Members Transaction History" \
    "\n6. List All Members Data\n7. List All Children\n8. Back to Main Menu"
class BillStatus(Enum):
    UNPAID = 'UNPAID'
    PAID = 'PAID'
class RequestStatus(Enum):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
class RequestType(Enum):
    COLLECT_MONEY = "Collect Money"
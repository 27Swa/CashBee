from Validations import PhoneValidationStrategy, ValidatorContext
from data import *
from person import *
from person_handling import FamilyFacade, RegistrationFacade, RoleManager, UserHandling
from postgres import PostgresSQl
from enums import BillOrganization, CharityOrganization, PaymentType, RequestType, Role
from AppllicationDisplay import *
from mappers import *
from pay import *

def main():
    # Initialize components
    db_handler = PostgresSQl()
    registration = RegistrationFacade(db_handler)
    user_session = UserSession()
    
    while True:
        print(STARTING_APPLICATION)
        if user_session.get_user() is None:
            print(GET_USER_MESSAGE)            
            try:
                choice = input(SELECTING_OPTION).strip()
            except (EOFError, KeyboardInterrupt):
                print(INVALID_OPERATIION)
                              
            if choice == "1":
                # Registration use case
                print(Registration)
                try:
                    phone = input(PHONE_NUMBER).strip()
                    national_id = input(NATIONAL_ID).strip()
                    name = input(NAME).strip()
                    password = input(PASSWORD).strip()                
                    user = User(phone,national_id,name, password,Role.USER)       
                    result = registration.register_user(user)
                    print(result)
                except (EOFError, KeyboardInterrupt):
                    print(OPERATION_CANCELLED)
                    
            elif choice == "2":
                # Login use case
                print(LOGIN)
                try:
                    phone = input(PHONE_NUMBER).strip()
                    password = input(PASSWORD).strip()                
                    result = registration.login_user(phone, password)
                    print(result)                    
                except (EOFError, KeyboardInterrupt):
                    print(OPERATION_CANCELLED)                    
            elif choice == "3":
                print(CLOSING_APPLICATION)
                break
            else:
                print(INVALID_OPERATIION)
        else:
            current_user = user_session.get_user()
            print(f"Welcome, {current_user.name} ({current_user.role})!")
            print(MAIN_OPERATIONS_APPLIED)
            if current_user.role == Role.PARENT:
                print(PARENTOPERATIONS+"6. "+LOGOUT)
            else:
                print("5. "+LOGOUT)
            try:
                choice = input(SELECTING_OPTION).strip()
            except (EOFError, KeyboardInterrupt):
                print(INVALID_OPERATIION)
                continue
            if choice == "1":
                print(WalletRepresentation.display(current_user.wallet))
            elif choice == "2":
                print(MAKE_TRANSACTION)

                try:
                    tx_choice = input("Choose transaction type: ").strip()
                    amount = float(input("Amount: ").strip())

                    if tx_choice == "1":
                        # Send money use case
                        recipient_phone = input("Recipient phone number: ").strip()

                        # Validate recipient phone
                        phone_validator = ValidatorContext(PhoneValidationStrategy())
                        if not phone_validator.validate(recipient_phone):
                            print(f"❌ {phone_validator.get_error()}")
                            continue

                        # Check if recipient exists
                        recipient = QueryHandling.retrieve_data('User_',UserMapper,'','phone_number = %s',(recipient_phone,))
                        if recipient:
                            # Create transaction operation
                            tx_operation = TransactionOperation(current_user,recipient)
                            result = tx_operation.execute_transaction(PaymentType.SEND, amount)
                            print(result)
                        else:
                            print("Recipient not found")

                    elif tx_choice == "2":
                        # Receive money use case (simplified - usually triggered by sender)
                        # Check if recipient exists
                        # Send money use case
                        recipient_phone = input("Sender phone number: ").strip()

                        # Validate recipient phone
                        phone_validator = ValidatorContext(PhoneValidationStrategy())
                        if not phone_validator.validate(recipient_phone):
                            print(f"❌ {phone_validator.get_error()}")
                            continue
                        recipient = QueryHandling.retrieve_data('User_',UserMapper,'','phone_number = %s',(recipient_phone,))
                        if recipient:
                            # Create transaction operation
                            tx_operation = CollectMoney(current_user,amount,recipient)
                            result = tx_operation.execute(RequestType.COLLECT_MONEY)
                            print(result)
                        else:
                            print("Recipient not found")

                    elif tx_choice == "3":
                        # Donate to charity use case
                        print("Available charities:")
                        charities = list(CharityOrganization)
                        for i, charity in enumerate(charities, 1):
                            print(f"{i}. {charity}")

                        charity_choice = int(input("Choose charity: ").strip()) - 1
                        if 0 <= charity_choice < len(charities):
                            selected_charity = charities[charity_choice]
                            tx_operation = TransactionOperation(current_user,db_handler)
                            result = tx_operation.execute_transaction(PaymentType.DONATE, amount, selected_charity)
                            print(result)
                        else:
                            print("❌ Invalid charity selection")

                    elif tx_choice == "4":
                        # Pay bill use case
                        print("Available bill organizations:")
                        orgs = list(BillOrganization)
                        for i, org in enumerate(orgs, 1):
                            print(f"{i}. {org}")

                        org_choice = int(input("Choose organization: ").strip()) - 1
                        if 0 <= org_choice < len(orgs):
                            selected_org = orgs[org_choice]
                            tx_operation = TransactionOperation(current_user,db_handler)
                            result = tx_operation.execute_transaction(PaymentType.BILL_PAY, amount, selected_org)
                            print(result)
                        else:
                            print("❌ Invalid organization selection")

                    else:
                        print(INVALID_TRANSCTION)

                except (ValueError, EOFError, KeyboardInterrupt):
                    print(INVALID_OPERATIION)

            elif choice == "3":
                # View Transaction History use case
                print(UserHandling.get_user_transactions(current_user))

            elif choice == "4":
                # Change Role use case
                print(CHANGE_RULE_BLOCK)
                try:
                    role_choice = input(SELECTING_NEW_RULE).strip()
                    if role_choice == "1":
                        role = Role.USER
                    elif role_choice == "2":
                        role = Role.PARENT
                    else:
                        print("❌ Invalid role selection")
                        continue
                    result = RoleManager.change_user_role(current_user, role, db_handler)
                    print(result)

                except (EOFError, KeyboardInterrupt):
                    print(OPERATION_CANCELLED)
            elif choice == "5":
                if current_user.role == Role.PARENT:
                    # Family Wallet Operations use case (for parents only)
                    family_ops = FamilyFacade(user_session)
                    if not current_user.family_id:
                        print("No family wallet found. Creating one...")
                        fname = input("Enter family name: ").strip()
                        family_ops.create_family(fname)
                    print(FAMILY_BLOCK)
                    try:
                        family_choice = input("Choose option: ").strip()
                        if family_choice == "1":
                            # Add family member - enhanced to handle both existing and new users
                            print("\n--- Add Family Member ---")
                            # Add existing user
                            member_phone = input(PHONE_NUMBER).strip()
                            member_name = input(NAME).strip()
                            member_nid = input(NATIONAL_ID)
                            member_password = input(PASSWORD)
                            initial_limit = float(input(INITIAL_SPENDING_LIMIT).strip())
                            user = User(member_phone,member_nid,member_name, member_password,role=Role.CHILD)       
                            result = family_ops.create_child_account(user,maxlimit=initial_limit)
                            print(result)

                        elif family_choice == "2":
                            # View member info
                            member_phone = input(PHONE_NUMBER).strip()
                            info = family_ops.get_member_info(member_phone)
                            print(info)

                        elif family_choice == "3":
                            # Set spending limit
                            member_phone = input(PHONE_NUMBER).strip() 
                            new_limit = float(input("New max limit: ").strip())
                            result = family_ops.set_max_limit(member_phone, new_limit)
                            print(result)

                        elif family_choice == "4":
                            # View member transaction history
                            member_phone = input(PHONE_NUMBER).strip()
                            result = family_ops.see_transactions(member_phone)
                            print(result)

                        elif family_choice == "5":
                            # View all members transaction history
                            res = family_ops.see_all_children_history()
                            print(res)

                        elif family_choice == "6":
                            # List all members
                            members_list = family_ops.get_family_details()
                            print(members_list)
                        elif family_choice == "7":
                            # list all children 
                            children = family_ops.get_children_details()
                            print(children)                           
                        elif family_choice == "8":
                            # back to main menu
                            continue
                        else:
                            print("Invalid option")
                    except (ValueError, EOFError, KeyboardInterrupt):
                        print(INVALID_OPERATIION)
                else:
                    # Logout for non-parent users
                    user_session.clear_user()
                    print(LOGOUTMSG)        
            elif choice == "6" and current_user.role == Role.PARENT:
                # Logout use case for parents
                user_session.clear_user()
                print(LOGOUTMSG)

            else:
                print(INVALID_OPERATIION)
if __name__ == "__main__":
    main()